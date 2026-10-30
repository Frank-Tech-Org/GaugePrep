---
name: studio-reset-owner-decisions
description: Owner's standing decisions from the 2026-10 studio reset (free GitHub plan, board unchanged, weekly demo, real attacks on own systems, approved 18-agent roster)
metadata:
  type: project
---

The owner is a non-technical product owner who handed the build and marketing to the agency, and intervenes only on highly important matters. Approved the reset on 2026-10-29.

- Board stays at 8 columns; GitHub stays on the free plan (no branch protection, so governance is scripts, a bot account, a `main` alarm and an owner-only deploy).
- Weekly demo (Friday) with a security scorecard and a performance scorecard.
- Security, performance and optimization matter most, including real attacks, but only on systems we own (staging or a local copy).
- Team is the 17 agents in the approved plan plus the `cto` agent, added 2026-10-29 because sessions are not always open and no session should be special. tech-lead duties went to `cto` and `code-reviewer`, release-manager to `platform-engineer` (with notes by `content-marketer`, Done moves by `product-manager`), technical-writer to each area owner. No agent memory: lessons go into agent or rule files.
- Licences: only MIT or Apache skills are committed; Trail of Bits skills are CC-BY-SA and keep attribution; Remotion and claude-a11y-skill are not committed.
- No money for paid tools: the pre-release pentest is free tools run by `security-engineer` in Claude Code (D-3). Paid services run in production only; dev and staging are free or self-hosted (D-7), and all provider accounts in #9 are free plans.
- No tool signature anywhere: Claude Code attribution is switched off in the owner's user settings (2026-10-30).

**Why:** these were the owner's explicit answers; reopening them wastes their attention.
**How to apply:** don't propose paid GitHub features or board changes; see [[agents-commit-owner-merges]] and [[no-generated-with-claude-line]].
