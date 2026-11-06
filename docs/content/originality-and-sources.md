# Originality and sources

All GaugePrep content is original (spec 10.4, PRD Section 11). Exam owners forbid reproducing their papers, and a learner who memorises our texts must not be memorising theirs. This file says what authors may use, how, and how copying is detected.

## 1. Sources and what they may be used for

| Source | Allowed use | Not allowed |
|---|---|---|
| FEI candidate manual (TCF, version Q), sample items, published sample subjects | Study format, length and level; check that our items look like the exam (spec 9.1) | Copying, translating, or paraphrasing closely any item, text, subject or document |
| Other preparation material (TV5Monde, RFI, books, websites, competitors) | Nothing beyond general awareness of formats | Any reuse of texts, items, subjects or model answers |
| CEFR descriptors (Council of Europe) | Basis for our own level descriptions (spec Section 2) | Official descriptor wording in the learner interface (PRD Section 11) |
| Lexique 3.83 French lexical database (lexique.org) | Word frequency to help choose vocabulary entries and to check that a stimulus fits its level | Publishing a derived word list without honouring its licence (see 1.1) |
| FLELex (CEFR-graded French lexicon, UCLouvain) | None | Any use: its licence is CC BY-NC-SA 4.0, which forbids commercial use |
| Large language models | Drafting under this kit, with `drafted_with_ai` and the model recorded | Publishing anything not reviewed under `README.md` |
| Generated images (L1 items, lessons) | Images from a generator whose terms allow commercial use, recorded in the item notes | Real people, logos, brands, text in images that gives away the answer |
| Background sound beds | Royalty-free recordings with a commercial licence stored with the file | Unlicensed recordings |

### 1.1 Lexique licence

Lexique 3.83 is distributed under Creative Commons Attribution-ShareAlike 4.0 (as listed by the pylexique package that wraps it; confirm on lexique.org before first use). Attribution is required. ShareAlike applies to adaptations of the database: we use frequency values only as an input to our own choices, and we do not publish frequency data. The headwords, translations, examples and levels of our entries are our own work. If we ever publish a list derived from Lexique data (for example frequency ranks), it must carry the same licence.

## 2. Copying and closeness checks

The validator does not check originality; a separate check runs in CI on every content pull request:

1. **Reference set.** A private folder `reference/do-not-copy/`, outside the content tree and never imported, holds the text of FEI sample items and published subjects that the team has studied, and any other material an author reports having read. It exists only for comparison.
2. **Exact overlap.** Any sequence of 8 or more consecutive identical words (after normalising case and punctuation) between a new item and the reference set, or another item in the bank, fails the check (the same threshold the product applies to learners, spec 5.3).
3. **Near duplicates.** Cosine similarity of sentence embeddings above 0.90 between a new stimulus and any reference text or bank item sends the item to the human reviewer with defect O1 suspected.
4. **Within the bank.** Two items in the bank with near-duplicate stimuli are allowed only if one is a planned new version of the other.

A failed check blocks the merge until the item is rewritten or the human reviewer records why it is not copying.

## 3. Rights for content from people

- Voices created from a real speaker need that speaker's written consent and licence for commercial use.
- Learner texts or recordings are never turned into content (items, model answers). They may become anchors only under the anchor protocol and the learner's optional consent (PRD ACC-7).
