---
name: github-accounts-owner-and-agents
description: "Since 2026-11-02 KefouegFrank is the agents' account (fine-grained token) and frankkefoueg the owner's approver and release account; both are org owners"
metadata:
  node_type: memory
  type: reference
  originSessionId: 35c92eb1-c4fe-4a39-8230-fcc811cf0242
  modified: 2026-11-02T00:00:00.000Z
---

On 2026-11-02 the owner swapped the accounts so the agents' commits count on their main account. `KefouegFrank` is the agents' account: the active `gh` account on this machine through a fine-grained token (repo `linguamentor-v3`, Contents, Pull requests and Issues read and write, Actions and Commit statuses read, org Projects read and write, no Workflows), git identity `kefouegFrank` <kefoueg@gmail.com>. `frankkefoueg` is the owner's approver: approves PRs into `develop` as a sign-off (checked by `merge.sh`), merges `stage` and `main`, tags and releases. The owner chose to keep both as organisation Owner, so the token is the agents' only GitHub-side limit. Setup steps are in `docs/process/branching-and-release.md` section 9.

As of 2026-10-30 a token with those permissions gets 403 on org issue types, org issue fields and repo Actions secrets. Issue type can still be set with a REST PATCH on the issue, and field values through IDs read from an issue.

**How to apply:** never switch `gh` to `frankkefoueg`, and never approve a PR, in the browser or anywhere else; the approval is the owner's. Work through the 403s rather than asking for broader rights, unless a read-only permission saves the owner a manual step. See [[agents-commit-owner-merges]].
