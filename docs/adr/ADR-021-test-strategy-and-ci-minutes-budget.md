# ADR-021: Test strategy and CI minutes budget

- Status: Accepted
- Date: 2026-11-02

## Context

Tests exist piecemeal and nothing says which kinds are required, how much coverage is enough, or what runs where. The repository is private on GitHub's free plan: 2,000 Actions minutes a month for the organisation, each job billed rounded up to the whole minute, and no branch protection or required checks. The full suite cannot run on every pull request, and `.claude/scripts/merge.sh`, which refuses a PR unless every workflow run on its head commit passed, is the only enforcement.

Measured on 30 October to 2 November 2026: 42 `ci.yml` runs for 21 PRs, about 2 runs per PR; the four jobs each finish in under a minute, so a run bills 4 minutes.

## Decision

### Layers

| Layer | Tool | Covers | Runs on |
|---|---|---|---|
| `examcore` | pytest and Hypothesis property tests | Every exam rule: fixed answers from each table of the exam specification, plus properties (bounds, monotonicity, round trips) | Every PR with code |
| Backend | pytest-django against PostgreSQL 18, never SQLite | Module services and views, idempotency, append-only enforcement, authorisation; every endpoint has success, not-found and other-learner-refused tests | Every PR with code |
| API contract | Schemathesis, in-process, against `backend/openapi.json` | Documented statuses only, no 5xx on bad input, responses match their schemas | Every PR with code |
| Web | Vitest and React Testing Library | Components and hooks, as the learner uses them | Every PR with code |
| End to end, smoke | Playwright at 375 px with slow-3G throttling, axe-core | About 5 happy-path flows; zero serious or critical axe-core violations | Every PR touching `apps/` or `backend/` |
| End to end, full | Playwright at 375 px and 1440 px with slow-3G throttling, axe-core | All flows, plus a server error, offline, session expiry, another learner's URL refused | The `develop` to `stage` promotion PR |
| Mutation | mutmut on `examcore` and scoring code | Mutation score at least 80% | The `develop` to `stage` promotion PR |
| Scoring recovery | pytest on simulated data | Full recovery and reference comparison (a small set runs with the backend tests) | The `develop` to `stage` promotion PR |

"Every PR with code" means every PR not limited to docs and agent prompts, as `ci.yml` already filters.

Smoke runs at 375 px only, for minutes: a second width would double the smoke line below (360 to 720 minutes) and break the budget. The phone width is the one learners use most; 1440 px is checked by the full suite at every promotion.

### Coverage

- Branch coverage floors: `examcore` 95%, backend 85%, web 80%, set in config.
- 90% branch coverage on the lines a PR changes, measured with diff-cover against the base branch.
- Floors only go up. A PR that lowers one is refused in review.

### Run rules

- Under CI (`CI=true`) no test may be skipped or marked xfail; the run fails and names the test. Locally a skip only warns.
- Tests run in random order: pytest-randomly for Python, `sequence.shuffle` for Vitest. The seed is printed so a failure can be replayed. Playwright tests are independent, each with its own learner, and run fully parallel.
- Every test has a timeout: 30 s for pytest, 10 s for Vitest, 60 s for Playwright. A test that needs longer sets its own, with a one-line reason.
- No retries for unit or integration tests.
- Playwright retries 0 on PRs. On the promotion PR it retries once, only to tell a flaky test from a broken one: a pass on retry still fails the run (`failOnFlakyTests`).

### Where the minutes go

Two changes to `ci.yml` keep the budget: the `changes`, `pr-title` and `gitleaks` jobs merge into one `gate` job (each bills a full minute today), and the smoke end-to-end set runs as a step of the `check` job, reusing its PostgreSQL service and installs. No scheduled nightly runs; the full suites run on the promotion PR, the last point before staging.

Assumptions:

- 100 PRs a month at 2 runs each; 85% of runs touch code; 60% touch `apps/` or `backend/`.
- 3 promotions a month (sprint end plus feature releases), each run twice.
- 70 deploy pushes a month: about 65 merges into `develop` and 5 into `stage`, 4 minutes each, 280 minutes.
- Measured: `gate` and `check` per-run minutes (the current jobs). Estimated, since no Playwright, mutmut or deploy workflow exists yet: smoke 3 minutes (about 5 flows on 2 workers, with the browser install cached); full end to end 25 (about 60 tests, all flows at two widths, at about 40 s each on 2 workers, plus build and install); mutmut with scoring recovery 25; deploy 4 (ARM image build on a cached layer, Kamal switch). Each estimate becomes the job or step `timeout-minutes`, so a run never bills more than its line.
- Sensitivity: at the measured pace of about 150 PRs a month (21 PRs in 4 days) the same arithmetic gives 2,570 (gate 300, check 1,020, smoke 540, promotion 300, about 100 deploys 400, alarm 10). Past 1,600 used in a month, cut in this order: smoke runs only on the head that passed review (−270 at 150 PRs); deploy to dev skips docs-only merges (−60); then the full end to end drops 1440 px on promotions. If that still exceeds 2,000, paid minutes or a public repository go to the owner as a decision.

| Workflow and job | Runs a month | Billed minutes per run | Minutes |
|---|---|---|---|
| `ci.yml` `gate` (changed paths, PR title, gitleaks) | 200 | 1 | 200 |
| `ci.yml` `check` (`pnpm check`: lint, types, unit, integration, contract, coverage) | 170 | 4 | 680 |
| `ci.yml` smoke end-to-end step in `check` | 120 | 3 | 360 |
| `ci.yml` promotion jobs in parallel: full end-to-end (25) and mutmut with scoring recovery (25) | 3 × 2 = 6 | 50 | 300 |
| Deploy to dev and staging (pushes to `develop` and `stage`) | 70 | 4 | 280 |
| `main-alarm.yml` | 10 | 1 | 10 |
| Total | | | 1,830 of 2,000 |

### Enforcement

Branch protection and required checks are unavailable on the free private plan. `merge.sh` refusing a PR whose head commit lacks a green run is the gate for `develop`; the owner applies the same rule when merging into `stage` and `main`, where the promotion jobs run.

### Dependencies accepted

| Package | Licence | Latest release | Known vulnerabilities (OSV, 2026-11-02) | Runtime dependencies | Use |
|---|---|---|---|---|---|
| Hypothesis | MPL-2.0 | 6.170.14, 2026-10-30 | None | 1 (sortedcontainers) | Dev only, Python tests |
| axe-core | MPL-2.0 | 4.14.0, 2026-10-05 | None | 0 | Dev only, Playwright tests |
| @axe-core/playwright | MPL-2.0 | 4.14.0, 2026-10-15 | None | 1 (axe-core) | Dev only, Playwright tests |

MPL-2.0 is file-level copyleft: obligations apply only when modified files are distributed. Both run in tests, unmodified, and never ship to learners. Neither could be written in 200 lines (a shrinking property engine; a WCAG rule engine). The other tools are MIT, BSD-3-Clause or Apache-2.0 (pytest-randomly, pytest-timeout, pytest-cov, Schemathesis, mutmut, diff-cover, Playwright, React Testing Library) and are checked by the ticket that adds them.

- `@vitest/coverage-v8` (MIT, dev-only), pinned to the exact Vitest version (peer dependency); measures the web branch-coverage floor; `vitest` and it are bumped together. Accepted in #84 (checks in the PR).

### When each layer starts

| Layer or rule | Starts |
|---|---|
| Backend pytest on PostgreSQL 18 | Now (M0) |
| Coverage floors, no skips, random order, timeouts | M0, with the coverage gate ticket |
| Schemathesis contract tests | M0 |
| 90% on changed lines; `gate` job merge | M0, one ticket staging the `ci.yml` change for the owner |
| Hypothesis | The first exam rule in `examcore` |
| Vitest with React Testing Library | The first React component (M1) |
| Playwright smoke with axe-core | The first learner flow on dev, sign-up (M1) |
| Full end-to-end on the promotion PR | The first promotion with a learner screen (M1) |
| mutmut and full scoring recovery | The first scoring code, scoring engine v0 (M2) |

## Alternatives considered

- **Full suite on every PR:** about 120 runs × 25 extra minutes = 3,000 minutes a month for end to end alone. Over the free plan; needs paid minutes, an owner decision.
- **Nightly full suite (the earlier plan):** 30 runs × 50 minutes = 1,500 minutes, mostly on unchanged code, and a failure lands a day after the PR that caused it. The promotion PR runs the same suites only when something ships.
- **No end-to-end on PRs:** cheapest, but a broken sign-up or route reaches `develop` and dev before anyone sees it.
- **Self-hosted runner on the dev server:** unlimited minutes, but PR code from the agents' account runs on a machine holding deploy access, and the free ARM server is already shared by dev and staging.
- **Retries on every layer:** hides flaky tests, which then fail at random on later PRs.

## Consequences

- The budget leaves 170 minutes of headroom. A busy month can exceed it; the agent's token cannot read billing, so the owner checks usage on the 20th.
- A regression caught only by the full suite is found at promotion, not on its PR. The fix is a ticket on `develop` and a new promotion.
- Merging the three small jobs means a title or gitleaks failure shows as one red `gate` check; the log names which step failed.
- The architecture document's §13.2 and §15 are updated to match. The coverage gate, endpoint-test, contract, migration-check and breaking-change tickets need no change.
- Confirmation: `ci.yml` has a single `gate` job and no `schedule` trigger; `pnpm check` fails below a floor, on a skipped test and on a timeout; the promotion PR shows the full end-to-end and mutmut jobs.
- Reconsider when monthly usage passes 1,600 minutes, the `check` job median passes 5 minutes, the repository becomes public (unlimited free minutes), or the plan changes to one with required checks. The cuts, in order, are in the sensitivity line above.

## Sources

- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://playwright.dev/docs/api/class-testconfig#test-config-fail-on-flaky-tests
- https://www.mozilla.org/en-US/MPL/2.0/FAQ/
