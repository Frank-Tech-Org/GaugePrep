import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Edits:
    errors: int
    reference_words: int


def edit_counts(reference: Sequence[str], hypothesis: Sequence[str]) -> Edits:
    """Substitutions, deletions and insertions between two token lists."""
    previous = list(range(len(hypothesis) + 1))
    for i, ref_word in enumerate(reference, start=1):
        current = [i]
        for j, hyp_word in enumerate(hypothesis, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (ref_word != hyp_word),
                )
            )
        previous = current
    return Edits(previous[-1], len(reference))


def word_error_rate(edits: Sequence[Edits]) -> float:
    """Corpus-level WER in percent: total errors over total reference words."""
    words = sum(e.reference_words for e in edits)
    if words == 0:
        raise ValueError("no reference words to score")
    return 100 * sum(e.errors for e in edits) / words


def contains_run(tokens: Sequence[str], run: Sequence[str]) -> bool:
    """True when `run` appears in `tokens` as consecutive words."""
    n = len(run)
    return n > 0 and any(
        tuple(tokens[i : i + n]) == tuple(run) for i in range(len(tokens) - n + 1)
    )


def percentile(values: Sequence[float], pct: float) -> float:
    """Nearest-rank percentile of a non-empty list."""
    if not values:
        raise ValueError("no values")
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]
