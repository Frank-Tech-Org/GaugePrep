import hashlib
import json
import time
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

from asr_benchmark.engines import Engine, EngineError, Transcript, Word

# Statuses that mean the account, not the clip: stop the engine at the first one.
STOP_STATUSES = frozenset({401, 402, 403, 429})
RETRIES = 2
# Fraction of each free allowance left untouched for the owner's later checks.
RESERVE = 0.30
# Minutes assumed for a clip whose length is unknown (Common Voice averages about 5 s).
UNKNOWN_CLIP_MINUTES = 10 / 60
PROGRESS_EVERY = 10


def options_digest(settings: Mapping[str, Any] | None) -> str:
    return hashlib.sha256(
        json.dumps(settings or {}, sort_keys=True).encode()
    ).hexdigest()[:8]


class EngineStopped(EngineError):
    """The engine must not be called again: quota, rate limit, bad key or budget."""


class Guard:
    """Disk cache, retry cap, stop on quota errors and a usage log for paid engines."""

    def __init__(
        self,
        cache_dir: Path,
        allowance_minutes: Mapping[str, float],
        minutes_by_path: Mapping[str, float],
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.cache_dir = cache_dir
        self.allowance = allowance_minutes
        self.minutes_by_path = minutes_by_path
        self.sleep = sleep
        self.log = cache_dir / "usage.jsonl"
        self.stopped: dict[str, str] = {}
        self.used = self._load_used()
        self.calls: dict[str, int] = {}

    def _load_used(self) -> dict[str, float]:
        used: dict[str, float] = {}
        if self.log.exists():
            for line in self.log.read_text().splitlines():
                row = json.loads(line)
                if not row["cached"]:
                    used[row["engine"]] = used.get(row["engine"], 0.0) + row["minutes"]
        return used

    def budget(self, engine: str) -> float:
        return self.allowance.get(engine, 0.0) * (1 - RESERVE)

    def wrap(
        self, engine: Engine, model: str, settings: Mapping[str, Any] | None = None
    ) -> Engine:
        """Cache and cap `engine`; `settings` (request options) are part of the key."""
        options = options_digest(settings)
        return replace(
            engine, transcribe=lambda path: self._call(engine, model, options, path)
        )

    def _cache_file(self, engine: str, model: str, options: str, path: Path) -> Path:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:24]
        return self.cache_dir / engine / model / f"{digest}-{options}.json"

    def charge(self, engine: str, clip: str, minutes: float) -> None:
        """Count audio sent outside `wrap` (the streaming pass) against the cap."""
        self._check_budget(engine, minutes)
        self._log(engine, "stream", clip, minutes, cached=False)

    def _log(
        self, engine: str, model: str, clip: str, minutes: float, cached: bool
    ) -> None:
        row = {
            "engine": engine,
            "model": model,
            "clip": clip,
            "minutes": round(minutes, 4),
            "cached": cached,
        }
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with self.log.open("a") as handle:
            handle.write(json.dumps(row) + "\n")
        if not cached:
            self.used[engine] = self.used.get(engine, 0.0) + minutes
            self.calls[engine] = self.calls.get(engine, 0) + 1
            calls = self.calls[engine]
            if calls % PROGRESS_EVERY == 0:
                print(self.usage_line(engine), flush=True)

    def usage_line(self, engine: str) -> str:
        return (
            f"usage {engine}: {self.used.get(engine, 0.0):.1f} of "
            f"{self.budget(engine):.0f} budgeted minutes "
            f"({self.allowance.get(engine, 0.0):.0f} free, {RESERVE:.0%} kept back)"
        )

    def _check_budget(self, name: str, minutes: float) -> None:
        if name in self.stopped:
            raise EngineStopped(self.stopped[name])
        if self.used.get(name, 0.0) + minutes > self.budget(name):
            self.stopped[name] = f"{name}: usage budget reached"
            raise EngineStopped(self.stopped[name])

    def _call(self, engine: Engine, model: str, options: str, path: Path) -> Transcript:
        name = engine.name
        if name in self.stopped:
            raise EngineStopped(self.stopped[name])
        cache = self._cache_file(name, model, options, path)
        if cache.exists():
            data = json.loads(cache.read_text())
            self._log(name, model, path.name, 0.0, cached=True)
            return Transcript(
                data["text"], tuple(Word(**w) for w in data["words"]), data["seconds"]
            )
        minutes = self.minutes_by_path.get(str(path), UNKNOWN_CLIP_MINUTES)
        transcript = self._attempt(engine, model, path, minutes)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps(
                {
                    "text": transcript.text,
                    "words": [w.__dict__ for w in transcript.words],
                    "seconds": transcript.seconds,
                }
            )
        )
        return transcript

    def _attempt(
        self, engine: Engine, model: str, path: Path, minutes: float
    ) -> Transcript:
        failures = 0
        while True:
            self._check_budget(engine.name, minutes)
            try:
                transcript = engine.transcribe(path)
            except EngineError as exc:
                if exc.status in STOP_STATUSES:
                    self.stopped[engine.name] = f"{engine.name}: stopped, {exc}"
                    raise EngineStopped(self.stopped[engine.name]) from exc
                # Every attempt that reached the provider may be billed.
                self._log(engine.name, model, path.name, minutes, cached=False)
                transient = exc.status is None or exc.status >= 500
                if not transient or failures >= RETRIES:
                    raise
                failures += 1
                self.sleep(2.0 * failures)
            else:
                self._log(engine.name, model, path.name, minutes, cached=False)
                return transcript
