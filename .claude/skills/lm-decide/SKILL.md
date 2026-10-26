---
name: lm-decide
description: Walk the open LinguaMentor decisions in docs/DECISIONS.md with options, a recommendation and the cost of delay, record the owner's answers, and unblock the affected tickets.
disable-model-invocation: true
---

# Pending decisions

## Open now

!`sed -n '/^## Open/,/^## Decided/p' docs/DECISIONS.md || true`

## 1. Present

Delegate to `product-owner`. It reads only the files and issues each decision references. If there are none, say "No open decisions" and stop.

For each decision, highest cost of delay first:
```
### D-<n>: <question>
Context: two sentences.
Options: A, <consequence> · B, <consequence>
Recommendation: <option>, because <one sentence>.
Cost of delay: <what is blocked and how it grows>
Reversible: yes | no
```
Reversible decisions get a shorter treatment: a recommendation, plus a note that we can change course cheaply.

Ask me for the answers with one question per decision, and wait for them.

## 2. Record

For each answer:
- Move the entry to `## Decided` with the date, the option and my reason, then commit on the current work branch. If there is none, on `chore/decisions-<date>`, pushed with a PR into `develop`.
- If it settles an architecture question, `tech-lead` writes the ADR.
- On each ticket it blocked, post a comment explaining the decision so a future agent understands it, and remove the blocker if the decision was the only one.
