---
name: pm
description: Run the GaugePrep project manager. With no argument it reads the board, gets the cto agent's technical read, and says what is done, what is next and what needs the owner. "plan" sorts new ideas, writes acceptance criteria and a Definition of Done, and fills the sprint; "decide" resolves owner decisions; "report" posts the weekly delivery report to Notion.
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
4. **Release due**, only when the rule in `docs/process/branching-and-release.md` section 7 holds: the key feature completed, or the end of the sprint, and the command `/lm-release`.
5. **Needs the owner**: open entries in `docs/DECISIONS.md`, owner-only PRs, `owner-task` tickets, anything waiting on money or access.

End with `/lm-next`, or `/pm plan` when Ready is empty.

## `plan [all | #n]`

One pass from Ideas to a filled sprint:
1. **Sort.** Every ticket in Ideas gets Type, Area, Priority, Milestone and a verdict: `Backlog`, `duplicate of #x` (a comment linking the original; the owner closes it), `outside release 1`, or `needs the owner`. Apply with `board.sh type|set`, `gh issue edit --milestone`, `board.sh move <n> Backlog`.
2. **Refine.** The Backlog and Ready tickets missing acceptance criteria or a Definition of Done, highest priority first: five by default, every one with `all`, just one with `#n`. Rewrite each body in the ticket format from the `product-manager` agent, keeping sound criteria (never untick a ticked one). The DoD comes from the matching `.github/ISSUE_TEMPLATE/*.yml` with the non-applicable items deleted and every item measurable. The technical read confirms where it lands, dependencies and the two-day size; split anything larger and link blockers with `board.sh block`. Edit with `gh issue edit <n> --body-file <file>`, then `board.sh move <n> Ready`.
3. **Sprint.** Fill the next sprint from Ready in the ordering rule's order with `board.sh sprint <n> "Sprint N"`, never before a ticket's blockers.

Show the table of changes first. More than five issues created or edited: state the scope and wait for the owner's go-ahead.

## `decide`

Walk the open entries in `docs/DECISIONS.md` one at a time: question, options, recommendation, cost of delay. Record the owner's answer in the file, create or unblock the tickets that follow, and the `cto` agent writes an ADR when the answer is technical.

## `report`

The weekly delivery report, posted by `product-manager` as one entry in the Notion database "Weekly demos" (data source `collection://b059f097-50cf-4c20-92d6-ce8d8d55a766`). The day before the Friday demo; any day on request. If an entry for this week exists, update it instead.

The owner reads it for product progress only. It speaks of features a learner can use, never of tickets, issue or PR numbers, merges, branches, columns or agents. Decisions stay in `docs/DECISIONS.md`; one waiting on the owner appears only as a risk to the launch date.

The unit is the 13 key features of release 1, the functional requirements in `docs/product/PRD.md` §8.1 to §8.13. A feature counts as delivered once a learner (or the owner, for internal tools) can use all of it on staging or in production, at every screen size; part of a feature is reported as "Partly usable" with what works.

- **Properties:** Week ("Week of <Monday date>"), Demo date (that Friday), Status `Ready for demo`, Features delivered, Features to deliver, Security, Performance, Try it (the staging link once staging exists).
- **Body, in plain words:**
  1. A callout: "Release 1: N of 13 key features delivered", one sentence on the week, and the launch forecast from features delivered per week over the last three ("forecast once two weeks of feature delivery are measured" before that).
  2. **Delivered this week:** each feature as what a learner can now do, and how to try it on staging, on a phone or a computer. Groundwork with nothing to use is one line.
  3. **Key features of release 1:** one row per feature: Delivered, Partly usable, Being built or Not started, and what works today.
  4. **Next week:** the features or parts expected, in learner terms.
  5. **Launch readiness:** the six release 1 launch conditions in PRD §13.2, each with its measured state.
  6. **Performance:** measured numbers against the targets (page load on 3G under 3 s, writing results under 30 s, speaking under 60 s, examiner reply under 2.5 s, simulation under 15 MB), from `performance-engineer`.
  7. **Security:** serious issues open (target zero) and the date of the last attack test on staging, from `security-engineer`.
  8. **Risks to the launch date:** only what moves it, including a decision waiting on the owner, named in one line.

Reply with the Notion link and one line: features delivered against features to deliver.

## Rules

- Short. Verdict first, no recap.
- Only `product-manager` writes or edits issues. Titles are plain phrases with no type prefix. Never comment on a ticket that has not started; post the checkpoint from `CLAUDE.md` only on tickets In progress, In review or In QA.
