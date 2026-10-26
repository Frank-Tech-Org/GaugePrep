---
name: pm
description: Run the LinguaMentor project manager. With no argument it reads the board, asks tech-lead for the technical read, and says what is done, what is next and in what order. Also triages Ideas, refines tickets with acceptance criteria and a Definition of Done, plans the sprint, records blockers, resolves owner decisions and resumes work.
argument-hint: "[triage | refine <n|all> | plan | block <n> <blocker> | decide | resume [n] | report | <free text>]"
disable-model-invocation: true
---

# PM: $ARGUMENTS

## State now

!`.claude/scripts/board.sh list || true`
!`.claude/scripts/board.sh wip || true`

Delegate everything below to the `pm` agent. It asks `tech-lead` for a technical read first (what is really done, hidden dependencies, risks, splits) and uses it as input.

## No argument: status and next

Reply in under 15 lines:
1. **Done** since last time (tickets that reached Ready to deploy or Done, merged PRs).
2. **In flight**: each ticket, its column, anything stuck.
3. **Next**: the set of tickets to start now (up to the parallel limit), in order, one line of why each, using the ordering rule and the overlap rule in the `pm` agent. Name the command: `/lm-start <n>`.
4. **Needs the owner**: open entries in `docs/DECISIONS.md`, owner-only PRs, anything waiting on money or access.

## `triage`

Classify every ticket in Ideas: Type, Area, Priority, Milestone, and a verdict (`Backlog`, `duplicate of #x`, `outside release 1`, `needs the owner`). Show the table. More than five tickets means wait for the owner's go-ahead. Then apply with `board.sh type|set`, `gh issue edit --milestone`, `board.sh move <n> Backlog`. Duplicates get a comment linking the original; closing is the owner's.

## `refine <n|all>`

For each ticket, rewrite the body in the ticket format from the `pm` agent: Context, Scope, Acceptance criteria, **Definition of Done**, Files and paths, Out of scope, Dependencies. Keep existing acceptance criteria that are sound (never untick a ticked one). Add the Definition of Done from the matching template in `.github/ISSUE_TEMPLATE/` with the non-applicable items deleted and every item measurable. Ask `tech-lead` to confirm the paths, dependencies and the two-day size. Split anything larger (new tickets go to Backlog, blocked links set with `board.sh block`). Edit with `gh issue edit <n> --body-file <file>`, then `board.sh move <n> Ready`. `all` or more than five tickets: state the scope and wait for the owner's go-ahead.

## `plan`

Fill the next sprint from Ready tickets in the ordering rule's order, with `board.sh sprint <n> "Sprint N"`. Sprints sit inside the milestones. Do not put a ticket in before its blockers.

## `block <n> <blocker>`

Check the blocker is not itself blocked by `<n>` (a cycle means split one). If the blocker doesn't exist, draft it, show the owner, create it after the go-ahead. Then `board.sh block <n> <blocker>`, `board.sh move <n> Ready`, a checkpoint on `<n>` saying what is done and where to resume. The blocker takes priority in the next ordering.

## `decide`

Walk the open entries in `docs/DECISIONS.md` one at a time: question, options, recommendation, cost of delay. Record the owner's answer in the file, create or unblock the tickets that follow, and ask `tech-lead` for an ADR when the answer is technical.

## `resume [n]`

State lives on GitHub and in git. Use the given ticket, otherwise the ticket(s) in flight (a hotfix first). Read `gh issue view <n> --comments`; the last `**Checkpoint**` comment is the instruction: `Next` is the task, `Done` is not redone, `Verified` is not rerun unless its code changed. Reply in three lines (ticket and column, last checkpoint, command to continue) and continue with `/lm-start`, `/lm-review` or `/lm-qa`.

## `report`

Weekly: tickets that reached Ready to deploy, milestone forecast from that velocity, defect clusters from failed QA, open decisions, next week's set. Under 25 lines.

## Rules

- Short. Verdict first, no recap.
- Only `pm` writes or edits issues. Post the checkpoint from `CLAUDE.md` on every ticket changed.
