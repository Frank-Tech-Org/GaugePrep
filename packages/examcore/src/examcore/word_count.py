# TCF Canada counts space-separated tokens; French puts a space before ? ! : ;
# so a token with no letter or digit is stray punctuation and is not a word.
def count_words(text: str) -> int:
    return sum(1 for token in text.split() if any(ch.isalnum() for ch in token))
