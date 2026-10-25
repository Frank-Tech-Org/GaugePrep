---
name: agents-commit-owner-merges
description: "Within the /lm-* workflow agents commit, push work branches and open PRs; only the owner merges, tags and publishes releases"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 7d0fe753-8c22-4a99-91d8-108bdd9024c7
  modified: 2026-10-25T07:35:03.170Z
---

As of 2026-10-24, agents working a ticket through the `/lm-*` commands commit, push their own branch (`feature/*`, `release/*`, `hotfix/*`) and open the PR, with Conventional Commit messages and the attribution lines. The owner still merges PRs, pushes tags and publishes GitHub releases. The guard hook (`.claude/hooks/guard-bash.sh`) enforces this: it blocks direct pushes to main or develop, plain `--force` and `+refspec` pushes, quoted push arguments, tag and delete pushes, `--amend`, `gh pr merge` and `gh release create`. Since 2026-10-25 it allows `--force-with-lease` on work branches; the user asked for that so I could repair a bad push myself.

**Why:** On 2026-10-22 I committed and opened a PR without being asked, and the user said they do all commits. On 2026-10-24 they asked for full automation instead: "all the agents commit and create the PR".

**How to apply:** Commit and push only inside the ticket's own branch while working a ticket. Outside the workflow (setup work like this session's), still leave changes in the working tree unless asked. Never merge, tag or release. PR text stays short ([[keep-prs-short]]). See [[workflow-redesign-from-friend-template]].
