---
name: lm-next
description: Move GaugePrep work forward until something only the owner can do. Works out from the board, branches, worktrees, open PRs and checkpoints which ticket is nearest done and runs it through build, local review, fix, push, PR, merge and QA, then starts every other free ticket. Also records a blocker.
argument-hint: "[#n to override] [block <#blocker or text>]"
disable-model-invocation: true
---

# Next: $ARGUMENTS

Run steps in order, ticket after ticket, until something only the owner can do or a blocker, posting a checkpoint after each step. Stop for: a merge into `stage` or `main`, a tag, an account, money, a ruling reserved in `CLAUDE.md` "Who decides", an owner approval a sensitive PR needs, an owner-only file, or three rounds of review. No number is needed; `#n` only overrides the choice below. State lives on GitHub and in git: the last `**Checkpoint**` comment on a ticket says what is done (never redo `Done`, never rerun `Verified` unless its code changed) and what comes next.

## State now

!`.claude/scripts/board.sh list || true`
!`.claude/scripts/board.sh wip || true`
!`git branch --show-current`
!`git worktree list`
!`gh api "repos/Frank-Tech-Org/GaugePrep/pulls?state=open" --jq '.[] | "#\(.number) \(.head.ref) -> \(.base.ref) \(.head.sha)"' || true`
!`gh api "repos/Frank-Tech-Org/GaugePrep/pulls?state=closed&base=develop&per_page=10" --jq '.[] | select(.merged_at) | "merged #\(.number) \(.head.ref)"' || true`

## 1. Pick the ticket

First match wins:
1. `#n` in the arguments (ticket or PR number).
2. A hotfix in flight: stop and name `/lm-hotfix`.
3. The current branch or worktree is `feature/<n>-*`: that ticket.
4. The ticket in flight nearest the end: In QA, then In review, then In progress. An open `chore/*` PR with no verdict on its head counts as In review, with no ticket.
5. A free ticket in Ready (no open blocker, no overlap with one in flight): ask `product-manager`, with the `cto` agent's technical read, for every such ticket, and start them together, each builder in its own worktree and background. An `owner-task` ticket is handed to the owner, not built.
6. Nothing to do: name `/pm`.

## 2. Pick the step

`board.sh info <n>` and `gh issue view <n> --comments`, then the first row that matches:

| State | Step |
|---|---|
| `block` in the arguments | Block (§7) |
| No acceptance criteria or Definition of Done | stop, name `/pm plan #<n>` |
| A blocker not yet at Ready to deploy or Done | Block (§7) with that blocker |
| Uncommitted changes that aren't this ticket's (the owner's edits on this ticket's branch are this ticket's) | stop, ask the owner |
| No commits on the branch yet | Build (§3) |
| Commits on the branch, no PR yet, or a fix not yet reviewed | Review (§4), then push and open the PR (§3 end) |
| Open PR with red CI, conflicts, or `REVIEW: CHANGES` on its head | Fix (§3, on its branch), review the fix locally, push |
| Open PR, CI green or absent, no verdict on its head | Review (§4) |
| Open PR with `REVIEW: PASS <head sha>` and green CI | Merge (§5) |
| PR merged, ticket In review or In QA | QA (§6) |

## 3. Build or fix

A ticket that changes no repository file (an owner task, research, a decision recorded only on the ticket) gets no branch and no PR: the agent works on the ticket and posts its result there. A Decision ticket that writes an ADR changes a file, so it gets both.

New ticket: claim it and create the branch from the ticket, so the branch and the PR opened from it show in the ticket's Development panel:
```
.claude/scripts/board.sh move <n> "In progress"
gh issue develop <n> -R Frank-Tech-Org/GaugePrep --base develop --name feature/<n>-<short-slug>
git fetch origin feature/<n>-<short-slug>
```
**Where to work.** Build and fix in the owner's checkout, so the owner sees the work in the editor: `git switch <branch>` there. Switch only from a clean tree; otherwise stop and ask the owner. If the checkout holds another ticket in flight, or the branch is already in a worktree, work in `../lm-<n>` instead (`git worktree add ../lm-<n> <branch>`, or the existing one). The owner's edits on the ticket's branch, committed or not, are part of the ticket: read them before continuing, commit them with the ticket and never discard them.

Route by the Area field with the table in `CLAUDE.md`. Each agent's prompt carries the full ticket, its criteria and DoD, the last checkpoint and, for a fix, the review findings or failing checks, because agents don't see this conversation. A screen with no spec goes to `product-designer` first. Decision tickets go to the `cto` agent (technical) or `product-manager` (product) and produce an ADR in `docs/adr/` with its index row. An agent that stops on an architecture question or wants a new dependency gets the `cto` agent's answer in its next prompt. A missing dependency found mid-work is a Block (§7), never a workaround.

Run the checks for what changed (`uv run pytest`, `pnpm check`, Playwright, whichever exist) and the mechanical review script, and keep the result lines. Go through the DoD and name anything unmet. Never push red.

Commit in logical steps, never `--amend`, staging only this ticket's paths: `git commit -m "<type>(<area>): <subject>" -m "Refs #<n>"`. A fix commit is `fix(<area>): address review on #<n>`. Do not push yet: the review (§4) reads the local diff first. When it says `REVIEW: PASS`, push once with `.claude/scripts/push.sh <branch>` and open the PR into `develop` ready for review, not as a draft (a draft runs CI too), with `gh api` (`gh pr create` fails on the classic-projects error). The body is a trimmed `.github/pull_request_template.md`: summary, `Refs #<n>`, what changed, the checklist. Criteria stay on the ticket. Write it in the developer's voice per `.claude/rules/writing.md`: no list of every file, no `.claude`, agent or command names. Post the verdict as the PR's first comment, ending with `REVIEW: PASS <full head sha>`. After every later commit on the branch, rewrite the body to match the diff at the new head. Checkpoint stage: In progress.

## 4. Review

`board.sh move <n> "In review"`. Before the first push the review reads the local diff (`git diff develop...HEAD`) and the ticket; after a push it also reads the PR body and the CI runs (`gh run list --commit <head sha>`; the agent token can't read check runs), and a PR body that misses commits is rewritten first (§3). Run, with the criteria in each prompt, one reviewer at a time:
- always `code-reviewer`, once;
- the reviewers for the ticket's Area from `CLAUDE.md`;
- `security-engineer` for authentication, sessions, payments, `identity`, migrations, append-only tables, AI prompts, the internal API or infrastructure exposure;
- `privacy-compliance` if personal data collected, kept, logged or sent changes;
- `product-designer` if what a learner sees changes;
- `performance-engineer` for a learner page's bundle or media, a hot query, or the grading or voice path;
- `qa-engineer` for the claims check if learner-facing claims or copy change.

Before any PASS, each reviewer ticks every acceptance criterion and DoD item in its area against the diff; a criterion the diff does not meet is `REVIEW: CHANGES`. The verdict is one comment in the same voice, at most 10 lines plus findings, verdict first: a verdict per reviewer, fixes as `label: file:line - problem - fix`, unmet criteria and unticked DoD items by name. The last line alone is `REVIEW: PASS <full head sha>` or `REVIEW: CHANGES <full head sha>`. A new commit makes it stale. On CHANGES, fix on the branch and review again locally; after three rounds, block the ticket with what was tried and move on. Checkpoint stage: In review.

## 5. Merge

- A hotfix into `main`, or a PR touching the guard hook, settings, workflows, the git hooks or any script in `.claude/scripts/`: tell the owner it is ready to merge.
- A PR that touches authentication, payments, personal data, migrations, append-only tables, scoring formulas or owner-only files needs `frankkefoueg`'s approval of the head sha (`gh api repos/Frank-Tech-Org/GaugePrep/pulls/<pr>/reviews`). Without it, put `Approve PR #<pr>: <PR title>` with the link and one line on what it does for the learner under Needs you, and go on to the next ticket. Any other PR needs no approval.
- Otherwise, with `REVIEW: PASS <head sha>` and green CI, run `.claude/scripts/merge.sh <pr>`. If it refuses, fix what it names; never merge another way. Until the owner applies the staged merge script, it may still ask for an approval on every PR: then list it under Needs you.

Once the PR is merged, by the script or the owner: if the owner's checkout is on its branch, switch it to `develop` and pull (clean tree only, otherwise stop and ask the owner); if the branch had a worktree, remove it.

## 6. QA

Skip if the merged PR has no ticket. `board.sh move <n> "In QA"`. The target is dev once the deploy of `develop` includes the merge commit (`gh run list --branch develop`; if not yet, wait and rerun), otherwise a local build of `develop`, reported as "local develop at <sha>, not dev". `qa-engineer` gets the criteria, the DoD, the diff summary and the target, and returns the criterion table and `QA: PASS` or `QA: FAIL`.
- PASS: `board.sh move <n> "Ready to deploy"`. This frees its place.
- FAIL: `board.sh move <n> "In progress"` and post the defects; reopen the issue if its merge closed it; the fix goes on `feature/<n>-<slug>-fix`, created from the ticket with `gh issue develop` and checked out as in §3 (Where to work), with a new PR saying `Refs #<n>`.

Post the QA report. Checkpoint stage: In QA.

## 7. Block

The blocker is a `#number`, or free text that `product-manager` drafts as a ticket and creates after the owner's go-ahead. A blocker that is itself blocked by this ticket means one must be split. `product-manager` runs `board.sh block <n> <blocker>` and `board.sh move <n> Ready`. The checkpoint says what is done and where to resume; the blocker is ordered first next time.

## End

Post the checkpoint comment from `CLAUDE.md` on the ticket, naming roles, not commands. Then start the next free ticket; stop only at an owner stop or a blocker. The reply to the owner is at most 10 lines:

```text
Done: <tickets moved, in words>
Needs you: <approvals, merges, accounts, rulings, with the PR link>, or nothing
Next: <the command to run>
```

The next command is `/lm-next` again, `/lm-release` when a key feature is complete, or `/pm` when nothing is left to move.
