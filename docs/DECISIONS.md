# Decisions waiting on the owner

Any agent can add an entry. `product-manager` keeps the list tidy, `/pm` shows it, and `/pm decide` resolves it. If an entry appears in two reports without an answer, it is flagged as blocking.

Settled architecture choices become ADRs in `docs/adr/`. This file is for open questions and short rulings.

## Open

### D-16: What runs dev and staging once the free server hours end?
- Raised: 2026-11-11 by cto on #179
- Context: dev and staging share one AWS t4g.small in Stockholm, free under AWS's t4g.small trial until 31 Dec 2026. From January it bills by the hour, about $12 to $15 a month with its disk, unless we move.
- Options: A, keep it and pay from January; no work · B, an Oracle Always Free ARM server; free, a rebuild with the existing script and new DNS records, but Oracle reclaims idle free servers and free capacity is often unavailable · C, a Hetzner ARM server like production will use; about €4 to €5 a month, the same rebuild.
- Recommendation: C, because it costs about a third of A and staging runs on the same kind of server as production.
- Cost of delay: none until mid-December; after 31 Dec about $3 a week.
- Reversible: yes
- Blocks: none

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

### D-11: What may cto and product-manager decide without the owner?
- Decided: 2026-11-05: a standing delegation list · the owner. `cto` decides technical items and `product-manager` decides product items, then records each ruling here with "under D-11". Delegated: a free MIT, BSD, Apache-2.0 or ISC dependency with no open CVE and under 5 new lockfile packages (a package already in the lockfile counts as none); whether an acceptance criterion is met when its number is met; splitting or merging tickets; process wording that loosens no safety rule. Kept by the owner: money, legal identity, accounts, physical access, anything irreversible, scoring or grading formulas, PR approvals, owner-only files, releases and tags.
- Effect: owner asks come as one list before the Friday demo.

### D-12: Does an owner task that is only waiting count against the one-at-a-time rule?
- Decided: 2026-11-05: no · the owner. Once the owner's part is done and only a third party's reply is awaited, the next owner task can start. First case: #18 alongside #14.
- Effect: process doc §1, the CLAUDE.md parallel-tickets rule.

### D-13: Verify sign-ups by SMS?
- Decided: 2026-11-05: no, email verification only, Google sign-in stays · the owner. SMS costs money per message and the owner prefers email.
- Effect: Twilio and the MTN sender ID are dropped; sign-up uses email (or Google); no phone number is collected. ADR-023 supersedes ADR-018.

### D-14: Which email provider, and what does dev send to?
- Decided: 2026-11-05: under D-11 · cto. Resend free in staging and production through plain SMTP (no SDK), Mailpit (MIT) locally and in dev so synthetic addresses never bounce on the real account. Brevo free is the fallback if mail logs must stay in the EU.
- Effect: ADR-024. Owner actions: the Resend account, the sending subdomain's DNS records in Cloudflare and the API key values. Resend Pro ($20 a month) past 100 emails a day is a later owner call.

### D-15: Which app server runs the backend container?
- Decided: 2026-11-10: gunicorn 26.2, under D-11 · cto. MIT, no required dependencies, no open CVE, the standard Django WSGI server; 2 sync workers fit the 320 MB dev container. Added to the backend's dependencies below 27, whose release was a few hours old.
- Effect: #11 (production image stage and Kamal dev deploy).

### D-16: Pay for GitHub Team to enforce required checks on develop?
- Raised: 2026-11-12 by cto on #167
- Decided: 2026-11-12: no, not yet · the owner. The repository is private on a free organization plan, so rulesets and branch protection are not enforced (checked in the settings pages). The merge step's checks, the develop alarm and the guard hook stand in for it.
- Effect: revisit before the first production release or when more people get write access.

<!-- Move an entry here when answered, adding:
- Decided: <YYYY-MM-DD>: <option> · <the owner's reason>
-->
