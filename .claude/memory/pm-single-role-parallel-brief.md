---
name: pm-single-role-parallel-brief
description: Owner wants one senior pm agent and one /pm command for the board, parallel tickets (2, then 3 with CI), brief agent comments, and a Definition of Done on every ticket
metadata:
  type: feedback
---

One `product-manager` agent (named `pm` until 2026-10-29) owns tickets and the board (product-owner and delivery-manager were merged into it), reached through `/pm`. It takes the technical read the CTO (main session) writes into its prompt, orders work with blockers first, and writes tickets with both acceptance criteria and a Definition of Done. Up to 2 tickets in flight, 3 once CI exists, each in its own worktree and only when they cannot conflict. Agent reviews, comments and checkpoints are brief.

Commands take no ticket number and infer their ticket from the board, current branch/worktree, open PRs and checkpoints; `#n` is an optional override. Decided 2026-10-28. On 2026-10-29 the owner found 8 commands too many and approved 4: `/pm [plan|decide|report]`, `/lm-next` (one step per run: build, fix, review, merge or QA, plus `block`), `/lm-release <version>|check` (claims and performance live in its gate) and `/lm-hotfix`.

**Why:** The owner found many board commands pointless for what is one senior PM job, wanted tickets clear enough to build, and found existing tickets had ACs but no DoD. Decided 2026-10-26.

Also (2026-10-26): issue titles carry no type prefix, and tickets that have not started get no comments; checkpoints begin when work starts. I had to strip prefixes from 19 titles and delete 17 early checkpoints.

**How to apply:** Draft tickets for `product-manager`, never create issues elsewhere. Keep comments verdict-first and under about 10 lines. Don't add commands; extend `/pm` or `/lm-next` instead. The owner uses two in a normal week. Supersedes the one-ticket rule in [[workflow-redesign-from-friend-template]] and the PM notes in [[pm-role-github-setup]].
