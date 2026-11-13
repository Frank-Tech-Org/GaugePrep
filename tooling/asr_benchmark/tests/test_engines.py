from pathlib import Path
from typing import Any

import pytest
from asr_benchmark import engines
from asr_benchmark.engines import Transcript


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


def test_voxtral_without_confidence_is_reported_as_missing(
    monkeypatch: pytest.MonkeyPatch, clip: Path
) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "k")
    stub_post(
        monkeypatch,
        {"text": "bonjour", "words": [{"word": "bonjour", "start": 0, "end": 1}]},
    )
    result: Transcript = engines.mistral_voxtral(clip)
    assert result.words[0].confidence is None
    assert result.words[0].start == 0


def test_multipart_body_has_fields_and_file(clip: Path) -> None:
    body, content_type = engines._multipart({"a": "1"}, "file", clip)
    boundary = content_type.split("boundary=")[1]
    assert body.startswith(f"--{boundary}".encode())
    assert b'name="a"\r\n\r\n1' in body and b'filename="clip.wav"' in body
    assert body.endswith(f"--{boundary}--\r\n".encode())


def test_mistral_sends_no_language_with_word_timestamps(
    monkeypatch: pytest.MonkeyPatch, clip: Path
) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "k")
    seen = stub_post(monkeypatch, {"text": "x", "words": []})
    engines.mistral_voxtral(clip)
    assert b'name="timestamp_granularities"' in seen["body"]
    assert b'name="language"' not in seen["body"]


def test_every_engine_has_a_price() -> None:
    assert all(price is not None for _, price, _ in engines.PRICED.values())
    assert engines.PRICED["mistral-voxtral"][1] == pytest.approx(0.18)
    assert engines.PRICED["deepgram-nova-3"][1] == pytest.approx(0.258)
