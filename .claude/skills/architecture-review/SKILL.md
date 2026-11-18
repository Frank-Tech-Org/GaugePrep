---
name: architecture-review
description: Reviews a design or architecture question against GaugePrep's invariants, stack and quality targets, and returns a ruling with the options compared. Use when a ticket stops on an architecture question, when a new dependency or module boundary is proposed, or for a technical Decision ticket.
---

# Architecture review

Follow the steps in order. Stop as soon as a step settles the question.

1. **Start from what exists.** Read `docs/architecture/system-architecture.md` and the ADRs on the topic. If they answer it, say so and stop. A deviation needs evidence, three options and the owner's yes.
2. **State each concern as a scenario:** stimulus, environment, response, measure. A concern with no measure is not a requirement yet: ask `product-manager` for the number or mark it unverified.
3. **Check the invariants.** Say pass or fail for each: `examcore` never imports Django; modules talk only through `public.py`; grades, scores and predictions are append-only with their versions; personal data lives only in `identity`; learner text reaches models as delimited data; async work goes through the outbox in the same transaction; migrations are expand-then-contract.
4. **Compare at least three options, including doing nothing.** For each: cost now, cost at ten times the load, what is hard to undo, and the evidence for every claim (a doc, source or a run). Label each claim verified or unverified.
5. **Put the scrutiny where it is hard to reverse:** schema, module boundaries, public API, auth model, data ownership. Rule on anything easy to reverse in one line.
6. **Name one automated check that fails if the ruling is broken** (an Import Linter contract, a test, a CI budget, a query-plan assertion). If none exists, state the risk.
7. **Give one revisit trigger:** a number or an event.
8. **List every assumption** about anything the brief calls closed, unavailable or already decided. Never invent a number: ask `product-manager` for it.
9. **Reply in at most ten lines, no more:** ruling, invariant results, options one line each, the check, the revisit trigger, what is unverified.

Stop and hand to `product-manager` for the owner: scoring or grading formulas, a production paid service, pricing, cutting scope. Destructive migrations and auth design are the CTO's (D-34).
