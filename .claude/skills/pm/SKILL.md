---
name: pm
description: Run the LinguaMentor project manager. With no argument it reads the board, gets the cto agent's technical read, and says what is done, what is next and what needs the owner. "plan" sorts new ideas, writes acceptance criteria and a Definition of Done, and fills the sprint; "decide" resolves owner decisions; "report" posts the weekly delivery report to Notion.
argument-hint: "[plan [all | #n] | decide | report]"
disable-model-invocation: true
---

# PM: $ARGUMENTS

## State now

!`.claude/scripts/board.sh list || true`
!`.claude/scripts/board.sh wip || true`

First ask the `cto` agent for the technical read (skip it for `report` and `decide` with no technical entry). Then delegate everything below to the `product-manager` agent with that read pasted into its prompt. Subagents can't call each other, so this session carries the read from one to the other.

## No argument: status and next

Reply in under 15 lines:
1. **Done** since last time (tickets that reached Ready to deploy or Done, merged PRs).
2. **In flight**: each ticket, its column, anything stuck.
3. **Next**: the tickets to start now, up to the parallel limit, in order, one line of why each, by the ordering and overlap rules in the `product-manager` agent.
4. **Needs the owner**: open entries in `docs/DECISIONS.md`, owner-only PRs, `owner-task` tickets, anything waiting on money or access.

End with `/lm-next`, or `/pm plan` when Ready is empty.

## `plan [all | #n]`

One pass from Ideas to a filled sprint:
1. **Sort.** Every ticket in Ideas gets Type, Area, Priority, Milestone and a verdict: `Backlog`, `duplicate of #x` (a comment linking the original; the owner closes it), `outside release 1`, or `needs the owner`. Apply with `board.sh type|set`, `gh issue edit --milestone`, `board.sh move <n> Backlog`.
2. **Refine.** The Backlog and Ready tickets missing acceptance criteria or a Definition of Done, highest priority first: five by default, every one with `all`, just one with `#n`. Rewrite each body in the ticket format from the `product-manager` agent, keeping sound criteria (never untick a ticked one). The DoD comes from the matching `.github/ISSUE_TEMPLATE/*.yml` with the non-applicable items deleted and every item measurable. The technical read confirms paths, dependencies and the two-day size; split anything larger and link blockers with `board.sh block`. Edit with `gh issue edit <n> --body-file <file>`, then `board.sh move <n> Ready`.
3. **Sprint.** Fill the next sprint from Ready in the ordering rule's order with `board.sh sprint <n> "Sprint N"`, never before a ticket's blockers.

Show the table of changes first. More than five issues created or edited: state the scope and wait for the owner's go-ahead.

## `decide`

Walk the open entries in `docs/DECISIONS.md` one at a time: question, options, recommendation, cost of delay. Record the owner's answer in the file, create or unblock the tickets that follow, and the `cto` agent writes an ADR when the answer is technical.

## `report`

The weekly delivery report, posted by `product-manager` as one entry in the Notion database "Weekly demos" (data source `collection://b059f097-50cf-4c20-92d6-ce8d8d55a766`). The day before the Friday demo; any day on request. If an entry for this week exists, update it instead.

- **Properties:** Week ("Week of <Monday date>"), Demo date (that Friday), Status `Ready for demo`, Milestone (the current one), Delivered and Remaining (ticket counts in that milestone), Security, Performance, Needs you (one line), Links (the board).
- **Body, in plain words for a non-technical owner:**
  1. A table per open milestone: Released (Done), On staging (Ready to deploy), In progress (in flight), Not started (Ideas, Backlog, Ready), and a forecast date from the tickets reaching Ready to deploy per week over the last three weeks ("not enough data yet" before two weeks).
  2. **Delivered this week:** each ticket as what a learner or the owner can now do, with its PR link and a staging link to try it if one exists. Infrastructure work is grouped as one line: "Foundations".
  3. **Still to deliver:** the remaining tickets in order, with In progress first, and any risk to the forecast.
  4. **Security** and **Performance:** one line each from `security-engineer` and `performance-engineer` (open High or Critical findings; budgets held or breached with the ticket). "Not measured yet" until the tools exist.
  5. **Needs you:** decisions, merges and owner tasks.

Reply with the Notion link and three lines: delivered, remaining, needs the owner.

## Rules

- Short. Verdict first, no recap.
- Only `product-manager` writes or edits issues. Titles are plain phrases with no type prefix. Never comment on a ticket that has not started; post the checkpoint from `CLAUDE.md` only on tickets In progress, In review or In QA.
