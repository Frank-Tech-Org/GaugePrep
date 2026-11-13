from pathlib import Path

import pytest
from asr_benchmark.corpora import Clip
from asr_benchmark.engines import Engine, EngineError, Transcript
from asr_benchmark.guard import EngineStopped, Guard
from asr_benchmark.runner import evaluate


class Counting:
    def __init__(self, errors: list[EngineError] | None = None) -> None:
        self.calls = 0
        self.errors = errors or []

    def __call__(self, path: Path) -> Transcript:
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return Transcript("bonjour", (), 0.5)


def make(
    tmp_path: Path, backend: Counting, allowance: float = 100.0, minutes: float = 1.0
) -> tuple[Engine, Path, Guard]:
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"audio")
    guard = Guard(
        tmp_path / "cache",
        {"fake": allowance},
        {str(audio): minutes},
        sleep=lambda _: None,
    )
    engine = guard.wrap(Engine("fake", "K", 1.0, "", backend), "m1")
    return engine, audio, guard


def test_second_call_comes_from_the_cache_and_costs_nothing(tmp_path: Path) -> None:
    backend = Counting()
    engine, audio, guard = make(tmp_path, backend)
    engine.transcribe(audio)
    again = engine.transcribe(audio)
    assert backend.calls == 1 and again.text == "bonjour"
    assert guard.used["fake"] == 1.0
    rerun = Guard(tmp_path / "cache", {"fake": 100.0}, {}, sleep=lambda _: None)
    assert rerun.used["fake"] == 1.0


def test_transient_errors_are_retried_twice_then_given_up(tmp_path: Path) -> None:
    backend = Counting([EngineError("down")] * 5)
    engine, audio, _ = make(tmp_path, backend)
    with pytest.raises(EngineError):
        engine.transcribe(audio)
    assert backend.calls == 3


def test_a_bad_request_is_not_retried(tmp_path: Path) -> None:
    backend = Counting([EngineError("bad audio", 400)] * 5)
    engine, audio, _ = make(tmp_path, backend)
    with pytest.raises(EngineError):
        engine.transcribe(audio)
    assert backend.calls == 1


@pytest.mark.parametrize("status", [401, 402, 403, 429])
def test_quota_and_auth_errors_stop_the_engine_for_good(
    tmp_path: Path, status: int
) -> None:
    backend = Counting([EngineError("limit", status)])
    engine, audio, _ = make(tmp_path, backend)
    with pytest.raises(EngineStopped):
        engine.transcribe(audio)
    with pytest.raises(EngineStopped):
        engine.transcribe(audio)
    assert backend.calls == 1


def test_the_reserve_is_never_spent(tmp_path: Path) -> None:
    backend = Counting()
    engine, audio, _ = make(tmp_path, backend, allowance=10.0, minutes=8.0)
    with pytest.raises(EngineStopped):
        engine.transcribe(audio)
    assert backend.calls == 0


def test_evaluate_stops_at_the_first_quota_error(tmp_path: Path) -> None:
    backend = Counting([EngineError("limit", 429)])
    engine, audio, _ = make(tmp_path, backend)
    clips = [Clip(f"c{n}", "x", "g", str(audio), "bonjour", None) for n in range(4)]
    result, _ = evaluate(engine, clips, {})
    assert backend.calls == 1
    assert len(result.missing) == 4 and result.stopped
