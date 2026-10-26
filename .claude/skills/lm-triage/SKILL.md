---
name: lm-triage
description: Triage the Ideas column of the LinguaMentor board. Classify each ticket, flag duplicates and out-of-scope ideas, and move accepted ones to Backlog.
argument-hint: "[issue numbers, default: every ticket in Ideas]"
disable-model-invocation: true
---

# Triage: $ARGUMENTS

## Ideas column now

!`.claude/scripts/board.sh list Ideas || true`

## 1. Classify

Delegate to `product-owner`. For each ticket (only the numbers in `$ARGUMENTS` if given), it reads `gh issue view <n>` and proposes:

| # | Title | Type | Area | Priority | Milestone | Verdict |
|---|---|---|---|---|---|---|

The verdict is one of: `Backlog`, `duplicate of #x`, `outside release 1` (stays in Ideas with a one-line reason), or `needs the owner` (a question).

## 2. Confirm

Show me the table. If it changes more than five tickets, wait for my go-ahead before writing anything.

## 3. Apply

For each accepted ticket:
```
.claude/scripts/board.sh type <n> <Type>
.claude/scripts/board.sh set <n> Area <area>
.claude/scripts/board.sh set <n> Priority <priority>
gh issue edit <n> --milestone "<milestone title>"
.claude/scripts/board.sh move <n> Backlog
```
On duplicates, comment the link to the original. Closing is mine.

## 4. Report

The final table, then one line: which Backlog ticket to refine first, as `/lm-refine <n>`.
