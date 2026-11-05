# UX specification

> Guidance only: the API contract is the OpenAPI document generated from the code, and the code wins where they differ.

Screens, navigation, states and key copy of the release 1 PWA. It turns the PRD journeys (PRD 6.1) and requirements into what the frontend builds. Visual design (colour, type, illustration) is defined separately in a design system; until it exists, the frontend uses the neutral tokens of Section 7 so that screens can be built and tested now and restyled later without structural change.

## 1. Principles

1. **Small screens first.** A responsive web app, designed at a 360 x 640 CSS pixel viewport and tested in the browser of a mid-range smartphone over slow 3G (PRD 14). Wider screens get the same layout with a wider content column (maximum 720 px) and keyboard support.
2. **Exam fidelity.** Simulation screens look and behave like a computer-based exam: no hints, no feedback, timers visible, rules stated before starting (PRD 2.3, SIM-3).
3. **Honest numbers.** Every predicted score is shown as a range with its confidence and the estimate notice (PRE-5). Never show a single number without its range.
4. **Light on data.** Images only where they carry meaning; audio downloaded once and cached; no autoplay video.
5. **Two languages.** Every string comes from the FR and EN catalogues (ACC-3). Exam content stays in French whatever the interface language.
6. **Clear next step.** Every screen has one primary action.

## 2. Navigation

Signed-in learners on the exam track have a bottom tab bar with five tabs:

| Tab | Route | Content |
|---|---|---|
| Today | `/app` | This week's plan, today's tasks, review queue, readiness |
| Learn | `/app/learn` | Curriculum levels, units and lessons |
| Practise | `/app/practise` | The four skills in TCF format |
| Exam | `/app/exam` | Simulations: start, resume, history |
| Progress | `/app/progress` | Predictions per skill over time, target |

The account menu (avatar, top right) holds profile, plan and billing, notifications, settings (language, reminders, consents), help, sign out.

Free-track learners (goal track `free`) have three tabs: Today (daily session and streak), Words (themes), Exam (bridge to the diagnostic and the plans).

Public routes: `/` landing, `/pricing`, `/accuracy`, `/help`, `/legal/*`, `/signin`, `/signup`.

## 3. Screen inventory

Each screen lists its route, requirements, main content and the states it must handle. "Standard states" means: loading (skeleton, not spinner, for lists and cards), error (problem detail message with retry), offline (banner: content cached is shown, actions that need the server are disabled with a reason).

### 3.1 Account and onboarding

| ID | Screen | Route | PRD | Content and behaviour | States |
|---|---|---|---|---|---|
| S01 | Sign up | `/signup` | ACC-1, ACC-2, ACC-3, ACC-7 | Email, password, date of birth (three selects, not a calendar), interface language, required consent with link, optional consents unticked, Google button | Under 16 message; field errors; code sent |
| S02 | Verify | `/verify` | ACC-1 | 6-digit code input with auto-advance, resend timer (60 s), change email | Wrong code with attempts left; expired; locked |
| S03 | Sign in | `/signin` | ACC-5 | Email and password, Google, forgot password | Generic error |
| S04 | Reset password | `/reset` | ACC-5 | Request code, then code and new password | |
| S05 | Choose goal | `/app/onboarding/goal` | ACC-4 | Two cards: "Prepare TCF Canada" and "Improve my French (free)". For TCF: target NCLC per skill (default 7 with a note "Express Entry French category needs NCLC 7 in each skill"), exam date (optional), minutes per day (15, 30, 60, 90) | |
| S06 | Diagnostic intro | `/app/diagnostic` | DIA-1 | What it measures, 25 to 35 minutes, can be done in parts, headphones advised | Resume if started |
| S07 | Diagnostic item | `/app/diagnostic/run` | DIA-1 to DIA-3 | Same item components as practice in exam mode, progress by skill (not by item count), skip for writing and speaking | Offline: pause with resume |
| S08 | Diagnostic result | `/app/diagnostic/result` | DIA-4, PLN-1 | CEFR per skill, first NCLC range with low confidence and the reason, gap to target, button "See my plan" | Pending (under 1 minute) |

### 3.2 Today and plan

| ID | Screen | Route | PRD | Content and behaviour | States |
|---|---|---|---|---|---|
| S10 | Today | `/app` | PLN-1, CUR-3, PLN-4 | Days left to the exam; today's tasks from the plan (lesson, practice, review) with estimated minutes; review queue count; readiness card when ready; late-start warning card when set | Empty plan (no diagnostic yet): call to start the diagnostic |
| S11 | Weekly plan | `/app/plan` | PLN-1, PLN-3, PLN-5 | Weeks with items and done marks; which skills get more time and why; change exam date or minutes | Plan updated banner after a simulation |

### 3.3 Learn

| ID | Screen | Route | PRD | Content and behaviour | States |
|---|---|---|---|---|---|
| S20 | Levels and units | `/app/learn` | CUR-1, CUR-4 | Levels A1 to C1, current level open, units with progress; locked units on Free show the plan offer | |
| S21 | Lesson | `/app/learn/[code]` | CUR-2, CUR-5 | Steps: goal, input (text or audio with transcript after), explanation, practice exercises with instant check, production task, summary. Step indicator; can leave and resume | Audio not yet cached on slow network: download indicator |
| S22 | Review queue | `/app/review` | CUR-3 | Cards one at a time, under 10 minutes, "Done for today" | Empty: nothing due |
| S23 | Unit or level test | `/app/learn/test/[id]` | CUR-4 | Timed items, result, next step | |

### 3.4 Practise

| ID | Screen | Route | PRD | Content and behaviour | States |
|---|---|---|---|---|---|
| S30 | Practise home | `/app/practise` | PRA-1 to PRA-4 | Four skill cards with predicted level and today's usage (writing evaluations left, speaking minutes left) | Usage limit reached state per card |
| S31 | Listening and reading set | `/app/practise/[paper]` | PRA-1, PRA-2 | Filters (level, type, theme), mode toggle Exam / Learning for listening. Item screen: audio player (exam mode: single play, no seek; learning mode: replay and 0.75x speed), question, four options, Confirm. Feedback after each item: correct answer, why each distractor is wrong, transcript or text with key passage highlighted, skill note, flag button | Free daily limit reached |
| S32 | Writing task | `/app/practise/writing/[prompt]` | PRA-3, PRA-6 | Prompt (with documents for task 3), editor with live word count and the task range coloured (under, in, over: never blocks), no spellcheck (`spellcheck=false`, autocorrect off), draft saved locally every 5 s, Submit | Usage left shown before submit |
| S33 | Writing result | `/app/productions/[id]` | PRA-3, PRA-5, PRA-6 | Rule checks first (word count, copying, topic, template flags with explanations); task level and level per criterion; three strengths and three priorities quoted from the text; corrected version with explanations (tap a correction to see why); improved version at the next level; Rewrite button | Grading (progress text, target under 30 s); grading delayed (notice, the result will come by notification) |
| S34 | Speaking task | `/app/practise/speaking/[task]` | PRA-4 | Microphone permission explained in context; mic check (level meter); AI examiner disclosure; task card (EO2 with 2-minute preparation and notes area); in-task screen: timer, examiner speaking indicator, learner speaking indicator, End button | Mic denied: instructions per browser; network poor: warning before start; reconnecting |
| S35 | Speaking result | `/app/productions/[id]` | PRA-4, PRA-5 | Transcript with low-confidence words underlined and a "this is not what I said" flag; level and criteria; fluency measures (speech rate, pauses); strengths and priorities; reformulations; pronunciation notes only where intelligibility suffered; Redo | Transcribing and grading (target under 60 s) |
| S36 | Compare attempts | `/app/productions/[id]/compare` | PRA-5 | Two attempts side by side: level, criteria, word count | |

### 3.5 Exam (simulation)

| ID | Screen | Route | PRD | Content and behaviour | States |
|---|---|---|---|---|---|
| S40 | Exam home | `/app/exam` | SIM-1, SIM-2, SIM-7 | Start a full simulation or paper by paper; open sitting with expiry date; past simulations with results | Daily simulation limit reached; Premium required (Free) |
| S41 | Paper rules | `/app/exam/[sitting]/[paper]/rules` | SIM-1, SIM-3 | The paper's rules in plain words (items, time, plays, word ranges), equipment check (headphones for listening, mic for speaking), network check, "Start the paper" with a warning that it cannot be paused | |
| S42 | Listening paper | `/app/exam/[sitting]/CO` | SIM-3, SIM-6 | Item counter (12 / 39), server-based countdown, recording plays automatically once, then question and options with a 10-second answer bar; Next; no back | Connection lost: answers keep being saved locally, timer keeps running, banner "Reconnecting, your answers are saved" |
| S43 | Reading paper | `/app/exam/[sitting]/CE` | SIM-3, SIM-6 | Countdown, item navigator grid (answered, flagged), document and question, flag for review, free navigation, Submit with summary of unanswered items | As S42 |
| S44 | Writing paper | `/app/exam/[sitting]/EE` | SIM-3, SIM-4, SIM-6 | Three task tabs, each with its prompt and editor and word counter; one 60-minute countdown; copy and paste from the prompt disabled; no spellcheck | As S42; warning at 10 and 1 minute |
| S45 | Speaking paper | `/app/exam/[sitting]/EO` | SIM-5 | Mic check, then tasks back to back: task 1 (2 min), task 2 card with 2-minute preparation and notes, task 2 (3 min 30), task 3 (4 min 30); the examiner announces each task | Network drop: the session resumes the current task if back within 60 s; otherwise the paper is closed with what was recorded and the learner is told |
| S46 | Paper done | `/app/exam/[sitting]/[paper]/done` | SIM-3 | Confirmation, results pending, next paper or later | |
| S47 | Result | `/app/exam/[sitting]/result` | SIM-8, PRE-1, PRE-5 | Per skill: scale score out of 699 (CO, CE) or mark out of 20 (EE, EO) as a range, CEFR, NCLC, confidence, against the target; estimate notice; the three priorities with links into the plan | Partial results in paper-by-paper mode |
| S48 | Review | `/app/exam/[sitting]/review/[paper]` | SIM-9 | Every item or task with the feedback of S31, S33, S35 | |

### 3.6 Progress, notifications, billing, reporting

| ID | Screen | Route | PRD | Content and behaviour | States |
|---|---|---|---|---|---|
| S50 | Progress | `/app/progress` | PRE-1 to PRE-5, PLN-4 | Four skill cards: NCLC range band against the target line, confidence, what would raise confidence; chart of predicted NCLC over time; minimum-evidence messages (PRE-2) | No evidence yet |
| S51 | Notifications | `/app/notifications` | NOT-1 | List, unread markers | Empty |
| S52 | Plans and payment | `/app/billing` | PAY-1 to PAY-7 | Current plan, usage meters, plans with prices in the learner's currency; payment flow: choose plan, choose MTN MoMo or Orange Money (or card where available), enter phone number, "Confirm on your phone" screen with status polling; receipts; refund request | Pending up to 3 minutes; failed with provider message and retry; success with new end date |
| S53 | Report your result | `/app/report` | REP-1 to REP-4 | Scores per skill as on the attestation, test date, consent to use for calibration, attestation upload, reward explanation (one free month after verification) | Submitted, verifying, verified, rejected with reason |
| S54 | Settings | `/app/settings` | ACC-3, ACC-5, ACC-6, ACC-7, NOT-3, NOT-4 | Language, reminders and reminder time, push permission, consents, sign out of all devices, export data, delete account | |

### 3.7 Free track

| ID | Screen | Route | PRD | Content and behaviour | States |
|---|---|---|---|---|---|
| S60 | Free today | `/app` (free track) | FRE-2, FRE-3 | Streak, daily session card (5 to 10 minutes), words learned | Done for today |
| S61 | Daily session | `/app/free/daily` | FRE-2 | Vocabulary cards (audio, example), one listening and one reading item | |
| S62 | Themes | `/app/free/words` | FRE-1, FRE-3 | 60 themes with level per theme; theme detail with words and audio | |
| S63 | TCF bridge | `/app/free/tcf` | FRE-4 | What the learner's level means for TCF Canada; start the diagnostic | |

### 3.8 Public pages

| ID | Screen | Route | PRD | Content |
|---|---|---|---|---|
| S70 | Landing | `/` | 2.2, 15.3 | What the product does, the prediction promise with "estimate" wording, how it works, prices, sign-up. No exam owner logos; exam names used descriptively |
| S71 | Pricing | `/pricing` | PAY-1, PRD 12 | Three plans, limits stated plainly, FCFA or USD by location with a switch |
| S72 | Accuracy | `/accuracy` | REP-5 | Published accuracy per skill and how it is measured; before 50 verified reports: "We publish our accuracy once 50 learners per skill have reported their real results" |
| S73 | Help | `/help` | ADM-3 | FAQ in French and English, contact form |

## 4. Key flows

1. **First session:** S01, S02, S05, S06 to S08, S11, S10. Target: a learner can finish sign-up and start the diagnostic in under 3 minutes.
2. **Daily study:** S10, then a lesson (S21) or practice (S31 to S35), then review (S22).
3. **Full simulation:** S40, then for each paper S41, the paper screen, S46; then S47 and S48. Across up to 7 days.
4. **Payment:** S52 from any Premium gate. A gate always explains what Premium unlocks and the price before the payment screen.
5. **Result reporting:** notification on exam date plus 15 working days (REP-1), S53.

## 5. Interaction rules

- **Timers** show minutes and seconds from the server deadline; they turn amber at 5 minutes left and announce 10 and 1 minute left to screen readers.
- **Saving** is silent and continuous in practice and simulation; a small "Saved" indicator shows the last sync. Never ask the learner to save.
- **Audio** in exam mode has no seek bar; in learning mode it has replay, 0.75x speed and a transcript after answering.
- **Word counter** uses the exam rule (same function as the backend through a shared test suite) and shows "62 / 60 to 120 words".
- **Premium gates** appear when a Free learner opens a Premium feature; they never interrupt an activity already started.
- **Errors** in AI features (grading delayed, examiner unavailable) never lose the learner's work and say when the result will arrive.
- **Accessibility:** text size setting (100%, 115%, 130%) for reading content; contrast AA; all controls reachable by keyboard on desktop; touch targets at least 44 px; captions or transcripts after every audio outside simulation (PRD 14, spec 12).

## 6. Key copy

These strings carry rules or promises and must be used as written (catalogue keys in brackets).

| Key | English | French |
|---|---|---|
| `prediction.notice` | This is an estimate based on your work in GaugePrep, not an official result. See how accurate our estimates are. | Ceci est une estimation fondée sur votre travail dans GaugePrep, pas un résultat officiel. Voir la précision de nos estimations. |
| `prediction.confidence.low` | Low confidence: we need more of your work in this skill. | Confiance faible : nous avons besoin de plus de travaux de votre part dans cette compétence. |
| `prediction.missing` | Complete {what} to get a prediction for {skill}. | Faites {what} pour obtenir une estimation en {skill}. |
| `examiner.disclosure` | Your examiner is an AI voice. The conversation is recorded so that we can assess it. | Votre examinateur est une voix artificielle. La conversation est enregistrée pour être évaluée. |
| `writing.range.out` | Your text has {count} words. In the real exam, a text outside {min} to {max} words is rated "A1 not reached". | Votre texte compte {count} mots. À l'examen, un texte hors de la limite de {min} à {max} mots est noté « A1 non atteint ». |
| `writing.copy` | Some passages repeat the instructions or documents word for word. In the real exam, a copied text is rated "A1 not reached". | Certains passages reprennent mot pour mot la consigne ou les documents. À l'examen, un texte recopié est noté « A1 non atteint ». |
| `writing.template` | This text looks like a model text or template. Examiners rate memorised texts "A1 not reached". Write with your own words for this subject. | Ce texte ressemble à un modèle ou un texte appris. Les correcteurs notent les textes mémorisés « A1 non atteint ». Rédigez avec vos propres mots pour ce sujet. |
| `sim.rules.noPause` | Once started, this paper cannot be paused. The timer keeps running even if you lose your connection. Your answers are saved. | Une fois commencée, cette épreuve ne peut pas être mise en pause. Le chronomètre continue même en cas de coupure. Vos réponses sont enregistrées. |
| `sim.listening.once` | Each recording plays once, as in the real exam. | Chaque enregistrement est diffusé une seule fois, comme à l'examen. |
| `usage.limit` | You have used today's {metric}. It resets at {time}. | Vous avez utilisé votre quota du jour pour {metric}. Il se renouvelle à {time}. |
| `offline.banner` | You are offline. Your work is saved on this device and will be sent when you reconnect. | Vous êtes hors ligne. Votre travail est enregistré sur cet appareil et sera envoyé à la reconnexion. |
| `readiness.ready` | You look ready to book your exam: your last two simulations meet your target in all four skills. | Le moment semble venu de vous inscrire à l'examen : vos deux dernières simulations atteignent votre objectif dans les quatre compétences. |
| `plan.lateStart` | Your target may be hard to reach by {date}. Consider a later exam date or more study time per day. | Votre objectif risque d'être difficile à atteindre d'ici le {date}. Envisagez une date d'examen plus tardive ou plus de temps d'étude par jour. |
| `brand.independence` | GaugePrep is independent and not affiliated with France Éducation international. | GaugePrep est indépendant et n'est pas affilié à France Éducation international. |

## 7. Interim design tokens

Until the design system exists, use these tokens so screens can be built now.

| Token | Value |
|---|---|
| Font | System UI stack; base 16 px, line height 1.5 |
| Spacing | 4, 8, 12, 16, 24, 32 px |
| Radius | 8 px for cards and inputs, 999 px for pills |
| Colours | `--bg`, `--surface`, `--text`, `--muted`, `--primary`, `--success`, `--warning`, `--danger`, with light and dark values meeting WCAG AA |
| Layout | Single column, 16 px side gutter, content maximum 720 px |
| Touch target | At least 44 x 44 px |
