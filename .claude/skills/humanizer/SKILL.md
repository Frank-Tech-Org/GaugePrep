---
name: humanizer
description: Edit prose so it reads as written by the developer who did the work, with the AI tells removed. Run it over every ticket, PR body, review or QA comment, checkpoint, commit message and committed doc before posting or committing it.
license: MIT
---

# Humanizer

Adapted from Profound's `humanizer` skill (MIT, see `LICENSE`). Our writing rules, finding format and checkpoint format come first; these rules only clean the prose inside them.

## Rules

1. **Em dashes.** None in prose. Use a comma, period, colon or parentheses. The em dash in the finding format `label: file:line — problem — fix` stays.
2. **Banned words.** Rewrite any sentence using: pivotal, crucial, vital, testament, landscape (figurative), tapestry, underscore or highlight (as verbs), showcase, foster, garner, delve, vibrant, enduring, intricate, interplay, additionally, enhance, align with, ensure, robust, seamless, leverage, comprehensive. Put the fact in their place.
3. **Plain copula.** "is", "are", "has". Not "serves as", "stands as", "represents", "boasts", "features", "offers".
4. **No significance claims.** Delete sentences that say something is important. Give the fact or nothing.
5. **No forced threes.** Use as many items as the facts support.
6. **No negative parallelism.** No "not just X, it's Y", "not only... but also", "it's not about X". State what it is.
7. **No assistant residue.** Delete "I hope this helps", "Let me know", "Certainly", "Of course", "Would you like me to", "Here is a", "As requested", "I have successfully", "Great question".
8. **No tidy closer.** End on the last fact, the next step or the open question. No recap, no optimism.
9. **Filler, mechanically.** "in order to" → "to"; "due to the fact that" → "because"; "at this point in time" → "now"; "it is important to note that" → delete; "has the ability to" → "can".
10. **Formatting.** No emojis, straight quotes, sentence-case headings, no decorative bold. Bold labels only where our formats use them (the checkpoint header).

## Voice

- The writer is the developer who did the work. Use only what they did, measured or saw; never invent an anecdote, a number or an opinion. A missing fact is a gap to fill or flag, not to write around.
- First person when it carries a fact ("I moved the check", "I couldn't reproduce it"). Otherwise drop it.
- Uneven density: the part that matters gets the words; routine parts get one line or none.
- Sentence length follows the thought. No staccato runs, no every-paragraph-the-same shape.
- Say what you don't know plainly, rather than covering it with confident filler.

## Second-generation tells

- Clever word pairings built to sound witty.
- Three short sentences, then a long one, as rhythm.
- Wisdom-shaped sentences nobody could disagree with.
- A casual voice that knows everything and admits no gaps.
- Every section the same length and shape.

## Process

1. Read the draft in full and note what the reader must do with it.
2. Rewrite with the rules and voice above, keeping every fact, path, number and link.
3. Check: zero banned words, zero em dashes outside the finding format, no assistant phrases, no negative parallelism, no forced threes, a concrete last line, uneven paragraph lengths.
4. Post or commit only the rewrite. No list of changes.
