---
name: lm-qa
description: QA a merged LinguaMentor ticket on staging (or a local build of develop until staging exists). Pass moves it to Ready to deploy and frees the slot; fail sends it back to In progress with defects.
argument-hint: <issue-number>
disable-model-invocation: true
---

# QA #$ARGUMENTS

## 1. Check it's merged

```
gh pr list --state merged --search "Refs #$ARGUMENTS in:body" --json number,title,mergedAt,baseRefName,mergeCommit
```
The PR must be merged into `develop`. If not, say so and stop.

```
.claude/scripts/board.sh move $ARGUMENTS "In QA"
gh issue view $ARGUMENTS
```

## 2. Pick the target

- If staging exists: confirm the last staging deploy (`gh run list --branch develop`) includes the merge commit. If the deploy hasn't finished, wait.
- If staging doesn't exist yet: `git switch develop && git pull`, then run the app or tests locally. The report must say "local develop at <sha>, not staging".

## 3. Verify

Delegate to `qa-engineer`, with the acceptance criteria, the PR diff summary and the target. It returns the criterion table and a `QA: PASS` or `QA: FAIL` verdict.

## 4. Move

- **PASS:** run `.claude/scripts/board.sh move $ARGUMENTS "Ready to deploy"`. The slot is now free. Finish with `/lm-next`.
- **FAIL:** run `.claude/scripts/board.sh move $ARGUMENTS "In progress"` and post the defects on the issue. The fix goes on a new branch from `develop` (`feature/$ARGUMENTS-<slug>-fix`), which the agents commit, push and open a new PR for, saying `Refs #$ARGUMENTS`. Continue with `/lm-start $ARGUMENTS`.

Post the QA report and the checkpoint comment from `CLAUDE.md` (stage: In QA) on the issue.
