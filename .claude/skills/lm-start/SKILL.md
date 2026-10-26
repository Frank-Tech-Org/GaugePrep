---
name: lm-start
description: Start or continue one LinguaMentor ticket. Check the parallel limit and overlap, create the branch in its own worktree from develop, route the work to the owning agents by Area, implement and test, commit, push and open the PR into develop.
argument-hint: <issue-number>
disable-model-invocation: true
---

# Start #$ARGUMENTS

One ticket, one branch, one worktree, one PR. Don't touch any other ticket in this session.

## 1. Load

```
.claude/scripts/board.sh info $ARGUMENTS
.claude/scripts/board.sh wip
gh issue view $ARGUMENTS --comments
git status --short && git branch --show-current
```

If the ticket is already In progress and has a checkpoint, continue from that checkpoint's `Next` line. Don't redo what its `Done` line lists.

## 2. Refuse (say which check failed, then stop)

- `wip` already lists the parallel limit (2, or 3 once CI exists; process doc §1) and this ticket is not one of them. A hotfix is the only exception.
- Overlap: a ticket in `wip` has the same Area with intersecting "Files and paths", blocks or is blocked by this one, or both change a migration chain, the lockfile, the OpenAPI contract or shared config. Name the clashing ticket and stop.
- The ticket is not in Ready or In progress.
- A blocker is not yet at Ready to deploy or Done.
- The ticket has no acceptance criteria or no Definition of Done section. Suggest `/pm refine $ARGUMENTS`.
- The working tree has uncommitted changes that don't belong to this ticket. Don't commit someone else's work; ask me to deal with them first.

## 3. Claim

```
.claude/scripts/board.sh move $ARGUMENTS "In progress"
git fetch origin develop
git worktree add ../lm-$ARGUMENTS -b feature/$ARGUMENTS-<short-slug> origin/develop
```
Work only inside `../lm-$ARGUMENTS`. If the worktree already exists, continue in it.

## 4. Build

Route by the Area field, using the table in `CLAUDE.md`. Each agent's prompt carries the full ticket text, the acceptance criteria and the latest checkpoint, because agents don't see this conversation.

- Decision tickets go to `tech-lead` or `pm`, and the output is an ADR in `docs/adr/` plus the index row.
- Work that needs a screen spec goes to `ux-designer` first.
- If the work reveals a missing dependency, stop and run `/pm block $ARGUMENTS <blocker>` instead of working around it.

## 5. Verify

Run the checks for what changed: `uv run pytest`, `pnpm check` and the Playwright run, whichever exist. Paste the commands and their result lines. Go through the ticket's Definition of Done and list any acceptance criterion or item that is not met. Don't open a PR on red checks; fix them, or stop and say why.

## 6. Commit, push, open the PR

Commit in logical steps as the work goes, never with `--amend`. Stage only this ticket's files: name the paths, and don't use `git add -A` when unrelated files are dirty.
```
git add <paths>
git commit -m "<type>(<area>): <subject>" -m "Refs #$ARGUMENTS"
.claude/scripts/push.sh feature/$ARGUMENTS-<short-slug>
gh pr create --base develop --title "<type>(<area>): <subject>" --body-file <body file in the scratchpad>
```
The PR body is a trimmed `.github/pull_request_template.md`: summary, `Refs #$ARGUMENTS`, what changed, the criteria and DoD checklist, and risks only when they're real. It has no "Generated with Claude Code" line or other tool signature.

Post the checkpoint comment from `CLAUDE.md` (stage: In progress) on the issue, with the PR link. Then continue with `/lm-review $ARGUMENTS`.
