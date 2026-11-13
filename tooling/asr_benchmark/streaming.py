import asyncio
import base64
import json
import os
import time
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

from asr_benchmark.engines import Word, optional_float
from asr_benchmark.metrics import percentile

# Raw PCM the live endpoints take: 16 kHz, 16-bit, mono.
BYTES_PER_SECOND = 32_000
CHUNK_SECONDS = 0.1
DEEPGRAM_LIVE = (
    "wss://api.deepgram.com/v1/listen?model=nova-3&language=fr&encoding=linear16"
    "&sample_rate=16000&channels=1&interim_results=true&punctuate=false&smart_format=false"
)
ELEVENLABS_LIVE = (
    "wss://api.elevenlabs.io/v1/speech-to-text/realtime?model_id=scribe_v3_live"
    "&audio_format=pcm_16000&language_code=fra&commit_strategy=manual"
    "&include_timestamps=true&no_verbatim=false"
)
MISTRAL_LIVE_MODEL = "voxtral-mini-transcribe-realtime-2602"


@dataclass(frozen=True)
class StreamEvent:
    kind: Literal["partial", "final"]
    text: str
    at: float
    words: tuple[Word, ...] = ()


@dataclass(frozen=True)
class StreamTiming:
    """First-token and final latency in seconds, plus the text heard."""

    first_token_s: float | None
    final_s: float | None
    text: str
    words: tuple[Word, ...]


class StreamSession(Protocol):
    async def send(self, chunk: bytes) -> None: ...

    async def finish(self) -> None: ...

    def events(self) -> AsyncIterator[StreamEvent]: ...


async def measure(
    session: StreamSession,
    pcm: bytes,
    clock: Callable[[], float] = time.perf_counter,
    sleep: Callable[[float], Any] = asyncio.sleep,
) -> StreamTiming:
    """Feed `pcm` at real-time pace; event times must come from the same `clock`."""
    started = clock()
    audio_end = started

    async def feed() -> None:
        nonlocal audio_end
        size = int(BYTES_PER_SECOND * CHUNK_SECONDS)
        for offset in range(0, len(pcm), size):
            await session.send(pcm[offset : offset + size])
            await sleep(CHUNK_SECONDS)
        audio_end = clock()
        await session.finish()

    feeder = asyncio.ensure_future(feed())
    first: float | None = None
    last_final: float | None = None
    finals: list[str] = []
    words: list[Word] = []
    try:
        async for event in session.events():
            if first is None and event.text.strip():
                first = event.at - started
            if event.kind == "final":
                last_final = event.at
                finals.append(event.text.strip())
                words.extend(event.words)
    finally:
        await feeder
    final_s = None if last_final is None else max(0.0, last_final - audio_end)
    return StreamTiming(first, final_s, " ".join(t for t in finals if t), tuple(words))


def load_pcm16k(path: Path) -> bytes:
    """Decode any clip to 16 kHz mono 16-bit PCM."""
    import av  # type: ignore[import-not-found]  # run-time extra, not a repo dependency

    resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
    out = bytearray()
    with av.open(str(path)) as container:
        for frame in container.decode(audio=0):
            for piece in resampler.resample(frame):
                out += bytes(piece.planes[0])[: piece.samples * 2]
        for piece in resampler.resample(None):
            out += bytes(piece.planes[0])[: piece.samples * 2]
    return bytes(out)


class _Websocket:
    """Shared plumbing: a websocket plus a function turning one message into events."""

    def __init__(
        self,
        socket: Any,
        parse: Callable[[Any, float], list[StreamEvent]],
        encode: Callable[[bytes], str | bytes],
        closing: Callable[[], str | bytes],
        stop_after_final: bool,
    ) -> None:
        self._socket = socket
        self._parse = parse
        self._encode = encode
        self._closing = closing
        self._stop_after_final = stop_after_final
        self._finished = False

    async def send(self, chunk: bytes) -> None:
        await self._socket.send(self._encode(chunk))

    async def finish(self) -> None:
        self._finished = True
        await self._socket.send(self._closing())

    async def events(self) -> AsyncIterator[StreamEvent]:
        async for message in self._socket:
            for event in self._parse(message, time.perf_counter()):
                yield event
                if self._stop_after_final and self._finished and event.kind == "final":
                    return


def _deepgram_events(message: Any, now: float) -> list[StreamEvent]:
    data = json.loads(message)
    if data.get("type") != "Results":
        return []
    best = data["channel"]["alternatives"][0]
    words = tuple(
        Word(
            w["word"],
            optional_float(w.get("start")),
            optional_float(w.get("end")),
            optional_float(w.get("confidence")),
        )
        for w in best.get("words", [])
    )
    kind: Literal["partial", "final"] = "final" if data.get("is_final") else "partial"
    return [
        StreamEvent(
            kind, best.get("transcript", ""), now, words if kind == "final" else ()
        )
    ]


def _elevenlabs_events(message: Any, now: float) -> list[StreamEvent]:
    data = json.loads(message)
    kind = data.get("message_type")
    if kind == "partial_transcript":
        return [StreamEvent("partial", data.get("text", ""), now)]
    if kind == "committed_transcript_with_timestamps":
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
        return [StreamEvent("final", data.get("text", ""), now, words)]
    return []


@asynccontextmanager
async def deepgram_session() -> AsyncIterator[StreamSession]:
    from websockets.asyncio.client import connect  # type: ignore[import-not-found]  # run-time extra

    headers = {"Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}"}
    async with connect(DEEPGRAM_LIVE, additional_headers=headers) as socket:
        yield _Websocket(
            socket,
            _deepgram_events,
            lambda c: c,
            lambda: json.dumps({"type": "CloseStream"}),
            False,
        )


@asynccontextmanager
async def elevenlabs_session() -> AsyncIterator[StreamSession]:
    from websockets.asyncio.client import connect  # run-time extra

    def chunk(audio: bytes, commit: bool = False) -> str:
        return json.dumps(
            {
                "message_type": "input_audio_chunk",
                "audio_base_64": base64.b64encode(audio).decode(),
                "sample_rate": 16000,
                "commit": commit,
            }
        )

    headers = {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}
    async with connect(ELEVENLABS_LIVE, additional_headers=headers) as socket:
        yield _Websocket(
            socket,
            _elevenlabs_events,
            lambda c: chunk(c),
            lambda: chunk(b"", commit=True),
            True,
        )


class _MistralSession:
    """Voxtral Realtime through the provider SDK, which sends text deltas only."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()

    async def send(self, chunk: bytes) -> None:
        await self._queue.put(chunk)

    async def finish(self) -> None:
        await self._queue.put(None)

    async def _audio(self) -> AsyncIterator[bytes]:
        while (chunk := await self._queue.get()) is not None:
            yield chunk

    async def events(self) -> AsyncIterator[StreamEvent]:
        from mistralai.client import Mistral  # type: ignore[import-not-found]  # run-time extra
        from mistralai.client.models import (  # type: ignore[import-not-found]  # run-time extra
            AudioFormat,
            TranscriptionStreamDone,
            TranscriptionStreamTextDelta,
        )

        client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
        audio_format = AudioFormat(encoding="pcm_s16le", sample_rate=16000)
        heard = ""
        async for event in client.audio.realtime.transcribe_stream(
            audio_stream=self._audio(),
            model=MISTRAL_LIVE_MODEL,
            audio_format=audio_format,
        ):
            now = time.perf_counter()
            if isinstance(event, TranscriptionStreamTextDelta):
                heard += event.text
                yield StreamEvent("partial", event.text, now)
            elif isinstance(event, TranscriptionStreamDone):
                yield StreamEvent("final", heard, now)


@asynccontextmanager
async def mistral_session() -> AsyncIterator[StreamSession]:
    yield _MistralSession()


STREAMING: dict[str, Callable[[], AbstractAsyncContextManager[StreamSession]]] = {
    "deepgram-nova-3": deepgram_session,
    "elevenlabs-scribe": elevenlabs_session,
    "mistral-voxtral": mistral_session,
}


async def stream_clip(engine: str, path: Path) -> StreamTiming:
    pcm = load_pcm16k(path)
    async with STREAMING[engine]() as session:
        return await measure(session, pcm)


def summarise(timings: list[StreamTiming]) -> dict[str, float | None]:
    """Median and p95 of first-token and final latency."""
    firsts = [t.first_token_s for t in timings if t.first_token_s is not None]
    finals = [t.final_s for t in timings if t.final_s is not None]
    return {
        "first_token_p50": percentile(firsts, 50) if firsts else None,
        "first_token_p95": percentile(firsts, 95) if firsts else None,
        "final_p50": percentile(finals, 50) if finals else None,
        "final_p95": percentile(finals, 95) if finals else None,
    }
