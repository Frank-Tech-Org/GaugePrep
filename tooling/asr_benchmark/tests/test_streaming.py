import asyncio
import json
from collections.abc import AsyncIterator

from asr_benchmark import streaming
from asr_benchmark.streaming import StreamEvent, StreamTiming, measure, summarise


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += seconds
        await asyncio.sleep(0)


class FakeSession:
    """Partial after `first_after` s of audio; final `lag` s after the audio ends."""

    def __init__(self, clock: FakeClock, first_after: float, lag: float) -> None:
        self.clock = clock
        self.first_after = first_after
        self.lag = lag
        self.sent = 0
        self.done = asyncio.Event()

    async def send(self, chunk: bytes) -> None:
        self.sent += len(chunk)

    async def finish(self) -> None:
        self.done.set()

    async def events(self) -> AsyncIterator[StreamEvent]:
        while self.clock.now < self.first_after:
            await asyncio.sleep(0)
        yield StreamEvent("partial", "bon", self.clock.now)
        await self.done.wait()
        self.clock.now += self.lag
        yield StreamEvent("final", "bonjour", self.clock.now)


def one_second_of_audio() -> bytes:
    return bytes(streaming.BYTES_PER_SECOND)


def test_measure_reports_first_token_and_final_latency() -> None:
    clock = FakeClock()
    session = FakeSession(clock, first_after=0.4, lag=0.25)
    timing = asyncio.run(
        measure(session, one_second_of_audio(), clock=clock, sleep=clock.sleep)
    )
    assert timing.first_token_s is not None
    assert abs(timing.first_token_s - 0.4) < 1e-6
    assert timing.final_s is not None
    assert abs(timing.final_s - 0.25) < 1e-6
    assert timing.text == "bonjour"
    assert session.sent == streaming.BYTES_PER_SECOND


def test_measure_paces_audio_in_real_time() -> None:
    clock = FakeClock()
    session = FakeSession(clock, first_after=0.0, lag=0.0)
    asyncio.run(measure(session, one_second_of_audio(), clock=clock, sleep=clock.sleep))
    assert abs(clock.now - 1.0) < 1e-6


def test_silent_session_has_no_latency() -> None:
    class Silent:
        async def send(self, chunk: bytes) -> None: ...

        async def finish(self) -> None: ...

        async def events(self) -> AsyncIterator[StreamEvent]:
            return
            yield

    clock = FakeClock()
    timing = asyncio.run(
        measure(Silent(), one_second_of_audio(), clock=clock, sleep=clock.sleep)
    )
    assert timing.first_token_s is None and timing.final_s is None


def test_summarise_uses_nearest_rank() -> None:
    timings = [StreamTiming(0.1 * n, 0.2 * n, "", ()) for n in range(1, 11)]
    summary = summarise(timings)
    assert summary["first_token_p50"] == 0.5
    assert summary["final_p95"] == 2.0
    assert summarise([StreamTiming(None, None, "", ())])["final_p50"] is None


def test_deepgram_result_parsing() -> None:
    message = json.dumps(
        {
            "type": "Results",
            "is_final": True,
            "channel": {
                "alternatives": [
                    {
                        "transcript": "je suis allé",
                        "words": [
                            {"word": "je", "start": 0.1, "end": 0.2, "confidence": 0.9}
                        ],
                    }
                ]
            },
        }
    )
    [event] = streaming._deepgram_events(message, 3.0)
    assert event.kind == "final" and event.text == "je suis allé"
    assert event.words[0].confidence == 0.9
    assert streaming._deepgram_events(json.dumps({"type": "Metadata"}), 1.0) == []


def test_elevenlabs_message_parsing() -> None:
    partial = json.dumps({"message_type": "partial_transcript", "text": "je"})
    final = json.dumps(
        {
            "message_type": "committed_transcript_with_timestamps",
            "text": "je suis",
            "words": [
                {
                    "text": "je",
                    "type": "word",
                    "start": 0.0,
                    "end": 0.2,
                    "logprob": -0.1,
                },
                {"text": " ", "type": "spacing"},
            ],
        }
    )
    assert streaming._elevenlabs_events(partial, 1.0)[0].kind == "partial"
    [event] = streaming._elevenlabs_events(final, 2.0)
    assert event.kind == "final" and len(event.words) == 1


def test_summarise_counts_the_clips_behind_each_number() -> None:
    timings = [
        StreamTiming(0.5, 1.0, "", ()),
        StreamTiming(None, 2.0, "", ()),
        StreamTiming(0.7, None, "", ()),
    ]
    summary = summarise(timings)
    assert (summary["clips"], summary["first_token_timed"]) == (3, 2)
    assert summary["final_timed"] == 2
