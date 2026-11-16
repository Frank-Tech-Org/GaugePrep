---
name: scope-ticket-work-to-what-is-asked
description: Create only the tickets the user asked for (foundation/M0 first); never bulk-publish the whole backlog to GitHub without confirming scope
metadata:
  node_type: memory
  type: feedback
  originSessionId: dcbded2e-a6da-4de3-bade-7cc9dd2caa68
  modified: 2026-10-23T12:45:01.645Z
---

When asked to review and create tickets "so the board is ready before the team comes in", the user meant the foundation (M0, the start of the project), not the whole product backlog M0 to M8.

**Why:** On 2026-10-23 I drafted 654 tickets for M0 to M8 and started publishing them; the user interrupted ("i did not even ask you to create all the complete project tickets just the foundation") and told me to undo everything. I deleted the 16 issues I had created (#24 to #39) and restored the 22 originals (#1, #3 to #23) from their event history.

**How to apply:** Before any bulk write to GitHub, state the exact scope (milestones, ticket count) and confirm it. Default to the smallest reading of the request: foundation first, later milestones only when asked. The full drafts (M0 to M8) are local only, in the session scratchpad, not on GitHub. See [[pm-role-github-setup]] and [[agents-commit-owner-merges]].
