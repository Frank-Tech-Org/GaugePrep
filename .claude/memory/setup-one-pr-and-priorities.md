---
name: setup-one-pr-and-priorities
description: Owner's standing rules for setup work - one branch and PR until finished, stick to what was proposed, free tools only, robustness first
metadata:
  type: feedback
---

- A setup effort (team, commands, hooks, process) stays on one `chore/*` branch and one PR until it is finished; later fixes are commits on it, never a new PR.
- Once a plan is approved, deliver exactly what it said (the 17-agent roster went to 20 and the owner pushed back). Wiping existing setup to match the plan is fine.
- Dev and staging use only free plans or services self-hosted on the owner's machine, which is powerful enough; paid services (Anthropic, ElevenLabs, Twilio, Hetzner) are for production only (D-7, 2026-10-30). Before relying on a free plan, research whether its limits (usage, licence, commercial terms) cover the work; if not, find the best free or self-hosted alternative and either adopt it and report it, or open a decision. D-8: dev and staging grading uses the best self-hosted model available.
- Changes not tied to a ticket go on the currently open setup PR's branch, never on `develop`; every other branch and PR links to a ticket.
- Robustness, efficiency, maintainability and quality are the priorities throughout.

**Why:** owner's message on 2026-10-29 after the roster drifted and a paid pentest cap was proposed.
**How to apply:** check the approved plan before adding or keeping a role, tool or PR; see [[studio-reset-owner-decisions]].
