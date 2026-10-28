---
name: command-handoff-loops
description: When reviewing /lm-* or /pm command changes, trace every hand-off row against the target command's refusal table to find loops
metadata:
  type: feedback
---

PR #46 (2026-10-28) made the commands find their own ticket and hand off when a check fails. It got CHANGES for two loops. (1) `/lm-start` refused a ticket that was already in flight at the parallel limit and sent it to `/lm-review`, which had no PR, so it sent it back to `/lm-start`. (2) An open PR with red CI went to "the building agent" with no command named, and `/lm-start` sent any open-PR ticket to `/lm-review`.

**Why:** each refusal table looks right by itself. Loops only show up when you pair rows across commands, and the in-flight ticket is the usual case that slips through.

**How to apply:** for every "Hand off to" row, check the target command's first matching row for the same state. A ticket that is already in `wip` must never be refused by the parallel limit. Every hand-off must name a slash command, not an agent. Also check the order of the rows: a board-column row placed before the PR rows sent In review tickets with CHANGES to `/pm refine` (round 2 of #46). Also check that the branch-prefix filters in lm-review and `merge.sh` agree (`chore/*`). When a filter is widened (round 3 of #46: `chore/*` in lm-review), every hand-off target must also resolve that branch kind. `/lm-start` only knows `feature/<n>-*`, so it would claim an unrelated Ready ticket. See [[merge-gate-rulings]].
