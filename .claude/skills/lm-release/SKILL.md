---
name: lm-release
description: Release LinguaMentor. With a version, run the full release gate, cut and push release/x.y.z with the changelog, and open the release PR into main. With "<version> done", after the owner has merged, tagged and published, open the back-merge PR and move the released tickets to Done.
argument-hint: <version> [done]
arguments: [version, phase]
disable-model-invocation: true
---

# Release v$version $phase

Follow `docs/process/branching-and-release.md` section 7. Agents push the release branch and open the PRs. Only the owner merges, pushes the tag and publishes the GitHub release.

## Ready to deploy now

!`.claude/scripts/board.sh list "Ready to deploy" || true`

## Prepare (no phase given)

### 1. Gate: every item runs, and any failure stops the release

| # | Check | Who |
|---|---|---|
| 1 | Slot empty, and the Ready to deploy list matches the commits on `develop` since the last tag | `platform-engineer` |
| 2 | CI green on the head of `develop` | `platform-engineer` |
| 3 | Security pass on `git diff <last-tag>..origin/develop`: no CRITICAL or HIGH | `security-engineer` |
| 4 | Dependencies: `uvx pip-audit` and `pnpm audit --audit-level high`, no high or critical | `security-engineer` |
| 4b | Attack test on staging (never production): the permanent attack tests, ZAP active scan, Nuclei and Schemathesis against the OpenAPI contract (all free), no open HIGH or CRITICAL | `security-engineer` |
| 5 | Performance: `/lm-perf-audit` on what changed, including the k6 load run on staging, `PERF: PASS` | `performance-engineer` |
| 6 | Claims: `/lm-verify-claims`, `CLAIMS: GO` | `qa-engineer` |
| 7 | UX and accessibility on every changed screen | `product-designer`, `qa-engineer` |
| 8 | Privacy: no new personal data flow without a ruling | `privacy-compliance` (only if data flows changed) |
| 9 | Migrations are expand-then-contract, with a rollback written down | `code-reviewer` |
| 10 | Grader changes have a stored, passing release-check report | `ai-engineer` (only if grading changed) |
| 11 | Rollback command documented for this deploy | `platform-engineer` |

Show the table with each result. If any check fails, stop with `RELEASE: NO-GO — <check>`, and hand a draft ticket for each failure to `product-manager`, which creates them.

### 2. Cut the branch and the PR

Delegate to `platform-engineer`:
```bash
git switch develop && git pull && git switch -c release/$version
# write the CHANGELOG.md entry
git add CHANGELOG.md
git commit -m "chore(release): v$version"
.claude/scripts/push.sh release/$version
gh pr create --base main --head release/$version --title "Release v$version" --body-file <release PR body>
```
`content-marketer` writes `release-notes.md`, in French then English, in the scratchpad.

### 3. Regression

Once the staging deploy has run on `release/$version`, `qa-engineer` runs the regression. Fixes are committed and pushed on the release branch.

### 4. Hand over to the owner

```
Merge the release PR with a merge commit (not a squash), then:
git switch main && git pull && git tag -a v$version -m "Release v$version" && git push origin v$version
gh release create v$version --title "v$version" --notes-file <path to release-notes.md>
Then run: /lm-release $version done
```

## Close (phase = done)

1. Confirm the tag and the release exist: `git ls-remote --tags origin v$version` and `gh release view v$version`. If either is missing, stop.
2. Open the back-merge PR: `gh pr create --base develop --head main --title "chore: back-merge v$version" --body "Back-merge after the v$version release."`. Tell me to merge it with a merge commit.
3. Delegate to `product-manager`, for each released ticket:
   ```
   .claude/scripts/board.sh move <n> Done
   gh issue close <n> --comment "Released in v$version."
   ```
4. Report the closed tickets in one line, then `/pm`.
