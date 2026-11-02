---
name: agents-commit-owner-merges
description: "Agents commit and open PRs; after the owner approves, the merge step of /lm-next merges reviewed PRs into develop via merge.sh; only the owner merges into main, tags and releases"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 7d0fe753-8c22-4a99-91d8-108bdd9024c7
  modified: 2026-10-26T00:00:00.000Z
---

As of 2026-10-24, agents working a ticket through the `/lm-*` commands commit, push their own branch (`feature/*`, `hotfix/*`, `chore/*`) and open the PR. Since 2026-10-26 the owner has delegated merging into `develop`; since the 2026-10-29 reset the merge step of `/lm-next`, in whatever session runs it, runs `.claude/scripts/merge.sh <pr>` after `REVIEW: PASS` and green CI. On 2026-10-30 the owner chose to approve every PR into `develop` from their approver account (`frankkefoueg` since 2026-11-02; [[github-accounts-owner-and-agents]]) as a sign-off, once the agents' review has passed; `merge.sh` checks the approval is for the head sha. The owner still merges into `stage` and `main`, pushes tags and publishes GitHub releases. The guard hook (`.claude/hooks/guard-bash.sh`) is owner-only and still refuses `gh pr merge`, raw `git push`, `--amend`, tags and releases. Agents upload only with `.claude/scripts/push.sh <work-branch>`, run on its own.

**Why:** On 2026-10-22 I committed and opened a PR without being asked, and the user said they do all commits. On 2026-10-24 they asked for full automation: "all the agents commit and create the PR". On 2026-10-26 they said "the tech lead should merge tickets".

**How to apply:** Never merge a PR yourself other than by running `merge.sh` from the merge step of `/lm-next` after a posted PASS on the final commit; a merge attempted before the review gets blocked. Never merge, tag or release into `main`. PR text stays short ([[keep-prs-short]]). See [[workflow-redesign-from-friend-template]].
