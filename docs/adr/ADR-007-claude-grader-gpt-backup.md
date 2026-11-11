# ADR-007: Claude Sonnet 5.5 as the grader, Haiku 5.5 for light tasks, GPT-6.1 Sol as backup

- Status: Accepted
- Date: 2026-10-22

## Context

Calibration is only valid if the grading model cannot change underneath it. Costs must fit local prices.

## Decision

Grade with `claude-sonnet-5-5` ($2 and $10 per million input and output tokens), a pinned model ID that Anthropic states will not change, with no retirement before 28 September 2027 and at least 60 days' notice. Use `claude-haiku-5-5` for the examiner dialogue and light tasks, the Batch API for offline jobs, prompt caching for rubrics and anchors. Integrate `gpt-6.1-sol` as a backup that is used only after passing the release checks. Request zero data retention before production.

## Alternatives considered

- **GPT-6.1 Sol as primary:** Rejected as primary: same price, but its models page lists no pinned dated version.
- **Gemini models:** Rejected: no stated minimum notice before shutdown.

## Consequences

Each grader version (model, prompt, rubric, anchors, settings) passes the release checks before use; no silent fallback between providers.

## Sources

- https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions
- https://platform.claude.com/docs/en/about-claude/model-deprecations
- https://platform.claude.com/docs/en/about-claude/pricing
- https://developers.openai.com/api/docs/models
