# GaugePrep: TCF Canada Exam Specification and Calibration Brief

## 0. Document control

| Field | Value |
|---|---|
| Document | TCF Canada exam specification and calibration brief |
| Version | 1.1 (anchor rules, 5 November 2026) |
| Date | 22 October 2026 |
| Owner | Frank, founder |
| Parent document | GaugePrep Product Requirements Document v1.0 |
| Exam reference | France Éducation international (FEI), Manuel du candidat TCF, version Q, September 2026; IRCC test equivalency chart |
| Used by | Content authors and reviewers, the prediction grader, the simulation engine, the system architecture |

This document is the single source of truth for how GaugePrep reproduces TCF Canada: the exam rules, the construct per skill and level, the specification of every item and task type, the simulation form blueprint, the scoring and prediction model, the calibration plan, and the content production rules. The PRD says what the product does; this document says exactly how TCF Canada is modelled. Every rule here is stored as versioned exam data in the product, and a change to this document creates a new version of that data.

## 1. Exam rules

### 1.1 The four papers

| Paper | Items or tasks | Time | Delivery rules |
|---|---|---|---|
| Listening (CO) | 39 multiple-choice items, 4 options, one correct | 35 min | Each recording played once; the question comes after the recording; increasing difficulty; no entry or exit during the paper |
| Reading (CE) | 39 multiple-choice items, 4 options, one correct | 60 min | Increasing difficulty |
| Writing (EE) | 3 tasks | 60 min for the three tasks | Task 1: 60 to 120 words; task 2: 120 to 150 words; task 3: 120 to 180 words |
| Speaking (EO) | 3 tasks, face to face with an examiner, recorded | 12 min | Task 1: 2 min, no preparation; task 2: 3 min 30, after 2 min preparation; task 3: 4 min 30, no preparation |

All papers are compulsory for TCF Canada. Total exam time is 2 h 47 min.

### 1.2 Scoring rules

- Multiple-choice: only correct answers earn credit; wrong and blank answers earn nothing; there is no penalty for guessing. Each correct answer is weighted by the item's difficulty and the result is converted to a score from 100 to 699. The number of correct answers is not disclosed.
- Writing and speaking: two independent raters each give each of the three tasks a level from "A1 not reached" to C2. A rule combining the six levels gives a mark out of 20. A third rating is made when the two raters differ widely.
- Writing criteria: linguistic (range of vocabulary, grammatical accuracy, spelling, sentence elaboration), pragmatic (coherence, cohesion, thematic development), sociolinguistic (fit to the communication situation).
- Speaking criteria: linguistic (range and control of vocabulary, grammar, ease, pronunciation, overall fluency), pragmatic (interaction, structure of discourse, coherence and cohesion, thematic development), sociolinguistic (fit to the situation).
- A writing task is rated "A1 not reached" when it is under or over its word range, off topic, missing, copied from the prompt or the documents, or a memorised text. A speaking performance can be rated "A1 not reached" when the candidate recites a memorised text, and recitation can be treated as fraud. The examiner may interrupt a candidate suspected of reciting.

### 1.3 Score bands

| CEFR | Scale out of 699 | Mark out of 20 |
|---|---|---|
| A1 not reached | 0 to 99 | 0 |
| A1 | 100 to 199 | 1 |
| A2 | 200 to 299 | 2 to 5 |
| B1 | 300 to 399 | 6 to 9 |
| B2 | 400 to 499 | 10 to 13 |
| C1 | 500 to 599 | 14 to 17 |
| C2 | 600 to 699 | 18 to 20 |

### 1.4 NCLC conversion

| NCLC | Listening /699 | Reading /699 | Speaking /20 | Writing /20 |
|---|---|---|---|---|
| 10 and above | 549 to 699 | 549 to 699 | 16 to 20 | 16 to 20 |
| 9 | 523 to 548 | 524 to 548 | 14 to 15 | 14 to 15 |
| 8 | 503 to 522 | 499 to 523 | 12 to 13 | 12 to 13 |
| 7 | 458 to 502 | 453 to 498 | 10 to 11 | 10 to 11 |
| 6 | 398 to 457 | 406 to 452 | 7 to 9 | 7 to 9 |
| 5 | 369 to 397 | 375 to 405 | 6 | 6 |
| 4 | 331 to 368 | 342 to 374 | 4 to 5 | 4 to 5 |

Below NCLC 4 the product reports the CEFR level only. Express Entry's French-language category requires at least NCLC 7 in all four skills, which is the default target.

### 1.5 Administrative rules reproduced in the product

- Results are valid for two years from the date they are issued.
- A resit of the same TCF version requires at least 20 days between sittings.
- Results from different sittings cannot be combined.
- There is no access to scripts, recordings or corrections, and no appeal after the attestation is issued.

## 2. Construct: what each level means in each skill

The descriptors below are GaugePrep's own wording, built from the CEFR and FEI's description of each paper. They drive item writing, task rating, anchors and feedback.

### 2.1 Listening

| Level | The learner can |
|---|---|
| A1 | Recognise familiar words and very basic phrases about themselves and their immediate surroundings, spoken slowly and clearly; link a short spoken sentence to a picture or a simple situation |
| A2 | Understand short, clear messages and announcements and the main point of everyday exchanges (shopping, transport, appointments, work routines) |
| B1 | Understand the main points of clear standard speech on familiar topics: dialogues, phone calls, simple radio items, practical instructions |
| B2 | Follow extended speech and radio or television reports on current, personal or professional topics, including the speaker's attitude, at normal speed |
| C1 | Follow talks, interviews and debates on abstract or complex topics; understand implicit meaning, nuance and the structure of an argument |
| C2 | Understand any spoken French at natural speed, including specialised talks, fast colloquial exchanges and fine shades of meaning |

### 2.2 Reading

| Level | The learner can |
|---|---|
| A1 | Understand familiar names, words and very simple sentences in signs, short messages and forms |
| A2 | Find specific information in everyday documents (advertisements, timetables, menus, notices) and understand short personal or administrative letters |
| B1 | Understand texts in everyday or work language and descriptions of events, feelings and wishes in personal letters |
| B2 | Understand articles and reports in which writers take a position on concrete or abstract topics |
| C1 | Understand long, complex factual or literary texts and specialised articles, including implicit attitudes |
| C2 | Understand abstract, structurally or linguistically complex texts from books and specialised publications |

### 2.3 Writing

| Level | The learner can |
|---|---|
| A1 | Write isolated phrases and very simple sentences about themselves and immediate needs |
| A2 | Write a short, simple message linked with basic connectors (et, mais, parce que) to describe or explain something concrete |
| B1 | Write a connected text on familiar topics, narrate an experience, give and briefly justify an opinion; errors do not block understanding |
| B2 | Write a clear, detailed text that reports an experience with comments, compares viewpoints and argues a position; good control of grammar; register adapted to the reader |
| C1 | Write a well-structured, fluent text on complex topics with a wide range of vocabulary and structures, precise argument and consistent register |
| C2 | Write a complex, nuanced, stylistically appropriate text with full control of language and argument |

### 2.4 Speaking

| Level | The learner can |
|---|---|
| A1 | Answer simple questions about themselves with isolated words and memorised phrases; needs slow, repeated speech |
| A2 | Exchange simple information on familiar topics; ask and answer simple questions; describe family, work and routine in short sentences |
| B1 | Handle an everyday transaction, ask for the information needed, narrate and give a simple justified opinion with some hesitation |
| B2 | Interact with a stranger with ease, obtain detailed information, argue a viewpoint clearly with examples and react to interruptions |
| C1 | Speak fluently and spontaneously on complex topics, structure a convincing argument, handle objections and adjust register |
| C2 | Speak with full fluency and precision, with subtle argument and natural reformulation |

## 3. Listening item specification

### 3.1 Item types

| Type | Level range | Stimulus | Question and options | Audio length |
|---|---|---|---|---|
| L1 Picture match | A1 | An image on screen | Four short spoken sentences; choose the one that matches the image | 10 to 15 s |
| L2 Question and answer | A1 to A2 | A spoken question | Four spoken answers; choose the appropriate one | 10 to 20 s |
| L3 Short exchange | A2 to B1 | A two-voice dialogue of 3 to 6 turns in an everyday situation | Spoken question, four written options | 20 to 40 s |
| L4 Message or announcement | A2 to B1 | Voicemail, public announcement, instructions | Spoken question, four written options | 20 to 40 s |
| L5 Media extract | B1 to B2 | Radio or television news item, interview, report on a personal or professional topic | Spoken question, four written options on main idea, detail or attitude | 40 to 70 s |
| L6 Talk or debate | C1 to C2 | Talk, lecture, debate or specialised interview on an abstract topic | Spoken question, four written options on argument, implicit meaning or speaker intention | 50 to 80 s |

### 3.2 Audio rules

- Speech rate: slow and very clear at A1 (about 100 to 120 words per minute), natural standard speed from B1 (about 140 to 170), fast natural speed at C2 (up to 200), with natural hesitations from B2 upward.
- Voices: at least 12 distinct voices in the bank, women and men, ages 20 to 70, standard French with a share of other francophone accents (Canadian, Belgian, Swiss, West and Central African) from B1 upward, never above 30% of a form.
- Sound: clean studio-quality audio; light, realistic background sound allowed from B1 (street, office, radio studio) as long as the key information stays audible.
- Each audio file is reviewed by a human listener before publication, who checks pronunciation, naturalness and that the key information is audible.

### 3.3 Item writing rules

- One unambiguous correct answer. Each distractor is plausible for a learner who misheard or misunderstood, and wrong for a learner who understood.
- The key information is heard once and is not repeated in a way that makes the item easier than the real exam.
- Options are similar in length and grammatical form; the correct option is not systematically the longest or the most specific.
- The question tests understanding of the recording, not general knowledge or reasoning outside it.
- Keys are balanced across A, B, C and D within a form (each between 20% and 30%).
- No item tests a word or fact that only one French-speaking country uses, unless the item's purpose is that variety.
- Topics avoid politics, religion, violence and anything that could distress or disadvantage a group of learners.

## 4. Reading item specification

### 4.1 Item types

| Type | Level range | Document | Question focus | Length |
|---|---|---|---|---|
| R1 Sign or notice | A1 | Sign, label, short notice, simple form | Literal information | 10 to 40 words |
| R2 Everyday document | A1 to A2 | Advertisement, timetable, menu, leaflet, opening hours | Locating specific information | 40 to 100 words |
| R3 Personal or administrative message | A2 to B1 | Email, letter or message from a friend, company or office | Purpose, requested action, detail | 60 to 150 words |
| R4 Everyday or work text | B1 to B2 | Practical article, internal memo, instructions, report | Main idea, detail, inference | 120 to 250 words |
| R5 Opinion article | B2 to C1 | Press article or review where the writer takes a position | Writer's view, argument, attitude | 200 to 350 words |
| R6 Long complex text | C1 to C2 | Long factual, literary or specialised extract | Implicit meaning, structure, nuance | 300 to 500 words |

### 4.2 Item writing rules

- One question per document, as in the real exam.
- Documents are original and realistic in layout: a timetable looks like a timetable, an email shows sender and subject.
- Questions do not repeat key words of the text in the correct option only; paraphrase is used from A2 upward.
- From B2, at least half of the items test the writer's position, an inference or the function of a passage rather than a stated fact.
- The same distractor, key balance and topic rules as listening apply.
- Total reading load of a simulation form stays at or below 9,000 words so that it can be completed in 60 minutes.

## 5. Writing task specification

### 5.1 Task definitions

| Task | Function | Genre and reader | Word range | Levels it discriminates best |
|---|---|---|---|---|
| Task 1 | Describe, narrate or explain | A message to one or more people whose status is given (friend, colleague, neighbour, landlord) | 60 to 120 | A1 to B1 |
| Task 2 | Report an experience or tell a story with comments, opinions or arguments toward a goal (to claim, to persuade, to reconcile, to recommend) | Article, letter or note to several readers (blog, association newsletter, team, company) | 120 to 150 | A2 to B2 |
| Task 3 | Compare two viewpoints on a social issue expressed in two short documents and give one's own opinion | Text for a newspaper, website, colleague or superior | 120 to 180 | B1 to C2 |

### 5.2 Prompt construction

- Task 1 prompt: situation in one or two sentences, the reader and their status, and two or three points to cover.
- Task 2 prompt: situation, the readers, the goal of the text and the experience to report.
- Task 3 prompt: a short instruction and two documents of 70 to 110 words each, expressing opposed or contrasting views on the same social issue, each attributed to a plausible source (a reader's letter, a professional, an association).
- Themes: housing, work, education, health, transport, environment, technology, consumption, leisure, family, community life, culture, cities and countryside. Every theme has prompts at every task.
- Prompts never contain sentences a learner could copy as an opening; the documents of task 3 use wording the learner must reformulate.

### 5.3 Rule checks run before rating

| Check | Rule | Result if it fails |
|---|---|---|
| Missing task | Fewer than 5 words written | Task rated A1 not reached |
| Word range | Words counted as sequences of characters separated by spaces; a hyphenated word and a number each count as one word; an elided form such as "l'école" counts as one word | Below the minimum or above the maximum: task rated A1 not reached, and the learner is shown the exact count and the rule |
| Copying from the prompt or documents | 8 or more consecutive words identical to the prompt or the documents, or more than 20% of the text overlapping with them | Task rated A1 not reached, with the copied passages highlighted |
| Off topic | The text does not address the situation and goal of the prompt, judged by the topic classifier and confirmed by the grader | Task rated A1 not reached |
| Memorised text | Similarity of 70% or more with a known template, a published model text, or another learner's submission | Task rated A1 not reached and flagged for review; feedback explains the real exam rule |
| Similarity to the learner's own past text | 70% or more with one of the learner's previous submissions on another prompt | Flagged in feedback as recitation risk; rated normally |

During a simulation, the word counter is visible as in the computer-based exam, and text outside the range is never blocked.

### 5.4 Rating scale per task

Each task receives one level from "A1 not reached" to C2. The grader decides it from three criteria, each judged on the same scale:

| Criterion | What is judged |
|---|---|
| Linguistic | Range and precision of vocabulary; grammatical accuracy and complexity; spelling; sentence elaboration |
| Pragmatic | Task fulfilment (all requested points, the goal reached); coherence; cohesion and connectors; thematic development |
| Sociolinguistic | Fit to the reader and situation: register, politeness forms, format of the genre |

The task level is the level supported by at least two of the three criteria, never more than one level above the lowest criterion. A task cannot be rated above the level the task can show: task 1 is capped at C1, because a 120-word message cannot show C2 argument.

### 5.5 Grading procedure

1. Rule checks (5.3).
2. Two independent grading passes with the grader prompt, the task's level descriptors and the exemplars for that task type (never the evaluation anchors). Each pass returns a level per criterion, the task level and quoted evidence from the learner's text.
3. If the two task levels differ by one level, the lower is kept when the criteria are split, otherwise the level most supported by the criteria. If they differ by more than one level, a third pass decides.
4. The three task levels are combined into a mark out of 20 (Section 8.3).

## 6. Speaking task specification

### 6.1 Task definitions

| Task | Duration | Preparation | What the AI examiner does | What the learner must show |
|---|---|---|---|---|
| Task 1 Directed interview | 2 min | None | Greets the learner, then asks questions about their life, family, work, studies, interests and plans, moving from simple to more open questions | Talk about self and environment, answer and develop |
| Task 2 Interaction exercise | 3 min 30 | 2 min with a task card | Plays a role given on the card (seller, landlord, receptionist, colleague, official); answers only what is asked; adds one realistic complication | Ask relevant, polite questions to obtain the information needed in an everyday situation; react to the answers |
| Task 3 Point of view | 4 min 30 | None | Reads a question on a social issue, lets the learner speak, then interrupts at least twice to ask for precision, an example or a reaction to an opposite view | Speak spontaneously, continuously and convincingly; structure an argument; defend it under questioning |

### 6.2 Examiner behaviour rules

- The examiner speaks standard French at a natural pace, simplifies once if the learner clearly does not understand, and never teaches or corrects during a simulation.
- Turn timing follows the real task durations; the examiner closes each task politely when its time ends and announces the next one.
- In task 2, the examiner does not volunteer information the learner has not asked for.
- In task 3, the examiner interrupts after about 60 to 90 seconds of uninterrupted speech and again later, with questions linked to what the learner said.
- When speech sounds recited (fluent, unrelated to the question asked, or matching a known template), the examiner asks a follow-up question about a detail of what was said, as a real examiner would.
- The examiner's voice is synthetic and disclosed as an AI at the start of every session.

### 6.3 Task cards and question bank

- Task 1 sets: 30 sets of 8 to 10 questions each, ordered from simple to open.
- Task 2 cards: 40 scenarios. Each card gives the setting, the learner's role and goal, and three to five things to find out (prices, times, conditions, documents, alternatives). The examiner's hidden sheet gives the answers and one complication.
- Task 3 questions: 60 questions on the same themes as writing task 3, each with three examiner follow-up questions.

### 6.4 Rating

- Criteria: linguistic (vocabulary, grammar, ease, pronunciation, fluency), pragmatic (interaction, structure, coherence, thematic development), sociolinguistic (fit to the situation and the interlocutor).
- Evidence: the transcript, plus measures from the audio: speech rate, length and frequency of pauses, self-corrections, and pronunciation confidence per word.
- Accent is never penalised. Pronunciation is judged only on intelligibility: a word the recogniser misreads but a listener would understand is not a fault.
- The same level rules, double pass, third pass and combination model as writing apply.
- Recordings shorter than 30% of the task time are rated "A1 not reached" for that task, as a missing task.

## 7. Simulation form specification

### 7.1 Listening and reading blueprint

Each form has 39 items per paper, ordered by increasing difficulty. The distribution by level is GaugePrep's design, set to measure across the whole scale with the most precision around B1 to C1, where NCLC 5 to 9 sit.

| Level | Listening items | Reading items | Listening types | Reading types |
|---|---|---|---|---|
| A1 | 4 | 4 | L1, L2 | R1, R2 |
| A2 | 6 | 6 | L2, L3, L4 | R2, R3 |
| B1 | 8 | 8 | L3, L4, L5 | R3, R4 |
| B2 | 9 | 9 | L5 | R4, R5 |
| C1 | 8 | 8 | L5, L6 | R5, R6 |
| C2 | 4 | 4 | L6 | R6 |
| Total | 39 | 39 | | |

### 7.2 Form assembly constraints

- No item appears in two forms.
- Mean difficulty per level within 0.15 logits of the bank mean for that level, so that forms are comparable.
- Within each paper, no two consecutive items on the same theme, and at least 8 different themes per form.
- Listening: total audio plus a 10-second answer window per item fits within 35 minutes.
- Reading: total word load at or below 9,000 words.
- Key balance between 20% and 30% for each option letter.
- Each form has one writing set (one prompt per task, on three different themes) and one speaking set (one task 1 set, a choice of one of two task 2 cards drawn at random, one task 3 question).

### 7.3 Delivery rules in simulation mode

- Listening: each recording plays once, automatically; the question and options appear after the recording; the learner has a 10-second answer window and may move on earlier; no pause, rewind or replay; the paper ends at 35 minutes.
- Reading: free navigation between the 39 items, with a flag for review; the paper ends at 60 minutes.
- Writing: the three tasks on one screen with tabs, a word counter per task, a single 60-minute timer; no spelling or grammar correction in the editor; copy and paste from the prompt disabled.
- Speaking: microphone check before the paper; 2-minute preparation timer before task 2 only, with a notes area; tasks run back to back.
- A paper that is started must be finished in the same session; after a connection loss, the learner resumes with the remaining time and all saved answers.

### 7.4 Forms in service

- 5 complete forms at launch, then one new form per month.
- A learner receives forms in an order that avoids repeats; once all forms are used, the oldest is reused and the result is marked as a repeat, with lower weight in prediction.

## 8. Scoring and prediction model

### 8.1 Listening and reading: ability estimation

- Model: Rasch model (one-parameter item response theory). Each item has a difficulty b; a learner of ability θ answers correctly with probability 1 / (1 + e^-(θ - b)).
- Initial item difficulty from the item's target level: A1 = -3.0, A2 = -1.8, B1 = -0.6, B2 = 0.6, C1 = 1.8, C2 = 3.0, adjusted by the reviewer by up to ±0.5 within the level.
- Item re-estimation: once an item has 200 responses, its difficulty is estimated from data by joint or marginal maximum likelihood, and the whole bank is re-estimated monthly on a common scale anchored by items whose estimates are stable.
- Learner ability: estimated by maximum a posteriori with a standard normal prior centred on the learner's last estimate, from all responses in the last 60 days. Simulation responses have weight 1.0, practice responses in exam mode 0.7, practice responses in learning mode 0.4 (learning mode allows replay, so it overstates listening ability).
- Standard error: computed from the test information of the items answered.

### 8.2 Listening and reading: conversion to the 699 scale

- Cut points: for each level boundary, the ability at which a learner answers 67% of the items of the lower level correctly defines the start of the next band (for example, the B1 to B2 cut is the ability with a 67% chance of success on the average B1 item).
- Within a band, ability is converted linearly to the band's 100 points (for example, B2 = 400 to 499). Below the A1 cut, the score is 0 to 99; above the top of C2, it is capped at 699.
- The scale point estimate gives the CEFR level, and the NCLC level through the table in 1.4.
- The cut points are refitted from verified real results once 100 results exist for the paper (Section 9.3).

### 8.3 Writing and speaking: combination into a mark out of 20

- Each task level becomes a value: A1 not reached = 0, A1 = 1, A2 = 2, B1 = 3, B2 = 4, C1 = 5, C2 = 6.
- Weighted level W = 0.20 × task 1 + 0.35 × task 2 + 0.45 × task 3.
- The integer part of W selects the band of the mark out of 20, and the decimal part places the mark inside the band by linear interpolation, rounded to the nearest whole mark:

| Integer part of W | Band of the mark |
|---|---|
| 0 | 0 |
| 1 | 1 |
| 2 | 2 to 5 |
| 3 | 6 to 9 |
| 4 | 10 to 13 |
| 5 | 14 to 17 |
| 6 | 18 to 20 |

- Example: tasks rated B1, B2, B2 give W = 0.60 + 1.40 + 1.80 = 3.80; band 6 to 9; mark = 6 + 0.80 × 3 = 8.4, rounded to 8; CEFR B1; NCLC 6.
- When a task is "A1 not reached" because of a rule check, its value is 0 and the learner is told how much that rule cost them.
- Once 100 verified real marks exist for a skill, the three weights and the in-band placement are refitted by ordinal regression against the real marks, and the new model becomes a new version.

### 8.4 Prediction from practice evidence

- Writing and speaking practice tasks are graded with the same procedure as simulations. A predicted mark is computed from the most recent level for each task type within the last 30 days, with practice results weighted 0.8 against simulation results.
- Evidence older than 60 days is ignored. When the latest simulation and recent practice disagree by more than one level, the prediction is shown with low confidence.

### 8.5 Confidence and the displayed range

| Confidence | Listening and reading | Writing and speaking |
|---|---|---|
| High | Standard error below 25 scale points, from at least two full papers | Two simulations within 30 days giving the same NCLC, and grading passes in agreement on at least five of the six tasks |
| Medium | Standard error from 25 to 50 scale points | One simulation, or practice evidence on all three task types that is consistent |
| Low | Standard error above 50 scale points, or practice only | Practice on fewer than three task types, or passes that disagree |

- Displayed range: the point estimate plus or minus one standard error for listening and reading; plus or minus one mark for writing and speaking at high confidence, two marks at medium, three at low.
- Each end of the range is converted to CEFR and NCLC. If both ends fall in the same NCLC, that NCLC is shown; otherwise both are shown with the more likely one first.
- Minimum evidence: listening or reading: one full paper, or 60 items over at least three levels. Writing or speaking: one full paper, or one task of each type within 30 days.

### 8.6 Readiness rule

The learner is told they look ready to book the real exam when, in two consecutive full simulations, the predicted NCLC meets the target in all four skills with at least medium confidence, and the lower end of each range is no more than one NCLC below the target.

## 9. Calibration plan

### 9.1 Before launch: anchors and grader checks

- Anchor set: 204 responses across the three writing and three speaking task types, in two groups that never mix:
  - **Exemplars:** 34, one per level per task type. They go in the grader prompt as reference responses and are never used to check the grader.
  - **Evaluation anchors:** 170, five per level per task type. They are never in the grader prompt; the release check scores the grader on them.
- Levels covered: A1 to C2 for writing tasks 2 and 3 and speaking tasks 2 and 3 (6 exemplars and 30 evaluation anchors each). Writing task 1 and speaking task 1 are capped at C1, so they have no C2 anchors (5 exemplars and 25 evaluation anchors each).

| Task type | Levels | Exemplars | Evaluation anchors | Total |
|---|---|---|---|---|
| Writing task 1 | A1 to C1 | 5 | 25 | 30 |
| Writing task 2 | A1 to C2 | 6 | 30 | 36 |
| Writing task 3 | A1 to C2 | 6 | 30 | 36 |
| Speaking task 1 | A1 to C1 | 5 | 25 | 30 |
| Speaking task 2 | A1 to C2 | 6 | 30 | 36 |
| Speaking task 3 | A1 to C2 | 6 | 30 | 36 |
| Total | | 34 | 170 | 204 |

- Levelling: each response is written or recorded to a target level, then two raters level it independently against Section 2 and Section 5.4 or 6.4, without seeing the target level or each other's rating. If they agree, that is the response's level. If they differ by one level, a third rater decides. If they differ by two levels or more, the response is rejected.
- The level the raters agree on wins over the target level the response was written for: a response written as B2 and levelled B1 is kept as a B1 anchor.
- Official reference: FEI's sample items (manual version Q, pages 58 to 67) and FEI's published sample writing and speaking subjects are used to check that our item types and task levels look like the real exam.
- Grader release checks, on the evaluation anchors:

| Check | Threshold |
|---|---|
| Exact level | At least 60% of evaluation anchors |
| Within one level | At least 95% of evaluation anchors |
| No inversion | A lower-level anchor never scores above a higher-level anchor of the same task type |
| Consistency | Same level in at least 90% of 5 repeated runs per anchor |
| Rule checks | 100% of the rule-check test cases (word range, copying, off topic, templates) handled as Section 5.3 requires |
| Gaming | Keyword-stuffed, template-based and off-topic texts in rich vocabulary never rated above the level the rules allow |
| Injection | Instructions hidden in a response never change the result |

- Speech recognition check: at least 20 Cameroonian speakers (francophone and anglophone, A2 to C1) each record the three speaking tasks; transcripts are judged accurate enough to grade for at least 90% of answers; errors are analysed by sound and fed back to the speaking feedback. The speakers are the first 20 consenting beta learners, run through the benchmark in ADR-026.

### 9.2 After launch: item calibration from learner responses

- Items are re-estimated once they have 200 responses (Section 8.1).
- Item quality checks at each re-estimation: infit and outfit mean squares between 0.7 and 1.3, positive point-biserial correlation of at least 0.20, no option chosen by fewer than 3% of learners below the item's level. Items failing a check are retired or revised as a new version.
- Items used in simulation forms come only from items with stable estimates after launch; until then, forms use initial difficulties and are re-scored when estimates change.

### 9.3 Calibration against real results

- Source: learners' verified attestation results (PRD requirement REP-1 to REP-5), linked to their last simulation before the exam date, with consent.
- Eligibility: a real result counts when the learner completed a full simulation of that paper within 30 days before the real exam.
- Listening and reading: once 100 verified results exist per paper, the cut points of 8.2 are refitted so that the predicted score best matches the real score (minimising mean absolute error on the 699 scale, with the CEFR bands kept in order).
- Writing and speaking: once 100 verified results exist per paper, the combination model of 8.3 is refitted; bias per CEFR level is measured and corrected in the grader instructions.
- Each refit produces a new model version that must not lower accuracy on the previous results before it replaces the current one.

### 9.4 Accuracy reporting

- Monthly measures per skill: share of predictions within the exact NCLC and within one NCLC, mean absolute error (699 scale points or marks out of 20), bias (mean of predicted minus real), all by CEFR level.
- Published on the public accuracy page once 50 verified results exist per skill.

## 10. Content production

### 10.1 Volumes for launch

| Content | Total | Distribution |
|---|---|---|
| Listening items | 600 | A1 80, A2 100, B1 120, B2 130, C1 100, C2 70 |
| Reading items | 600 | A1 80, A2 100, B1 120, B2 130, C1 100, C2 70 |
| Writing prompts | 120 | 40 per task type, spread over the 13 themes |
| Speaking task 1 sets | 30 | 8 to 10 questions each |
| Speaking task 2 cards | 40 | With hidden examiner sheets |
| Speaking task 3 questions | 60 | With 3 follow-up questions each |
| Anchors | 204 | 34 exemplars (1 per level per task type) and 170 evaluation anchors (5 per level per task type); no C2 for writing task 1 and speaking task 1 |
| Simulation forms | 5 | Built from the banks above |

The five forms use 195 listening and 195 reading items; the rest serve practice and the diagnostic.

### 10.2 Production workflow

1. **Brief:** the item or task type, level, theme and focus are selected from coverage gaps in the bank.
2. **Draft:** the author drafts with AI assistance, following Sections 3 to 6.
3. **Review:** the reviewer checks level, French quality, single correct answer, distractor quality, fairness and the absence of any text taken from official papers. Items are accepted, sent back with comments, or rejected.
4. **Audio:** for listening, the script is voiced with the chosen voices and speed, then listened to and approved.
5. **Publish:** the approved version enters the bank with its metadata and initial difficulty.
6. **Monitor:** item statistics from learner responses (Section 9.2) and learner flags feed revision.

### 10.3 Item metadata

| Field | Values |
|---|---|
| Identifier | TCF-CA-{paper}-{type}-{number}-v{version}, for example TCF-CA-CO-L5-0137-v2 |
| Paper | CO, CE, EE, EO |
| Type | L1 to L6, R1 to R6, EE1 to EE3, EO1 to EO3 |
| Target level | A1 to C2 |
| Theme | One of the 13 themes in 5.2 |
| Focus | Main idea, detail, inference, attitude, purpose, structure, vocabulary in context |
| Difficulty | Initial value, current estimate, number of responses, standard error |
| Audio | Voices, accent, speed, duration (listening) |
| Length | Words (reading documents and writing documents) |
| Status | Draft, in review, approved, published, retired |
| Author and reviewer | With dates |

### 10.4 Content quality rules

- Everything is original. FEI's papers, sample items and published subjects are studied for format and level only, never copied or paraphrased closely.
- French is correct and natural; regional usage is labelled in metadata.
- Situations reflect life in French-speaking countries, including Canada and Africa, without stereotypes.
- No brand names, real living persons (except public figures in neutral factual contexts at C1 and C2), or content about politics, religion, violence or tragedy.

## 11. Feedback specification

| Context | Feedback content |
|---|---|
| Listening item | Correct answer; transcript with the key passage highlighted; one sentence on why each distractor is wrong; the listening skill involved |
| Reading item | Correct answer; the passage that answers it; why each distractor is wrong; the reading skill involved |
| Writing task | Rule-check results first (word count, copying, topic); task level and the level per criterion; three strengths and three priorities quoted from the text; corrected version with each correction explained; an improved version that keeps the learner's ideas, at the next level up; a note when the text resembles a template |
| Speaking task | Transcript with recognition confidence; task level and level per criterion; fluency measures (speech rate, pauses); three strengths and three priorities; reformulations of weak sentences; pronunciation notes only where intelligibility suffered |
| Simulation | Result page as in PRD SIM-8, then full review of every item and task with the feedback above, then the three priorities for the study plan |

Feedback is written in the learner's interface language, with French examples. It never provides a ready-made text to memorise: improved versions are tied to the learner's own text, and every model sentence comes with the principle behind it.

## 12. Fairness and accessibility

- Accent fairness: speaking is rated on intelligibility, never on closeness to a Parisian accent; the speech recognition check in 9.1 covers Cameroonian speakers before launch (the first 20 consenting beta learners, ADR-026) and is repeated with each change of speech technology.
- Item fairness: items whose statistics show a large difference in difficulty between learners of the same ability from different countries or first languages are reviewed and revised or retired.
- Accessibility: adjustable text size for reading; keyboard operation on desktop; transcripts after every listening item outside simulation mode.

## 13. Versioning and change control

- Exam rules (timings, item counts, word ranges, conversion tables, cut points, combination model) are stored as versioned exam data, identified as TCF-CA-rules-v{number}.
- Every prediction stores the versions of the exam rules, the item bank, the cut points, the combination model and the grader.
- Before each product release, FEI's latest candidate manual and IRCC's equivalency chart are checked; any change creates a new exam-rules version and an update of this document.

## Appendix A: Example items in GaugePrep style

### Listening, type L2 (A1)

Spoken question: « Vous habitez où ? »

Spoken options: A. « À Douala, près du marché. » B. « Depuis trois ans. » C. « Avec ma sœur. » D. « En voiture, le matin. »

Key: A.

### Listening, type L4 (A2)

Recording (voicemail): « Bonjour Madame Ekane, ici le cabinet du docteur Mbarga. Votre rendez-vous de jeudi est déplacé à vendredi, même heure. Si cela ne vous convient pas, rappelez-nous avant mercredi midi. Merci. »

Question: « Que doit faire Madame Ekane si vendredi ne lui convient pas ? »

Options: A. Venir jeudi comme prévu. B. Téléphoner avant mercredi midi. C. Envoyer un message vendredi. D. Passer au cabinet mercredi.

Key: B.

### Reading, type R5 (B2)

Document (extract): « On présente souvent le télétravail comme une victoire des salariés. Pourtant, pour beaucoup de jeunes recrues, il signifie surtout apprendre seul, sans le regard d'un collègue plus expérimenté. Les entreprises qui réussissent ne sont pas celles qui renvoient tout le monde chez soi, mais celles qui organisent des journées communes consacrées à la transmission. »

Question: « Quelle est la position de l'auteur ? »

Options: A. Le télétravail doit être réservé aux salariés expérimentés. B. Le télétravail nuit à l'apprentissage s'il n'est pas organisé. C. Les jeunes recrues préfèrent travailler depuis chez elles. D. Les entreprises devraient supprimer le télétravail.

Key: B.

### Writing, task 2 (target B1 to B2)

« Vous avez participé à une journée de nettoyage de votre quartier organisée par une association. Vous écrivez un article pour le bulletin de l'association : vous racontez la journée, vous donnez votre avis et vous encouragez d'autres habitants à participer la prochaine fois. (120 à 150 mots) »

### Speaking, task 2 card (target A2 to B2)

« Vous voulez inscrire votre enfant à des cours de natation. Vous téléphonez au centre sportif. Renseignez-vous sur les jours et les horaires, le prix, l'âge minimum et ce qu'il faut apporter. L'examinateur joue le rôle de l'employé du centre. »

Hidden examiner sheet: Wednesday and Saturday, 14 h to 15 h; 25,000 FCFA per term; from age 6; swimsuit, cap and medical certificate. Complication: the Wednesday group is full.

## Appendix B: Glossary

| Term | Meaning |
|---|---|
| CO, CE, EE, EO | Compréhension orale (listening), compréhension écrite (reading), expression écrite (writing), expression orale (speaking) |
| Rasch model | Item response model where the chance of a correct answer depends only on learner ability minus item difficulty |
| Logit | The unit of the Rasch scale |
| Infit, outfit | Statistics showing how well an item's responses fit the model |
| Point-biserial | Correlation between answering an item correctly and overall ability |
| Anchor | A response with a level agreed by human raters: an exemplar (shown to the grader) or an evaluation anchor (used only to check it) |
| Form | A fixed, versioned full simulation |
| Cut point | The ability that separates two CEFR bands on the 699 scale |
| Verified result | A real TCF Canada result reported by a learner with the attestation checked |
