import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Seconds before one provider request gives up.
REQUEST_TIMEOUT = 120


class EngineError(RuntimeError):
    pass


@dataclass(frozen=True)
class Word:
    text: str
    start: float | None
    end: float | None
    confidence: float | None


@dataclass(frozen=True)
class Transcript:
    text: str
    words: tuple[Word, ...]
    seconds: float


@dataclass(frozen=True)
class Engine:
    name: str
    key_env: str | None
    price_per_hour_usd: float | None
    price_note: str
    transcribe: Callable[[Path], Transcript]


def _post(url: str, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(
        url, data=body, headers=dict(headers), method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:  # noqa: S310  # fixed https provider URLs
            payload: dict[str, Any] = json.load(response)
            return payload
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise EngineError(f"{url} answered {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise EngineError(f"{url} unreachable: {exc}") from exc


def _multipart(
    fields: Mapping[str, str], file_field: str, path: Path
) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
            ).encode()
        )
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    head = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
        f'filename="{path.name}"\r\nContent-Type: {mime}\r\n\r\n'
    )
    parts += [head.encode(), path.read_bytes(), f"\r\n--{boundary}--\r\n".encode()]
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def optional_float(value: Any) -> float | None:
    return float(value) if isinstance(value, int | float) else None


def deepgram(path: Path) -> Transcript:
    url = "https://api.deepgram.com/v1/listen?model=nova-3&language=fr&punctuate=false&smart_format=false"
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    headers = {
        "Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}",
        "Content-Type": mime,
    }
    started = time.perf_counter()
    data = _post(url, path.read_bytes(), headers)
    seconds = time.perf_counter() - started
    best = data["results"]["channels"][0]["alternatives"][0]
    words = tuple(
        Word(
            w["word"],
            optional_float(w.get("start")),
            optional_float(w.get("end")),
            optional_float(w.get("confidence")),
        )
        for w in best.get("words", [])
    )
    return Transcript(best.get("transcript", ""), words, seconds)


def elevenlabs_scribe(path: Path) -> Transcript:
    fields = {
        "model_id": os.environ.get("ELEVENLABS_STT_MODEL", "scribe_v3"),
        "language_code": "fra",
        "timestamps_granularity": "word",
        "tag_audio_events": "false",
        "no_verbatim": "false",
    }
    body, content_type = _multipart(fields, "file", path)
    headers = {
        "xi-api-key": os.environ["ELEVENLABS_API_KEY"],
        "Content-Type": content_type,
    }
    started = time.perf_counter()
    data = _post("https://api.elevenlabs.io/v1/speech-to-text", body, headers)
    seconds = time.perf_counter() - started
    words = tuple(
        Word(
            w["text"],
            optional_float(w.get("start")),
            optional_float(w.get("end")),
            optional_float(w.get("logprob")),
        )
        for w in data.get("words", [])
        if w.get("type") == "word"
    )
    return Transcript(data.get("text", ""), words, seconds)


def _get(url: str, headers: Mapping[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=dict(headers), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:  # noqa: S310  # fixed https provider URLs
            payload: dict[str, Any] = json.load(response)
            return payload
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise EngineError(f"{url} answered {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise EngineError(f"{url} unreachable: {exc}") from exc


# Seconds between job status checks, and how many checks before giving up.
SPEECHMATICS_POLL = 1.0
SPEECHMATICS_POLLS = 300


def speechmatics(path: Path) -> Transcript:
    base = "https://eu1.asr.api.speechmatics.com/v2"
    config = {
        "type": "transcription",
        "transcription_config": {
            "language": "fr",
            "operating_point": "enhanced",
        },
    }
    body, content_type = _multipart({"config": json.dumps(config)}, "data_file", path)
    auth = {"Authorization": f"Bearer {os.environ['SPEECHMATICS_API_KEY']}"}
    started = time.perf_counter()
    job = _post(f"{base}/jobs", body, {**auth, "Content-Type": content_type})
    job_id = job["id"]
    for _ in range(SPEECHMATICS_POLLS):
        state = _get(f"{base}/jobs/{job_id}", auth)
        status = state.get("job", state).get("status")
        if status == "done":
            break
        if status == "rejected":
            raise EngineError(f"speechmatics job {job_id} was rejected")
        time.sleep(SPEECHMATICS_POLL)
    else:
        raise EngineError(f"speechmatics job {job_id} did not finish")
    data = _get(f"{base}/jobs/{job_id}/transcript", auth)
    seconds = time.perf_counter() - started
    words = tuple(
        Word(
            str(item["alternatives"][0]["content"]),
            optional_float(item.get("start_time")),
            optional_float(item.get("end_time")),
            optional_float(item["alternatives"][0].get("confidence")),
        )
        for item in data.get("results", [])
        if item.get("type") == "word"
    )
    return Transcript(" ".join(w.text for w in words), words, seconds)


def whisper_local(model_dir: Path) -> Callable[[Path], Transcript]:
    """Whisper large-v3 on the CPU through faster-whisper."""
    from faster_whisper import WhisperModel  # type: ignore[import-not-found]  # run-time extra, not a repo dependency

    model = WhisperModel(str(model_dir), device="cpu", compute_type="int8")

    def transcribe(path: Path) -> Transcript:
        started = time.perf_counter()
        segments, _info = model.transcribe(
            str(path),
            language="fr",
            word_timestamps=True,
            beam_size=5,
            condition_on_previous_text=False,
        )
        collected = list(segments)
        seconds = time.perf_counter() - started
        words = tuple(
            Word(w.word, float(w.start), float(w.end), float(w.probability))
            for s in collected
            for w in (s.words or [])
        )
        return Transcript(" ".join(s.text.strip() for s in collected), words, seconds)

    return transcribe


# WHY: list prices per audio hour from the providers' public pages, checked 2026-11-13.
PRICED: dict[str, tuple[str | None, float | None, str]] = {
    "deepgram-nova-3": (
        "DEEPGRAM_API_KEY",
        0.0043 * 60,
        "monolingual batch $0.0043 a minute; streaming $0.0048 a minute",
    ),
    "elevenlabs-scribe": (
        "ELEVENLABS_API_KEY",
        0.20,
        "Scribe v3 batch $0.20 an hour; Scribe v3 Live $0.22 an hour",
    ),
    "speechmatics": (
        "SPEECHMATICS_API_KEY",
        0.75,
        "Enhanced batch $0.75 an hour ($0.80 real time); Melia 1 batch $0.24",
    ),
    "whisper-large-v3": (None, 0.0, "open weights run locally; compute is ours"),
}

REMOTE: dict[str, Callable[[Path], Transcript]] = {
    "deepgram-nova-3": deepgram,
    "elevenlabs-scribe": elevenlabs_scribe,
    "speechmatics": speechmatics,
}


def available_engines(
    whisper_dir: Path | None, env: Mapping[str, str]
) -> tuple[list[Engine], list[str]]:
    """Engines that can run now, and one plain line per engine that cannot."""
    engines: list[Engine] = []
    skipped: list[str] = []
    for name, (key_env, price, note) in PRICED.items():
        if key_env is None:
            if whisper_dir is None:
                skipped.append(f"{name}: skipped, no --whisper-dir given")
            else:
                engines.append(
                    Engine(name, None, price, note, whisper_local(whisper_dir))
                )
        elif not env.get(key_env):
            skipped.append(f"{name}: skipped, {key_env} is not set")
        else:
            engines.append(Engine(name, key_env, price, note, REMOTE[name]))
    return engines, skipped
