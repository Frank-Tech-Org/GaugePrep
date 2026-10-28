---
name: check-scope-gaps
description: Recurring defect - lint/type/test tool configs silently omit a uv workspace member (voice); verify by planting a bad file
metadata:
  type: feedback
---

When reviewing check tooling, plant a deliberate error in every workspace member (backend, packages/examcore, voice, apps/web) and confirm `pnpm check` goes red. PR #45 (2026-10-26) left `voice` out of mypy `files`, and only a planted type error showed it.

**Why:** a green run on a nearly empty tree proves nothing about coverage. Gaps only show up later, as unchecked code.
**How to apply:** for any change to ruff, mypy, pytest, Import Linter, ESLint, tsc or Prettier scope, run a planted-error script from the scratchpad (git with `$` is guard-blocked inline, see [[guard-hook-review-workarounds]]).
