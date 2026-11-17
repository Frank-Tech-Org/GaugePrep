# ADR-021: Test strategy and CI minutes budget

- Status: Accepted
- Date: 2026-11-02

## Context

Tests existed piecemeal and nothing said which kinds are required, how much coverage is enough, or what runs where. The repository is on GitHub's free plan: 2,000 Actions minutes a month for the organisation while it is private, each job billed rounded up to the whole minute, and no branch protection or required checks. The full suite cannot run on every pull request, and the merge script, which refuses a PR unless every workflow run on its head commit passed, is the only enforcement.

## Decision

### Layers

| Layer | Tool | Covers | Runs on |
|---|---|---|---|
| `examcore` | pytest and Hypothesis property tests | Every exam rule: fixed answers from each table of the exam specification, plus properties (bounds, monotonicity, round trips) | Every PR with code |
| Backend | pytest-django against PostgreSQL 18, never SQLite | Module services and views, idempotency, append-only enforcement, authorisation; every endpoint has success, not-found and other-learner-refused tests | Every PR with code |
| API contract | Schemathesis, in-process, against `apps/backend/openapi.json` | Documented statuses only, no 5xx on bad input, responses match their schemas | Every PR with code |
| Web | Vitest and React Testing Library | Components and hooks, as the learner uses them | Every PR with code |
| End to end, smoke | Playwright at 375 px with slow-3G throttling, axe-core | About 5 happy-path flows; zero serious or critical axe-core violations | Every PR touching `apps/` |
| End to end, full | Playwright at 375 px and 1440 px with slow-3G throttling, axe-core | All flows, plus a server error, offline, session expiry, another learner's URL refused, interrupted and resumed simulations | The `develop` to `stage` promotion PR |
| Mutation | mutmut on `examcore` and scoring code | Mutation score at least 80% | The `develop` to `stage` promotion PR |
| Scoring recovery | pytest on simulated data | Full recovery and reference comparison (a small set runs with the backend tests) | The `develop` to `stage` promotion PR |

"Every PR with code" means every PR not limited to docs, as the CI path filter decides. Smoke runs at 375 px only, to save minutes; 1440 px is checked by the full suite at every promotion. A layer starts with the first code it covers.

### Coverage

- Branch coverage floors: `examcore` 95%, backend 85%, web 80%, set in config.
- 90% coverage on the backend lines a PR changes, measured against the base branch.
- Floors only go up. A PR that lowers one is refused in review.

### Run rules

- Under CI (`CI=true`) no test may be skipped or marked xfail; the run fails and names the test. Locally a skip only warns.
- Tests run in random order: pytest-randomly for Python, `sequence.shuffle` for Vitest. The seed is printed so a failure can be replayed. Playwright tests are independent, each with its own learner, and run fully parallel.
- Every test has a timeout: 30 s for pytest, 10 s for Vitest, 60 s for Playwright. A test that needs longer sets its own, with a one-line reason.
- No retries for unit or integration tests.
- Playwright retries 0 on PRs. On the promotion PR it retries once, only to tell a flaky test from a broken one: a pass on retry still fails the run (`failOnFlakyTests`).
- No scheduled nightly runs; the full suites run on the promotion PR, the last point before staging.

### Dependencies accepted

| Package | Licence | Latest release | Known vulnerabilities (OSV, 2026-11-02) | Runtime dependencies | Use |
|---|---|---|---|---|---|
| Hypothesis | MPL-2.0 | 6.170.14, 2026-10-30 | None | 1 (sortedcontainers) | Dev only, Python tests |
| axe-core | MPL-2.0 | 4.14.0, 2026-10-05 | None | 0 | Dev only, Playwright tests |
| @axe-core/playwright | MPL-2.0 | 4.14.0, 2026-10-15 | None | 1 (axe-core) | Dev only, Playwright tests |

MPL-2.0 is file-level copyleft: obligations apply only when modified files are distributed. These run in tests, unmodified, and never ship to learners. Neither could be written in 200 lines (a shrinking property engine; a WCAG rule engine). `@vitest/coverage-v8` (MIT, dev-only) is pinned to the exact Vitest version and bumped with it (#84).

## Alternatives considered

- **Full suite on every PR:** about 3,000 minutes a month for end to end alone, over the free plan.
- **Nightly full suite:** about 1,500 minutes, mostly on unchanged code, and a failure lands a day after the PR that caused it.
- **No end to end on PRs:** cheapest, but a broken sign-up or route reaches dev before anyone sees it.
- **Self-hosted runner on the dev server:** unlimited minutes, but PR code would run on a machine holding deploy access.
- **Retries on every layer:** hides flaky tests, which then fail at random on later PRs.

## Consequences

- A regression caught only by the full suite is found at promotion, not on its PR. The fix is a ticket on `develop` and a new promotion.
- Confirmation: `pnpm check` fails below a floor, on a skipped test and on a timeout; the promotion PR shows the full end-to-end and mutmut jobs; `ci.yml` has no `schedule` trigger.
- Reconsider when monthly usage nears 2,000 minutes, the `check` job median passes 5 minutes, the repository becomes public (unlimited free minutes), or the plan changes to one with required checks. Cut first: smoke only on the reviewed head, then 1440 px on promotions.

## Sources

- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://playwright.dev/docs/api/class-testconfig#test-config-fail-on-flaky-tests
- https://www.mozilla.org/en-US/MPL/2.0/FAQ/
