---
name: github-accounts-owner-and-agents
description: "KefouegFrank is the owner and approver, frankkefoueg is the agents' account with a fine-grained token; what that token can and cannot do"
metadata:
  node_type: memory
  type: reference
  originSessionId: 35c92eb1-c4fe-4a39-8230-fcc811cf0242
  modified: 2026-10-30T11:53:53.708Z
---

The LinguaMentor org has two people. `KefouegFrank` is the owner: admin, approves PRs into `develop` as a sign-off, merges `stage` and `main`, tags and releases. `frankkefoueg` is the agents' account, the active `gh` account on this machine, using a fine-grained token (repo `linguamentor-v3`, Contents, Pull requests and Issues read and write, Actions and Commit statuses read, org Projects read and write, no Workflows). Setup steps are in `docs/process/branching-and-release.md` section 9.

As of 2026-10-30 that token gets 403 on org issue types, org issue fields and repo Actions secrets. Issue type can still be set with a REST PATCH on the issue, and field values through IDs read from an issue.

The owner keeps both accounts logged in to `gh` on this machine and keeps the local git identity as `kefouegFrank`; on 2026-10-30 they declined logging the owner out and setting an agent git identity. Don't raise either again.

**How to apply:** never switch to the owner's account. Work through the 403s rather than asking for broader rights, unless a read-only permission saves the owner a manual step. See [[agents-commit-owner-merges]].
