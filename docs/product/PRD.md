# GaugePrep: Product Requirements Document

## 0. Document control

| Field | Value |
|---|---|
| Product | GaugePrep: an AI exam-preparation platform that teaches learners from their current level to exam-ready and predicts their real exam result |
| Document | Product Requirements Document (PRD) |
| Version | 1.0 |
| Date | 22 October 2026 |
| Owner | Frank, founder |
| Scope of this version | Product definition for all exams in scope, with the full specification of the first release: TCF Canada and the free French track |
| Related documents | TCF Canada exam specification and calibration brief; system architecture |

This document states what GaugePrep does, for whom, in what order, and why. How it is built is specified in the system architecture document. The PRD is a living reference: when a requirement changes, this document is updated in place and its version number raised.

All exam facts come from the exam owners' own publications current in October 2026 (Appendix D). Exam rules change, so every exam's facts are re-checked against its owner's latest publication before the release that ships it.

## 1. Summary

GaugePrep prepares adults and older teenagers for the language exams that decide their visa, residence, studies or job. It finds the learner's current level, teaches them from that level (from zero if needed) up to the level their target requires, lets them sit full simulations of the real exam under real conditions, and predicts the result they would get on the real exam, expressed in that exam's own scale and levels.

The product has three layers:

1. **A curriculum per language** (French first), from A1 to the level the exams require, shared by every exam in that language.
2. **An exam layer per exam**: practice in the exam's real task formats, full timed simulations, and a prediction grader that reproduces the exam's own scale, levels, floors and conversion tables.
3. **A free track** for vocabulary and everyday practice, for learners without an exam target and as the entry point to the paid product.

**First release:** TCF Canada end to end (curriculum to the level required, practice in all four skills, full four-paper simulation, NCLC prediction per skill) and the free French track. First market: Cameroon, then francophone Africa.

**Why TCF Canada first.** It is the largest single exam in scope, with 124,667 candidates in 2025 inside a TCF family of 310,473 that grew 21% in one year. Cameroon is the second-largest TCF market in the world, with 31,726 candidates in 2024. Most target learners already speak French, so the course mainly carries them from B1 to B2 or C1, which shortens the path to a first paying learner.

**What the learner cannot get elsewhere.** The exam owner publishes no syllabus and returns no annotations, no advice, no count of correct answers, and no appeal once results are issued. GaugePrep gives a diagnosis per skill, a path, a faithful rehearsal of the exam, and a prediction in the exam's own terms before the learner pays for the real sitting.

## 2. Vision and positioning

### 2.1 Vision

Make exam-ready language preparation and an honest prediction of the real result affordable to every learner in Africa first, then worldwide, for the exams that decide their future.

### 2.2 Positioning: the prediction grader

AI essay scoring and score predictors are common and often free. GaugePrep is positioned as **the grader that predicts with the exam's own rules and says how sure it is**:

- It reproduces each exam's real scale, levels, per-skill floors and conversion tables. For TCF Canada: CEFR level per task, mark out of 20, score out of 699, NCLC per skill.
- Every prediction is a likely range with a stated confidence. The exam owner itself shows that the same candidate can score 304 (B1) and then 295 (A2) a few weeks apart, so a single exact number would be false precision.
- Every prediction is labelled as an estimate. The product never claims to be, or to be affiliated with, an exam owner.
- Confidence grows with evidence. Learners report their real results after the exam, and the product publishes how closely its predictions matched.

### 2.3 Product principles

1. **Exam fidelity first.** Formats, timings, number of plays, word limits and scoring rules match the real exam. A simulation that is easier or kinder than the exam is a defect.
2. **Skills, not templates.** TCF and telc score memorised or copied texts as "A1 not reached", zero, or fraud. The product teaches transferable skills and never trains learners to recite templates.
3. **Honest numbers.** Ranges and confidence are always shown. Accuracy is measured and published.
4. **Built for the learner's reality.** Works on a computer and on a mid-range smartphone, over costly data, with mobile money and a French or English interface.
5. **One engine, many exams.** Each new exam adds content and an exam model, not a new product.

### 2.4 What the product is not

- Not a general fluency app competing with Duolingo or Babbel. The free track is a light entry point, not the core product.
- Not a human tutor marketplace.
- Not an institution or B2B product in its first releases.

## 3. Problem and market

### 3.1 The job to be done

"Tell me where I stand today against the score my immigration file needs, teach me what I am missing, let me rehearse the real exam until it feels familiar, and tell me honestly when I am ready, before I pay for the real sitting."

Preparation is bought in a burst of one to six months before an exam date, driven by a hard external target such as NCLC 7 in each of the four skills.

### 3.2 Demand evidence

| Fact | Source |
|---|---|
| TCF family 2025: 310,473 candidates (+21%): TCF Canada 124,667; TCF tout public and DAP 96,590; TCF IRN 64,902; TCF Québec 24,314 | FEI key figures 2025 |
| Cameroon is the second TCF market worldwide: 31,726 candidates in 2024; Algeria first with 54,553; Morocco third with 25,264 | OIF, La langue française dans le monde 2026 |
| TEF family about 130,500 candidates in 2025, of which TEF Canada about 47% | CCI Paris Île-de-France key figures |
| Express Entry French-language draws in 2026: 11 draws and 55,500 invitations by July, minimum CRS about 393 to 420 | CIC News, July 2026 |
| Express Entry French-language category: at least NCLC 7 in all four abilities | IRCC, October 2026 |
| TCF Canada centres in Cameroon: Institut français du Cameroun in Yaoundé and Douala, Alliances françaises in Dschang, Garoua and Ngaoundéré | Centre listings, September 2026 |

### 3.3 Alternatives and how GaugePrep beats them

| Alternative | What it offers | What GaugePrep adds |
|---|---|---|
| FEI candidate manual and sample papers | Official format and sample items | Scoring of the learner's own work, a path, full simulations, NCLC prediction |
| TV5Monde TCF, RFI Le français facile | Free practice material | Exam-faithful simulation, prediction, a plan built on the learner's gaps |
| AmiGrade, TCFCAD and similar | AI scoring toward NCLC for about 10 to 15 USD a month | A full curriculum from the learner's level, speaking with an AI examiner, exam rules reproduced, published accuracy |
| General AI chat assistants | Free essay feedback on request | Knowledge of TCF task rules, word limits, disqualification rules and NCLC tables, without the learner having to know them |
| Local preparation centres | Classes in person | Available any time, full simulations on demand, consistent scoring |

## 4. Users

### 4.1 Primary persona

**Aminata, 29, Douala.** Accountant, francophone, applying through Express Entry. She needs NCLC 7 in each skill on TCF Canada. Her everyday French is good, but she has never seen the exam, never written a 180-word argued text against the clock, and does not know her level. She uses a mid-range smartphone with costly data, pays with Orange Money, and plans to sit the exam in three months.

### 4.2 Secondary personas

- **Jean, 34, Bamenda.** Anglophone Cameroonian with school French at about A2. Targets TCF Canada, NCLC 7. He needs several months of curriculum before simulations make sense, and he prefers the interface in English.
- **Grâce, 17, Yaoundé.** Secondary-school student who wants to improve her French vocabulary and may sit the TCF for studies later. She uses the free track.

### 4.3 Personas for later releases

- A learner targeting TEF Canada for the same Canadian route.
- A nurse or apprentice targeting Goethe B1 or B2 for Germany, starting from zero German.
- An English-speaking learner targeting IELTS for the UK, Canada or university admission.

### 4.4 Roles

| Role | Responsibilities |
|---|---|
| Learner | Uses the product |
| Content reviewer | Approves items, lessons, prompts and model answers before publication; reviews flagged predictions and learner reports |
| Support admin | Manages accounts, payments, refunds and learner messages |
| Owner | Sets prices and plans, publishes accuracy statistics, manages reviewers |

## 5. Goals, scope boundaries and success metrics

### 5.1 First-release goals

1. A learner goes from sign-up to a full TCF Canada simulation with a predicted NCLC per skill on a mid-range smartphone over a 3G-class connection.
2. MCQ predictions (listening, reading) fall within one NCLC level of the real result for at least 70% of learners who report their result.
3. Learners who follow their plan for eight weeks raise their predicted level in at least two skills.
4. Learners in Cameroon pay with MTN Mobile Money or Orange Money from day one.

### 5.2 Outside the first release

- Exams other than TCF Canada. Other TCF versions (IRN, Québec, tout public) and TEF Canada form release 2.
- Native mobile apps. The product is a web app with progressive web app (PWA) support.
- Offline use, institution accounts, human tutoring.

### 5.3 Success metrics

| Metric | Target | Basis |
|---|---|---|
| Free to paid conversion within 30 days of sign-up | 3 to 5% | Education app median about 2.6%, top quartile about 5% |
| Paying learners who complete at least one full simulation | 70% | Simulation is the core value |
| MCQ prediction accuracy | 70% of reported real results within one NCLC level of the last prediction | Learner-reported results |
| Writing and speaking prediction accuracy | 60% within one NCLC level at launch, 75% after 500 reported results | Learner-reported results |
| Learners who report their real result | 30% of those who reach their exam date | Feeds calibration |
| Monthly paid retention | 75% of monthly subscribers renew at least once | Preparation lasts one to six months |
| Gross margin per paying learner | At least 60% after AI and payment costs | Sustainable at local prices |

## 6. Product overview

### 6.1 The learner journey

1. **Sign up:** email or Google, interface language (French or English), age check (16 or older).
2. **Set a goal:** target exam (TCF Canada in the first release), target NCLC per skill (prefilled with NCLC 7 for Express Entry), exam date if known. Or choose the free track with no exam.
3. **Diagnostic:** an adaptive placement across the four skills, 25 to 35 minutes, which can be done in parts.
4. **Plan:** the gap between the diagnostic and the target per skill, turned into a weekly plan fitted to the weeks left before the exam date.
5. **Learn:** curriculum lessons at the learner's level, with spaced review of weak points.
6. **Practise:** exam-format tasks per skill at the learner's level, with immediate feedback.
7. **Simulate:** full timed simulations under real exam rules.
8. **Predict:** the predicted result in the exam's own terms, updated after every simulation and from practice evidence.
9. **Report:** after the exam date, the learner reports the real result, which earns a reward and improves future predictions.

### 6.2 Curriculum layer

- One curriculum per language, organised by CEFR level, shared by all exams in that language. French covers A1 to C1 in the first release.
- Each level is a sequence of units built around communicative goals from the CEFR descriptors (for example "give and justify an opinion on a social issue" at B2), with grammar, vocabulary, listening, reading, writing and speaking activities.
- Lessons are fixed, versioned content, prepared with AI assistance and approved by a reviewer before publication.
- Deterministic exercises (choice, gap fill, ordering, matching, dictation) are checked automatically. Free writing and speaking go to the AI feedback engine.

### 6.3 Exam layer

Each exam has its own task bank in the exam's real formats, its own simulation rules (timers, plays per recording, word limits, order of papers), and its own prediction model that reproduces the exam's scoring and reporting. Exam rules are stored as versioned data so that a change in the real exam is a data update.

### 6.4 Free track

Thematic French vocabulary with spaced repetition, a short daily exercise, everyday listening and reading items, and progress streaks. It has no simulation and no prediction. Its purpose is to give real value to learners without an exam date and to bring them to the exam track when a target appears.

## 7. TCF Canada: the exam the first release reproduces

### 7.1 Papers

| Paper | Format | Time | Scoring |
|---|---|---|---|
| Listening (compréhension orale) | 39 multiple-choice questions, 4 options, each recording played once, question after the recording, increasing difficulty | 35 min | Difficulty-weighted scale from 100 to 699 |
| Reading (compréhension écrite) | 39 multiple-choice questions, 4 options, increasing difficulty | 60 min | Difficulty-weighted scale from 100 to 699 |
| Writing (expression écrite) | Task 1: message, 60 to 120 words. Task 2: article, letter or note reporting an experience with comments or arguments, 120 to 150 words. Task 3: compare two viewpoints from two short documents and give an opinion, 120 to 180 words | 60 min | Two raters each give each task a CEFR level; a rule combining the six levels gives a mark out of 20 |
| Speaking (expression orale) | Face to face with an examiner, recorded. Task 1: directed interview, 2 min, no preparation. Task 2: role-play to obtain information, 3 min 30, with 2 min preparation. Task 3: point of view on a question, 4 min 30, no preparation, the examiner may interrupt | 12 min | Same principle as writing, mark out of 20 |

### 7.2 Scoring and reporting rules

- Multiple-choice: only correct answers count, no penalty for guessing, and the number of correct answers is not disclosed.
- Scale out of 699 to CEFR: below A1 0 to 99; A1 100 to 199; A2 200 to 299; B1 300 to 399; B2 400 to 499; C1 500 to 599; C2 600 to 699.
- Mark out of 20 to CEFR: 0 = A1 not reached; 1 = A1; 2 to 5 = A2; 6 to 9 = B1; 10 to 13 = B2; 14 to 17 = C1; 18 to 20 = C2.
- A writing task is rated "A1 not reached" if it is under or over its word range, off topic, missing, copied from the prompt or documents, or memorised. Reciting a memorised text in speaking can be rated "A1 not reached" and treated as fraud.
- Results are valid two years. A resit of the same version needs at least 20 days between sittings. Results from different sittings cannot be combined.

### 7.3 TCF Canada to NCLC

| NCLC | Listening /699 | Reading /699 | Speaking /20 | Writing /20 |
|---|---|---|---|---|
| 10 and above | 549 to 699 | 549 to 699 | 16 to 20 | 16 to 20 |
| 9 | 523 to 548 | 524 to 548 | 14 to 15 | 14 to 15 |
| 8 | 503 to 522 | 499 to 523 | 12 to 13 | 12 to 13 |
| 7 | 458 to 502 | 453 to 498 | 10 to 11 | 10 to 11 |
| 6 | 398 to 457 | 406 to 452 | 7 to 9 | 7 to 9 |
| 5 | 369 to 397 | 375 to 405 | 6 | 6 |
| 4 | 331 to 368 | 342 to 374 | 4 to 5 | 4 to 5 |

Below NCLC 4 the product reports the CEFR level.

## 8. Functional requirements: first release

Each requirement has an identifier used by design, development and testing.

### 8.1 Account, onboarding and goal

| ID | Requirement | Acceptance criteria |
|---|---|---|
| ACC-1 | Sign up with email and password, or with Google | Account created; email verified by code before paid features; no phone number is asked for |
| ACC-2 | Minimum age 16, matching the minimum age of the TCF | Date of birth required; under 16 refused with a clear message |
| ACC-3 | Interface language French or English, changeable at any time | All screens, emails and feedback available in both languages |
| ACC-4 | Goal setting | Learner chooses an exam or the free track; for TCF Canada, a target NCLC per skill (default NCLC 7) and an optional exam date |
| ACC-5 | Password reset and session management | Reset by single-use, time-limited code; learner can sign out of all devices |
| ACC-6 | Account deletion | Learner can delete the account; personal data and free text deleted within 30 days; anonymous statistics kept |
| ACC-7 | Consent management | Separate, revocable consents for: processing (required), use of work for quality improvement (optional), marketing messages (optional) |

### 8.2 Diagnostic placement

| ID | Requirement | Acceptance criteria |
|---|---|---|
| DIA-1 | Adaptive listening and reading items, starting easy and adapting to answers | A total beginner finishes these parts in under 10 minutes; a strong learner reaches C1 items |
| DIA-2 | Short writing task matched to the level reached in reading | No essay asked of a learner below A2; the task is skippable with the skill marked "not measured" |
| DIA-3 | Short speaking task with the AI examiner | Two or three questions, under 3 minutes, skippable |
| DIA-4 | Diagnostic result | CEFR level per skill and the first predicted NCLC range per skill with low confidence; shown within 1 minute of finishing |
| DIA-5 | Re-diagnostic | Available every 30 days, or automatically replaced by simulation evidence |

### 8.3 Study plan

| ID | Requirement | Acceptance criteria |
|---|---|---|
| PLN-1 | Weekly plan from the gap per skill and the weeks left | Plan lists lessons, practice sets and simulations per week; more time on the largest gaps |
| PLN-2 | Study time setting | Learner sets available minutes per day (15, 30, 60, 90); plan adapts |
| PLN-3 | Plan update | Plan recalculated after each simulation, diagnostic or change of exam date |
| PLN-4 | Readiness message | When predicted levels meet the target in all four skills with at least medium confidence in two consecutive simulations, the product says the learner looks ready to book |
| PLN-5 | Late start warning | If the gap cannot reasonably be closed before the exam date, the product says so and suggests a later date |

### 8.4 Curriculum and lessons

| ID | Requirement | Acceptance criteria |
|---|---|---|
| CUR-1 | French curriculum A1 to C1 | 5 levels, 10 units per level, 4 lessons per unit (200 lessons) |
| CUR-2 | Lesson structure | Goal, input (text or audio), explanation, practice, short production task, summary |
| CUR-3 | Spaced review | Errors and new vocabulary scheduled for review; a daily review queue under 10 minutes |
| CUR-4 | Level completion | A unit test per unit; a level test that moves the learner to the next level |
| CUR-5 | Audio | Every listening input has a transcript available after the activity |

### 8.5 Skill practice

| ID | Requirement | Acceptance criteria |
|---|---|---|
| PRA-1 | Listening practice in TCF format | Exam mode plays once with no pause; learning mode allows replay and slower speed; feedback shows the answer, transcript and why each distractor is wrong |
| PRA-2 | Reading practice in TCF format | Items filtered by level and document type; feedback highlights the part of the text that gives the answer |
| PRA-3 | Writing practice for each of the three task types | Live word count with the task's range; result in under 30 seconds: estimated CEFR level, criterion feedback (linguistic, pragmatic, sociolinguistic), rule checks (range, copying, topic), corrected and improved version that keeps the learner's ideas |
| PRA-4 | Speaking practice with the AI examiner for each of the three task types | Examiner speaks, listens, plays the role in task 2 and interrupts in task 3; result in under 60 seconds: estimated CEFR level, feedback on fluency, range, accuracy, pronunciation, interaction and structure, full transcript |
| PRA-5 | Rewrite and retry | Learner can rewrite a writing task or redo a speaking task and compare the two results |
| PRA-6 | Template detection | Text or speech that matches a known template or a previous submission at high similarity is flagged with an explanation of the real exam rule |

### 8.6 Full simulation

| ID | Requirement | Acceptance criteria |
|---|---|---|
| SIM-1 | Four papers with real item counts, timings and order | Listening 39 items 35 min; reading 39 items 60 min; writing 3 tasks 60 min; speaking 3 tasks 12 min |
| SIM-2 | Full sitting or paper by paper | Learner chooses; a full simulation can be spread over up to 7 days |
| SIM-3 | Real conditions | Recordings play once, no pause or rewind; strict timers; a paper closes when time ends; no feedback until the paper ends |
| SIM-4 | Word ranges as in the exam | Out-of-range text is not blocked, it is scored under the real rule |
| SIM-5 | Speaking simulation | 12-minute session with the AI examiner, preparation only before task 2 |
| SIM-6 | Resilience | Every answer saved as given; after a connection loss the learner resumes with the remaining time |
| SIM-7 | Fixed forms | Each simulation is a fixed, versioned form; a learner does not get the same form twice until all forms are used |
| SIM-8 | Result page | Score out of 699 for listening and reading, mark out of 20 for writing and speaking, CEFR and NCLC per skill, each as a range with confidence, labelled as an estimate, followed by the three priorities to work on |
| SIM-9 | Review | After the result, the learner reviews every item and every task with feedback |

### 8.7 Prediction and progress

| ID | Requirement | Acceptance criteria |
|---|---|---|
| PRE-1 | Prediction per skill in TCF terms | Range on the exam's scale, CEFR, NCLC and confidence level (low, medium, high) as defined in Section 9 |
| PRE-2 | Minimum evidence | No prediction shown for a skill below its minimum evidence; the product shows what is missing |
| PRE-3 | Progress view | Predicted NCLC per skill over time against the target |
| PRE-4 | Traceability | Every prediction stores the versions of the item bank, scale mapping, grader, model, prompt and rubric that produced it |
| PRE-5 | Disclaimer | Every prediction carries a short estimate notice with a link to the published accuracy |

### 8.8 Real-result reporting

| ID | Requirement | Acceptance criteria |
|---|---|---|
| REP-1 | Prompt to report | On the exam date plus 15 working days, the learner is asked for the real results (in-app and by email) |
| REP-2 | Report form | Scores per skill as on the attestation, test date, optional upload of the attestation |
| REP-3 | Reward | A verified report (attestation uploaded and checked) earns one free month |
| REP-4 | Use | Reports feed calibration only with the learner's consent; the attestation file is deleted after verification |
| REP-5 | Published accuracy | A public page shows prediction accuracy per skill once at least 50 verified reports exist, updated monthly |

### 8.9 Free track

| ID | Requirement | Acceptance criteria |
|---|---|---|
| FRE-1 | Thematic vocabulary | 60 themes, about 3,000 words and expressions from A1 to B2, each with audio and an example sentence |
| FRE-2 | Daily exercise | A 5 to 10 minute daily session mixing vocabulary review, a short listening and a short reading item |
| FRE-3 | Streaks and progress | Daily streak, words learned, level of each theme |
| FRE-4 | Bridge to the exam track | The free track shows what the learner's level means for TCF Canada and offers the diagnostic |

### 8.10 Notifications

| ID | Requirement | Acceptance criteria |
|---|---|---|
| NOT-1 | In-app notifications | Results ready, plan updated, subscription ending |
| NOT-2 | Email | Account events, subscription receipts and renewals, result reporting prompt |
| NOT-3 | Web push (opt-in) | Daily study reminder at the time the learner chooses |
| NOT-4 | Frequency limit | No more than one marketing message per week; all reminders can be turned off |

### 8.11 Plans and payments

| ID | Requirement | Acceptance criteria |
|---|---|---|
| PAY-1 | Plans and prices as in Section 12 | Prices in FCFA for Cameroon and the CEMAC zone; USD for other countries |
| PAY-2 | Mobile money in Cameroon | MTN Mobile Money and Orange Money through Notch Pay; payment confirmed and access granted within 1 minute |
| PAY-3 | Card payment | Visa and Mastercard accepted where the payment provider's card channel is available; renewal follows PAY-4. Automatic card renewal ships with the release that opens markets outside the CEMAC zone |
| PAY-4 | Renewal for mobile money | Reminder 3 days and 1 day before expiry with one-step payment; 3-day grace period before access stops |
| PAY-5 | Receipts | Receipt by email and in the account for every payment |
| PAY-6 | Refunds | Full refund on request within 7 days of the first payment if fewer than 2 simulation papers were taken |
| PAY-7 | Usage limits | Daily limits and the monthly fair-use ceiling per plan enforced, with a clear message showing usage and when the limit resets |

### 8.12 Content management and review

| ID | Requirement | Acceptance criteria |
|---|---|---|
| CMS-1 | Content authoring | Create and edit items, lessons, prompts, audio scripts and model answers, with AI drafting assistance |
| CMS-2 | Review workflow | Draft, in review, approved, published, retired; only approved content is published |
| CMS-3 | Versioning | Editing published content creates a new version; results keep the version they used |
| CMS-4 | Metadata | Every item tagged with skill, CEFR level, task type, topic, document type and estimated difficulty |
| CMS-5 | Simulation form builder | Builds forms that match the real exam's item counts and difficulty progression |
| CMS-6 | Audio production | Generates audio from scripts with a chosen voice and speed, stores the reviewed file |
| CMS-7 | Flag queue | Learners can flag an item or a feedback; flags reach the reviewer queue |
| CMS-8 | Audit log | Every reviewer and admin action is logged |

### 8.13 Support and administration

| ID | Requirement | Acceptance criteria |
|---|---|---|
| ADM-1 | Learner lookup | Find a learner by email; see plan, payments and usage, not essay content unless the learner shares it |
| ADM-2 | Manual actions | Extend access, refund, verify a result report |
| ADM-3 | Help | Help centre with frequent questions in French and English; contact form |
| ADM-4 | Operations dashboard | Sign-ups, conversions, active learners, AI cost per day, prediction accuracy |

### 8.14 Product analytics

The product records these events for the success metrics: sign-up, goal set, diagnostic completed, first lesson, first practice task, first simulation paper, simulation completed, plan viewed, payment started, payment succeeded, renewal, result reported. Learner essays, recordings and transcripts are never sent to analytics.

## 9. Prediction grader specification

### 9.1 Listening and reading

- Every item in the bank has a difficulty on one ability scale estimated with item response theory (a Rasch model in the first release).
- Initial difficulties come from the item's target CEFR level and reviewer judgement. They are re-estimated from learner responses once an item has at least 200 responses, and the bank is re-estimated monthly.
- The learner's ability is estimated from all their recent answers, with simulation answers weighted above practice answers.
- Ability is mapped to the 100 to 699 scale by aligning the scale's CEFR bands with the bank's CEFR-tagged items, then corrected with verified real results.
- Minimum evidence: one full simulation paper, or 60 practice items spread over at least three CEFR levels.

### 9.2 Writing

1. Rule checks run first, outside the AI model: word count per task, text copied from the prompt or documents, off-topic detection, similarity to known templates and to the learner's earlier submissions. A task failing a rule is rated "A1 not reached", as in the real exam.
2. The AI grader rates each task to a CEFR level against the TCF criteria (linguistic, pragmatic, sociolinguistic), using our own descriptors and anchor texts per level, and returns criterion-level evidence quoted from the learner's text.
3. The grader runs twice per task in independent passes. If the two levels differ by more than one level, a third pass decides.
4. The three task levels are combined into a mark out of 20 with the combination model in 9.4.
- Minimum evidence: all three tasks of one simulation, or at least one task of each type in practice within 30 days.

### 9.3 Speaking

- The learner's speech is transcribed; the AI examiner follows the task structure, including the role in task 2 and interruptions in task 3.
- Each task is rated to a CEFR level from the transcript and audio measures (speech rate, pauses, self-corrections, pronunciation confidence), against the TCF speaking criteria.
- The learner sees the transcript, so a recognition error is visible and can be flagged. Accent itself is never penalised; only intelligibility is assessed.
- The same double-pass and combination rules as writing apply.
- Minimum evidence: the three tasks of one simulation, or one task of each type in practice within 30 days.

### 9.4 Combination model for the mark out of 20

The exam owner does not publish its combination rule, so the product uses an explicit model and refits it from verified results:

- Each task level becomes a value: A1 not reached = 0, A1 = 1, A2 = 2, B1 = 3, B2 = 4, C1 = 5, C2 = 6.
- The weighted level is 0.20 × task 1 + 0.35 × task 2 + 0.45 × task 3, reflecting the rise in difficulty from task 1 to task 3.
- The integer part selects the CEFR band of the mark out of 20 (A2 = 2 to 5, B1 = 6 to 9, B2 = 10 to 13, C1 = 14 to 17, C2 = 18 to 20), and the decimal part places the mark within the band.
- Once 100 verified results exist for a skill, the weights and band placement are refitted to minimise the error against real marks.

### 9.5 Confidence and display

| Confidence | Listening and reading | Writing and speaking |
|---|---|---|
| High | Standard error of the 699-scale estimate under 25 points, from at least two full papers | Two simulations within 30 days giving the same NCLC, and the grader's passes agreeing |
| Medium | Standard error 25 to 50 points | One simulation, or practice evidence consistent across task types |
| Low | Standard error above 50 points, or practice evidence only | Practice evidence only, or grader passes disagreeing |

- The range shown is the estimate plus or minus one standard error, converted to CEFR and NCLC at both ends.
- If both ends of the range fall in the same NCLC level, that level is shown as the predicted level; otherwise both levels are shown with the more likely one first.

## 10. Calibration and quality assurance

### 10.1 Sources of truth

1. **Official material.** FEI sample items, sample tasks and corrections in the candidate manual and on FEI's site, used to check that item difficulty and task levels are placed correctly.
2. **Our anchor set.** For each writing and speaking task type, at least 5 responses per CEFR level from A1 to C2, written or recorded and levelled by the content reviewer against the published criteria.
3. **Verified real results.** Learners' attestation results, the main source for fitting the 699-scale mapping, the combination model and per-level bias.

### 10.2 Grader release checks

A new grader version (new model, prompt or rubric) serves learners only after it passes all of these on the anchor set:

- Exact CEFR level on at least 60% of anchors and within one level on at least 95%.
- No inversion: a lower-level anchor never scores above a higher-level anchor of the same task.
- Consistency: the same input gives the same level in at least 90% of repeated runs.
- Gaming resistance: texts with keyword stuffing, templates, copied prompt text or off-topic content in rich vocabulary are rated as the real rules require.
- Injection resistance: instructions hidden inside a learner's text do not change the result.

### 10.3 Ongoing monitoring

- Monthly report of prediction accuracy against verified results, per skill and per CEFR level.
- Alert if the share of predictions within one NCLC level falls 10 points below its last value.
- The grading model is pinned to a fixed, dated version from a vendor that publishes advance notice before retiring a version. Any change of model, prompt or rubric creates a new grader version and repeats the release checks.
- Development may use free local models; anchor checks and production always use the production model.

## 11. Content specification for the first release

| Content | Volume | Notes |
|---|---|---|
| Listening items | 600 | At least 70 per CEFR level A1 to C2; 5 simulation forms use 195 of them |
| Reading items | 600 | Same distribution and form use as listening |
| Writing prompts | 120 | 40 per task type, across the topics of the real exam |
| Speaking prompts | 130 | Task 1: 30 interview sets; task 2: 40 role-play scenarios; task 3: 60 questions |
| Simulation forms | 5 complete forms | A new form added every month after launch |
| Curriculum lessons | 200 | A1 to C1 |
| Free-track vocabulary | About 3,000 entries in 60 themes | With audio and example sentences |
| Writing and speaking anchors | 5 per level per task type | Section 10.1 |

Content rules:

- All content is original. Official papers are used to learn formats and to check levels, never copied. Exam owners forbid reproducing their papers.
- AI-assisted drafting is allowed; publication requires reviewer approval.
- Audio uses varied voices, ages and francophone accents, including African francophone accents where the voice technology allows, at natural speed from B2 upward.
- Topics reflect the real exam: daily life, work, education, health, environment, technology, society and culture, in French-speaking contexts.
- No official logos, and no official descriptor wording in the learner interface; our own wording mapped to the official criterion names.

## 12. Plans and pricing

| Plan | Price (Cameroon and CEMAC) | Price (other countries) | Includes |
|---|---|---|---|
| Free | 0 | 0 | Free track; full diagnostic; first unit of each curriculum level; 10 listening and 10 reading practice items per day; one writing and one speaking evaluation per month; no simulation |
| Premium, monthly | 7,900 FCFA per month | 12.99 USD per month | Everything in the exam track: all lessons, unlimited listening and reading practice, writing and speaking practice within daily limits, full simulations, predictions, study plan |
| Premium, 3 months | 19,900 FCFA | 32.99 USD | Same as monthly, paid once for 3 months (about 16% saving), suited to learners with an exam date |

Usage limits on Premium, set to keep AI costs under control without blocking normal study: per day, 8 writing evaluations, 30 minutes of speaking practice and 1 full simulation; per month (fair-use ceiling), 300 minutes of speaking and 120 writing evaluations. The ceiling covers far more than an intensive three-month preparation needs.

Pricing rationale: competing AI scoring tools charge about 10 to 15 USD a month for scoring alone; GaugePrep includes the curriculum, speaking with an AI examiner and full simulations. A TCF Canada sitting costs far more than a month of Premium, and a failed sitting also costs at least 20 days of waiting.

Payments: Notch Pay for MTN Mobile Money and Orange Money in Cameroon (also covering Côte d'Ivoire, Senegal, Ghana and Kenya for later markets); card payments where the provider's card channel is available, renewed through the same reminder and one-step payment flow. Automatic card renewal ships with the release that opens markets outside the CEMAC zone.

## 13. Release plan

### 13.1 Releases

| Release | Scope | Starts when |
|---|---|---|
| 1 | TCF Canada (four skills, full simulation, prediction); French curriculum A1 to C1; free French track; payments in Cameroon | Now |
| 2 | TEF Canada (new simulator and prediction model with the three NCLC tables by test date; reuses the French curriculum and grading engines); TCF IRN, TCF Québec and TCF tout public | Release 1 live and the first 50 verified results collected |
| 3 | German: Goethe-Zertifikat B1 and B2, then A1, A2 and C1; German curriculum from A1 | Release 2 live |
| 4 | English: IELTS Academic and General Training (including the IELTS for UKVI route); English curriculum from A1 | Release 3 live |
| 5 | PTE Academic and Core; DELF A1 to B2; telc Deutsch A2·B1, B1, B2 and B1·B2 Pflege; Goethe PRO Pflege; TestDaF | Release 4 live |
| Later | DALF C1 and C2, Goethe C2, Duolingo English Test | Demand from existing learners |

IELTS comes before PTE because it is accepted on the most routes (UK, Canada, Australia, universities) and is the most requested English exam. PTE follows closely: it has a test centre in Yaoundé and a UK visa version, and its computer-based format reuses the IELTS English curriculum and the speaking engine. TOEFL, CELPIP and ÖSD are not planned.

### 13.2 Release 1 launch criteria

Release 1 launches only when all of these are true:

1. Every journey in 6.1 works end to end on a mid-range smartphone over a 3G-class connection.
2. Content volumes in Section 11 are published and reviewer-approved.
3. The grader passes every release check in 10.2 for writing and speaking.
4. Speech recognition tested with at least 20 Cameroonian speakers (francophone and anglophone) across levels, with transcripts judged accurate enough to grade on at least 90% of test answers.
   The check runs on the first 20 consenting beta learners, by the benchmark in ADR-026.
5. Mobile money payments work in production with real MTN and Orange accounts, including renewal and refund.
6. The security baseline in Section 15 is met, and backups have been restored once in a test.

## 14. Non-functional requirements

| Area | Requirement |
|---|---|
| Platform | Responsive web app with progressive web app (PWA) support, working in current mobile and desktop browsers |
| Performance | Core pages usable in under 3 seconds on a 3G-class connection; listening audio compressed to keep each item small; writing results in under 30 seconds and speaking results in under 60 seconds at the 95th percentile; AI examiner response to the learner in under 2.5 seconds at the 95th percentile |
| Data use | A full simulation, speaking excluded, uses less than 15 MB of data |
| Availability | 99.5% monthly for learning features; a simulation in progress is never lost |
| Scale | Release 1 supports 10,000 registered and 1,000 daily active learners without redesign |
| Languages | Interface in French and English; content language per exam |
| Accessibility | Readable text sizes, sufficient contrast, keyboard use on desktop, captions or transcripts for all audio after the activity |
| Cost | Free tools for local development and staging wherever possible; paid services only in production. Moving a component from a free to a paid service is a configuration change |
| Operations | Runnable by a single person: automated deployment, backups, monitoring and alerts; a team can join without redesign |
| Source code | Private repository |
| Traceability | Every score and prediction can be reproduced from its stored versions |

## 15. Security and privacy

### 15.1 Data handling

- Consent is explicit, specific and revocable (ACC-7); only the data the product needs is collected; learners can access, correct and delete their data.
- AI providers process learner work under a data processing agreement, with no training on submitted data, and receive only what grading needs (no name, email or phone number with the text).
- Learner work is used to teach and score that learner. It is used to improve quality only with the optional, revocable consent in ACC-7.
- Retention: essays and recordings kept 12 months after the last activity, then deleted; attestation uploads deleted after verification; payment data held by the payment provider, not by GaugePrep.

### 15.2 Application security

- Passwords stored with a modern memory-hard hashing algorithm; short-lived sessions with rotation.
- Rate limits on authentication and on every AI-backed action, in addition to plan limits.
- All input validated; learner text passed to AI models as data, never as instructions; AI output validated against a schema before storage or display.
- Internal services and databases not reachable from the internet.
- Audit log of reviewer and admin actions.
- Dependency vulnerability scanning in continuous integration; a security review for every change to authentication, payments or personal data.

### 15.3 Intellectual property and claims

- No claim of affiliation with France Éducation international, CCI Paris Île-de-France, the Goethe-Institut, telc, the IELTS partners or Pearson; no use of their logos.
- Exam names used only to describe what the product prepares for.
- Every score labelled as an estimate; accuracy claims always backed by the published accuracy figures.

## 16. Risks

| Risk | Likelihood | Impact | Response |
|---|---|---|---|
| Writing and speaking predictions less accurate than targets at launch | High | High | Ranges with honest confidence; anchors and release checks; refit from verified results; accuracy published |
| Too few verified real results | Medium | High | One free month per verified report; prompt at the right moment; simple form |
| Speech recognition weak on Cameroonian accents | Medium | High | Launch criterion 4; visible transcripts; flagging; intelligibility, not accent, is assessed |
| AI costs too high for local prices | Medium | High | Daily limits; cheaper models for non-grading tasks; caching of generated content; cost tracked daily |
| Content volume too large for a small team | High | High | AI-assisted drafting with review; one exam in release 1; monthly additions after launch |
| Change to the TCF format or rules | Medium | Medium | Exam rules stored as versioned data; check FEI publications before each release |
| Complaint from an exam owner | Low | High | Original content only; no logos; estimate labels |
| Low willingness to pay | Medium | High | Free track and free evaluations prove value first; 3-month plan for learners with an exam date |

## Appendix A: Glossary

| Term | Meaning |
|---|---|
| CEFR | Common European Framework of Reference for Languages, levels A1 to C2 |
| NCLC | Niveaux de compétence linguistique canadiens, Canada's French proficiency levels used for immigration |
| FEI | France Éducation international, owner of the TCF and DELF |
| Attestation | The official TCF result document |
| IRT | Item response theory: estimates item difficulty and learner ability on one scale |
| Prediction grader | The part of the product that predicts the real result using the exam's own rules |
| Anchor | A response with a known level used to check the grader |
| Simulation form | A fixed, versioned full exam built from the item bank |
| Ancien score | TEF Canada's former scale, still the value entered in Express Entry profiles |

## Appendix B: Prediction shapes for later releases

| Exam | How the real result is reported | Prediction the product shows |
|---|---|---|
| TCF IRN | Scores up to 499; overall level by floor rule: three skills at the level and the fourth at the upper part of the level below | Probability of reaching the overall level needed (A2, B1 or B2) |
| TCF Québec | Points from B2 upward per skill | Points range per skill |
| TEF Canada | Score out of 699 per skill, plus the ancien score used by Express Entry; three NCLC tables by test date | NCLC per skill from the right table, with the ancien score |
| Goethe A1 | 60/100 overall | Pass probability |
| Goethe A2 | 60/100 overall, at least 45/75 written and 15/25 oral | Pass probability under the floors |
| Goethe B1, B2, C1 | 100 points per module, pass at 60, modules independent | Pass probability per module |
| telc Deutsch B1, B2 | At least 60% written and 60% oral | Pass probability per part |
| telc Deutsch A2·B1 | B1: 168/240, 70% in three skills and 40% in all; A2: 96/240, 40% in three skills and 10% in all | Most likely certificate: B1, A2 or none |
| DELF A1 to B2 | Four skills out of 25; pass at 50/100 with at least 5/25 per skill; item weights from 0.5 to 2.5 | Pass probability under the floor rule |
| TestDaF | TDN 3, 4 or 5 per section | Level per section |
| IELTS | Bands 0 to 9 per skill; overall rounded to the nearest half band; per-skill minimums set by the route (UK work: 5.5 in each skill; Canada CLB 7: 6.0 in each) | Band range per skill and overall, with a check against the route's minimums |
| PTE | 10 to 90 per skill | Score range per skill |

## Appendix C: Exam reference for later releases

| Exam | Papers and timing | Key rules |
|---|---|---|
| TEF Canada | Listening and reading (MCQ), writing and speaking; computer-based | One point per correct MCQ answer, converted to /699 by an unpublished rule; three NCLC tables by test date |
| Goethe A2 | Reading 30 min, listening 30 min, writing 30 min (message 20 to 30 words, email 30 to 40 words), speaking in pairs about 15 min | Task fulfilment rated E makes the task worth 0 |
| Goethe B2 | Modular: reading 65 min, listening 40 min, writing 75 min (forum post about 150 words, message about 100 words), speaking about 15 min with 15 min preparation | Writing criteria with fixed point values; two raters averaged; third rater around the pass mark |
| telc Deutsch B1, B2 | Reading and language elements 90 min, listening 20 to 30 min, writing 30 min (email with guide points), oral in pairs with 20 min preparation | 300 points; second rater's mark replaces the first; memorised sample texts score zero |
| telc Deutsch A2·B1 | Written 125 min with mixed tasks; oral about 15 min in pairs | 240 points; criteria labelled by level |
| DELF B2 | Listening about 30 min, reading 1 h, writing 1 h (at least 250 words), speaking 20 min after 30 min preparation (monologue 5 to 7 min, debate 10 to 13 min) | Grids of 0, 1, 3 or 5 per criterion; under half the required words scores 0 |
| IELTS | Listening 40 items about 30 min heard once; reading 40 items 60 min; writing 60 min (task 2 counts double); speaking 11 to 14 min with an examiner | Public band descriptors with four criteria; one centre in Yaoundé, no UKVI sitting in Cameroon |
| PTE Academic, Core | About 2 hours, computer-based, integrated tasks scored by Pearson's AI | Test centre in Yaoundé |

## Appendix D: Sources

- France Éducation international: Manuel du candidat TCF, version Q (September 2026); key figures 2025; DELF documents and grids (2024).
- Immigration, Refugees and Citizenship Canada: test equivalency charts; Express Entry language requirements.
- CCI Paris Île-de-France: TEF Canada handbook and correspondence tables.
- Goethe-Institut: Prüfungsordnung and Durchführungsbestimmungen (2025); Modellsätze A1, A2, B2, C1.
- telc gGmbH: Rules and Regulations valid from 15 April 2025; Übungstests B1, B2 and A2·B1; Handbuch Deutsch B2.
- TestDaF-Institut: Prüfungsordnung (October 2020).
- IELTS partners: public band descriptors for writing and speaking; scoring guidance. GOV.UK list of approved secure English language tests.
- Pearson: PTE Academic and PTE Core format pages.
- Organisation internationale de la Francophonie: La langue française dans le monde 2026.
- Notch Pay developer documentation: mobile money coverage.
