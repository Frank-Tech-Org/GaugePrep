# Decisions waiting on the owner

Any agent can add an entry. `product-manager` keeps the list tidy, `/pm` shows it, and `/pm decide` resolves it. If an entry appears in two reports without an answer, it is flagged as blocking.

Settled architecture choices become ADRs in `docs/adr/`. This file is for open questions and short rulings.

## Open

No open entries.

<!-- Template:
### D-<n>: <question>
- Raised: <YYYY-MM-DD> by <agent> on #<issue>
- Context: two sentences.
- Options: A, <consequence> · B, <consequence>
- Recommendation: <option>, because <one sentence>.
- Cost of delay: what is blocked, and how that grows per week.
- Reversible: yes | no
- Blocks: #<issue>, ...
-->

## Decided

### D-1: Allow more than one ticket in flight at a time?
- Raised: 2026-10-26 by the owner, through Claude, on the team setup
- Decided: 2026-10-26: option B · two tickets in flight now, three once CI runs on every PR. Each in its own git worktree and branch, only when Areas or paths differ and neither blocks the other.
- Effect: process doc section 1, `/pm`, `/lm-next` (limit and overlap check) and `board.sh wip`.

### D-2: Do owner-run tickets (accounts, recordings, vendor requests) count against the in-flight limit?
- Raised: 2026-10-26 by product-manager on #9, #14, #16, #17, #18, #19
- Decided: 2026-10-29: option B · the owner approved the studio plan. Tickets with no repository code, labelled `owner-task`, run outside the limit, one at a time.
- Effect: process doc section 1, `/lm-next` limit check, the `owner-task` label.

### D-3: How do we pentest before each release?
- Raised: 2026-10-29 by the CTO on the studio reset
- Decided: 2026-10-29: free tools only · the owner has no budget for paid pentest runs. `security-engineer` leads the pentest itself in a Claude Code session on the existing subscription: ZAP active scan, Nuclei, Schemathesis against the OpenAPI contract, sqlmap and ffuf on suspect endpoints, and the permanent attack tests. Staging or a local copy only.
- Effect: `security-engineer`, `/lm-release` check 4b, `CLAUDE.md` quality gates. A paid AI pentest can be reconsidered once there is revenue.

### D-4: Follow build pack 2 for grader anchors instead of the exam spec?
- Raised: 2026-10-30 by product-manager on the build pack intake
- Decided: 2026-10-30: follow the pack · the owner. 204 anchors: 34 exemplars, one per level per task type, used in the grader prompt, and 170 evaluation anchors never in the prompt, instead of 180. The level two independent human raters agree on wins over the target level an item was written for. Two raters, plus a third on a one-level disagreement, instead of one reviewer.
- Effect: `docs/exam-specs/TCF-Canada.md` updated and ADR-020 written by `cto` in #53; raters recruited in #57.

### D-5: How does the human reviewer approve content batches?
- Raised: 2026-10-30 by product-manager on the build pack intake
- Decided: 2026-10-30: option A · the owner. Agents do the full first-line review; the human reviewer approves a batch after reviewing a 10% sample of each batch (at least 5 items) and 100% of simulation-form items.
- Effect: `docs/content/README.md` section 5 (#53); the reviewer is named in #60.

### D-6: Which GitHub plan?
- Raised: 2026-10-30 by product-manager on #9
- Decided: 2026-10-30: keep the free plan · the owner. Environments and environment secrets are not available for a private repository on it, so secrets are repository secrets told apart by name prefix: `DEV_`, `STAGING_`, `PROD_`.
- Effect: #9, #11, #12, #13, #17, #18 name secrets by prefix.

### D-7: Which services may cost money?
- Raised: 2026-10-30 by the owner on the build pack intake
- Decided: 2026-10-30: free in dev and staging, paid allowed in production · the owner. Dev and staging use free plans or self-hosted services (the owner's machine is powerful enough to self-host for dev). Production keeps the planned paid services: Anthropic, ElevenLabs, Twilio and Hetzner.
- Effect: tickets name no paid plan for dev or staging; dev and staging grade with a self-hosted model (D-8).

### D-8: How do dev and staging grade writing and speaking without a paid model?
- Raised: 2026-10-30 by product-manager on the build pack intake
- Decided: 2026-10-30: A, the best self-hosted model available · the owner. Dev and staging grade with a self-hosted open model behind the `TextModel` interface; `ai-engineer` picks the model by measured research at the start of M3, and the grader release checks run against the production model before each release.
- Effect: no paid AI calls in dev or staging; the only AI spend outside production is the release checks.

### D-9: Keep Husky for the Git hooks?
- Raised: 2026-11-02 by cto on #5
- Decided: 2026-11-02: keep Husky · the owner. The dependency check found no release since 2024-11-18 and a replacement of about 50 lines (`core.hooksPath` plus `sh -e` hooks); Husky is MIT, advisory-free, runs no install scripts and the ticket names it.
- Effect: #5 keeps `husky`; swapping it out later is a small follow-up.

### D-10: What is the product called?
- Raised: 2026-11-03 by the owner
- Decided: 2026-11-04: GaugePrep, domain gaugeprep.com, new resources prefixed `gaugeprep-` · the owner. The product was called LinguaMentor before.
- Effect: the rename ticket (#147); the deploy tickets use the new names.

<!-- Move an entry here when answered, adding:
- Decided: <YYYY-MM-DD>: <option> · <the owner's reason>
-->
