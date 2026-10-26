---
name: lm-plan-sprint
description: Plan a LinguaMentor two-week sprint by choosing Ready tickets from the current milestone that fit one developer, in dependency order, and setting their Sprint field.
argument-hint: "[\"Sprint N\", default: the next sprint]"
disable-model-invocation: true
---

# Plan sprint: $ARGUMENTS

## Ready and Backlog now

!`.claude/scripts/board.sh list Ready || true`
!`.claude/scripts/board.sh list Backlog || true`

## 1. Propose

Delegate to `delivery-manager`, with `product-owner` consulted on priority. Paste both lists. It produces:

1. A table: order · # · title · area · size · blockers.
2. Load against capacity: ten working days for one developer. If it doesn't fit, say so in the first sentence.
3. What was left out, and why.
4. Backlog tickets that must be refined before the sprint can start them.
5. The one risk most likely to break the sprint.

## 2. Confirm

Show me the plan and wait for my go-ahead.

## 3. Apply

`.claude/scripts/board.sh sprint <n> "<Sprint N>"` for each ticket kept.

Finish with `/lm-next`.
