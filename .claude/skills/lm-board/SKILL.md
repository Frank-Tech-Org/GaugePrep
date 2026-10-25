---
name: lm-board
description: Review the LinguaMentor board, or one column of it, and say what needs attention next. Read-only.
argument-hint: "[column: Ideas | Backlog | Ready | \"In progress\" | \"In review\" | \"In QA\" | \"Ready to deploy\"]"
disable-model-invocation: true
---

# Board review: $ARGUMENTS

## Board now

!`.claude/scripts/board.sh list || true`

## Work slot

!`.claude/scripts/board.sh wip || true`

## Do

Delegate to `delivery-manager`. Paste the two lists above into its prompt, with the column asked for (empty means the whole board). It changes nothing on the board.

What to report for each column:

| Column | Report |
|---|---|
| Ideas | How many are waiting and which look most valuable. Suggest `/lm-triage` |
| Backlog | The next three to refine, by milestone then priority. Suggest `/lm-refine <n>` |
| Ready | Which are in the current sprint and which has its blockers resolved |
| In progress / In review / In QA | The one ticket in the slot, its last checkpoint's `Next` line (`gh issue view <n> --comments`) and the command to continue |
| Ready to deploy | The count, and whether a release is due (end of sprint, or something worth shipping now) |

Report a broken rule first: more than one ticket in the slot (a hotfix is the only allowed second one), a blocked ticket in the slot, or a ticket in Ready with no acceptance criteria.

Finish with one line: the command to run next.
