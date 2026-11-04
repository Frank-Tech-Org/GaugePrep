---
name: progressive-delivery-by-milestone
description: Build milestone by milestone; the build pack is reference material brought in only when its milestone starts, never tickets or code ahead of the foundation
metadata:
  type: feedback
---

Work moves milestone by milestone (M0 foundations, M1 accounts and content, M2 listening and reading, M3 writing, M4 speaking, M5 simulation, M6 learning path, M7 business, M8 launch hardening). Nothing is built, and no tickets are created, for a milestone whose foundation does not exist yet. Engineering agents take on more as the milestones move on: ai-engineer from M3, voice-engineer from M4.

Build pack 2 sits outside the repo at `/home/user/Frank-workspace/`, in the folder ending `-build-pack-2-20261030T082255Z-1-001` (named before the GaugePrep rename). Its parts are brought in by the ticket of the milestone that needs them: consent wording for anchors (anchor protocol section 10) in M0 with #14; content kit, specs, validator, ADR (as ADR-020) and content reviewer in M1; prompts, rubrics and anchors (D-4) and the TCFLE-8 licence in M3, with raters and volunteer learners recruited during M2 because of lead time; voices in M4.

**Why:** owner, 2026-10-30, after eight pack tickets were created during M0: "you can't jump from setting up the codebase to direct implementation when the foundation is not there".
**How to apply:** `/pm plan` pulls pack work in only when its milestone is next; until then the pack is read for cross-checks only. See [[cto-session-owns-delivery]].
