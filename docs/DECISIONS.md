# Decisions waiting on the owner

Any agent can add an entry. `product-owner` keeps the list tidy, `/lm-brief` shows it, and `/lm-decide` resolves it. If an entry appears in two briefs without an answer, it is flagged as blocking.

Settled architecture choices become ADRs in `docs/adr/`. This file is for open questions and short rulings.

## Open

### D-1: Allow more than one ticket in flight at a time?
- Raised: 2026-10-26 by the owner, through Claude, on the team setup
- Context: The process allows one ticket in the work slot. The owner wants parallel work when tickets cannot conflict.
- Options: A, keep one ticket at a time, simplest, slowest · B, two or three tickets, each in its own git worktree and branch, only when their Areas and touched paths do not overlap and neither depends on the other · C, no limit, fastest, conflicts and review load grow quickly
- Recommendation: B, with a limit of two to start. `/lm-next` would name a second ticket only when its Area and paths differ from the first, `board.sh wip` would show both, and `/lm-start` would refuse an overlap.
- Cost of delay: M0 has about twenty chores that mostly touch separate areas (CI, Django skeleton, infra), so each week on one slot delays everything behind it.
- Reversible: yes
- Blocks: process doc section 1, `/lm-start`, `/lm-next`, `/lm-block`, `board.sh`

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

_None yet._

<!-- Move an entry here when answered, adding:
- Decided: <YYYY-MM-DD>: <option> · <the owner's reason>
-->
