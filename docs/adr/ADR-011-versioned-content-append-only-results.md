# ADR-011: Versioned content and append-only results

- Status: Accepted
- Date: 2026-10-22

## Context

Every prediction must be reproducible from the versions that produced it (PRD PRE-4).

## Decision

Store items, prompts, lessons, forms, exam rules, cut points, combination models and grader versions as immutable versions. Store grades, paper scores and predictions as append-only records with all versions used; database privileges prevent updates and deletes by the application. Keep personal data only in identity.

## Alternatives considered

- **Editable records with history tables:** Rejected: history can be skipped or diverge; harder to prove what produced a result.

## Consequences

More rows, handled by monthly partitioning of the largest tables. Deletion requests remove identity and free text while anonymous results remain.
