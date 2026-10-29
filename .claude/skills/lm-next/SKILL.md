---
name: lm-next
description: Move LinguaMentor work one step forward. Works out from the board, branches, worktrees, open PRs and checkpoints which ticket is nearest done and what its next step is (build, fix, review, merge, QA), does that step, or starts the next ticket when there is room. Also records a blocker.
argument-hint: "[#n to override] [block <#blocker or text>]"
disable-model-invocation: true
---

# Next: $ARGUMENTS

One step per run, on one ticket, then a checkpoint. No number is needed; `#n` only overrides the choice below. State lives on GitHub and in git: the last `**Checkpoint**` comment on a ticket says what is done (never redo `Done`, never rerun `Verified` unless its code changed) and what comes next.

## State now

!`.claude/scripts/board.sh list || true`
!`.claude/scripts/board.sh wip || true`
!`git branch --show-current`
!`git worktree list`
!`gh api "repos/LinguaMentor/linguamentor-v3/pulls?state=open" --jq '.[] | "#\(.number) \(.head.ref) -> \(.base.ref) \(.head.sha)"' || true`
!`gh api "repos/LinguaMentor/linguamentor-v3/pulls?state=closed&base=develop&per_page=10" --jq '.[] | select(.merged_at) | "merged #\(.number) \(.head.ref)"' || true`

## 1. Pick the ticket

First match wins:
1. `#n` in the arguments (ticket or PR number).
2. A hotfix in flight: stop and name `/lm-hotfix`.
3. The current branch or worktree is `feature/<n>-*`: that ticket.
4. The ticket in flight nearest the end: In QA, then In review, then In progress. An open `chore/*` PR with no verdict on its head counts as In review, with no ticket.
5. Fewer tickets in flight than the limit (2, or 3 once CI runs on every PR; `owner-task` tickets don't count): ask `product-manager`, with your technical read (see `/pm`), for the next non-overlapping ticket in Ready. An `owner-task` ticket is handed to the owner, not built.
6. Nothing to do: name `/pm`.

## 2. Pick the step

`board.sh info <n>` and `gh issue view <n> --comments`, then the first row that matches:

| State | Step |
|---|---|
| `block` in the arguments | Block (§7) |
| No acceptance criteria or Definition of Done | stop, name `/pm plan #<n>` |
| A blocker not yet at Ready to deploy or Done | Block (§7) with that blocker |
| Uncommitted changes that aren't this ticket's | stop, ask the owner |
| No PR yet | Build (§3) |
| Open PR with red CI, conflicts, or `REVIEW: CHANGES` on its head | Fix (§3, on its branch) |
| Open PR, CI green or absent, no verdict on its head | Review (§4) |
| Open PR with `REVIEW: PASS <head sha>` | Merge (§5) |
| PR merged, ticket In review or In QA | QA (§6) |

## 3. Build or fix

New ticket: claim it and work only inside its worktree (continue in it if it exists):
```
.claude/scripts/board.sh move <n> "In progress"
git fetch origin develop
git worktree add ../lm-<n> -b feature/<n>-<short-slug> origin/develop
```

Route by the Area field with the table in `CLAUDE.md`. Each agent's prompt carries the full ticket, its criteria and DoD, the last checkpoint and, for a fix, the review findings or failing checks, because agents don't see this conversation. A screen with no spec goes to `product-designer` first. Decision tickets go to the CTO (technical) or `product-manager` (product) and produce an ADR in `docs/adr/` with its index row. A missing dependency found mid-work is a Block (§7), never a workaround.

Run the checks for what changed (`uv run pytest`, `pnpm check`, Playwright, whichever exist) and paste the result lines. Go through the DoD and name anything unmet. Never push red.

Commit in logical steps, never `--amend`, staging only this ticket's paths: `git commit -m "<type>(<area>): <subject>" -m "Refs #<n>"`, then `.claude/scripts/push.sh <branch>`. A fix commit is `fix(<area>): address review on #<n>`. Open the PR into `develop` with `gh api` (`gh pr create` fails on the classic-projects error); the body is a trimmed `.github/pull_request_template.md`: summary, `Refs #<n>`, what changed, the criteria and DoD checklist. Checkpoint stage: In progress.

## 4. Review

`board.sh move <n> "In review"`. Read the diff (`gh pr diff <pr>`, or `gh api .../pulls/<pr>/files --paginate`), the checks and the ticket. Run, with the criteria in each prompt:
- always `code-reviewer`, once;
- the reviewers for the ticket's Area from `CLAUDE.md`;
- `security-engineer` for authentication, sessions, payments, `identity`, migrations, append-only tables, AI prompts, the internal API or infrastructure exposure;
- `privacy-compliance` if personal data collected, kept, logged or sent changes;
- `product-designer` if what a learner sees changes;
- `performance-engineer` for a learner page's bundle or media, a hot query, or the grading or voice path;
- `qa-engineer` for the claims check if learner-facing claims or copy change.

Each checks the DoD items in its area. Post one PR comment, at most 10 lines plus findings, verdict first: a verdict per reviewer, fixes as `file:line — problem — fix`, unmet criteria and unticked DoD items by name. The last line alone is `REVIEW: PASS <full head sha>` or `REVIEW: CHANGES <full head sha>`. A new commit makes it stale. After three rounds of CHANGES, stop and ask the owner. Checkpoint stage: In review.

## 5. Merge

- A hotfix into `main`, or a PR touching the guard hook, settings, workflows, `push.sh` or `merge.sh`: tell the owner it is ready to merge.
- Otherwise the CTO runs `.claude/scripts/merge.sh <pr>`. While no CI exists it refuses and the owner merges. Any other refusal: fix what it names; never merge another way.

## 6. QA

Skip if the merged PR has no ticket. `board.sh move <n> "In QA"`. The target is staging once the deploy of `develop` includes the merge commit (`gh run list --branch develop`; if not yet, wait and rerun), otherwise a local build of `develop`, reported as "local develop at <sha>, not staging". `qa-engineer` gets the criteria, the DoD, the diff summary and the target, and returns the criterion table and `QA: PASS` or `QA: FAIL`.
- PASS: `board.sh move <n> "Ready to deploy"`. This frees its place.
- FAIL: `board.sh move <n> "In progress"` and post the defects; the fix goes on `feature/<n>-<slug>-fix` from `develop` with a new PR saying `Refs #<n>`.

Post the QA report. Checkpoint stage: In QA.

## 7. Block

The blocker is a `#number`, or free text that `product-manager` drafts as a ticket and creates after the owner's go-ahead. A blocker that is itself blocked by this ticket means one must be split. `product-manager` runs `board.sh block <n> <blocker>` and `board.sh move <n> Ready`. The checkpoint says what is done and where to resume; the blocker is ordered first next time.

## End

Post the checkpoint comment from `CLAUDE.md` on the ticket, then name the next command: `/lm-next` again, or `/pm` when nothing is left to move.
