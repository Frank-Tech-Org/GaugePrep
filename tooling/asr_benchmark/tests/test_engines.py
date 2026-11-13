from pathlib import Path
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
