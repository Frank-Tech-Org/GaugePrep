---
name: board-token-scope
description: board.sh move/sprint fail when the gh token has only read:project; the owner must run gh auth refresh -s project
metadata:
  type: project
---

On 2026-10-26 every `board.sh move` and `board.sh sprint` failed: the gh token had scopes `read:project`, not `project`. Issue edits, fields (`set`, `type`), `block` and comments still worked.

**Why:** the project v2 board needs the `project` write scope; issue fields and dependencies do not.

**How to apply:** before bulk board work, run `gh auth status` and check for `project`. If it is missing, do the issue edits anyway, then hand the owner the exact `board.sh` commands to replay after `gh auth refresh -s project`.
