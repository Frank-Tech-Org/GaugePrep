# Audio script rules

These rules apply to listening items, audio lesson inputs, dictations and vocabulary entries. They implement spec 3.2, PRD CMS-6 and ADR-009 (ElevenLabs voices) and ADR-017 (Opus with AAC fallback).

## 1. Script markup

Scripts are plain French text with a few bracketed tags. The media job converts tags into the voice provider's controls, so authors never write provider-specific syntax.

| Tag | Effect |
|---|---|
| `[pause]` | Short pause, about 0.5 s |
| `[pause_long]` | Long pause, about 1.2 s (between parts of an announcement, before a question) |
| `[slow]` ... `[/slow]` | Slower delivery for a phrase (A1 and A2 only, for example a phone number) |
| `[noise:door]`, `[noise:phone]`, `[noise:applause]` | Short sound effect inserted at that point (from B1, never over key information) |

Write hesitations and fillers as words ("euh", "bon", "enfin", "disons") from B2 upward, where spec 3.2 asks for natural hesitations. Do not use them at A1 and A2.

## 2. Writing text for speech

- Write numbers, times and prices in words when the reading could be ambiguous: "quatorze heures", "vingt-cinq mille francs CFA", "le 06 75..." becomes "zéro six, soixante-quinze...".
- Write abbreviations in full: "Madame", "Docteur", "boulevard".
- Spell out a name the first time it matters if a learner must catch it ("Ekane, E-K-A-N-E") only when the real exam would do so (rare; mainly A1).
- Keep each turn under about 60 words so that voices stay natural; split longer speech into several turns of the same speaker.
- In dialogues, give each speaker a distinct voice (different gender or clearly different age or accent).

## 3. Voice bank

The bank holds at least 12 distinct voices (spec 3.2): women and men, ages 20 to 70, standard French with other francophone accents.

| Voice ID | Gender | Age band | Accent | Use |
|---|---|---|---|---|
| V01 to V06 | 3 female, 3 male | Spread over 20_34, 35_49, 50_70 | fr_FR | All levels |
| V07, V08 | 1 female, 1 male | 35_49 | fr_CA | B1 and above; Canadian settings |
| V09, V10 | 1 female, 1 male | 20_34, 50_70 | fr_AF_CENTRAL | B1 and above; Cameroonian and Central African settings |
| V11 | Female | 35_49 | fr_AF_WEST | B1 and above |
| V12 | Male | 35_49 | fr_BE or fr_CH | B1 and above |
| EX01 | Female | 35_49 | fr_FR | Examiner voice (ElevenLabs Flash), never used for content |
| EX02 | Male | 35_49 | fr_FR | Examiner voice, alternative |

- The voices are chosen by human listening in M1 from the provider's voice library. If the library has no convincing Central or West African French voice, a professional voice is created from a consenting speaker recorded in Douala, with a written licence for commercial use. Until then, V09 to V11 stay empty and their share is taken by V07, V08 and V12.
- Map each Voice ID to the provider's voice ID and settings in `infra/media/voices.yml`. Authors choose a voice profile; the media job picks the voice ID.
- Never more than 30% of a simulation form's listening items with a non-fr_FR voice (spec 3.2). The form builder checks it.

## 4. Speech rate

| Level | target_wpm |
|---|---|
| A1 | 100 to 120 |
| A2 | 115 to 135 |
| B1 | 140 to 160 |
| B2 | 150 to 170 |
| C1 | 160 to 185 |
| C2 | 170 to 200 |

The media job sets the provider's speed so the measured rate falls within 10% of `target_wpm`.

## 5. Background sound

- None at A1 and A2.
- From B1: light, realistic background (street, office, studio, station, shop, home, phone line) mixed at least 20 dB below speech, never over the key passage.
- Background beds are licensed royalty-free recordings stored in `infra/media/beds/` with their licence files.

## 6. Production and checks

1. Voice each turn with the mapped voice and speed; insert pauses and sound effects; mix the background.
2. Normalise loudness to -16 LUFS integrated, true peak below -1 dBTP.
3. Encode Opus 24 kb/s mono (WebM container) and AAC 48 kb/s mono (MP4 container) for iOS before 18.4; name both by content hash; store in R2.
4. Automatic checks: batch transcription compared with the script, word error rate at most 3% after normalising case, punctuation and numbers; duration within the type's range; measured rate within 10% of `target_wpm`. Failures are regenerated up to three times, then sent to the listener with the reason.
5. Human listening as in `README.md` Section 7. The listener approves, or rejects with a note (mispronounced word, unnatural intonation, key information masked).
6. Approved audio is attached to the item version. A new audio file for an approved item creates a new item version.
