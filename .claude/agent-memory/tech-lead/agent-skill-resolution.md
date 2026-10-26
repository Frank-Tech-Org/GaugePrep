---
name: agent-skill-resolution
description: Recurring defect where agent frontmatter skills resolve only from ~/.claude/skills or uninstalled plugins; how to check them
metadata:
  type: project
---

This is a recurring defect pattern, seen in PR #43 on 2026-10-26.

Agent `skills:` entries name skills that resolve only from the owner's machine: `~/.claude/skills`, or a plugin installed at user scope but not enabled in the repo's `settings.json`. Some entries name skills that exist nowhere. In PR #43 these were dataviz (missing everywhere), claude-api (resolves only if Claude Code bundles it), frontend-design (user-scope plugin), and architecture-decision-record, domain-driven-design, system-design, twelve-factor, test-design and the git conventions skill (all user-home).

**Why:** agents are committed with the repo. On another machine or in CI, a skill that does not resolve leaves the agent without guidance while its prompt says "use only these".

**How to apply:** in any review that touches `.claude/agents/`, resolve every `skills:` entry against `.claude/skills/<name>/SKILL.md` first. Anything else must be vendored with provenance or enabled as a plugin in `settings.json`. See [[merge-gate-rulings]].
