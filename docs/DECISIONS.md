# Decisions waiting on the owner

Any agent can add an entry. `pm` keeps the list tidy, `/pm` shows it, and `/pm decide` resolves it. If an entry appears in two reports without an answer, it is flagged as blocking.

Settled architecture choices become ADRs in `docs/adr/`. This file is for open questions and short rulings.

## Open

_None._

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
