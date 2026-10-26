---
name: lm-hotfix
description: Fix an urgent LinguaMentor production bug from main. Pause the ticket in flight with a checkpoint, branch hotfix/* from main, fix and test, and hand the owner the PR, tag and back-merge steps.
argument-hint: <issue-number>
disable-model-invocation: true
---

# Hotfix #$ARGUMENTS

Follow `docs/process/branching-and-release.md` section 8. This is the only thing allowed to interrupt the work slot.

## 1. Check

```
.claude/scripts/board.sh info $ARGUMENTS
.claude/scripts/board.sh wip
git describe --tags --abbrev=0 origin/main
```
The ticket must be a Bug with priority Urgent and the `hotfix` label, and it must affect something already tagged on `main`. If not, it's a normal ticket: say so and stop.

## 2. Pause the ticket in flight

If `wip` shows a ticket, post the checkpoint comment from `CLAUDE.md` on it: "paused for hotfix #$ARGUMENTS", with what is done and the exact next step. Leave its column as it is.

Save its work first: commit the ticket's paths on its branch as `wip(<area>): ...` with `Refs #<n>` and the co-author trailer, then push that branch.

## 3. Branch from main

Next version: the last tag with PATCH + 1.
```
.claude/scripts/board.sh move $ARGUMENTS "In progress"
git switch main && git pull
git switch -c hotfix/<version>-<short-slug>
```

## 4. Fix

Route by the Area field, as `/lm-start` does. Change only what the bug needs, and add a test that fails without the fix. Commit (`fix(<area>): <subject>`, with `Refs #$ARGUMENTS` and the co-author trailer), push the hotfix branch, and open the PR into `main` (`gh pr create --base main`). Then run `/lm-review $ARGUMENTS`, with `security-engineer` included if the area is sensitive.

## 5. QA, then hand over to the owner

1. Once the staging deploy has run on the hotfix branch, `qa-engineer` verifies the fix there.
2. Then tell me:
   ```
   Merge the hotfix PR with a merge commit, then:
   git switch main && git pull && git tag -a v<version> -m "Hotfix v<version>" && git push origin v<version>
   gh release create v<version> --title "v<version>" --notes-file <notes>
   ```
3. After the tag exists, open the back-merge PRs: `gh pr create --base develop --head main --title "chore: back-merge v<version>"`, and one into each open `release/*` branch.
4. Then: `.claude/scripts/board.sh move $ARGUMENTS Done`, close the issue, and resume the paused ticket with `/lm-resume`.

Post the checkpoint comment from `CLAUDE.md` (stage: Hotfix) on the issue.
