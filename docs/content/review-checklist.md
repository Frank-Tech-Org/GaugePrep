# Review checklist

The reviewing agent applies this checklist to every item of a batch. The human reviewer applies it to the sample. Record each defect with its code.

## 1. Defect codes

| Code | Defect | Severity |
|---|---|---|
| K1 | Key is wrong | Critical |
| K2 | Two or more options are defensible | Critical |
| K3 | Item can be answered without the stimulus (general knowledge, logic, option wording) | Critical |
| O1 | Text copied or closely paraphrased from exam material or another source | Critical |
| F1 | Offensive, stereotyped, distressing or unfair content (politics, religion, violence, tragedy, a group put at a disadvantage) | Critical |
| L2 | Level off by two or more levels | Critical |
| L1 | Level off by one level | Major |
| D1 | Distractor implausible (no learner would choose it) | Major |
| D2 | Options not parallel (the key stands out by length, precision or form) | Major |
| T1 | Type rule broken (length, number of turns, genre, one question per document, task content) | Major |
| N1 | Unnatural or incorrect French | Major |
| R1 | Regional word or fact that only one country uses, not labelled or not the item's purpose | Major |
| P1 | Writing prompt contains a copyable opening, or EE3 documents are quotable slogans | Major |
| E1 | EO2 examiner facts incomplete or contradictory | Major |
| M1 | Metadata wrong (theme, focus, rationale, key passage, skill note) | Minor |
| Y1 | Typography or small wording issue | Minor |

## 2. Checks per type

### Listening and reading items

1. Answer the item yourself before reading the key. If your answer differs, decide whether the key or you are wrong, and record K1 or K2.
2. Cover the stimulus and try to answer from the options alone. If you can, record K3.
3. Check the level of the stimulus against the level controls of `authoring-guide.md` 1.1 and the question against spec Section 2.
4. Check each distractor: who would choose it and why? Is it clearly wrong?
5. Check option length and form, and that the key is not the only paraphrase or the only hedged option.
6. Listening: speech rate, number of voices, accents, background, duration estimate. The key is said once.
7. Reading: layout realistic; word count in range; from B2, the focus is not a stated fact for more than half the batch.
8. Theme, focus, rationale and key passage correct.

### Writing prompts

1. The task matches its type (spec 5.1) and contains all required parts (reader, points, goal, documents).
2. The prompt allows answers across its whole band.
3. No copyable opening; EE3 documents are 70 to 110 words, contrasting, attributed, and need reformulation.
4. `topic_brief` and `on_topic_requirements` are checkable and complete.

### Speaking tasks

1. EO1: 8 to 10 questions in order simple, developing, open; suitable for any adult.
2. EO2: the learner card is clear in 2 minutes of reading; 3 to 5 things to find out; examiner answers and other facts complete and consistent; the complication is realistic and has a way forward.
3. EO3: the question is open and two-sided; arguments on both sides; follow-ups are precision, example and counter view.

### Lessons

1. Structure of PRD CUR-2 complete; goal matches the unit goal in `curriculum-map.md`.
2. Input at level; explanation correct and illustrated by the input; at least two examples.
3. Every exercise item has one correct answer (or all accepted variants listed) and an explanation in both languages.
4. Production task fits the goal and has checkable success criteria.

### Vocabulary entries

1. Headword with article and gender correct; level plausible; translation accurate.
2. Example natural, at or below level, 5 to 14 words, varied settings.

## 3. Recording the verdict

The reviewing agent posts this table in the pull request:

```
| Code | Verdict | Defects | Comment |
|---|---|---|---|
| TCF-CA-CO-L4-0012 | accept | | |
| TCF-CA-CO-L4-0013 | revise | D1, M1 | Option C is never chosen: nobody would think the shop opens at midnight |
```

The human reviewer records the sample in the batch issue with the same table plus the sample decision: approved, or returned with the reason under `README.md` Section 5.
