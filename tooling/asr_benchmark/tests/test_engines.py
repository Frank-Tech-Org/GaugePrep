from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

import pytest
from asr_benchmark import engines


def stub_post(
    monkeypatch: pytest.MonkeyPatch, answer: dict[str, Any]
) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    def post(url: str, body: bytes, headers: dict[str, str]) -> dict[str, Any]:
        seen.update(url=url, body=body, headers=headers)
        return answer

    monkeypatch.setattr(engines, "_post", post)
    return seen


@pytest.fixture
def clip(tmp_path: Path) -> Path:
    path = tmp_path / "clip.wav"
    path.write_bytes(b"RIFFdata")
    return path


def test_deepgram_reads_words_with_timing_and_confidence(
    monkeypatch: pytest.MonkeyPatch, clip: Path
) -> None:
    monkeypatch.setenv("DEEPGRAM_API_KEY", "k")
    answer = {
        "results": {
            "channels": [
                {
                    "alternatives": [
                        {
                            "transcript": "bonjour à tous",
                            "words": [
                                {
                                    "word": "bonjour",
                                    "start": 0.1,
                                    "end": 0.5,
                                    "confidence": 0.98,
                                }
                            ],
                        }
                    ]
                }
            ]
        }
    }
    seen = stub_post(monkeypatch, answer)
    result = engines.deepgram(clip)
    assert result.text == "bonjour à tous"
    assert result.words[0].confidence == 0.98
    assert "model=nova-3" in seen["url"] and "language=fr" in seen["url"]
    assert seen["headers"]["Authorization"] == "Token k"
    assert seen["body"] == b"RIFFdata"


def test_scribe_keeps_words_only_and_sends_verbatim_options(
    monkeypatch: pytest.MonkeyPatch, clip: Path
) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
    answer = {
        "text": "il a tombé",
        "words": [
            {"text": "il", "type": "word", "start": 0.0, "end": 0.2, "logprob": -0.1},
            {"text": " ", "type": "spacing", "start": 0.2, "end": 0.3, "logprob": 0.0},
        ],
    }
    seen = stub_post(monkeypatch, answer)
    result = engines.elevenlabs_scribe(clip)
    assert [w.text for w in result.words] == ["il"]
    assert b'name="no_verbatim"\r\n\r\nfalse' in seen["body"]
    assert b'name="timestamps_granularity"\r\n\r\nword' in seen["body"]
    assert seen["headers"]["xi-api-key"] == "k"


def test_speechmatics_runs_a_job_and_reads_word_confidence(
    monkeypatch: pytest.MonkeyPatch, clip: Path
) -> None:
    monkeypatch.setenv("SPEECHMATICS_API_KEY", "k")
    seen = stub_post(monkeypatch, {"id": "job1"})
    calls: list[str] = []

    def get(url: str, headers: dict[str, str]) -> dict[str, Any]:
        calls.append(url)
        if url.endswith("/transcript"):
            return {
                "results": [
                    {
                        "type": "word",
                        "start_time": 0.5,
                        "end_time": 0.9,
                        "alternatives": [{"content": "bonjour", "confidence": 0.97}],
                    },
                    {
                        "type": "punctuation",
                        "alternatives": [{"content": ".", "confidence": 1.0}],
                    },
                ]
            }
        return {"job": {"status": "done"}}

    monkeypatch.setattr(engines, "_get", get)
    result = engines.speechmatics(clip)
    assert result.text == "bonjour"
    assert result.words[0].confidence == 0.97 and result.words[0].start == 0.5
    assert calls[-1].endswith("/jobs/job1/transcript")
    assert seen["headers"]["Authorization"] == "Bearer k"
    assert b'"language": "fr"' in seen["body"]
    assert b'"operating_point": "enhanced"' in seen["body"]


def test_speechmatics_rejected_job_is_an_error(
    monkeypatch: pytest.MonkeyPatch, clip: Path
) -> None:
    monkeypatch.setenv("SPEECHMATICS_API_KEY", "k")
    stub_post(monkeypatch, {"id": "job1"})
    monkeypatch.setattr(
        engines, "_get", lambda url, headers: {"job": {"status": "rejected"}}
    )
    with pytest.raises(engines.EngineError):
        engines.speechmatics(clip)


def test_multipart_body_has_fields_and_file(clip: Path) -> None:
    body, content_type = engines._multipart({"a": "1"}, "file", clip)
    boundary = content_type.split("boundary=")[1]
    assert body.startswith(f"--{boundary}".encode())
    assert b'name="a"\r\n\r\n1' in body and b'filename="clip.wav"' in body
    assert body.endswith(f"--{boundary}--\r\n".encode())


def test_every_engine_has_a_price() -> None:
    assert all(price is not None for _, price, _ in engines.PRICED.values())
    assert engines.PRICED["speechmatics"][1] == pytest.approx(0.75)
    assert engines.PRICED["deepgram-nova-3"][1] == pytest.approx(0.258)


def test_extra_settings_reach_the_deepgram_url(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    clip = tmp_path / "a.wav"
    clip.write_bytes(b"x")
    seen = stub_post(monkeypatch, {"results": {"channels": [{"alternatives": [{}]}]}})
    monkeypatch.setenv("DEEPGRAM_API_KEY", "k")
    monkeypatch.setenv("ASR_EXTRA_DEEPGRAM", '{"filler_words": "true"}')
    engines.deepgram(clip)
    assert "filler_words=true" in seen["url"]
    assert "smart_format=false" in seen["url"]


def test_extra_settings_must_be_an_object(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASR_EXTRA_DEEPGRAM", "[1]")
    with pytest.raises(ValueError):
        engines.extra_settings("ASR_EXTRA_DEEPGRAM")


def serve(handler: type[BaseHTTPRequestHandler]) -> tuple[HTTPServer, int]:
    server = HTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, int(server.server_address[1])


def test_a_redirect_is_an_error_and_never_reaches_a_second_host() -> None:
    hits: list[str] = []

    class Target(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            hits.append(self.headers.get("xi-api-key", ""))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")

        do_GET = do_POST

        def log_message(self, *args: Any) -> None:
            return

    target, target_port = serve(Target)

    class Bounce(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{target_port}/steal")
            self.end_headers()

        do_GET = do_POST

        def log_message(self, *args: Any) -> None:
            return

    bounce, bounce_port = serve(Bounce)
    url = f"http://127.0.0.1:{bounce_port}/v1"
    try:
        with pytest.raises(engines.EngineError) as post_error:
            engines._post(url, b"x", {"xi-api-key": "k"})
        with pytest.raises(engines.EngineError):
            engines._get(url, {"xi-api-key": "k"})
    finally:
        bounce.shutdown()
        target.shutdown()
    assert post_error.value.status == 302
    assert hits == []


@pytest.mark.parametrize("name", ['a"b.wav', "a\rb.wav", "a\nb.wav"])
def test_clip_names_with_quotes_or_line_breaks_are_refused(
    tmp_path: Path, name: str
) -> None:
    path = tmp_path / name
    path.write_bytes(b"RIFF")
    with pytest.raises(engines.EngineError):
        engines._multipart({}, "file", path)
