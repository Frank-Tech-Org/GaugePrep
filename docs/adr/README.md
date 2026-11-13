# Architecture decision records

| ID | Decision | Status |
|---|---|---|
| [ADR-001](ADR-001-modular-monolith-four-process-types.md) | Modular monolith with four process types | Accepted |
| [ADR-002](ADR-002-python-django-shared-examcore.md) | Python and Django for all backend processes, with a shared examcore package | Accepted |
| [ADR-003](ADR-003-postgresql-procrastinate-no-redis.md) | PostgreSQL 18 as database and job queue (Procrastinate), no Redis at launch | Accepted |
| [ADR-004](ADR-004-nextjs-static-export-pwa.md) | Next.js static export as the PWA, served from Cloudflare | Accepted |
| [ADR-005](ADR-005-session-cookie-authentication.md) | Session cookie authentication | Accepted |
| [ADR-006](ADR-006-chained-voice-pipeline-livekit-agents.md) | Chained voice pipeline on LiveKit Agents instead of a speech-to-speech model | Accepted |
| [ADR-007](ADR-007-claude-grader-gpt-backup.md) | Claude Sonnet 5.5 as the grader, Haiku 5.5 for light tasks, GPT-6.1 Sol as backup | Accepted |
| [ADR-008](ADR-008-speech-recognition-accent-test.md) | Speech recognition chosen by a measured accent test | Superseded by ADR-026 |
| [ADR-009](ADR-009-elevenlabs-examiner-content-voices.md) | ElevenLabs for examiner and content voices | Accepted |
| [ADR-010](ADR-010-in-house-rasch-scoring-engine.md) | In-house Rasch scoring engine verified against a reference | Accepted |
| [ADR-011](ADR-011-versioned-content-append-only-results.md) | Versioned content and append-only results | Accepted |
| [ADR-012](ADR-012-hosting-hetzner-neon-cloudflare.md) | Hosting: Hetzner Germany, Neon Frankfurt, Cloudflare edge | Accepted |
| [ADR-013](ADR-013-livekit-self-hosted-cloud-staging.md) | Self-hosted LiveKit in production, LiveKit Cloud free in staging | Accepted |
| [ADR-014](ADR-014-notch-pay-payments.md) | Notch Pay for payments; automatic card renewal after release 1 | Accepted |
| [ADR-015](ADR-015-github-actions-kamal-delivery.md) | GitHub Actions and Kamal for delivery | Accepted |
| [ADR-016](ADR-016-sentry-grafana-observability.md) | Sentry and Grafana Cloud for observability | Accepted |
| [ADR-017](ADR-017-opus-with-aac-fallback.md) | Opus with AAC fallback for audio | Accepted |
| [ADR-018](ADR-018-twilio-sms-verification.md) | Twilio for SMS verification codes behind an SMS provider interface | Superseded by ADR-023 |
| [ADR-019](ADR-019-dev-staging-production-branches.md) | Dev, staging and production from develop, stage and main | Accepted |
| [ADR-020](ADR-020-production-deploys-on-owner-tag.md) | Production deploys on the owner's tag, without an approval gate | Accepted |
| [ADR-021](ADR-021-test-strategy-ci-minutes-budget.md) | Test strategy and CI minutes budget | Accepted |
| [ADR-022](ADR-022-pr-security-scanners-scope.md) | PR security scanners catch accidents, not a deliberate bypass | Accepted |
| [ADR-023](ADR-023-email-verification-only.md) | Email verification only, no SMS sign-up | Accepted |
| [ADR-024](ADR-024-resend-transactional-email-mailpit.md) | Resend for transactional email, Mailpit locally and in dev | Accepted |
| [ADR-025](ADR-025-content-as-validated-files.md) | Content authored as validated files, imported into the content module | Proposed |
| [ADR-026](ADR-026-speech-recognition-corpus-benchmark.md) | Speech recognition chosen by a public-corpus benchmark | Accepted |

## Template

File name `ADR-NNN-<short-slug>.md`, five words at most in the slug.

```markdown
# ADR-NNN: <decision in a few words>

- Status: Proposed | Accepted | Superseded by ADR-NNN
- Date: YYYY-MM-DD

## Context
What the system design doc and earlier ADRs say, and why that is not enough here.

## Options considered
At least three, including doing nothing: what each costs, what breaks, how we would undo it.

## Evidence
Docs, source lines or measurements behind each claim above.

## Decision

## Consequences
Good, bad, and what changes in the design doc (changed in the same PR).

## Revisit when
The condition that would reopen this.
```
