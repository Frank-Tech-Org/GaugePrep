---
name: keep-prs-short
description: "PR text I hand the user must be short and direct; only what is needed, no padding"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1dd11a6b-59c4-4019-9fd0-8b8a194a0087
  modified: 2026-10-23T13:31:27.657Z
---

Keep pull request descriptions (and commit messages) brief and direct: a one or two sentence summary, the ticket ref, a few lines of what changed, and only the checklist items that matter. Do not list every criterion or restate the ticket.

**Why:** After I gave a long PR for #1 the user said to always avoid long PRs and give only what is needed.

**How to apply:** Fill the PR template but trim it; skip sections that add nothing. Remember I never commit or push, so this is text for the user to paste. See [[agents-commit-owner-merges]].
