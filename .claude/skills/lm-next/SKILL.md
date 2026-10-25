---
name: lm-next
description: Name the single LinguaMentor ticket to work on next, following the one-ticket rule and blockers. Read-only.
disable-model-invocation: true
---

# What's next

## Work slot

!`.claude/scripts/board.sh wip || true`

## Ready

!`.claude/scripts/board.sh list Ready || true`

## Do

Delegate to `delivery-manager` with the two lists above. It applies its "Choosing the next ticket" rules, using `.claude/scripts/board.sh info <n>` for the priority and blockers of each candidate.

Report three lines and nothing else:
```
Next: #<n> <title>
Why: <one line>
Run: /lm-start <n>    (or /lm-review, /lm-qa, /lm-refine, /lm-hotfix, /lm-plan-sprint)
```
