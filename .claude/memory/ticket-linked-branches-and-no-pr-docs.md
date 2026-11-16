---
name: ticket-linked-branches-and-no-pr-docs
description: Ticket branches are created from the ticket so branch and PR show in its Development panel; tickets that change no repository file get no branch or PR
metadata:
  type: feedback
---

- A ticket's branch is created from the ticket (`gh issue develop <n> --base develop --name feature/<n>-<slug>`), so the branch and its PR appear in the ticket's Development panel. `Refs #<n>` alone does not link them. An existing branch can't be linked afterwards; recreate it from the ticket.
- A docs, decision or owner ticket gets a branch and PR only when it writes something into the repository (an ADR does); otherwise its result goes on the ticket.
- A PR linked this way closes the issue when it merges into `develop`; the board Status is the truth, a failed QA reopens it.

**Why:** owner, 2026-10-30, after #12's PR was opened from an unlinked branch.
**How to apply:** `/lm-next` §3 and the process doc carry this; check it whenever a branch or PR is created. See [[agents-commit-owner-merges]].
