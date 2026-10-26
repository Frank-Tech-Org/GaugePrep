---
name: merge-gate-rulings
description: Rulings on what merge.sh and the guard must enforce before tech-lead merges into develop (sha-bound verdict, owner-only files, CI fail-open)
metadata:
  type: project
---

Rulings from the PR #43 review (2026-10-26). PR #43 added merge.sh and the guard hook, and got CHANGES with 4 blockers.

- A PASS verdict must name the reviewed head sha, and merge.sh must refuse when that sha differs from the PR head. Comparing the comment time with the commit's committer date is not acceptable, because the committer's clock sets that date.
- PRs that touch `.claude/hooks/`, `.claude/settings*.json`, `.claude/scripts/push.sh` or `.claude/scripts/merge.sh` go to the owner. merge.sh itself must refuse them, not only `tech-lead.md`.
- merge.sh is a guardrail file. It belongs in the settings deny lists and in the guard's path rule, with a pinned fingerprint like `PUSH_SHA`.
- Blocking `gh pr merge` alone is not enough. `gh api -X PUT .../pulls/N/merge` and ref, tag or release writes through `gh api` bypass it.
- `gh api --paginate --jq` applies the filter per page. Any "last verdict" logic must slurp all pages first.
- When there are no CI checks, merge.sh fails open. That is acceptable only until `.github/workflows/` exists.

**Why:** there is no GitHub branch protection (free private org plan), so the guard and merge.sh are the only gates.

**How to apply:** when merge.sh, the guard or `/lm-review` change, check these points first. Before relying on merge.sh, check whether these rulings were fixed. See [[guard-hook-review-workarounds]] and [[agent-skill-resolution]].
