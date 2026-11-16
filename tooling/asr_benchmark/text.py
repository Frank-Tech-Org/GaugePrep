import re
import unicodedata

_APOSTROPHES = re.compile(r"[’‘`´]")
_NOT_WORD = re.compile(r"[^\w\s]|_", re.UNICODE)


def normalise(text: str) -> list[str]:
    """Split text into comparable tokens, the same way for every engine.

    Lowercases, drops punctuation, and splits elisions and hyphens into separate
    tokens, so "j'ai" and "J’ai" match. Accents and spelling are kept: a fixed
    accent or agreement is an error the learner did not make.
    """
    text = unicodedata.normalize("NFC", text).lower()
    text = _APOSTROPHES.sub("'", text).replace("'", " ").replace("-", " ")
    return _NOT_WORD.sub(" ", text).split()
