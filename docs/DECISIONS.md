# Decisions waiting on the owner

Any agent can add an entry. `pm` keeps the list tidy, `/pm` shows it, and `/pm decide` resolves it. If an entry appears in two reports without an answer, it is flagged as blocking.

Settled architecture choices become ADRs in `docs/adr/`. This file is for open questions and short rulings.

## Open

### D-2: Do owner-run tickets (accounts, recordings, vendor requests) count against the in-flight limit?
- Raised: 2026-10-26 by pm on #9, #14, #16, #17, #18, #19
- Context: Six M0 tickets involve no code. They are mostly waiting: #14 recruits speakers and #18 waits up to 3 weeks for MTN. If they count against the limit of 2 in flight, they hold back #4, #5 and #6 for weeks.
- Options: A, they count; the long-lead requests start late · B, tickets with no repository code (no Files and paths except `.env.example`) run outside the limit, still one at a time per owner
- Recommendation: B, because the limit protects review load and `develop`, and these tickets touch neither.
- Cost of delay: #14 and #18 have 3-week lead times. Each week they wait pushes the speech-provider choice (#15) and phone sign-up back a week.
- Reversible: yes
- Blocks: #14, #18 starting now

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
- Effect: process doc section 1, `/pm`, `/lm-start` (limit and overlap check) and `board.sh wip`.

<!-- Move an entry here when answered, adding:
- Decided: <YYYY-MM-DD>: <option> · <the owner's reason>
-->
