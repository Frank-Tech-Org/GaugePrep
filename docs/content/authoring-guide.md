# Authoring guide

How to write each content type for TCF Canada and the French curriculum. Read Section 1 for every type, then the section for your type. "Spec" means the TCF Canada exam specification.

## 1. Rules for every type

### 1.1 Level controls

The target level decides the language of the stimulus (what the learner hears or reads) and the difficulty of the task. Use these controls with the construct descriptions of spec Section 2.

| Level | Vocabulary | Grammar and sentences | Text organisation | Topics |
|---|---|---|---|---|
| A1 | The most frequent everyday words; names, numbers, days, times, prices | Present tense; short main clauses; questions with est-ce que, où, quand, combien | One or two sentences; no connectors beyond et | Self, family, home, shopping, transport, time |
| A2 | Frequent words for routine and practical life | Passé composé, futur proche, imperative; simple relative qui; parce que, mais | Short messages and announcements, one idea per sentence | Appointments, travel, work routine, services, health basics |
| B1 | Wider everyday and work vocabulary; common expressions | Imparfait with passé composé, futur simple, conditionnel of politeness, relatives que and où, simple subordinates | Connected paragraphs; clear main point; standard order of events | Work, studies, housing, local news, leisure, opinions on familiar topics |
| B2 | Abstract and professional vocabulary; some idioms | Subjunctive after opinion and necessity, passive, gérondif, concession (bien que, même si), reported speech | Argument with position and reasons; contrast; implicit attitude | Society, environment, technology, education, consumption |
| C1 | Precise, nuanced, low-frequency vocabulary; register shifts | Full range, including complex nominal phrases, nuanced modality | Long, dense texts; implicit links; irony and hedging | Abstract and specialised topics, debates |
| C2 | Specialised, literary and idiomatic language | Any structure, including literary tenses in written texts | Complex structure; fine shades of meaning; the point is often implicit | Any topic, including specialised and cultural |

An item tests its level in two ways: the stimulus is written at the level, and the question targets what a learner at that level can do (spec Section 2). A hard question on an easy text, or an easy question on a hard text, does not make a well-placed item.

### 1.2 Themes and settings

- Use the 13 themes of spec 5.2 (codes in `schemas/common.schema.json`): housing, work, education, health, transport, environment, technology, consumption, leisure, family, community life, culture, city and countryside.
- Set situations across the French-speaking world: Cameroon and other francophone African countries, Canada (Québec and outside Québec), France, Belgium, Switzerland. Learners preparing for Canada should meet Canadian situations (renting, workplace, services) often, but never so often that the exam feels foreign to a learner in Douala.
- Names: mix names common in Cameroon (Ngo Bayiha, Mbarga, Ekane, Tchoupo, Abena, Fouda, Nkoulou, Atangana), elsewhere in Africa, Québec and France. Use invented names only; never a real living person, except public figures in neutral factual contexts at C1 and C2 (spec 10.4).
- No brand names, no politics, religion, violence, tragedy, or content that could distress or disadvantage a group (spec 3.3 and 10.4).
- Money: FCFA in African settings, dollars in Canadian settings, euros in European settings.

### 1.3 Multiple-choice rules

These apply to listening and reading (spec 3.3, 4.2).

1. **One defensible answer.** Ask yourself: could a strong learner argue for another option? If yes, rewrite.
2. **Plausible distractors.** Each distractor must attract a learner who misheard, misread or misunderstood, and must be clearly wrong for one who understood. Proven techniques:
   - a word or number that is heard or read in the text but answers a different question (the "echo" distractor);
   - the right topic with the wrong detail (day, price, person, place);
   - a statement that is true in general but not said in the text;
   - an inference that goes too far;
   - the opposite of the speaker's or writer's attitude, or the attitude of another person in the text.
3. **Parallel options.** Similar length and grammar; the correct option is not systematically the longest, the most specific or the only one with a hedge.
4. **No word matching.** From A2, the correct option paraphrases the text; distractors may reuse text words (that is what makes them attractive).
5. **Key balance.** Spread keys evenly within the batch, each letter between 20% and 30% of the batch.
6. **Independence.** The answer to one item must never depend on, or appear in, another item of the same batch.
7. **Rationales.** Write one rationale per option: why it is right, or why a learner might choose it and why it is wrong. These are shown in feedback (spec 11).
8. **Key passage.** Copy the exact words of the script or document that answer the question into `key_passage`. The validator checks that they occur verbatim.

### 1.4 Language quality

- Correct, natural French; standard spelling (French typographic spaces before ? ! : ; are allowed).
- Mark regional usage in `authoring.regional_usage`.
- Learner-facing instructions in exam style: "Vous écrivez...", "Écoutez...", "Lisez le document...".
- English is used only for reviewer and grader fields (`situation`, `topic_brief`, `rationale`, `skill_note`, labels).

## 2. Listening items (L1 to L6)

Schema: `schemas/listening-item.schema.json`. Example: `examples/TCF-CA-CO-L4-0001-v1.json`. Audio markup and voices: `audio-script-rules.md`.

| Type | How to write it |
|---|---|
| L1 Picture match (A1) | Write an image brief showing one clear scene. Write four short spoken sentences (`options_mode: spoken`), one describing the scene, three describing a nearby scene (wrong object, wrong number, wrong action). The script has no turns: the options are the recording. The alt text must not reveal the answer. |
| L2 Question and answer (A1 to A2) | The script is one spoken question. The four options are spoken answers; only one is a natural answer to that question. Distractors answer a different question word (où vs quand vs avec qui). |
| L3 Short exchange (A2 to B1) | Two voices, 3 to 6 turns, an everyday situation. The question is spoken; the four options are written. Test what was decided, asked or proposed, not a detail mentioned in passing. |
| L4 Message or announcement (A2 to B1) | Voicemail, public announcement or instructions, one speaker. Test the action requested, a changed detail or a condition. |
| L5 Media extract (B1 to C1) | News item, interview or report on a personal or professional topic, 40 to 70 s. Test main idea, a key detail, or the speaker's attitude. At B2 and C1, use attitude and inference. |
| L6 Talk or debate (C1 to C2) | Talk, lecture, debate or specialised interview on an abstract topic, 50 to 80 s. Test the argument, an implicit meaning or the speaker's intention. Natural hesitations and reformulations belong in the script. |

Additional rules:

- The key information is said once. Do not repeat it in a way that makes the item easier than the exam (spec 3.3).
- Speech rate (`target_wpm`): A1 100 to 120, A2 115 to 135, B1 140 to 160, B2 150 to 170, C1 160 to 185, C2 170 to 200 (spec 3.2).
- From B1, up to 30% of the items in a batch may use a non-French-from-France accent; label it in the voice profile. Never put the key information in a word whose pronunciation differs strongly between varieties.
- Estimate duration: words divided by target_wpm, times 60, plus pauses. Keep within the type's range.

## 3. Reading items (R1 to R6)

Schema: `schemas/reading-item.schema.json`. Example: `examples/TCF-CA-CE-R5-0001-v1.json`.

| Type | How to write it |
|---|---|
| R1 Sign or notice (A1), 10 to 40 words | A sign, label, short notice or simple form. Literal question. Use `layout` sign, label or form. |
| R2 Everyday document (A1 to A2), 40 to 100 words | Advertisement, timetable, menu, leaflet or opening hours. Use `table` for tabular documents. The question asks to locate one piece of information; distractors are other values present in the document. |
| R3 Personal or administrative message (A2 to B1), 60 to 150 words | Email, letter or text message with a visible header (`email_header`). Ask about the purpose, the requested action, or a detail. |
| R4 Everyday or work text (B1 to B2), 120 to 250 words | Practical article, internal memo, instructions or report. Ask about the main idea, a detail or a simple inference. |
| R5 Opinion article (B2 to C1), 200 to 350 words | A press article or review where the writer takes a position. Give a fictional `attribution`. Ask about the writer's view, an argument, or the function of a passage. |
| R6 Long complex text (C1 to C2), 300 to 500 words | Long factual, literary or specialised extract. Ask about implicit meaning, structure or nuance. |

Additional rules:

- One question per document, as in the real exam (spec 4.2).
- Realistic layout: a timetable looks like a timetable, an email shows sender and subject.
- Word counts use the exam rule and are checked by the validator.
- A form's reading load stays at or below 9,000 words (spec 4.2); the form builder enforces it, so do not inflate documents beyond what the type needs.

### 3.1 Light markup in `body`

- Blank line between paragraphs.
- `**bold**` for headings inside notices and leaflets.
- Lines starting with `- ` for lists.
- No other markup, no HTML.

## 4. Writing prompts (EE1 to EE3)

Schema: `schemas/writing-prompt.schema.json`. Example: `examples/TCF-CA-EE-EE3-0001-v1.json`.

| Task | What the prompt contains (spec 5.1, 5.2) |
|---|---|
| EE1, 60 to 120 words | A situation in one or two sentences, the reader and their status, and 2 or 3 points to cover. Genre message, email or note. Designed to discriminate A1 to B1. |
| EE2, 120 to 150 words | A situation, the readers (several), the goal (claim, persuade, reconcile, recommend...) and the experience to report. Genre article, blog post, newsletter article or letter. Discriminates A2 to B2. |
| EE3, 120 to 180 words | A short instruction and two documents of 70 to 110 words each, with contrasting views on the same social issue, each with a plausible fictional source. The learner compares them and gives an opinion. Discriminates B1 to C2. |

Rules:

- Every theme has prompts in every task type: 40 prompts per type over 13 themes means 3 per theme plus one extra for 1 theme.
- The prompt never contains a sentence a learner could copy as an opening (spec 5.2). The EE3 documents use wording the learner must reformulate: avoid short, quotable slogans.
- The `instruction_fr` ends with the word range in the exam's style: "(60 mots minimum, 120 mots maximum)".
- `topic_brief` and `on_topic_requirements` drive the off-topic check and the grader's task-fulfilment judgement. Write them as checkable statements.
- A prompt must allow an answer at every level of its band: an EE3 issue that only a specialist can discuss is unfair at B1.

## 5. Speaking tasks (EO1 to EO3)

Schema: `schemas/speaking-task.schema.json`. Examples: `examples/TCF-CA-EO-EO1-0001-v1.json`, `...-EO2-0001-v1.json`, `...-EO3-0001-v1.json`.

| Task | What to write (spec 6.1, 6.3) |
|---|---|
| EO1 interview set | 8 to 10 questions ordered simple, developing, open. Start with identity and home, move to work or studies and daily life, end with experiences, plans and an opinion. Questions must suit an adult in Cameroon or Canada: never assume a car, a degree or children. |
| EO2 interaction card | The learner-facing card (`card_fr`), roles, 3 to 5 things to find out with the examiner's answers, one realistic complication with its trigger and alternatives, and `other_facts_fr` covering likely extra questions (address, payment, opening hours, documents) so that the examiner never invents facts that contradict each other. |
| EO3 question | One question on a social issue from the writing themes, a short issue summary, at least two arguments on each side for the examiner and the grader, and exactly three follow-ups: one asking for precision, one for an example, one presenting the opposite view. |

The examiner reads only the French fields to the learner; English fields guide the examiner model and the grader.

## 6. Curriculum lessons

Schema: `schemas/lesson.schema.json`. Example: `examples/FR-CUR-B1-U04-L2-v1.json`. Units and goals: `curriculum-map.md`.

- A lesson follows PRD CUR-2: goal, input, explanation, practice, short production task, summary.
- 15 to 25 minutes for most learners (`estimated_minutes`).
- The input (text or audio) is at the lesson's level and illustrates the explanation.
- Two to four practice exercises, each with 3 to 12 items, automatically checkable (choice, gap fill, ordering, matching, dictation). Accept every correct variant in `answer`, separated by ` || `.
- The production task is short (writing 40 to 120 words, or speaking 1 to 2 minutes) and has 2 to 4 success criteria that the feedback engine uses.
- Explanations and summaries are given in French and English. Keep the French explanation at or below the lesson's level from B1 upward; at A1 and A2, the English explanation carries the detail.
- Link lessons to the TCF task types they prepare (`tcf_link`), so the study plan can recommend them for a skill gap.
- The fourth lesson of each unit ends with exam practice in the linked task format.

## 7. Free-track vocabulary

Schema: `schemas/vocabulary-entry.schema.json`. Example: `examples/FR-VOC-transport-0001-v1.json`. Themes: `vocabulary-themes.md`.

- About 50 entries per theme, A1 to B2, words and fixed expressions. Nouns are taught with their article.
- The example sentence is natural, 5 to 14 words, at or below the entry's level, and set in a varied francophone context.
- Add a `regional_note` where a common alternative exists in Cameroon, Canada or France.
- Word selection uses frequency information under the licence rules of `originality-and-sources.md`. The headword list, translations and example sentences are our own.
