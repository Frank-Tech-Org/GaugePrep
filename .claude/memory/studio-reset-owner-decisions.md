---
name: studio-reset-owner-decisions
description: Owner's standing decisions from the 2026-10 studio reset (free GitHub plan, board unchanged, weekly demo, real attacks on own systems, approved roster)
metadata:
  type: project
---

The owner is a non-technical product owner who handed the build and marketing to the agency, and intervenes only on highly important matters. Approved the reset on 2026-10-29.

- Board stays at 8 columns; GitHub stays on the free plan (no branch protection, so governance is scripts, a bot account, a `main` alarm and an owner-only deploy).
- Weekly demo (Friday) with a security scorecard and a performance scorecard.
- Security, performance and optimization matter most, including real attacks, but only on systems we own (staging or a local copy).
- Team is 20 agents: the 17 in the plan plus `tech-lead`, `release-manager`, `technical-writer`, which were kept because the `/lm-*` commands depend on them.
- Licences: only MIT or Apache skills are committed; Trail of Bits skills are CC-BY-SA and keep attribution; Remotion and claude-a11y-skill are not committed.
- Pentest cap proposal is D-3 in `docs/DECISIONS.md`.

**Why:** these were the owner's explicit answers; reopening them wastes their attention.
**How to apply:** don't propose paid GitHub features or board changes; see [[agents-commit-owner-merges]] and [[no-generated-with-claude-line]].
