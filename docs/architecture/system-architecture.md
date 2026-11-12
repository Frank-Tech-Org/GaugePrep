# GaugePrep: System Architecture

## 0. Document control

| Field | Value |
|---|---|
| Document | System architecture |
| Version | 1.0 |
| Date | 22 October 2026 |
| Owner | CTO, GaugePrep |
| Product owner | Frank |
| Inputs | Product Requirements Document v1.0; TCF Canada exam specification and calibration brief v1.0 |
| Companion files | Architecture decision records (docs/adr), milestone 0 backlog |
| Audience | Every engineer, reviewer and operator working on GaugePrep |

This document describes how GaugePrep is built and run: its structure, technologies, data, AI and speech pipelines, infrastructure, delivery process, quality practices and the plan to start development. Every technology choice was made from the vendor's or project's own current documentation in October 2026; versions and limits are listed in Appendix A with their sources. Each major decision also has a short decision record (Appendix B) explaining the alternatives considered.

When the PRD or the exam specification and this document disagree, the PRD wins on what the product does, the exam specification wins on exam rules, and this document wins on how the system does it. Any change to a decision in this document is made by writing a new decision record and updating the affected section.

## 1. What the system must do

### 1.1 Product in one paragraph

GaugePrep prepares learners for high-stakes language exams. It places the learner, teaches them from their level to the level their target needs, lets them sit full simulations under real exam conditions (including a live AI examiner for speaking), and predicts their real result using the exam's own scoring rules, as a range with a stated confidence. The first release covers TCF Canada and a free French track for learners in Cameroon; later releases add TEF Canada, German, English and other exams through the same engine.

### 1.2 Architecture drivers

| Driver | Source | What it forces in the design |
|---|---|---|
| Live speaking examiner, reply under 2.5 s, French with Cameroonian accents | PRD PRA-4, SIM-5, Section 14 | A dedicated real-time process, a voice framework with turn detection, a speech recognition service chosen by a measured accent test |
| Writing and speaking results in under 30 s and 60 s | PRD PRA-3, PRA-4 | Asynchronous grading on a job queue, never inside a web request |
| Predictions in the exam's own terms with confidence | PRD Section 9, exam specification Section 8 | A statistics engine (Rasch model), versioned scale mappings and combination models |
| Every prediction reproducible | PRD PRE-4, exam specification Section 13 | Versioned content and rules, append-only results that store every version used |
| Exam fidelity on 3G phones | PRD SIM-3, SIM-6, Section 14 | Server-owned timers, answers saved twice, small static pages and compressed audio served from the nearest edge |
| One engine, many exams | PRD Section 2.3, release plan | An exam plug-in contract with rules as versioned data |
| Free tools for local and staging, paid only in production | PRD Section 14 | Provider interfaces and configuration-only switches between free and paid services |
| Runnable by one person, no dependence on team size | PRD Section 14 | One deployable codebase, managed database, automated deploys, backups and alerts |
| Costs compatible with 7,900 FCFA a month | PRD Section 12 | Per-minute cost model, usage limits enforced in the backend, cheapest adequate model per task |

### 1.3 Load assumptions for release 1

| Measure | Value |
|---|---|
| Registered learners | 10,000 |
| Daily active learners | 1,000 |
| Peak concurrent learners | 300 |
| Peak concurrent speaking sessions | 30 |
| Multiple-choice answers per day | About 150,000 |
| Writing evaluations per day | About 1,500 |
| Speaking minutes per day | About 3,000 |

The design must reach these without changes and must scale tenfold by adding servers, not by redesign (Section 14.4).

## 2. System context

### 2.1 People

| Actor | Uses |
|---|---|
| Learner | The PWA on a phone or computer |
| Content reviewer | The internal console to author, review and publish content and to handle flags |
| Support admin | The internal console for accounts, payments and result-report verification |
| Owner | The internal console for plans, prices and accuracy publication |

### 2.2 External systems

| System | Role | Environment use |
|---|---|---|
| Anthropic API | Grading (Claude Sonnet 5.5) and light tasks (Claude Haiku 5.5) | Staging and production; local uses open models |
| OpenAI API | Backup grader (GPT-6.1 Sol), used only after it passes the release checks | Integrated, disabled by default |
| Speech recognition provider | Live and batch French transcription, chosen in milestone 0 among Deepgram, Mistral Voxtral and ElevenLabs Scribe | Staging and production |
| ElevenLabs | Examiner voice and listening content voices | Staging and production |
| LiveKit | Real-time audio rooms (WebRTC) for the examiner | Local dev server, LiveKit Cloud free tier in staging, self-hosted in production |
| Notch Pay | MTN Mobile Money, Orange Money and cards in Cameroon | Test keys locally and in staging, live keys in production |
| Resend | Transactional email | Staging and production |
| Cloudflare | DNS, CDN (data centre in Douala), static hosting of the PWA, R2 object storage, edge rate limits | All environments except local |
| Neon | Managed PostgreSQL 18 in Frankfurt | Staging (free) and production (paid) |
| Sentry, Grafana Cloud | Errors and traces; logs, metrics, dashboards and alerts | Staging and production |

### 2.3 Context diagram

```
                         +---------------------------+
   Learner (PWA) ------> |  Cloudflare (Douala edge) | --static app, audio--> R2
        |                +---------------------------+
        | HTTPS (api.)                 |
        v                              v
 +-------------------------------------------------+        Anthropic / OpenAI
 |                GaugePrep platform            | -----> Speech recognition
 |  core app | job worker | scoring | voice examiner|        ElevenLabs
 +-------------------------------------------------+        Notch Pay, Resend
        |  WebRTC via LiveKit (UDP, TURN/TLS 443)            Sentry, Grafana
        v
   Learner's microphone and speaker
 Reviewers and admins use the internal console of the core app.
```

## 3. Architecture style and process types

### 3.1 Style

GaugePrep is a modular monolith: one codebase, deployed as one application, divided into modules with enforced boundaries. Three additional process types run from the same codebase because their workloads differ from web requests. Microservices are not used: they would add network calls, distributed consistency and multiple deployments without a benefit at the planned scale (ADR-001).

### 3.2 Process types

| Process | Runs | Scales by |
|---|---|---|
| Core application | REST API (Django Ninja), internal console (Django admin and custom views), webhooks | Adding stateless instances behind the load balancer |
| Job worker | Procrastinate workers on queues: grading, media, notifications, billing, reporting | Adding worker instances per queue |
| Scoring engine | Procrastinate workers on the scoring queue: ability estimates, predictions, monthly calibration and refits | Adding worker instances; monthly batch runs on one instance |
| Voice examiner | LiveKit Agents workers that join a learner's audio room and run the examiner | Adding workers; each worker runs several sessions |

All four are Python and share the `examcore` package, so every exam rule exists once (ADR-002).

### 3.3 Communication rules

- Browser to platform: HTTPS JSON API on `api.<domain>`; WebRTC audio through LiveKit for speaking.
- Between modules inside the core: in-process calls to a module's public interface only.
- Core to workers: jobs written to the PostgreSQL queue in the same transaction as the change that causes them (transactional outbox, ADR-003).
- Voice examiner to core: an internal HTTPS API, authenticated with a service token, for session context and for storing recordings, transcripts and events. The voice examiner never reads or writes module tables directly.
- No process writes to another module's schema.

## 4. Modules

### 4.1 Module catalogue

| Module | Responsibility | Owns (schema) | Public interface offers |
|---|---|---|---|
| identity | Accounts, sessions, consents, account deletion | identity | current learner, consent checks, deletion request |
| learner | Goals, study plan, progress view | learner | goal and plan read and update |
| curriculum | Levels, units, lessons, spaced review queue | curriculum | next lessons, review items, level tests |
| content | Items, prompts, lessons content, media, simulation forms, review workflow, versions | content | published versions by ID, form assembly, media URLs |
| exammodels | Exams, rules versions, cut points, combination models, grader versions, exam plug-ins | exammodels | rules for an exam, active versions, the plug-in |
| practice | Practice sessions and answers | practice | start session, record answer |
| simulation | Simulation sittings, paper sittings, timers, answer sync, resume | simulation | start sitting, sync answers, submit paper, state |
| assessment | Grading jobs, task grades, paper scores | assessment | request grading, read grades and scores |
| prediction | Predictions per skill, readiness | prediction | latest prediction, history, readiness |
| calibration | Item parameters, bank calibrations, refits | calibration | current difficulties, run calibration |
| billing | Plans, entitlements, payments, usage counters, refunds | billing | entitlement check, usage check and increment, payment start |
| engagement | Notifications, reminders, push subscriptions, free track | engagement | notify, schedule reminder |
| reporting | Real-result reports, verification, accuracy snapshots | reporting | submit report, accuracy figures |
| admin | Support tools, audit log | admin | audit write |

### 4.2 Events between modules

Modules react to each other through events written to the outbox (jobs) in the same transaction as the change.

| Event | Emitted by | Consumed by |
|---|---|---|
| answers_recorded | practice, simulation | scoring engine (ability update) |
| paper_submitted | simulation | assessment (grading for writing and speaking), scoring engine (MCQ papers) |
| production_submitted | practice, simulation | assessment (grading job) |
| task_graded | assessment | prediction, learner (plan update), engagement (result ready) |
| paper_scored | assessment, scoring engine | prediction |
| prediction_updated | prediction | learner (plan), engagement (readiness message) |
| payment_completed | billing | engagement (receipt) |
| report_verified | reporting | billing (free month), calibration (refit data) |
| content_published | content | calibration (initial difficulty), media (audio build) |

### 4.3 Boundary enforcement

- Each module is a Python package with a `public.py` file. Other modules import only that file.
- Import Linter contracts in CI enforce: independence between modules except through `public`; `examcore` never imports Django; no import cycles.
- Each module has its own PostgreSQL schema. Cross-schema foreign keys are allowed only towards `identity.user` (by learner ID) and towards immutable content versions.

## 5. Exam plug-in model

### 5.1 Contract

Each exam is a plug-in implementing one interface in `examcore`:

```
class ExamModel(Protocol):
    code: str                                   # "TCF_CA"
    def blueprint(rules) -> Blueprint           # papers, item counts, timings, form constraints
    def delivery_rules(rules, paper) -> Delivery  # plays per recording, navigation, timers, word ranges
    def rule_checks(rules, task, text) -> list[RuleResult]   # deterministic checks
    def score_mcq(rules, ability, cut_points) -> PaperScore  # ability -> exam scale
    def score_production(rules, task_levels, combination) -> PaperScore  # levels -> mark
    def report(rules, scores) -> ExamResult     # NCLC per skill for TCF Canada
```

### 5.2 Exam rules as data

- An `exam_rules_version` is a JSON document validated against a Pydantic schema when it is published: papers, timings, item counts, word ranges, score bands, conversion tables, delivery rules.
- Cut points, combination models and grader versions are separate versioned records because they are refitted on their own schedules.
- TCF Canada is implemented first as `TCF_CA`, with rules version `TCF-CA-rules-v1` taken from the exam specification. TEF Canada later adds its own scoring and its three date-dependent NCLC tables without changes to the core.

## 6. Key flows

### 6.1 Sign-up and goal

1. The learner signs up with email and a password, or with Google, and a date of birth (16 or older). No phone number is collected.
2. identity creates the account and records the required consent; a single-use, time-limited verification code is sent by email (Resend).
3. The learner sets a goal: exam, target NCLC per skill (default 7), exam date.

### 6.2 Multiple-choice answer (practice or simulation)

1. The PWA shows the item version and plays audio from the CDN.
2. On answer, the PWA writes the answer to its local journal with a client-generated ID, then sends it to the API.
3. The API stores the `response` with the client ID as an idempotency key, so a resend never duplicates.
4. The same transaction writes an `answers_recorded` job.
5. The scoring engine recomputes the learner's ability for that skill and writes a new `paper_score` (simulation) or updates practice evidence, then a new `prediction`.

### 6.3 Writing grading

1. The learner submits a task; practice or simulation stores a `production` and writes a grading job.
2. The worker runs the rule checks from `examcore` (word count, copying, off-topic, memorised text, similarity to own past texts).
3. If a rule fails, the task level is "A1 not reached" and no model call is made.
4. Otherwise, two independent grading passes run on Claude Sonnet 5.5 with the task's rubric and exemplars (cached prompt prefix; never the evaluation anchors), each returning criterion levels, task level and quoted evidence as validated JSON.
5. A third pass runs when the passes differ by more than one level.
6. The worker writes an append-only `task_grade` with the grader version, and the feedback text.
7. When the three tasks of a paper are graded, the combination model produces the mark out of 20, CEFR and NCLC in a `paper_score`, followed by a new `prediction`.
8. Target: result visible in under 30 s at the 95th percentile.

### 6.4 Speaking session

1. The learner opens a speaking task or the speaking paper; the core checks entitlement and usage, creates a LiveKit room and returns a short-lived token for that room only.
2. LiveKit dispatches a voice examiner worker to the room.
3. The worker loads the session context (task cards, hidden sheet, timing, learner level) from the internal API.
4. Live loop: learner audio is streamed to the speech recognition service; turn detection decides when the learner has finished; Claude Haiku 5.5 produces the examiner's next line under the task rules; ElevenLabs Flash speaks it.
5. The examiner follows the timing rules: preparation only before task 2, interruptions in task 3 after 60 to 90 s, probing questions when an answer sounds recited.
6. The worker records the learner's audio on the server, stores it in R2 (private) and posts the live transcript and audio measures to the internal API.
7. After each task, the batch transcription of the recording produces the grading transcript, then grading follows the writing flow with speaking criteria.
8. Targets: examiner reply under 2.5 s at the 95th percentile; result under 60 s after the task.

### 6.5 Full simulation and resume

1. Starting a paper creates a `paper_sitting` with a server deadline (start time plus paper duration).
2. The PWA displays the remaining time from the server and keeps a local journal of answers and writing drafts.
3. On connection loss, the PWA keeps working against its journal; listening items already played cannot be replayed.
4. On reconnect, the PWA sends the journal; the server accepts answers time-stamped before the deadline and returns the remaining time.
5. At the deadline, the server closes the paper whether or not the device is online, and grading starts with the saved answers.

### 6.6 Monthly calibration

1. A scheduled job runs the Rasch estimation by marginal maximum likelihood on all responses, with stable items fixed as anchors.
2. It computes fit statistics per item and flags items for review.
3. It writes a new `bank_calibration` and `item_parameter` rows.
4. It checks prediction accuracy on verified real results against the current calibration; the new calibration becomes active only if accuracy does not decrease.

### 6.7 Payment

1. The learner chooses a plan; billing creates a `payment` with our reference and calls Notch Pay to initialise and charge.
2. The learner confirms on their phone.
3. Notch Pay sends a webhook; billing verifies the `x-notch-signature`, then confirms the status with `GET /payments/{reference}`.
4. On `complete`, billing creates or extends the entitlement in the same transaction and emits `payment_completed`.
5. A reconciliation job every 15 minutes re-checks payments still processing.

### 6.8 Real-result reporting

1. On the exam date plus 15 working days, engagement sends the request.
2. The learner submits scores and optionally the attestation.
3. A support admin verifies the attestation; the file is deleted after verification.
4. `report_verified` grants a free month and adds the result to the calibration data when consent was given.

### 6.9 Content publishing

1. An author drafts an item with AI assistance in the console.
2. A reviewer approves it; the version becomes immutable.
3. For listening, the media job voices the script with ElevenLabs, encodes Opus and AAC, stores both in R2 under content-hashed names and attaches them after the reviewer approves the audio.
4. Publication assigns the initial difficulty from the item's level.

## 7. Data architecture

### 7.1 Principles

1. Content and rules are versioned: a stable identity plus immutable numbered versions. A correction creates a new version.
2. Results are append-only: grades, paper scores and predictions are never updated or deleted by the application. Database privileges enforce it. Re-scoring creates new records linked to the ones they replace.
3. Personal data lives only in identity; every other table uses an anonymous learner ID.
4. Identifiers are `uuidv7()` (time-ordered, PostgreSQL 18); scores are `numeric` with fixed precision.
5. Each module owns one PostgreSQL schema.

### 7.2 Main tables

| Schema | Tables |
|---|---|
| identity | user, consent, auth sessions |
| learner | goal, study_plan, plan_item |
| curriculum | level, unit, lesson, lesson_version, review_queue, level_test_result |
| content | item, item_version, prompt, prompt_version, media_asset, simulation_form, form_version, review_event |
| exammodels | exam, exam_rules_version, cut_point_set, combination_model, grader_version |
| calibration | bank_calibration, item_parameter |
| practice | practice_session, response (partitioned), production |
| simulation | simulation_sitting, paper_sitting, response (partitioned), production |
| assessment | grading_job, task_grade, paper_score |
| prediction | prediction, readiness_event |
| billing | plan, entitlement, payment, webhook_event, usage_counter, refund |
| engagement | notification, push_subscription, free_track_progress |
| reporting | real_result_report, report_verification, accuracy_snapshot |
| admin | audit_log |

### 7.3 Traceability record

Every `task_grade`, `paper_score` and `prediction` stores: exam rules version, item bank calibration version, cut point set version, combination model version, grader version (model ID, prompt fingerprint, rubric version, anchor set version, settings), and the IDs of the evidence used. Any result can be recomputed from these.

### 7.4 Retention and deletion

| Data | Kept |
|---|---|
| Account and identity | Until deletion request; removed within 30 days |
| Essays and transcripts | 12 months after last activity, then deleted |
| Speaking recordings | 12 months, by R2 lifecycle rule |
| Attestation uploads | Deleted after verification |
| Grades, scores, predictions | Kept without personal data for accuracy statistics |
| Payment records | Kept as required for accounting; card data never stored by GaugePrep |
| Raw webhooks | 24 months |

### 7.5 Growth

The `response` tables are partitioned by month from day one (about 150,000 rows a day at launch, about 55 million a year). `task_grade`, `paper_score` and `prediction` adopt the same partitioning once they pass a few million rows.

## 8. AI and speech architecture

### 8.1 Provider interfaces

All external AI and speech services sit behind three interfaces in the backend and voice packages:

| Interface | Implementations |
|---|---|
| TextModel | Anthropic (production), OpenAI (backup), Ollama with open models (local) |
| SpeechToText | Streaming and batch adapters for the provider chosen in milestone 0; open-weight Voxtral for local development |
| TextToSpeech | ElevenLabs (Flash for the examiner, v3 for content); a local engine for development |

Switching provider is a configuration change. There is no silent fallback: if the configured grader is unavailable, grading jobs wait and retry; a backup grader is used only if it has its own passed release check and is enabled by configuration.

### 8.2 Models and use

| Use | Model | Notes |
|---|---|---|
| Writing and speaking grading | `claude-sonnet-5-5` | Pinned model ID; no retirement before 28 September 2027 per Anthropic's published table; 60 days' minimum notice |
| Examiner dialogue, topic classification, light generation | `claude-haiku-5-5` | Fastest Anthropic model |
| Content drafting, anchor re-runs | Same models through the Batch API | 50% lower price |
| Backup grader | `gpt-6.1-sol` | Disabled until it passes the release checks |

### 8.3 Grader versioning and release

- A grader version is the combination of model ID, prompt, rubric, anchor set and settings. Any change creates a new version.
- A new version serves learners only after it passes the release checks of the exam specification (Section 9.1): exact level on at least 60% of evaluation anchors, within one level on 95%, no inversions, 90% consistency over repeated runs, rule checks, gaming and injection tests.
- The release check is a CI workflow that calls the real model and stores its report with the grader version.

### 8.4 Prompt and output safety

- Learner text and transcripts are passed as clearly delimited data, never as instructions.
- Outputs are requested as structured JSON and validated against a schema before storage; invalid outputs are retried once, then flagged.
- Requests carry no name, email or phone number.
- A zero data retention agreement is requested from Anthropic before production.

### 8.5 Voice pipeline

| Stage | Choice |
|---|---|
| Framework | LiveKit Agents 1.8 (Python) |
| Transport | LiveKit media server, WebRTC over UDP with built-in TURN over UDP and TLS on port 443 |
| Turn detection | LiveKit turn detector with French support; light version on CPU |
| Speech recognition | Chosen by the milestone 0 accent test |
| Dialogue | Claude Haiku 5.5, streaming |
| Voice | ElevenLabs Flash, streaming |
| Recording | Server-side capture of the learner's track, Opus, stored in private R2 |

The chained pipeline is used instead of a speech-to-speech model because grading needs a word-level transcript of the learner's own words, the recognition service must be chosen for Cameroonian accents, and the examiner rules are easier to enforce and test as text (ADR-006).

### 8.6 Speech recognition selection (milestone 0)

- Candidates: Deepgram Nova-3 Multilingual, Mistral Voxtral Realtime, ElevenLabs Scribe v2 Realtime, each with its batch counterpart.
- Data: 20 Cameroonian speakers, francophone and anglophone, A2 to C1, recording the three TCF speaking tasks, with signed consent; verbatim human transcripts.
- Measures: word error rate; preservation of the learner's grammatical errors (at least 95%); word-level timing and confidence available; latency; price.
- Rule: the lowest word error rate among candidates that meet the preservation and word-level requirements; within one point, the cheaper wins.

### 8.7 Cost controls

- Usage counters per learner per day and per month enforce the PRD limits (8 writing evaluations, 30 speaking minutes and 1 simulation per day; 300 speaking minutes and 120 writing evaluations per month).
- Prompt caching for rubric and exemplars.
- Rule checks before any model call; no model call for a task that fails a rule.
- Daily AI spend per provider tracked against budget, with alerts.

## 9. Scoring engine

| Aspect | Design |
|---|---|
| Model | Rasch (one-parameter item response theory), implemented in `examcore` with NumPy and SciPy |
| Learner ability | Maximum a posteriori estimate from the last 60 days of responses, weighted 1.0 (simulation), 0.7 (practice in exam mode), 0.4 (practice in learning mode) |
| Item difficulty | Initial value by target level (A1 -3.0 to C2 3.0, adjustable by ±0.5); re-estimated after 200 responses |
| Calibration | Monthly marginal maximum likelihood with stable items fixed as anchors |
| Item quality | Infit and outfit 0.7 to 1.3; point-biserial at least 0.20; each distractor chosen by at least 3% of learners below the item level |
| Scale conversion | Cut points per CEFR boundary at 67% success on the lower level's items; linear within bands; refitted from 100 verified real results |
| Productive skills | Combination model 0.20, 0.35, 0.45 for tasks 1 to 3, refitted from 100 verified real results |
| Verification | Recovery tests on simulated data and comparison with an established statistics package in CI |
| Activation | A new calibration or refit becomes active only if it does not reduce accuracy on verified results |

## 10. Frontend architecture (PWA)

### 10.1 Structure

- Next.js 16 in static export mode: one HTML file per route, served from Cloudflare's edge, including Douala.
- React and TypeScript in strict mode; the API client is generated from the backend OpenAPI contract.
- Public pages (landing, pricing, accuracy page, help) are pre-rendered for search engines; the learner app runs client-side after sign-in.
- Interface text in French and English through message catalogues; the content language is the exam's language.

### 10.2 Offline and resilience

- Service worker built with Serwist: caches the app shell, the next practice set's audio and the active simulation's media.
- Local journal in IndexedDB for answers and writing drafts of the active session, synced whenever the app is open and online; no reliance on background sync, which iOS does not support.
- The server is the source of truth; local data is short-lived because iOS can clear site storage after 7 days without use or under storage pressure, and limits it to about 50 MB.

### 10.3 Audio

- Listening audio in Opus at 24 kb/s mono, with an AAC fallback for iOS before 18.4; the PWA chooses by `canPlayType`.
- File names are content hashes, cached indefinitely at the edge.
- Speaking uses the LiveKit JavaScript client; microphone permission is requested in context with an explanation.

### 10.4 Performance budget

| Measure | Budget |
|---|---|
| First load of a learner page on 3G | Usable in under 3 s |
| JavaScript per route | Kept small by per-route splitting; checked in CI |
| Full simulation data, speaking excluded | Under 15 MB |

## 11. API conventions

| Topic | Convention |
|---|---|
| Style | REST over HTTPS, JSON, under `/api/v1`; breaking changes create `/api/v2` |
| Contract | OpenAPI generated by Django Ninja; the frontend client is generated from it; CI fails on mismatch |
| Errors | Problem details format (RFC 9457) with a stable error code and a message in the learner's language |
| Idempotency | `Idempotency-Key` header on every write that may be retried (answers, submissions, payments); answer records also carry the client ID |
| Pagination | Cursor-based on time-ordered IDs |
| Time | ISO 8601 in UTC; the server's clock is authoritative for timers |
| Authentication | Session cookie (HttpOnly, Secure, SameSite Lax) shared across `app.` and `api.` of the same domain; CSRF token on writes |
| Authorisation | Every endpoint declares the role and entitlement it needs; learners can only reach their own data |
| Rate limits | At the edge for sign-in and sign-up; in the API per learner on AI-backed actions; usage limits from billing |
| Internal API | Separate `/internal/v1` path, reachable only from the private network, authenticated with a service token, used by the voice examiner |
| Webhooks | Signature verification, raw body stored, processing idempotent by provider reference |

## 12. Security

- Baseline: OWASP ASVS 5.0 Level 2 as the review checklist.
- Passwords hashed with Argon2 (Django's Argon2 hasher); sessions rotate on sign-in; "sign out of all devices" deletes all sessions.
- Database roles: the application role cannot UPDATE or DELETE append-only tables; migrations use a separate role; only identity reads personal data.
- Network: databases, workers, scoring and voice workers are not exposed to the internet; only the API, the LiveKit server ports and the static site are public.
- Secrets in GitHub repository secrets prefixed `DEV_`, `STAGING_` or `PROD_` (the free plan has no environments for a private repository) and Kamal secrets; distinct keys per environment.
- Edge: security headers and a strict content security policy for the static app; rate limits on authentication.
- LiveKit tokens valid for one room and a short time.
- Recordings and attestations in private buckets, reachable only through short-lived signed URLs.
- Dependency updates by Dependabot; secret scanning with gitleaks; a dedicated review for any change touching authentication, payments or personal data.
- Audit log for every reviewer and admin action.

## 13. Repository and delivery

### 13.1 Repository layout

```
gaugeprep/                      private GitHub repository
  apps/
    web/                           Next.js PWA (pnpm)
    backend/
      config/                      Django settings per environment
      modules/<module>/            models, services, api, tasks, public.py
    voice/                         LiveKit examiner worker
  packages/examcore/               exam rules, rule checks, Rasch maths, plug-ins (no Django)
  tooling/
    eslint/ typescript/ python/    shared lint, type and format configs
    ci/                            our own CI checks and their tests
    semgrep/                       custom Semgrep rules and their tests
  infra/
    docker/                        images for api, worker, voice
    kamal/                         deploy configs for staging and production
    server/                        rebuild script for the shared dev and staging server
  docs/
    architecture/                  this document
    adr/                           decision records
    exam-specs/                    exam specifications
    runbooks/                      operations procedures
```

- Python managed with uv (workspace, single lockfile, pinned Python 3.14); frontend with pnpm.
- Formatting, linting and type checks for Python and TypeScript run before commit and in CI.

### 13.2 Pipeline

| Trigger | Steps |
|---|---|
| Pull request | One `gate` job (changed paths, PR title, gitleaks); then, unless the PR is docs only, `pnpm check`: lint, types, Import Linter contracts, unit and integration tests with PostgreSQL 18, API contract check, frontend tests, coverage floors and 90% on changed lines; plus the smoke end-to-end set when `apps/` changed (ADR-021) |
| Promotion PR, `develop` into `stage` | The pull request checks, plus the full end-to-end suite, mutmut on `examcore` and scoring code, and the full scoring engine recovery tests (ADR-021) |
| Push to develop | Build ARM images on GitHub's arm64 runners, push to GitHub Container Registry, deploy to dev with Kamal, publish the static PWA to Cloudflare dev |
| Push to stage (or a manual run on `hotfix/*`) | The same images, deployed to staging with Kamal, and the PWA published to Cloudflare staging |
| Version tag pushed by the owner on a commit on main, no approval step (ADR-020) | Check the tag format, the owner as actor and the commit on main, then run migrations (expand-then-contract), deploy to production with Kamal (zero-downtime switch through kamal-proxy), publish the PWA |
| Change to grader prompt, rubric or model | Grader release check workflow against the real model |

No scheduled runs: the free plan's 2,000 Actions minutes a month go to pull requests and the promotion PR; the budget and its arithmetic are in ADR-021.

## 14. Environments and infrastructure

### 14.1 Region

Servers run in Germany (Hetzner) next to the database in Frankfurt (Neon). Traffic from French-speaking Central Africa routes through European hubs such as Paris and Marseille, so Western Europe is the closest network location. Static files and audio are served from Cloudflare's Douala data centre. A latency test from Douala on MTN and Orange mobile data confirms the region in milestone 0.

### 14.2 Environments

| Part | Local | Dev | Staging | Production |
|---|---|---|---|---|
| App, workers, scoring, voice | Docker Compose | Oracle Cloud Always Free ARM server, separate Kamal deploy | Oracle Cloud Always Free ARM server (2 OCPU, 12 GB) | Hetzner Cloud ARM servers (app server; voice server) |
| Database | PostgreSQL 18 in Docker | Neon Free branch, Frankfurt | Neon Free, Frankfurt | Neon Launch, Frankfurt |
| LiveKit | `livekit-server --dev` | LiveKit Cloud Build (free), shared with staging | LiveKit Cloud Build (free) | Self-hosted LiveKit server |
| Object storage | Local disk via Django storage | Cloudflare R2 free tier, own bucket | Cloudflare R2 free tier | Cloudflare R2 |
| CDN and DNS | None | Cloudflare free | Cloudflare free | Cloudflare free |
| AI and speech | Local open models | Self-hosted open models | Self-hosted open models | Real providers |
| Payments | Notch Pay test keys | Notch Pay test keys | Notch Pay test keys | Notch Pay live keys |
| Email | Mailpit | Mailpit | Resend free | Resend free, Pro once over 100 a day (owner decision) |
| Monitoring | Console | Sentry and Grafana Cloud free | Sentry and Grafana Cloud free | Sentry and Grafana Cloud |
| Host | `localhost` | `dev.gaugeprep.com` (planned) | `staging.gaugeprep.com` (planned) | Not yet named |
| Kamal service and image | None | `gaugeprep-dev`, `ghcr.io/<org>/gaugeprep-backend` (planned) | `gaugeprep-staging`, `ghcr.io/<org>/gaugeprep-backend` (planned) | Not yet named |

Dev deploys every merge into `develop` and is where each ticket is tested. Staging deploys the `stage` branch, the release candidate, and is where the release gate and the weekly demo run. Both are fully scripted and rebuilt from scratch in under an hour, because free tiers can change without notice (Oracle halved its free ARM allowance on 15 June 2026). Both hold only synthetic data from seed scripts. Branches and promotion are in `docs/process/branching-and-release.md` and ADR-019.

### 14.3 Production topology

```
 Cloudflare (DNS, CDN, static PWA, R2, edge rules)
        |
   api.<domain> ---> Hetzner app server: kamal-proxy -> core app containers
                                         job worker containers
                                         scoring engine container
   lk.<domain>  ---> Hetzner voice server: LiveKit server (Caddy TLS, TURN 443)
                                           voice examiner worker containers
        both servers ---> Neon PostgreSQL 18 (Frankfurt), private credentials
```

### 14.4 Scaling path

| Stage | Change |
|---|---|
| Release 1 (up to about 10,000 learners) | One app server, one voice server, Neon Launch |
| About 100,000 learners | More app and voice servers behind a load balancer; larger Neon compute and a read replica; partitioning of grade and prediction tables; queue moved to its own database |
| 1,000,000 learners and more | Dedicated queue system and caching behind existing interfaces; LiveKit cluster across several servers |

### 14.5 Infrastructure cost at launch

| Item | Monthly |
|---|---|
| Hetzner app server (ARM) | From €5.99 |
| Hetzner voice server (ARM, sized by load test) | About €41 |
| Neon Launch (about 0.5 compute unit average, storage) | About $40 to $45 |
| Cloudflare, R2, Resend, Sentry, Grafana Cloud at launch volume | €0 to €5 |
| Total | About €90 to €100 |

## 15. Testing strategy

The strategy, the minutes budget and when each layer starts are in ADR-021.

| Layer | Tests | When |
|---|---|---|
| examcore | pytest fixed-answer tests from every table of the exam specification; Hypothesis property tests; mutmut, mutation score at least 80% | Every pull request with code; mutmut on the promotion PR |
| Scoring engine | Recovery on simulated data; comparison with an established statistics package; mutmut, at least 80% | Pull request (small set), promotion PR (full, and mutmut) |
| Backend modules | pytest-django against PostgreSQL 18, never SQLite; idempotency of answers and webhooks; append-only enforcement; authorisation; every endpoint has success, not-found and other-learner-refused tests | Every pull request with code |
| API | Schemathesis in-process against `apps/backend/openapi.json`: documented statuses, no 5xx on bad input, schema-valid responses | Every pull request with code |
| Frontend | Vitest and React Testing Library | Every pull request with code |
| End to end | Playwright with slow 3G throttling and axe-core (zero serious or critical violations). Smoke: about 5 happy paths at 375 px. Full: 375 px and 1440 px, all flows, a server error, offline, session expiry, another learner's URL refused, interrupted and resumed simulations | Smoke on pull requests touching `apps/`; full on the promotion PR |
| Voice examiner | Scripted conversations with recorded audio: timings, interruptions, no volunteered information, recitation probing | Every change to voice |
| Grader | Release check on the anchor set with the real model | Every grader change; blocks release |
| Load | API and queue at twice expected peak; concurrent speaking sessions to size the voice server | Before launch and before infrastructure changes |
| Security | ASVS Level 2 review; dependency and secret scanning | Before launch; continuous |

Rules for every automated layer:

- Branch coverage floors: `examcore` 95%, backend 85%, web 80%, and 90% on the lines a PR changes (diff-cover). Floors live in config and only go up.
- Under CI no test may be skipped or xfail; tests run in random order with the seed printed; every test has a timeout (pytest 30 s, Vitest 10 s, Playwright 60 s unless the test sets its own with a reason).
- No retries for unit or integration tests. Playwright retries 0 on PRs and 1 on the promotion PR, where a pass on retry still fails the run.
- Branch protection is unavailable on the free private plan: `merge.sh` refusing a PR without a green run on its head commit is the gate.
- Hypothesis and axe-core are MPL-2.0, accepted as dev-only: used in tests, never shipped to learners.

## 16. Observability and operations

### 16.1 Signals

| Signal | Tool |
|---|---|
| Errors and traces (PWA, API, workers, voice) | Sentry |
| Logs (structured JSON from every container) and metrics | Grafana Cloud through Grafana Alloy |
| Availability of public endpoints | Alert when request metrics from the API or the LiveKit server stop for 5 minutes, plus Sentry error-rate alerts |
| AI and speech usage and spend | Usage counters and provider usage exported as metrics |

### 16.2 Alerts

| Alert | Threshold |
|---|---|
| API latency | 95th percentile over 1 s for 10 min |
| Writing grading time | 95th percentile over 30 s |
| Speaking result time | 95th percentile over 60 s |
| Examiner reply time | 95th percentile over 2.5 s |
| Queue delay | Oldest job older than 2 min on grading, 15 min elsewhere |
| Failed jobs | Any job failing after all retries |
| Payments stuck | Any payment processing for more than 30 min |
| AI spend | Daily spend over 120% of budget |
| Prediction accuracy | Share within one NCLC level down 10 points from last month |

### 16.3 Runbooks

Written in `docs/runbooks` before launch: deploy and rollback; restore the database from Neon history and from the weekly dump; rebuild staging; rotate a provider key; switch speech provider; disable a grader version; handle a payment dispute; respond to a data deletion request; incident response and post-incident review.

### 16.4 Backups

Neon history window (up to 7 days on Launch) plus a weekly encrypted logical dump to R2, kept 8 weeks. A restore is rehearsed monthly and timed.

## 17. Cost model per learner

| Activity | Cost |
|---|---|
| One minute of speaking practice | About $0.03 (live recognition $0.006, batch transcript $0.003, examiner voice $0.012, dialogue $0.001, grading $0.009) |
| One writing task graded | About $0.035 |
| Typical Premium month (80 speaking minutes, 24 writing tasks, 2 full simulations) | About $4.30, against about $13.50 of revenue: about 68% margin before payment fees |
| Worst case within limits (300 speaking minutes, 120 writing evaluations) | About $13.20, about break-even; this is the reason for the monthly fair-use ceiling |

Prices are those published by providers in October 2026 and are tracked monthly on the cost dashboard.

## 18. Technical risks

| Risk | Mitigation |
|---|---|
| No recognition service is accurate enough on Cameroonian accents | Measured selection in milestone 0; visible transcripts; intelligibility, not accent, is assessed; providers swappable |
| Grader below release thresholds | Prompt and rubric iteration on anchors; backup grader evaluated under the same checks; launch blocked until passed |
| Provider price or policy change | Provider interfaces; monthly cost review; pinned model IDs with published retirement dates |
| Free-tier change in staging | Staging scripted and rebuildable in under an hour on any provider |
| Voice server overloaded at peak | Load test sizing; horizontal scaling of examiner workers; usage limits |
| Data loss | Neon history plus weekly dumps; monthly restore rehearsal |
| Module boundaries erode | Import Linter contracts in CI; schema per module |
| Exam rules change | Rules as versioned data; check FEI and IRCC before each release |

## 19. Delivery plan

| Milestone | Delivers | Done when |
|---|---|---|
| M0 Foundations and checks | Repository, CI/CD, environments (local, dev, staging, production), deploy pipeline; accent test; latency test from Douala; Notch Pay confirmation; grader release-check pipeline skeleton | Dev deploys from develop and staging from stage; recognition provider chosen; region confirmed |
| M1 Accounts and content | Sign-up, consents, goals; content bank with review workflow, versions and audio pipeline | A reviewer publishes an item with audio; a learner signs up and sets a goal |
| M2 Listening and reading | Practice for both papers; scoring engine v0; diagnostic | A learner receives a predicted 699-scale range from the diagnostic |
| M3 Writing | Rule checks, grader, anchors, release checks, feedback | The grader passes every release check |
| M4 Speaking | Voice examiner, recording, transcription, grading | A full 12-minute speaking paper scored end to end |
| M5 Simulation and prediction | Sittings, forms, resume, result page, predictions, readiness | A full four-paper simulation produces NCLC ranges with confidence |
| M6 Learning path | Curriculum delivery, study plan, spaced review, free track | The plan adapts after a simulation; free track usable |
| M7 Business and operations | Plans, payments, usage limits, notifications, result reporting, accuracy page, admin | A learner pays with MTN or Orange money in production and gets access within a minute |
| M8 Launch hardening | Load tests, ASVS Level 2 review, accessibility, 3G tests, restore rehearsal | Every PRD launch criterion is met |

Content production (items, prompts, lessons, anchors) runs in parallel from M1 under the exam specification's workflow.

## Appendix A: Technology versions and sources

| Technology | Version or plan | Source checked |
|---|---|---|
| Python | 3.14 (bugfix support to October 2030) | Python developer guide, versions page |
| Django | 6.1 (released 5 August 2026), then 6.2 LTS (April 2027, supported to April 2030) | djangoproject.com download page and release post |
| Django Ninja | 1.7.1 (19 September 2026) | PyPI |
| Procrastinate | 3.10.0 (23 September 2026) | PyPI |
| PostgreSQL | 18 (18.6, supported to November 2030) | PostgreSQL support table via WZ-IT |
| Neon | Postgres 18 GA (May 2026); Free and Launch plans; Frankfurt region | neon.com pricing, regions, changelog |
| Next.js | 16.4.2 (21 October 2026), static export | versio.io release tracking; nextjs.org docs |
| Serwist | Service worker library referenced by the Next.js PWA guide | nextjs.org PWA guide |
| LiveKit Agents | 1.8.8 (15 October 2026), Python 3.10 to 3.14 | PyPI |
| LiveKit Cloud | Build free: 1,000 agent minutes, 5 concurrent sessions | livekit.com pricing |
| Claude Sonnet 5.5, Haiku 5.5 | $2/$10 and $0.10/$0.50 per million tokens; no retirement before September and October 2027 | Anthropic pricing and model deprecations pages |
| GPT-6.1 Sol | $2/$10 per million tokens | OpenAI pricing page |
| Deepgram Nova-3 Multilingual | $0.0058 per minute streaming (promotional) | deepgram.com pricing |
| Mistral Voxtral Realtime | $0.006 per minute; open weights Apache 2.0 | AI Business, February 2026 |
| ElevenLabs | Flash $0.04 and v3 $0.08 per 1,000 characters; Scribe v2 $0.22 per hour, Realtime $0.39 per hour | elevenlabs.io API pricing |
| Cloudflare R2 | 10 GB free; $0.015 per GB-month; no egress fees | Cloudflare R2 pricing |
| Hetzner Cloud | ARM CAX11 €5.99, CAX41 €40.99 after June 2026 repricing | privatedevops.com report |
| Oracle Always Free | 2 OCPU and 12 GB ARM since 15 June 2026 | InfoQ, July 2026 |
| Kamal | 2.12.0 (18 June 2026) | RubyGems |
| GitHub Actions | arm64 runners in private repositories since 29 January 2026; free plan over 33 hours a month | GitHub changelog |
| Import Linter | 2.15 (4 September 2026) | PyPI |
| Sentry | Developer plan free: 5,000 errors, 5 million spans | sentry.io pricing |
| Grafana Cloud | Free: 10,000 series, 50 GB logs and traces, 3 users | Last9 pricing analysis, September 2026 |
| Resend | Free 3,000 emails a month, 100 a day, 3 domains; Pro $20 for 50,000; data stored in the US (ADR-024) | resend.com pricing and GDPR page, 5 November 2026 |
| OWASP ASVS | 5.0.0 (May 2025) | OWASP ASVS repository |

## Appendix B: Decision records

| ID | Decision |
|---|---|
| ADR-001 | Modular monolith with four process types |
| ADR-002 | Python and Django for all backend processes, with a shared examcore package |
| ADR-003 | PostgreSQL 18 as database and job queue (Procrastinate), no Redis at launch |
| ADR-004 | Next.js static export as the PWA, served from Cloudflare |
| ADR-005 | Session cookie authentication |
| ADR-006 | Chained voice pipeline on LiveKit Agents instead of a speech-to-speech model |
| ADR-007 | Claude Sonnet 5.5 as the grader, Haiku 5.5 for light tasks, GPT-6.1 Sol as backup |
| ADR-008 | Speech recognition chosen by a measured accent test |
| ADR-009 | ElevenLabs for examiner and content voices |
| ADR-010 | In-house Rasch scoring engine verified against a reference |
| ADR-011 | Versioned content and append-only results |
| ADR-012 | Hosting: Hetzner Germany, Neon Frankfurt, Cloudflare edge |
| ADR-013 | Self-hosted LiveKit in production, LiveKit Cloud free in staging |
| ADR-014 | Notch Pay for payments; automatic card renewal after release 1 |
| ADR-015 | GitHub Actions and Kamal for delivery |
| ADR-016 | Sentry and Grafana Cloud for observability |
| ADR-017 | Opus with AAC fallback for audio |
| ADR-018 | Twilio for SMS verification codes behind an SMS provider interface (superseded by ADR-023) |
| ADR-019 | Dev, staging and production from develop, stage and main |
| ADR-020 | Production deploys on the owner's tag, without an approval gate |
| ADR-021 | Test strategy and CI minutes budget |
| ADR-022 | PR security scanners catch accidents, not a deliberate bypass |
| ADR-023 | Email verification only, no SMS sign-up |
| ADR-024 | Resend for transactional email, Mailpit locally and in dev |

## Appendix C: Glossary

| Term | Meaning |
|---|---|
| Modular monolith | One deployable application divided into modules with enforced boundaries |
| Outbox | Writing a job in the same database transaction as the change that triggers it |
| Append-only | Records are inserted, never updated or deleted by the application |
| examcore | The shared Python package holding exam rules and scoring maths |
| Grader version | The combination of model, prompt, rubric, anchors and settings that produced a grade |
| Rasch model | Item response model relating learner ability and item difficulty |
| TURN | A relay that lets real-time audio pass through restrictive networks |
| PWA | Progressive web app: a web app installable on the home screen |
| Kamal | A tool that deploys Docker containers to servers over SSH with zero downtime |
