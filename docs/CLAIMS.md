# Claims register

Every statement that tells a learner or the public what GaugePrep does is listed here with its evidence. This covers the landing, pricing, accuracy and help pages, onboarding, release notes, the README and app-store text. Only QA sets a claim to `VERIFIED`. The release gate refreshes the register before every release.

| Status     | Meaning                                                           | May appear publicly                        |
| ---------- | ----------------------------------------------------------------- | ------------------------------------------ |
| `VERIFIED` | Built, reachable by a learner, covered by a passing test          | Yes                                        |
| `PARTIAL`  | Built but gated, incomplete or unreachable for some learners      | Only with the limit stated                 |
| `MOCKED`   | The screen exists but returns fixtures, or the backend is missing | No: release blocker                        |
| `ABSENT`   | Not built                                                         | No: release blocker                        |
| `PLANNED`  | On the roadmap                                                    | Only in the future tense, marked as coming |

Accuracy figures (for example "70% within one NCLC level") are `VERIFIED` only when they come from the published accuracy figures computed on verified real results. A target from the PRD is not evidence.

| ID    | Claim (FR)                                                                   | Claim (EN)                                                           | Status   | Evidence (file:line + test)                                                                             | Surface | Checked    |
| ----- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------- | ------- | ---------- |
| C-001 | Le backend expose un point de santé qui indique l'état de la base de données | The backend serves a health endpoint that reports the database state | VERIFIED | apps/backend/config/health.py:32, apps/backend/tests/test_health.py; staging returned 200 on 2026-11-16 | README  | 2026-11-16 |
| C-002 | L'application web reste à construire; seules des pages provisoires existent  | The web app is still to build; only placeholder pages exist          | PLANNED  | apps/web holds placeholder pages only                                                                   | README  | 2026-11-16 |
| C-003 | L'examinateur vocal reste à construire                                       | The voice examiner is still to build                                 | PLANNED  | apps/voice/pyproject.toml, no code beyond the package stub                                              | README  | 2026-11-16 |
