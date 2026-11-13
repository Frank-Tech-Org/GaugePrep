from pathlib import Path

import pytest
from asr_benchmark.corpora import Clip, keep_clip, read_manifest, write_manifest
from asr_benchmark.engines import (
    Engine,
    EngineError,
    Transcript,
    Word,
    available_engines,
)
from asr_benchmark.metrics import contains_run, edit_counts, percentile, word_error_rate
from asr_benchmark.planted import PLANTED_CLIPS
from asr_benchmark.runner import (
    PLANTED_CORPUS,
    EngineResult,
    choose_winner,
    evaluate,
    has_word_data,
    table,
)
from asr_benchmark.text import normalise


def test_normalise_splits_elisions_and_ignores_case_and_punctuation() -> None:
    assert normalise("J’ai allé, au Marché !") == ["j", "ai", "allé", "au", "marché"]
    assert normalise("peut-être") == ["peut", "être"]


def test_normalise_keeps_accents() -> None:
    assert normalise("allé") != normalise("alle")


def test_edit_counts_covers_substitution_deletion_insertion() -> None:
    assert edit_counts(["a", "b", "c"], ["a", "x", "c"]).errors == 1
    assert edit_counts(["a", "b", "c"], ["a", "c"]).errors == 1
    assert edit_counts(["a", "c"], ["a", "b", "c"]).errors == 1
    assert edit_counts([], ["a"]).errors == 1


def test_word_error_rate_pools_words_across_clips() -> None:
    clips = [
        edit_counts(["a"] * 10, ["a"] * 9 + ["b"]),
        edit_counts(["a"] * 30, ["a"] * 30),
    ]
    assert word_error_rate(clips) == pytest.approx(2.5)


def test_word_error_rate_refuses_empty_input() -> None:
    with pytest.raises(ValueError):
        word_error_rate([])


def test_contains_run_needs_consecutive_words() -> None:
    assert contains_run(["il", "a", "tombé"], ["a", "tombé"])
    assert not contains_run(["il", "a", "bien", "tombé"], ["a", "tombé"])
    assert not contains_run(["a"], [])


def test_percentile_nearest_rank() -> None:
    assert percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 95) == 10
    assert percentile([5], 50) == 5


def test_planted_errors_are_spoken_and_differ_from_the_correction() -> None:
    assert len(PLANTED_CLIPS) >= 20
    for clip in PLANTED_CLIPS:
        assert contains_run(normalise(clip.spoken), normalise(clip.error)), clip.id
        assert normalise(clip.error) != normalise(clip.correct), clip.id
    assert len({c.id for c in PLANTED_CLIPS}) == len(PLANTED_CLIPS)


def test_keep_clip_is_stable_and_seeded() -> None:
    assert keep_clip("a.mp3", 15, 0.5) == keep_clip("a.mp3", 15, 0.5)
    picks = {
        seed: [keep_clip(f"c{i}.mp3", seed, 0.5) for i in range(40)] for seed in (1, 2)
    }
    assert picks[1] != picks[2]
    assert 5 < sum(picks[1]) < 35


def test_manifest_round_trip_keeps_accents(tmp_path: Path) -> None:
    clips = [Clip("x1", "common-voice-fr", "scripted", "/tmp/x.mp3", "Où êtes-vous ?")]
    write_manifest(clips, tmp_path / "m.jsonl")
    assert read_manifest(tmp_path / "m.jsonl") == clips


def fake_engine(
    answers: dict[str, str], name: str = "fake", price: float | None = 1.0
) -> Engine:
    def transcribe(path: Path) -> Transcript:
        if path.stem not in answers:
            raise EngineError("provider answered 500")
        words = tuple(Word(w, 0.0, 0.1, 0.9) for w in answers[path.stem].split())
        return Transcript(answers[path.stem], words, 0.4)

    return Engine(name, None, price, "", transcribe)


def test_evaluate_scores_wer_preservation_latency_and_missing_clips() -> None:
    planted = PLANTED_CLIPS[0]
    corrected = planted.spoken.replace(planted.error, planted.correct)
    clips = [
        Clip("c1", "openslr57", "cameroon", "c1.wav", "il a tombé"),
        Clip("c2", "openslr57", "cameroon", "c2.wav", "bonjour à tous"),
        Clip("c3", "openslr57", "cameroon", "gone.wav", "jamais lu"),
        Clip(planted.id, PLANTED_CORPUS, "tts", f"{planted.id}.wav", planted.reference),
        Clip("p01", PLANTED_CORPUS, "tts", "p01.wav", PLANTED_CLIPS[1].reference),
    ]
    engine = fake_engine(
        {
            "c1": "il est tombé",
            "c2": "bonjour à tous",
            planted.id: corrected,
            "p01": PLANTED_CLIPS[1].spoken,
        }
    )
    result, hypotheses = evaluate(
        engine, clips, {"c1": 2.0, "c2": 2.0, planted.id: 4.0, "p01": 4.0}
    )
    assert result.wer_by_group == {"openslr57/cameroon": pytest.approx(100 * 1 / 6)}
    assert result.preservation == 50.0
    assert result.missing == {"c3": "provider answered 500"}
    assert result.clips_scored == 4
    assert (result.word_timing, result.word_confidence) == (True, True)
    assert result.latency_median_s == pytest.approx(0.4)
    assert result.real_time_factor == pytest.approx(1.6 / 12)
    assert hypotheses["c1"] == "il est tombé"


def test_has_word_data_requires_every_word() -> None:
    complete = Transcript("a b", (Word("a", 0, 1, 0.9), Word("b", 1, 2, 0.8)), 0.1)
    no_confidence = Transcript("a", (Word("a", 0, 1, None),), 0.1)
    assert has_word_data([complete]) == (True, True)
    assert has_word_data([complete, no_confidence]) == (True, False)
    assert has_word_data([Transcript("", (), 0.1)]) == (False, False)


def result(
    name: str,
    wer: float,
    kept: float | None,
    price: float | None,
    timing: bool = True,
    confidence: bool = True,
) -> EngineResult:
    return EngineResult(
        name,
        price,
        "",
        {"openslr57/all": wer},
        kept,
        timing,
        confidence,
        0.5,
        0.9,
        0.2,
        10,
    )


def test_winner_is_lowest_wer_among_engines_that_keep_errors() -> None:
    rows = [
        result("a", 8.0, 90.0, 0.3),
        result("b", 10.0, 96.0, 0.5),
        result("c", 15.0, 99.0, 0.1),
    ]
    assert choose_winner(rows) == "b"


def test_within_one_point_the_cheaper_engine_wins() -> None:
    rows = [
        result("a", 8.0, 97.0, 0.5),
        result("b", 8.9, 97.0, 0.3),
        result("c", 9.5, 97.0, 0.1),
    ]
    assert choose_winner(rows) == "b"


def test_engine_without_word_timing_or_confidence_cannot_win() -> None:
    rows = [
        result("a", 5.0, 99.0, 0.2, confidence=False),
        result("b", 6.0, 99.0, 0.4, timing=False),
    ]
    assert choose_winner(rows) is None


def test_control_never_wins_and_no_eligible_engine_gives_none() -> None:
    assert choose_winner([result("whisper-large-v3", 3.0, 100.0, 0.0)]) is None
    assert choose_winner([result("a", 3.0, None, 0.1)]) is None


def test_engines_without_a_key_are_skipped_and_named() -> None:
    engines, skipped = available_engines(None, {"DEEPGRAM_API_KEY": "set"})
    assert [e.name for e in engines] == ["deepgram-nova-3"]
    assert any("elevenlabs-scribe" in s and "ELEVENLABS_API_KEY" in s for s in skipped)
    assert any("mistral-voxtral" in s and "MISTRAL_API_KEY" in s for s in skipped)
    assert any("whisper-large-v3" in s for s in skipped)


def test_skip_message_never_contains_the_key_value() -> None:
    _, skipped = available_engines(None, {"DEEPGRAM_API_KEY": "sekret-value"})
    assert "sekret-value" not in "\n".join(skipped)


def test_table_marks_missing_numbers_as_n_a() -> None:
    row = EngineResult("x", None, "", {}, None, False, False)
    assert "n/a" in table([row])
