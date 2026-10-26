# Claims register

Every statement that tells a learner or the public what LinguaMentor does is listed here with its evidence. This covers the landing, pricing, accuracy and help pages, onboarding, release notes, the README and app-store text. Only `product-verifier` sets a claim to `VERIFIED`. `/lm-verify-claims` refreshes the register before every release.

| Status | Meaning | May appear publicly |
|---|---|---|
| `VERIFIED` | Built, reachable by a learner, covered by a passing test | Yes |
| `PARTIAL` | Built but gated, incomplete or unreachable for some learners | Only with the limit stated |
| `MOCKED` | The screen exists but returns fixtures, or the backend is missing | No: release blocker |
| `ABSENT` | Not built | No: release blocker |
| `PLANNED` | On the roadmap | Only in the future tense, marked as coming |

Accuracy figures (for example "70% within one NCLC level") are `VERIFIED` only when they come from the published accuracy figures computed on verified real results. A target from the PRD is not evidence.

| ID | Claim (FR) | Claim (EN) | Status | Evidence (file:line + test) | Surface | Checked |
|---|---|---|---|---|---|---|
| | | | | | | |
