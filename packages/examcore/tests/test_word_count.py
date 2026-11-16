import pytest
from examcore import count_words


def test_sentence_with_spaced_question_mark() -> None:
    assert count_words("Il est arrivé à l'école à 8 h 30 ?") == 9


@pytest.mark.parametrize("word", ["porte-monnaie", "2026", "l'école", "l’école"])
def test_hyphenated_number_and_elided_forms_count_one(word: str) -> None:
    assert count_words(word) == 1


@pytest.mark.parametrize("mark", ["?", "!", ":", ";"])
def test_isolated_punctuation_counts_zero(mark: str) -> None:
    assert count_words(f" {mark} ") == 0
    assert count_words(f"Vraiment {mark} Oui") == 2


@pytest.mark.parametrize("text", ["", " ", "   \t\n  ", "\u00a0\u202f"])
def test_empty_or_whitespace_counts_zero(text: str) -> None:
    assert count_words(text) == 0


@pytest.mark.parametrize(
    "separator", [" ", "\u00a0", "\u202f", "\n", "\r\n", "\t"], ids=repr
)
def test_non_breaking_spaces_and_line_breaks_separate_words(separator: str) -> None:
    assert count_words(f"Bonjour{separator}madame") == 2


def test_narrow_no_break_space_before_punctuation() -> None:
    assert count_words("Vous venez\u202f? Oui\u202f!") == 3
