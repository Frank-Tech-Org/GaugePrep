---
name: ignore-other-repos
description: "Do not read or copy conventions from the GaugePrep v1/v2 repos or the old board; design from this project's docs and general expertise"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1dd11a6b-59c4-4019-9fd0-8b8a194a0087
  modified: 2026-10-23T08:21:30.893Z
---

Do not look at other repositories (the product's v1 and v2 repositories) or the old board (#2) for conventions, labels, epics or structure. Build everything for this repository from its own documents and from sound professional practice.

**Why:** While setting up issue hierarchy I read v2's epics and labels to copy their format; the user said I have no concern with the other repo and that my work should come from my own experience, adapted to this project.

**How to apply:** When a convention is needed (issue hierarchy, templates, board design), decide it from the PRD, architecture, `pm.md` and standard practice, and say it is my design. Do not run `gh` against other repos. See [[pm-role-github-setup]] and [[agents-commit-owner-merges]].
