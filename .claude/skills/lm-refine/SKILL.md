---
name: lm-refine
description: Refine one LinguaMentor Backlog ticket into Ready by writing context, scope, testable acceptance criteria, out of scope and dependencies, and splitting it if it is over two days.
argument-hint: <issue-number>
disable-model-invocation: true
---

# Refine #$ARGUMENTS

## 1. Load

```
.claude/scripts/board.sh info $ARGUMENTS
gh issue view $ARGUMENTS --comments
```
It must be in Backlog. If it's in Ideas, say to run `/lm-triage` first and stop.

## 2. Draft

Delegate to `product-owner`, pasting the issue text. It drafts the body from the matching template in `.github/ISSUE_TEMPLATE/`: Context, Scope, Acceptance criteria (checkboxes a QA engineer can verify), Out of scope and Dependencies.

Get help where the ticket needs it:
- `tech-lead`, for technical notes and dependencies, on any api, examcore, grading, voice, payments or infra ticket.
- `ux-designer`, for a short flow note, on anything a learner sees.
- `exam-content-author`, for exam rules, on anything that reproduces exam behaviour. Copy the rule into the ticket; don't link the spec.

Add a **Definition of Done** section: copy the list from the same template's "Definition of Done" field, and delete the items that don't apply to this ticket's area. Keep the wording measurable, and don't soften an item. The ticket must stand alone, so the items are written into it, not linked.

If anything needs my decision before the work can start, add it to `docs/DECISIONS.md` and record the ticket as blocked by it in the checkpoint.

If the work is over two days, propose the split as separate tickets and show me before creating them.

## 3. Write

```
gh issue edit $ARGUMENTS --body-file <draft file in the scratchpad>
```
For each dependency: `.claude/scripts/board.sh block $ARGUMENTS <blocker>`.

Then `.claude/scripts/board.sh move $ARGUMENTS Ready`.

## 4. Close out

Post the checkpoint comment from `CLAUDE.md` (stage: Refine). Report the acceptance criteria and blockers in a few lines.
