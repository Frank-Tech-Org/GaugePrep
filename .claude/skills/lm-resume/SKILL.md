---
name: lm-resume
description: Rebuild working context for LinguaMentor after /clear, a crash, a usage limit or a new day, from the board, the last checkpoint comment and git state, without exploring the repository.
argument-hint: "[issue-number, default: the ticket in the work slot]"
disable-model-invocation: true
---

# Resume

State lives on GitHub and in git, not in this conversation. Don't explore the repository.

## Where we are

!`.claude/scripts/board.sh wip || true`
!`git status --short && git branch --show-current || true`

## 1. Pick the ticket

Use `$ARGUMENTS` if it's given, otherwise the ticket in the slot. If the slot holds two (a hotfix and a paused ticket), take the hotfix. If the slot is empty, say so and suggest `/lm-next`.

## 2. Read the last checkpoint

```
gh issue view <n> --comments
```
The last comment that starts with `**Checkpoint**` is your instruction set:
- `Next` is the task.
- `Done` is what not to redo.
- `Verified` lists the checks not to rerun unless the code they cover has changed.

If there's no checkpoint, say so and read only the issue body.

## 3. Report in three lines, then continue

```
Resuming #<n> <title>  (column: <status>, branch: <branch>)
Last checkpoint: <date> by <agent>: <Next>
Continuing with: /lm-start | /lm-review | /lm-qa <n>
```
Then run that command's steps for this ticket.
