# Decisions waiting on the owner

Settled architecture choices become ADRs in `docs/adr/`. This file is for open questions and short rulings.

## Open

<!-- Template:
### D-<n>: <question>
- Raised: <YYYY-MM-DD> by <role> on #<issue>
- Context: two sentences.
- Options: A, <consequence> · B, <consequence>
- Recommendation: <option>, because <one sentence>.
- Cost of delay: what is blocked, and how that grows per week.
- Reversible: yes | no
- Blocks: #<issue>, ...
-->

## Decided

### D-38: Is the design canvas the approved design for the web build?

- Decided: 2026-11-26: yes, the canvas is the approved design · the owner. Web tickets build from it at phone, tablet and desktop, in French and English, light and dark. No photo enters the repository without a recorded source and licence, and phones download none of the carousel photos.
- Effect: #267 closed; the web build is planned in tickets and does not start until the owner has reviewed them. Route JavaScript cannot stay under 100 kB (the framework alone is 135 kB gzipped, ADR-028), so each route's limit is set from the shell's measured number, under D-11 · the product manager.

### D-39: What does "usable in under 3 s on slow 3G" mean when React cannot hydrate in time?

- Decided: 2026-11-26: the page's text shows in the learner's language and theme and every control on it responds, both before hydration, under D-11 · the CTO. Measured on #243: 140 kB of gzipped JavaScript needs 2.8 s of transfer alone at 400 kbps, so hydration lands near 4.8 s with any React page (the framework floor is 135 kB). Controls work first through native elements and the inline boot script; React takes over on hydration. Ruled out: counting read-only text as usable (dead buttons for 3.5 s), trimming the shell's 5 kB (saves 0.1 s), reopening ADR-004 (a framework change for two menus). Revisit when a route needs a control that cannot work before hydration.

### D-40: Lock an unverified account after 10 wrong codes in a day, whoever tries them?

- Decided: 2026-11-27: yes, per account across all its codes, not per client address, under D-11 · the CTO. A guesser behind many addresses still gets about 10 tries a day against a million codes; the cost is that a stranger can lock the owner out of verifying for 24 h, who then waits or asks for a new code after the day. Revisit if support sees owners locked out.

### D-2: Do owner-run tickets (accounts, recordings, vendor requests) count against the in-flight limit?

- Raised: 2026-10-26 on #9, #14, #16, #17, #18, #19
- Decided: 2026-10-29: option B · the owner approved the studio plan. Tickets with no repository code, labelled `owner-task`, run outside the limit, one at a time.

### D-3: How do we pentest before each release?

- Raised: 2026-10-29 by the CTO on the studio reset
- Decided: 2026-10-29: free tools only · the owner has no budget for paid pentest runs. The security engineer leads the pentest itself on the existing subscription: ZAP active scan, Nuclei, Schemathesis against the OpenAPI contract, sqlmap and ffuf on suspect endpoints, and the permanent attack tests. Staging or a local copy only.
- Effect: a paid AI pentest can be reconsidered once there is revenue.

### D-4: Follow build pack 2 for grader anchors instead of the exam spec?

- Raised: 2026-10-30 on the build pack intake
- Decided: 2026-10-30: follow the pack · the owner. 204 anchors: 34 exemplars, one per level per task type, used in the grader prompt, and 170 evaluation anchors never in the prompt, instead of 180. The level two independent human raters agree on wins over the target level an item was written for. Two raters, plus a third on a one-level disagreement, instead of one reviewer.
- Effect: `docs/exam-specs/TCF-Canada.md` updated in #53; raters recruited in #57.
- Addendum, decided 2026-11-12 · the owner: with no recruited speakers (#14 closed), the first speaking anchors are scripted transcripts written per level and task, levelled by the two raters (#57) and stored append-only with a source tag. Rated attempts from consenting learners replace them after launch. LANGSNAP and FLLOC can never be anchors: CC BY-NC-SA forbids commercial use and would carry share-alike into our content. Effect: speech recognition is chosen on public corpora instead (ADR-026).

### D-5: How does the human reviewer approve content batches?

- Raised: 2026-10-30 on the build pack intake
- Decided: 2026-10-30: option A · the owner. Automated first-line review covers every item; the human reviewer approves a batch after reviewing a 10% sample of each batch (at least 5 items) and 100% of simulation-form items.
- Effect: `docs/content/README.md` section 5 (#53); the reviewer is named in #60.

### D-6: Which GitHub plan?

- Raised: 2026-10-30 on #9
- Decided: 2026-10-30: keep the free plan · the owner. Environments and environment secrets are not available for a private repository on it, so secrets are repository secrets told apart by name prefix: `DEV_`, `STAGING_`, `PROD_`.
- Effect: #9, #11, #12, #13, #17, #18 name secrets by prefix.

### D-7: Which services may cost money?

- Raised: 2026-10-30 by the owner on the build pack intake
- Decided: 2026-10-30: free in dev and staging, paid allowed in production · the owner. Dev and staging use free plans or self-hosted services (the owner's machine is powerful enough to self-host for dev). Production keeps the planned paid services: Anthropic, ElevenLabs and Hetzner (Twilio was dropped by D-13).
- Effect: tickets name no paid plan for dev or staging; dev and staging grade with a self-hosted model (D-8).

### D-8: How do dev and staging grade writing and speaking without a paid model?

- Raised: 2026-10-30 on the build pack intake
- Decided: 2026-10-30: A, the best self-hosted model available · the owner. Dev and staging grade with a self-hosted open model behind the `TextModel` interface, picked by measured research at the start of M3; the grader release checks run against the production model before each release.
- Effect: no paid AI calls in dev or staging; the only AI spend outside production is the release checks.

### D-9: Keep Husky for the Git hooks?

- Raised: 2026-11-02 by the CTO on #5
- Decided: 2026-11-02: keep Husky · the owner. The dependency check found no release since 2024-11-18 and a replacement of about 50 lines (`core.hooksPath` plus `sh -e` hooks); Husky is MIT, advisory-free, runs no install scripts and the ticket names it.
- Effect: #5 keeps `husky`; swapping it out later is a small follow-up.

### D-10: What is the product called?

- Raised: 2026-11-03 by the owner
- Decided: 2026-11-04: GaugePrep, domain gaugeprep.com, new resources prefixed `gaugeprep-` · the owner. The product was called LinguaMentor before.
- Effect: the rename ticket (#147); the deploy tickets use the new names.

### D-11: What may the CTO and the product manager decide without the owner?

- Decided: 2026-11-05: a standing delegation list · the owner. The CTO decides technical items and the product manager product items, then records each ruling here with "under D-11". Delegated: a free MIT, BSD, Apache-2.0 or ISC dependency with no open CVE and under 5 new lockfile packages (a package already in the lockfile counts as none); whether an acceptance criterion is met when its number is met; splitting or merging tickets; process wording that loosens no safety rule. Kept by the owner: money, legal identity, accounts, physical access, anything irreversible (replaced by D-34), scoring or grading formulas, PR approvals, owner-only files, releases and tags.
- Effect: owner asks come as one list before the Friday demo.

### D-12: Does an owner task that is only waiting count against the one-at-a-time rule?

- Decided: 2026-11-05: no · the owner. Once the owner's part is done and only a third party's reply is awaited, the next owner task can start. First case: #18 alongside #14.

### D-13: Verify sign-ups by SMS?

- Decided: 2026-11-05: no, email verification only, Google sign-in stays · the owner. SMS costs money per message and the owner prefers email.
- Effect: Twilio and the MTN sender ID are dropped; sign-up uses email (or Google); no phone number is collected (ADR-023).

### D-14: Which email provider, and what does dev send to?

- Decided: 2026-11-05: under D-11 · the CTO. Resend free in staging and production through plain SMTP (no SDK), Mailpit (MIT) locally and in dev so synthetic addresses never bounce on the real account. Brevo free is the fallback if mail logs must stay in the EU.
- Effect: ADR-024. Owner actions: the Resend account, the sending subdomain's DNS records in Cloudflare and the API key values. Resend Pro ($20 a month) past 100 emails a day is a later owner call.

### D-15: Which app server runs the backend container?

- Decided: 2026-11-10: gunicorn 26.2, under D-11 · the CTO. MIT, no required dependencies, no open CVE, the standard Django WSGI server; 2 sync workers fit the 320 MB dev container. Added to the backend's dependencies below 27, whose release was a few hours old.

### D-16: Pay for GitHub Team to enforce required checks on develop?

- Raised: 2026-11-12 by the CTO on #167
- Decided: 2026-11-12: no, not yet · the owner. The repository is private on a free organization plan, so rulesets and branch protection are not enforced (checked in the settings pages). The merge step's checks, the develop alarm and the guard hook stand in for it.
- Effect: revisit before the first production release or when more people get write access.

### D-17: How are rulings split between the team and the owner?

- Decided: 2026-11-16: a ladder · the owner. An unsure team member asks their lead, then the owner only for scoring or grading formulas, destructive migrations, auth redesign (replaced by D-34), pricing, cutting scope, anything irreversible (replaced by D-34) and a production paid service. Every ruling is one line here.

### D-18: What format do briefs and reports use?

- Decided: 2026-11-16: a brief is at most 12 lines, a report at most 10, in a fixed shape (verdict, changed, verified, findings, rulings, draft tickets, next) · the owner. Findings are `label: file:line - problem - fix`.

### D-19: Does ticket delivery stop after each step?

- Decided: 2026-11-16: no, it runs to the next owner stop or blocker, then reports what is done, what needs the owner and what is next · the owner.

### D-20: When does the review run, and how many CI runs per change?

- Decided: 2026-11-16: the review reads the local diff before the first push, so the PR opens ready with its verdict and CI runs once. Review rounds stop at three · the owner. Measured November 1-16: 364 PR runs, 2.8 per PR, 35% on a commit that already had a run; 2,890 org minutes billed.

### D-21: Does every `develop` PR need the owner's approval?

- Decided: 2026-11-16: no, only PRs touching authentication, payments, personal data, migrations, append-only tables, scoring formulas or owner-only files · the owner. This relaxes a gate, so it is recorded on purpose. Confirmed again 2026-11-17: go ahead as long as it does no harm.
- Effect: the merge script and the develop alarm change in a staged file; until the owner applies it, the old rule stands.

### D-22: How do promotions to `stage` and `main` avoid running CI again?

- Decided: 2026-11-16: a tree-identity check against a green `develop` run, failing closed; hotfix branches still run full CI · the CTO, under D-11. Both promotions so far (#226, #228) had a tree identical to the tested tip.
- Effect: workflow changes staged for the owner, untested until applied.

### D-23: Which roles does the team have?

- Decided: 2026-11-16: 22, adding a research analyst, an exam item reviewer, a support lead (dormant until launch) and a process coach · the owner. The business analyst drafts criteria and the Definition of Done; the product manager orders and accepts.

### D-24: Who may delegate, and how deep?

- Decided: 2026-11-16: only the CTO (to its direct reports) and the product manager (to the CTO, business analyst and research analyst); one at a time, depth two · the owner. The limit is an instruction, not enforced by the tooling.

### D-25: How many skills does a team role preload?

- Decided: 2026-11-16: at most three, the rest on demand · the CTO, under D-11. Published results show 2-3 skills gain more than 4 or more; our own test gave identical rulings with and without one skill at 13-19% more tokens.

### D-26: How do agents change owner-only files?

- Decided: 2026-11-16: they stage the files in one folder with one apply script that copies them and shows the diff, labelled tested or untested · the owner.

### D-27: How many tickets may be in flight?

- Decided: 2026-11-19: no cap · the owner, replacing the 2026-11-16 ruling of three. All sprint tickets sit in Ready and every free one runs at once, each on its own branch and worktree. Free means no open blocker and no overlap in Area or paths with a ticket in flight. Dependencies, overlap, owner approvals on sensitive PRs and CI minutes are the only limits.

### D-28: What runs dev and staging once the free server hours end?

- Raised: 2026-11-11 by the CTO on #179
- Decided: 2026-11-17: try option B, an Oracle Always Free ARM server, first if a free one can be created; otherwise option C, a Hetzner ARM server, provided it meets the criteria below · the owner. Criteria: arm64; at least 2 GB RAM and about 20 GB disk (both inferred from today's t4g.small, the architecture doc gives no minimum); Western Europe, ideally Germany next to Neon Frankfurt; rebuilt from scratch by script in under an hour.
- Effect: Oracle is tried first. The move happens before 31 Dec 2026, when the AWS t4g.small trial ends.

### D-29: Make the repository private once Actions minutes allow it

- Raised: 2026-11-16 by the CTO
- Decided: 2026-11-17: the repository goes back to private once the owner's Actions usage is restored; the plan stays GitHub Free and is never paid · the owner.

### D-30: Who handles tickets that used to wait on the owner?

- Decided: 2026-11-17: the team, like an agency · the owner. Research, vendor requests and setup are worked by the owning agent. The owner is asked only for budget, accounts only the owner can create, passwords and the owner rows of the ladder, in the chat. Progress reaches the owner in the weekly report, where change requests come from.

### D-31: Which hosts do the app and API use in dev and staging?

- Decided: 2026-11-17: app on `dev.` and `staging.gaugeprep.com`, API on `api.dev.` and `api.staging.`, host-only `__Host-` cookies, CSRF token from the API, own CORS middleware, under D-11 · the CTO. Same site in every environment without cookies crossing environments (ADR-027).

### D-32: Can the research analyst use Scrapling for pages plain fetches can't read?

- Decided: 2026-11-17: yes, under D-11 · the CTO. BSD-3-Clause, 0.5.1 of 4 November 2026, no open advisory on it or its main dependencies, run pinned through `uvx` so it adds nothing to our lockfile (49 packages in its own environment); a browser fetcher is far past 200 lines. Script evaluation and saved browser state stay off; the no-CAPTCHA, no-login, robots rule stands.

### D-33: What happens to the append-only consent record when a learner deletes their account?

- Decided: 2026-11-18: A, under D-11 · the CTO. Consent rows stay under the bare learner ID, with no foreign key to the account, as proof of consent; deleting the account row removes the link, and no exception to the append-only rule is needed (B deleted them through an audited role, C waited). It can be undone later, since rows kept can still be deleted. The privacy reviewer agreed on conditions that the deletion ticket must meet: no payment, log, error-tracking, job or idempotency record keeps the learner ID next to an email, name, phone or IP; essays and transcripts are deleted; backups expire within 8 weeks and a restore reruns pending deletions; consent proof has a named retention period; the notice says "kept without any link to you", never "deleted".

### D-34: Which calls are the owner's?

- Decided: 2026-11-18: the owner. Technical and system-design calls are the CTO's, irreversible ones included (destructive migrations, auth design). The owner keeps accounts, budget, passwords, scoring or grading formulas, pricing, cutting scope and production paid services. This replaces "anything irreversible" in D-11 and the destructive migration, auth redesign and irreversible items in D-17. PR approvals, merges into `stage` and `main`, tags, releases and owner-only files stay with the owner.

### D-35: Does a local build at the same commit count as "verified on dev"?

- Decided: 2026-11-19: yes, when dev cannot exercise the case, under D-11 · the product manager. Dev is reachable from one IPv4 address, so IPv6 ranges, mapped addresses and 200-request runs behind a 6 a minute limit can't be tried there. QA runs those on a build of the same commit and the ticket names the commit. First case: #260.

### D-36: How are synthetic test accounts removed from dev and staging?

- Decided: 2026-11-24: through the account deletion path of #268, never by switching off the append-only trigger, under D-11 · the CTO. Deletes fail today only because consent cascades from the account; #268 drops that key (D-33), so deleting an account leaves its consent rows under the bare ID. A non-production command then runs that deletion at once, without the cooling period, for accounts on a reserved test domain (`example.com`, `.test`) and refuses on production settings. Ruled out: disabling the trigger (an exception D-33 rejected), a synthetic flag column (a migration for test data), resetting the staging database (loses the rest of staging for four rows). Until it ships the four accounts stay; they hold no real person's data. Revisit if a test account needs a real mailbox.

### D-37: When does a change get its own ticket or PR?

- Decided: 2026-11-25: by scope, not line count · the owner. A change confined to one file, or one small step, with no criteria of its own rides on the PR or setup branch it belongs to. A ticket gets one PR: review ticks every criterion before a PASS, and a gap found in review is fixed in the open PR. Ruled out: a line limit (a 40-line edit to one file is still one step), and doing nothing (it produced one-file tickets and a second PR for #287). Revisit if setup branches grow too big to review.

<!-- Move an entry here when answered, adding:
- Decided: <YYYY-MM-DD>: <option> · <the owner's reason>
-->
