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

<!-- Move an entry here when answered, adding:
- Decided: <YYYY-MM-DD>: <option> · <the owner's reason>
-->
