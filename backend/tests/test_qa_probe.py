import pytest

from config.qa_probe import classify


@pytest.mark.parametrize(
    ("n", "expected"), [(-1, "negative"), (0, "zero"), (5, "small"), (10, "large")]
)
def test_classify(n: int, expected: str) -> None:
    assert classify(n) == expected
