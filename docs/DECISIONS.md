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

### D-3: What is the spending cap for the AI pentest before each release?
- Raised: 2026-10-29 by tech-lead on the studio reset
- Context: Shannon is an AI tool that attacks our staging app the way a hacker would, and reports only attacks it proved. It uses paid Anthropic API calls, roughly $50 for one full run on a small app, and takes one to a few hours. It never touches production.
- Options: A, $75 hard cap per run, one run before each release · B, $150 per run, plus a run after any change to login, payments or grading · C, no AI pentest until launch, free scanners only
- Recommendation: A, with the cap set as a spending limit in the Anthropic console so it cannot be exceeded; the first run's real cost is reported before any raise.
- Cost of delay: none until the first release candidate.
- Reversible: yes
- Blocks: nothing now

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
