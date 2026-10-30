---
name: lm-hotfix
description: Fix an urgent LinguaMentor production bug from main. Finds the Urgent hotfix Bug on the board, pauses the tickets in flight with a checkpoint, branches hotfix/* from main, fixes and tests, and hands the owner the PR, tag and back-merge steps.
argument-hint: "[#n to override]"
disable-model-invocation: true
---

# Hotfix: $ARGUMENTS

Follow `docs/process/branching-and-release.md` section 8. This is the only thing allowed to pause tickets already in flight. No number is needed; `#n` only overrides the choice below.

## State now

!`.claude/scripts/board.sh list || true`
!`.claude/scripts/board.sh wip || true`
!`git describe --tags --abbrev=0 origin/main || true`
!`git branch --show-current`

## 1. Find the bug and check it

1. `#n` in the arguments.
2. The current branch is `hotfix/*`: its ticket, continue it.
3. Otherwise the Bug with priority Urgent and the `hotfix` label on the board.

| Finding | Hand off to |
|---|---|
| No such Bug, or no tag exists on `main` yet | nothing to hotfix: stop. A bug in untagged code is a normal ticket: `/pm`, then `/lm-next` |
| The bug is not in something already tagged on `main` | same: a normal ticket |
| A hotfix PR is already open | `/lm-next #<n>` (review) |

## 2. Pause the tickets in flight

For each ticket in `wip`, post the checkpoint comment from `CLAUDE.md`: "paused for hotfix #<n>", with what is done and the exact next step, naming roles, not commands. Leave its column. Save its work first: commit its paths on its branch as `wip(<area>): ...` with `Refs #<n>`, then push that branch with `.claude/scripts/push.sh <branch>`.

## 3. Branch from main

Next version is the last tag with PATCH + 1.
```
.claude/scripts/board.sh move <n> "In progress"
gh issue develop <n> -R LinguaMentor/linguamentor-v3 --base main --name hotfix/<version>-<short-slug>
git fetch origin hotfix/<version>-<short-slug>
git switch hotfix/<version>-<short-slug>
```

## 4. Fix

Route by the Area field, as `/lm-next` does. Change only what the bug needs, and add a test that fails without the fix. Commit (`fix(<area>): <subject>`, `Refs #<n>`), push the hotfix branch with `push.sh`, open the PR into `main` through `gh api`. Checkpoint Next: code-reviewer reviews the hotfix PR, with security-engineer if the area is sensitive; tell the owner to run `/lm-next #<n>`.

## 5. QA, then hand over to the owner

1. Run the staging deploy workflow on the hotfix branch; `qa-engineer` verifies the fix on staging. Staging returns to `stage` at the back-merge.
2. Tell the owner: merge the hotfix PR with a merge commit, tag `v<version>` on `main`, push the tag, publish the release with notes.
3. After the tag exists, open the back-merge PRs through `gh api`: `main` into `stage` first, then `main` into `develop`. Tell the owner to merge both with merge commits. Staging redeploys from `stage` after the first.
4. Then `board.sh move <n> Done`, close the issue (a PR into `main` doesn't close it, since `main` isn't the default branch), and tell the owner, in the reply only, to resume the paused tickets with `/lm-next`.

Post the checkpoint comment from `CLAUDE.md` (stage: Hotfix) on the issue, naming roles, not commands.
