import json
import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from asr_benchmark.corpora import Clip
from asr_benchmark.engines import Engine, EngineError, Transcript
from asr_benchmark.metrics import (
    Edits,
    contains_run,
    edit_counts,
    percentile,
    word_error_rate,
)
from asr_benchmark.planted import PLANTED_CLIPS
from asr_benchmark.text import normalise

PRESERVATION_MIN = 95.0
# WER points within which the cheaper engine wins.
WER_TIE = 1.0
PLANTED_CORPUS = "planted-errors"


@dataclass
class EngineResult:
    name: str
    price_per_hour_usd: float | None
    price_note: str
    wer_by_group: dict[str, float] = field(default_factory=dict)
    preservation: float | None = None
    word_timing: bool = False
    word_confidence: bool = False
    latency_median_s: float | None = None
    latency_p95_s: float | None = None
    real_time_factor: float | None = None
    clips_scored: int = 0
    missing: dict[str, str] = field(default_factory=dict)

    @property
    def wer(self) -> float | None:
        """Mean of the per-group rates, so a big corpus does not drown a small one."""
        scored = [v for k, v in self.wer_by_group.items() if k != PLANTED_CORPUS]
        return statistics.fmean(scored) if scored else None


def planted_as_clips(directory: Path) -> list[Clip]:
    return [
        Clip(c.id, PLANTED_CORPUS, "tts", str(directory / f"{c.id}.wav"), c.reference)
        for c in PLANTED_CLIPS
    ]


def has_word_data(transcripts: Sequence[Transcript]) -> tuple[bool, bool]:
    """Whether every word has timing, and whether every word has a confidence."""
    words = [w for t in transcripts for w in t.words]
    if not words:
        return False, False
    timing = all(w.start is not None and w.end is not None for w in words)
    confidence = all(w.confidence is not None for w in words)
    return timing, confidence


def evaluate(
    engine: Engine, clips: Sequence[Clip], durations: Mapping[str, float]
) -> tuple[EngineResult, dict[str, str]]:
    """Run one engine on every clip; returns scores and hypotheses by clip id."""
    result = EngineResult(engine.name, engine.price_per_hour_usd, engine.price_note)
    edits: dict[str, list[Edits]] = defaultdict(list)
    transcripts: list[Transcript] = []
    hypotheses: dict[str, str] = {}
    preserved = planted_total = 0
    planted = {c.id: c for c in PLANTED_CLIPS}
    audio_seconds = request_seconds = 0.0
    for clip in clips:
        try:
            transcript = engine.transcribe(Path(clip.path))
        except (EngineError, OSError) as exc:
            result.missing[clip.id] = str(exc)[:200]
            continue
        transcripts.append(transcript)
        hypotheses[clip.id] = transcript.text
        tokens = normalise(transcript.text)
        result.clips_scored += 1
        request_seconds += transcript.seconds
        audio_seconds += durations.get(clip.id, 0.0)
        if clip.corpus == PLANTED_CORPUS:
            planted_total += 1
            preserved += contains_run(tokens, normalise(planted[clip.id].error))
        else:
            edits[f"{clip.corpus}/{clip.group}"].append(
                edit_counts(normalise(clip.reference), tokens)
            )
    result.wer_by_group = {
        group: word_error_rate(e) for group, e in sorted(edits.items())
    }
    if planted_total:
        result.preservation = 100 * preserved / planted_total
    result.word_timing, result.word_confidence = has_word_data(transcripts)
    if transcripts:
        times = [t.seconds for t in transcripts]
        result.latency_median_s = statistics.median(times)
        result.latency_p95_s = percentile(times, 95)
    if audio_seconds:
        result.real_time_factor = request_seconds / audio_seconds
    return result, hypotheses


def choose_winner(
    results: Sequence[EngineResult], control: str = "whisper-large-v3"
) -> str | None:
    """The selection rule: lowest WER among engines that keep errors and give word data.

    Engines within WER_TIE points of the best are ranked by price.
    The control never wins.
    """
    eligible = [
        r
        for r in results
        if r.name != control
        and r.wer is not None
        and r.preservation is not None
        and r.preservation >= PRESERVATION_MIN
        and r.word_timing
        and r.word_confidence
    ]
    if not eligible:
        return None
    best = min(r.wer for r in eligible if r.wer is not None)
    close = [r for r in eligible if r.wer is not None and r.wer - best <= WER_TIE]
    priced = [r for r in close if r.price_per_hour_usd is not None]
    pool = priced or close
    return min(
        pool,
        key=lambda r: r.price_per_hour_usd if r.price_per_hour_usd is not None else 0.0,
    ).name


def table(results: Sequence[EngineResult]) -> str:
    groups = sorted({g for r in results for g in r.wer_by_group})
    head = [
        "Engine",
        *[f"WER {g} (%)" for g in groups],
        "Errors kept (%)",
        "Word timing",
        "Confidence",
        "Latency median / p95 (s)",
        "Real-time factor",
        "USD per audio hour",
    ]
    rows = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in results:
        latency = (
            "n/a"
            if r.latency_median_s is None or r.latency_p95_s is None
            else f"{r.latency_median_s:.2f} / {r.latency_p95_s:.2f}"
        )
        rtf = "n/a" if r.real_time_factor is None else f"{r.real_time_factor:.2f}"
        price = "n/a" if r.price_per_hour_usd is None else f"{r.price_per_hour_usd:.2f}"
        cells = [
            r.name,
            *[
                f"{r.wer_by_group[g]:.1f}" if g in r.wer_by_group else "n/a"
                for g in groups
            ],
            "n/a" if r.preservation is None else f"{r.preservation:.0f}",
            "yes" if r.word_timing else "no",
            "yes" if r.word_confidence else "no",
            latency,
            rtf,
            price,
        ]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def save(
    results: Sequence[EngineResult],
    hypotheses: Mapping[str, Mapping[str, str]],
    out: Path,
) -> None:
    """Write aggregates and hypotheses to `out`, which must be outside the repo."""
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(
        json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8"
    )
    (out / "hypotheses.json").write_text(
        json.dumps(hypotheses, ensure_ascii=False, indent=1), encoding="utf-8"
    )
