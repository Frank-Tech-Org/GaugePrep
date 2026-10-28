---
name: lm-qa
description: QA the right merged LinguaMentor ticket on staging (or a local build of develop until staging exists). Works out which ticket from the board and merged PRs, checks it is ready, then passes it to Ready to deploy or fails it back with defects.
argument-hint: "[#n to override]"
disable-model-invocation: true
---

# QA: $ARGUMENTS

No number is needed; `#n` only overrides the choice below.

## State now

!`.claude/scripts/board.sh wip || true`
!`gh api "repos/LinguaMentor/linguamentor-v3/pulls?state=closed&base=develop&per_page=10" --jq '.[] | select(.merged_at) | "#\(.number) \(.title) \(.merge_commit_sha)"' || true`

## 1. Find the ticket

1. `#n` in the arguments.
2. A ticket In QA.
3. Otherwise the ticket of the most recently merged PR into `develop` whose ticket is In review (the ticket is the `Refs #<n>` in the PR body).

## 2. Check the environment, hand off if it says no

| Finding | Hand off to |
|---|---|
| No merged PR waiting for QA | `/lm-review` if a PR is open, else `/pm` |
| Its PR is open, not merged | `/lm-review` |
| Staging exists but the last deploy of `develop` doesn't include the merge commit | wait for the deploy, then rerun |

Then `board.sh move <n> "In QA"` and read `gh issue view <n>`.

## 3. Pick the target

- Staging exists: use it (`gh run list --branch develop` shows the deploy).
- Otherwise: switch to `develop`, pull, and run the app or tests locally. The report says "local develop at <sha>, not staging".

## 4. Verify and move

Delegate to `qa-engineer` with the acceptance criteria, the DoD, the PR diff summary and the target. It returns the criterion table and `QA: PASS` or `QA: FAIL`.

- **PASS:** `board.sh move <n> "Ready to deploy"`; this frees the ticket's place in the parallel set. Next: `/pm`.
- **FAIL:** `board.sh move <n> "In progress"`, post the defects on the issue. The fix goes on a new branch from `develop` (`feature/<n>-<slug>-fix`) with a new PR saying `Refs #<n>`. Next: `/lm-start`.

Post the QA report and the checkpoint comment from `CLAUDE.md` (stage: In QA) on the issue.
