# Data model

> Guidance only: the API contract is the OpenAPI document generated from the code, and the code wins where they differ.

The tables of every module, in PostgreSQL 18. This document details architecture Section 7. Engineers turn it into Django models and migrations module by module; a change here is made in the same pull request as the migration.

## 1. Conventions

| Topic | Rule |
|---|---|
| Schemas | One PostgreSQL schema per module, named after the module (architecture 4.1) |
| Primary keys | `id uuid primary key default uuidv7()` |
| Learner reference | `learner_id uuid` everywhere outside `identity`. It is `identity.user.id`; the only cross-schema foreign keys allowed point to `identity.user` and to immutable content versions (architecture 4.3) |
| Time | `timestamptz`, stored in UTC; columns end in `_at` |
| Scores | `numeric(6,2)` for scale scores and marks, `numeric(7,4)` for logits and standard errors |
| Levels | Text enum `level` with values `BELOW_A1, A1, A2, B1, B2, C1, C2`, stored as a PostgreSQL enum in `exammodels` and reused |
| Money | `amount_minor bigint` plus `currency char(3)`; FCFA has no minor unit, so 7,900 FCFA is stored as 7900 |
| JSON | `jsonb`, always validated by a Pydantic model before write |
| Append-only tables | Marked "append-only": the application role has INSERT and SELECT only. Corrections insert a new row with `supersedes_id` |
| Soft data | No soft deletes. Deletion of personal data follows Section 16 |
| Partitioning | Marked "partitioned by month": range partition on `created_at`, partitions created ahead by a scheduled job |

Column notation below: `name type [constraints] : meaning`. Every table also has `created_at timestamptz not null default now()` unless stated otherwise; mutable tables also have `updated_at`.

## 2. identity

Personal data lives only here (architecture 7.1).

**user**
- `id uuid pk`
- `email citext unique not null` : no phone number is collected
- `email_verified_at timestamptz null`
- `password_hash text null` : Argon2; null for Google-only accounts
- `date_of_birth date not null` : check age at least 16 at sign-up time in the service, not as a constraint
- `interface_language text not null check in ('fr','en')`
- `country char(2) null` : ISO 3166, from sign-up, used for currency and later markets
- `status text not null check in ('active','deletion_requested','deleted')`
- `deletion_requested_at timestamptz null`
- `last_active_at timestamptz null`
- `role text not null default 'learner' check in ('learner','reviewer','support','owner')`

**oauth_account**: `id`, `user_id fk user`, `provider text check in ('google')`, `subject text`, unique (`provider`, `subject`)

**verification_code**: `id`, `user_id fk`, `purpose text check in ('verify','reset','login')`, `code_hash text`, `expires_at`, `attempts int default 0`, `used_at null`. Codes are 6 digits, valid 10 minutes, at most 5 attempts (PRD ACC-1, ACC-5).

**consent** (append-only): `id`, `user_id fk`, `kind text check in ('processing','quality_improvement','marketing')`, `granted boolean`, `policy_version text`, `source text` (`signup`, `settings`). The current consent is the latest row per kind (PRD ACC-7).

**auth_session**: Django's session table in this schema; plus `session_meta` with `session_key`, `user_id`, `user_agent`, `ip_prefix` (IPv4 /24 or IPv6 /48 only), `last_seen_at`, used for "sign out of all devices".

## 3. exammodels

**exam**: `id`, `code text unique` (`TCF_CA`), `name text`, `language text` (`fr`), `active boolean`

**exam_rules_version** (append-only): `id`, `exam_id fk`, `code text unique` (`TCF-CA-rules-v1`), `document jsonb not null` (papers, timings, item counts, word ranges, score bands, NCLC tables, delivery rules; validated by `examcore.rules.ExamRules`), `effective_from date`, `active boolean`. One active row per exam (partial unique index).

**cut_point_set** (append-only): `id`, `exam_id`, `paper text check in ('CO','CE')`, `version int`, `cuts jsonb` (ability per CEFR boundary), `method text` (`initial_67pct`, `refit_real_results`), `fitted_on jsonb` (evidence summary), `active boolean`. Unique (`exam_id`, `paper`, `version`).

**combination_model** (append-only): `id`, `exam_id`, `paper text check in ('EE','EO')`, `version int`, `weights jsonb` (`[0.20,0.35,0.45]` at v1), `placement jsonb`, `method text`, `active boolean`.

**grader_version** (append-only): `id`, `code text unique` (for example `TCF-CA-EE-grader-v3`), `paper text check in ('EE','EO')`, `model_id text`, `prompt_fingerprint char(64)` (SHA-256 of the assembled system prompt template), `rubric_version text`, `exemplar_set_version text`, `settings jsonb` (temperature, max tokens, passes), `release_check_report_uri text`, `release_check_passed boolean`, `active boolean`. Only a version with `release_check_passed = true` can be active (check constraint).

## 4. content

Content identity plus immutable versions ([ADR-011](../adr/ADR-011-versioned-content-append-only-results.md), [ADR-025](../adr/ADR-025-content-as-validated-files.md)).

**item**: `id`, `code text unique` (`TCF-CA-CO-L4-0001`), `exam_id`, `paper text check in ('CO','CE')`, `type text`, `current_published_version_id uuid null`

**item_version** (append-only): `id`, `item_id fk`, `version int`, `status text check in ('approved','published','retired')`, `target_level level`, `theme text`, `focus text`, `payload jsonb not null` (the authoring file, schema `listening-item/1` or `reading-item/1`), `initial_difficulty numeric(7,4)`, `audio_asset_ids uuid[]`, `word_count int null`, `audio_seconds int null`, `approved_by uuid`, `approved_at`, `published_at null`, `retired_at null`. Unique (`item_id`, `version`). Status changes are recorded as `review_event` rows; the status column is the only column the application may update, through a database function that also writes the event.

**prompt** and **prompt_version**: same shape as item and item_version, for writing prompts and speaking tasks (`paper` in `EE`, `EO`; `type` in `EE1..EE3`, `EO1..EO3`).

**lesson** and **lesson_version**: in `curriculum` (Section 5).

**media_asset**: `id`, `kind text check in ('audio','image')`, `format text` (`opus`, `aac`, `webp`), `r2_key text unique` (content hash), `bytes int`, `duration_ms int null`, `voice_ids text[]`, `checks jsonb` (automatic check results), `listened_by uuid null`, `listened_at null`

**simulation_form**: `id`, `code text unique` (`TCF-CA-FORM-0001`), `exam_id`

**form_version** (append-only): `id`, `form_id fk`, `version int`, `rules_version_id fk exammodels.exam_rules_version`, `payload jsonb` (schema `simulation-form/1`), `status`, `published_at`

**form_item** (append-only): `form_version_id fk`, `paper text`, `position smallint`, `item_version_id fk`, primary key (`form_version_id`, `paper`, `position`). Lets the scoring engine read a form without parsing JSON.

**review_event** (append-only): `id`, `object_type text`, `object_version_id uuid`, `from_status`, `to_status`, `actor_id uuid`, `batch_code text null`, `defects text[]`, `comment text`

**flag**: `id`, `learner_id`, `object_type` (`item_version`, `prompt_version`, `task_grade`, `transcript`), `object_id`, `reason text check in ('wrong_answer','unclear','audio_problem','feedback_wrong','transcript_wrong','offensive','other')`, `comment text`, `status text check in ('open','accepted','rejected')`, `handled_by null`, `handled_at null` (PRD CMS-7)

## 5. curriculum

**level**: `code text pk` (`A1`..`C1`), `position smallint`

**unit**: `id`, `level_code fk`, `number smallint`, `goal_fr text`, `goal_en text`, unique (`level_code`, `number`)

**lesson**: `id`, `code text unique` (`FR-CUR-B1-U04-L2`), `unit_id fk`, `number smallint`

**lesson_version** (append-only): `id`, `lesson_id fk`, `version int`, `status`, `payload jsonb` (schema `lesson/1`), `audio_asset_ids uuid[]`, `published_at`

**lesson_progress**: `id`, `learner_id`, `lesson_version_id fk`, `started_at`, `completed_at null`, `exercise_results jsonb`, `production_id uuid null` (practice.production for the production task)

**review_queue**: `id`, `learner_id`, `kind text check in ('vocabulary','error_pattern','exercise_item')`, `ref text` (vocabulary code or exercise reference), `ease numeric(4,2)`, `interval_days int`, `due_on date`, `last_result text null`, unique (`learner_id`, `kind`, `ref`). Spaced repetition by SM-2 style scheduling (PRD CUR-3, FRE-1).

**level_test_result** (append-only): `id`, `learner_id`, `kind text check in ('unit','level')`, `ref text`, `score numeric(5,2)`, `passed boolean`

## 6. learner

**goal**: `id`, `learner_id unique`, `track text check in ('exam','free')`, `exam_code text null` (`TCF_CA`), `target_nclc jsonb` (`{"CO":7,"CE":7,"EE":7,"EO":7}`), `exam_date date null`, `daily_minutes smallint check in (15,30,60,90)` (PRD ACC-4, PLN-2)

**study_plan** (append-only): `id`, `learner_id`, `version int`, `reason text check in ('diagnostic','simulation','date_change','time_change','weekly')`, `weeks jsonb` (per week: lessons, practice sets, simulations), `late_start_warning boolean` (PLN-5), `based_on_prediction_ids uuid[]`

**plan_item**: `id`, `plan_id fk`, `week smallint`, `kind text check in ('lesson','practice','simulation','review')`, `ref text`, `skill text null`, `done_at null`. The only mutable column is `done_at`.

## 7. practice

**practice_session**: `id`, `learner_id`, `kind text check in ('items','writing','speaking','diagnostic','free_daily')`, `paper text null`, `mode text check in ('exam','learning')`, `filters jsonb`, `started_at`, `ended_at null`

**response** (append-only, partitioned by month): `id`, `client_id uuid not null` (idempotency), `learner_id`, `session_id`, `item_version_id`, `chosen text check in ('A','B','C','D') null` (null = no answer), `correct boolean`, `mode text`, `replays smallint default 0`, `answered_at timestamptz` (client time, bounded by server checks), `received_at`. Unique (`learner_id`, `client_id`, `created_at`) per partition; the API checks idempotency before insert.

**production** (append-only): `id`, `client_id uuid`, `learner_id`, `session_id`, `prompt_version_id`, `modality text check in ('writing','speaking')`, `text text null`, `word_count int null`, `recording_r2_key text null`, `duration_seconds numeric(6,1) null`, `live_transcript jsonb null`, `batch_transcript jsonb null` (words with timing and confidence), `audio_measures jsonb null`, `previous_production_id uuid null` (rewrite and retry, PRD PRA-5), `submitted_at`

**speaking_session**: `id`, `learner_id`, `context text check in ('practice','simulation','diagnostic')`, `context_ref uuid`, `livekit_room text unique`, `task_types text[]`, `status text check in ('created','active','ended','failed')`, `started_at`, `ended_at`, `seconds_used int`, `events jsonb` (examiner turns, interruptions, preparation start and end). Owned by `practice`; `simulation` refers to it by ID through the public interface.

## 8. simulation

**simulation_sitting**: `id`, `learner_id`, `form_version_id`, `mode text check in ('full','by_paper')`, `opened_at`, `expires_at` (opened_at + 7 days, PRD SIM-2), `completed_at null`, `is_repeat boolean` (spec 7.4)

**paper_sitting**: `id`, `sitting_id fk`, `paper text check in ('CO','CE','EE','EO')`, `started_at`, `deadline_at` (started_at + duration from rules), `closed_at null`, `closed_reason text check in ('submitted','deadline','abandoned') null`, `eo2_choice uuid null` (the card drawn), unique (`sitting_id`, `paper`)

**response** (append-only, partitioned by month): as in practice, with `paper_sitting_id`, `position smallint`, `played_at timestamptz null` (listening: when the recording started; it cannot start again), and a check in the API that `answered_at <= deadline_at`

**production** (append-only): as in practice, with `paper_sitting_id` and `task text check in ('EE1','EE2','EE3','EO1','EO2','EO3')`, and `draft_saved_at` history kept in `journal_event`

**journal_event** (append-only): `id`, `paper_sitting_id`, `client_id`, `kind text` (`answer`, `draft`, `flag`, `navigate`, `play`), `payload jsonb`, `client_time`, `received_at`. The raw sync stream from the PWA journal; responses and productions are derived from it idempotently (architecture 6.5).

## 9. assessment

**grading_job**: `id`, `production_id uuid`, `production_source text check in ('practice','simulation')`, `status text check in ('queued','rule_checked','grading','graded','failed')`, `attempts smallint`, `error text null`, `requested_at`, `finished_at`

**rule_check_result** (append-only): `id`, `production_id`, `rules_version_id`, `results jsonb` (list of `{check, passed, detail}` per spec 5.3), `blocking boolean`

**grading_pass** (append-only): `id`, `job_id`, `pass_number smallint check (pass_number between 1 and 3)`, `grader_version_id`, `request_fingerprint char(64)`, `output jsonb` (validated grade output; its schema comes with the grader prompts in the grader milestone), `input_tokens int`, `output_tokens int`, `cache_read_tokens int`, `latency_ms int`, `cost_usd numeric(10,6)`

**task_grade** (append-only): `id`, `production_id`, `task text`, `level level`, `criteria jsonb` (level per criterion), `decision text check in ('rule_check','two_passes_agree','adjacent_rule','third_pass')`, `pass_ids uuid[]`, `feedback jsonb` (validated feedback output), `grader_version_id`, `rules_version_id`, `supersedes_id uuid null`

**paper_score** (append-only): `id`, `learner_id`, `paper text`, `source text check in ('simulation','practice_evidence','diagnostic')`, `paper_sitting_id null`, `ability numeric(7,4) null`, `ability_se numeric(7,4) null`, `scale_score numeric(6,2) null` (699 scale), `mark numeric(6,2) null` (out of 20), `level level`, `nclc smallint null`, `range_low numeric(6,2)`, `range_high numeric(6,2)`, `confidence text check in ('low','medium','high')`, `trace jsonb not null` (architecture 7.3: every version and evidence ID), `supersedes_id null`

## 10. prediction

**prediction** (append-only): `id`, `learner_id`, `exam_code`, `skill text check in ('CO','CE','EE','EO')`, `point numeric(6,2)`, `range_low`, `range_high`, `level_low level`, `level_high level`, `nclc_low smallint null`, `nclc_high smallint null`, `nclc_shown smallint[]`, `confidence text`, `minimum_evidence_met boolean`, `missing_evidence jsonb null` (PRE-2), `trace jsonb not null`. Index (`learner_id`, `skill`, `created_at desc`).

**readiness_event** (append-only): `id`, `learner_id`, `ready boolean`, `basis_prediction_ids uuid[]` (PLN-4, spec 8.6)

## 11. calibration

**bank_calibration** (append-only): `id`, `paper text`, `version int`, `method text check in ('initial','mml_monthly')`, `responses_used bigint`, `anchored_item_ids uuid[]`, `accuracy_before jsonb`, `accuracy_after jsonb`, `active boolean`, `report_uri text`

**item_parameter** (append-only): `id`, `calibration_id fk`, `item_version_id`, `difficulty numeric(7,4)`, `se numeric(7,4) null`, `n_responses int`, `infit numeric(5,3) null`, `outfit numeric(5,3) null`, `point_biserial numeric(5,3) null`, `option_shares jsonb null`, `flags text[]`. The current difficulty is the row in the active calibration.

## 12. billing

**plan**: `id`, `code text unique` (`free`, `premium_monthly`, `premium_3m`), `prices jsonb` (`{"XAF":7900,"USD":1299}` in minor units for USD), `duration_days smallint null`, `limits jsonb` (daily and monthly limits, PRD Section 12), `active boolean`

**entitlement**: `id`, `learner_id`, `plan_id`, `starts_at`, `ends_at`, `grace_ends_at` (ends_at + 3 days, PAY-4), `source text check in ('payment','reward','manual','refund_reversal')`, `source_ref uuid`. Active entitlement = the row covering now, latest `ends_at` wins.

**payment**: `id`, `learner_id`, `plan_id`, `reference text unique` (ours, sent to Notch Pay), `provider text default 'notchpay'`, `provider_reference text null unique`, `channel text check in ('mtn_momo','orange_money','card')`, `amount_minor bigint`, `currency char(3)`, `status text check in ('initiated','pending','complete','failed','canceled','refunded')`, `status_checked_at`, `completed_at null`

**webhook_event** (append-only): `id`, `provider`, `event_id text unique`, `signature_valid boolean`, `raw_body bytea`, `headers jsonb`, `processed_at null`, `result text null`. Kept 24 months (architecture 7.4).

**usage_counter**: `learner_id`, `metric text check in ('writing_evaluations','speaking_seconds','simulations','free_writing','free_speaking','free_items')`, `period text check in ('day','month')`, `period_start date`, `value int`, primary key (`learner_id`, `metric`, `period`, `period_start`). Incremented with `INSERT ... ON CONFLICT DO UPDATE ... WHERE value + delta <= limit RETURNING value`, so a limit can never be exceeded under concurrency (PAY-7). Day boundaries use Africa/Douala time for CEMAC learners and the learner's time zone otherwise.

**refund**: `id`, `payment_id`, `reason text`, `requested_at`, `decided_by uuid null`, `status text check in ('requested','approved','rejected','paid')`, `provider_reference null` (PAY-6)

**receipt**: `id`, `payment_id unique`, `number text unique`, `pdf_r2_key text`, `sent_at` (PAY-5)

## 13. engagement

**notification**: `id`, `learner_id`, `kind text` (`result_ready`, `plan_updated`, `subscription_ending`, `report_request`, `readiness`), `payload jsonb`, `channel text check in ('in_app','email','push')`, `scheduled_for`, `sent_at null`, `read_at null`

**push_subscription**: `id`, `learner_id`, `endpoint text unique`, `keys jsonb`, `reminder_time time null`, `time_zone text`, `active boolean` (NOT-3)

**notification_preference**: `learner_id pk`, `daily_reminder boolean`, `marketing boolean`, `last_marketing_at null` (NOT-4: at most one marketing message a week)

**free_track_progress**: `learner_id pk`, `streak_days int`, `last_session_on date`, `words_learned int`, `theme_levels jsonb` (FRE-3)

## 14. reporting

**real_result_report** (append-only): `id`, `learner_id`, `exam_code`, `test_date date`, `scores jsonb` (per skill as on the attestation), `attestation_r2_key text null`, `consent_calibration boolean`, `linked_simulation_ids uuid[]` (full simulations within 30 days before the test, spec 9.3)

**report_verification** (append-only): `id`, `report_id`, `verifier_id`, `outcome text check in ('verified','rejected','unreadable')`, `notes text`, `attestation_deleted_at timestamptz` (REP-4)

**accuracy_snapshot** (append-only): `id`, `month date`, `skill`, `n_results int`, `share_exact_nclc numeric(5,4)`, `share_within_one numeric(5,4)`, `mae numeric(7,3)`, `bias numeric(7,3)`, `by_level jsonb`, `published boolean` (REP-5, spec 9.4)

**product_event** (append-only, partitioned by month): `id`, `learner_id null`, `anonymous_id uuid null`, `name text` (PRD 8.14 list), `properties jsonb` (never essays, recordings or transcripts), `occurred_at`

## 15. admin

**audit_log** (append-only): `id`, `actor_id`, `actor_role`, `action text`, `object_type`, `object_id`, `before jsonb null`, `after jsonb null`, `ip_prefix text` (PRD CMS-8)

## 16. Deletion and retention jobs

| Job | Schedule | Effect |
|---|---|---|
| Account deletion | Daily | For users in `deletion_requested` for at least the cooling period (7 days, then cancel is no longer possible): delete identity rows, consents, sessions; null `text`, transcripts and recording keys in productions; delete R2 objects; the learner ID stays only in anonymous results (PRD ACC-6, within 30 days) |
| Production retention | Daily | Productions whose learner has had no activity for 12 months: text, transcripts and recordings removed (PRD 15.1) |
| Attestations | On verification | R2 object deleted and `attestation_deleted_at` set |
| Webhooks | Monthly | Delete raw webhooks older than 24 months |

Removing text from an append-only production is the one permitted update on those tables, done by a dedicated database function owned by a separate role and logged in `admin.audit_log`.
