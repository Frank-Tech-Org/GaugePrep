# CEFR levels, lowest first. examcore has no level constants yet;
# move these there when it does.
LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")


def rank(level: str) -> int:
    return LEVELS.index(level)
