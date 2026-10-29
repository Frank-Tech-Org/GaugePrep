---
name: lm-start
description: Start or continue the next LinguaMentor ticket. Works out which ticket from the board, branch and worktree, checks the environment allows it (parallel limit, overlap, blockers), builds it in its own worktree and opens the PR, or hands off to the right command.
argument-hint: "[#n to override]"
disable-model-invocation: true
---

# Start: $ARGUMENTS

One ticket, one branch, one worktree, one PR. No number is needed; `#n` only overrides the choice below.

## State now

!`.claude/scripts/board.sh list || true`
!`.claude/scripts/board.sh wip || true`
!`git branch --show-current`
!`git worktree list`

## 1. Find the ticket

In this order, first match wins:
1. `#n` in the arguments.
2. The current branch or worktree is `feature/<n>-*`: that ticket, continue it.
3. A ticket In progress with no worktree or an unfinished checkpoint: resume it (`gh issue view <n> --comments`, continue from the last checkpoint's `Next`; don't redo `Done`).
4. Otherwise ask `product-manager` for the next ticket in Ready (its ordering and overlap rules), and take the first it names.

## 2. Check the environment, hand off if it says no

Run `board.sh info <n>` and `gh issue view <n> --comments`. Stop at the first failure, say which, and name the command to run instead:

| Finding | Hand off to |
|---|---|
| Nothing in Ready | `/pm refine` if Backlog has tickets, else `/pm triage` |
| Ticket is not in Ready, In progress or In review, or has no acceptance criteria or Definition of Done | `/pm refine #<n>` |
| Parallel limit reached (2, or 3 once CI exists) and this ticket is not already in `wip`; a hotfix is exempt, and tickets labelled `owner-task` neither count nor are refused (one at a time) | `/lm-review` or `/lm-qa` for the ticket nearest the end |
| Overlaps another ticket in `wip` (same Area and intersecting paths, a blocking link, or a shared migration chain, lockfile, OpenAPI contract or config) | the next non-overlapping ticket from `product-manager`, else wait |
| A blocker is not at Ready to deploy or Done | `/lm-start #<blocker>`, or `/pm` if the blocker is not ready |
| Ticket has an open PR that is green with no CHANGES verdict on its head | `/lm-review` |
| Ticket has an open PR with red CI, conflicts or a `REVIEW: CHANGES` verdict | continue here on its branch: fix, commit, push, then `/lm-review` |
| Uncommitted changes that are not this ticket's | stop; ask the owner |

## 3. Claim

```
.claude/scripts/board.sh move <n> "In progress"
git fetch origin develop
git worktree add ../lm-<n> -b feature/<n>-<short-slug> origin/develop
```
Work only inside `../lm-<n>`. If the worktree exists, continue in it.

## 4. Build

Route by the Area field, using the table in `CLAUDE.md`. Each agent's prompt carries the full ticket text, the acceptance criteria and the latest checkpoint, because agents don't see this conversation.

- Decision tickets go to the CTO (this main session, technical) or `product-manager` (product), and the output is an ADR in `docs/adr/` plus the index row.
- Work that needs a screen spec goes to `product-designer` first.
- A missing dependency found mid-work: stop and run `/pm block <blocker>` instead of working around it.

## 5. Verify

Run the checks for what changed: `uv run pytest`, `pnpm check` and the Playwright run, whichever exist. Paste the commands and their result lines. Go through the Definition of Done and list any criterion or item not met. Don't open a PR on red checks.

## 6. Commit, push, open the PR

Commit in logical steps, never with `--amend`. Stage only this ticket's files by path.
```
git add <paths>
git commit -m "<type>(<area>): <subject>" -m "Refs #<n>"
.claude/scripts/push.sh feature/<n>-<short-slug>
```
Open the PR into `develop` with `gh api` (`gh pr create` fails on the classic-projects error). The body is a trimmed `.github/pull_request_template.md`: summary, `Refs #<n>`, what changed, the criteria and DoD checklist, risks only when real. No tool signature.

Post the checkpoint comment from `CLAUDE.md` (stage: In progress) with the PR link. Next: `/lm-review`.
