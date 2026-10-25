---
name: workflow-redesign-from-friend-template
description: "One-ticket lifecycle with department agents and /lm-* commands, adapted for LinguaMentor from a friend's OpenRisk setup; the owner's decisions on it"
metadata:
  node_type: memory
  type: project
  originSessionId: 7d0fe753-8c22-4a99-91d8-108bdd9024c7
  modified: 2026-10-24T19:58:45.070Z
---

On 2026-10-24 I built a new delivery workflow for linguamentor-v3. It is described in `docs/process/branching-and-release.md` and `CLAUDE.md`, with 19 agents in `.claude/agents/<department>/`, 12 `/lm-*` skills, `.claude/scripts/board.sh` and a guard hook.

The source material was a friend's setup, untracked in the repo root: `prompt` (their EduTrack/Acavira brief), the original `Branching & Release Workflow Proposal.md` and `claude_template_as_example_to_update_claude/` (their OpenRisk `.claude`).

Owner decisions:
- The work slot is freed at Ready to deploy, not Done. Releases batch Ready-to-deploy tickets.
- Full company team (19 agents).
- The process doc lives in `docs/process/`.
- Every open ticket goes back to Ideas when the board is migrated.
- Columns: Ideas, Backlog, Ready, In progress, In review, In QA, Ready to deploy, Done. The owner asked for Backlog after Ideas.

My own design calls:
- Release branches are cut from `develop` with no cherry-picking (one ticket in flight means `develop` holds only work that passed QA).
- No `stage` branch.
- Conventional Commits, with `Refs #n` rather than `Closes`.

**Why:** The owner said the brief, the proposal and the template are a friend's approach, shared so it can be adapted. The EduTrack steps (v1.0.0 release, platform redesign v2, acavira tags) do not apply.

**How to apply:** Write content for LinguaMentor's stack and never copy OpenRisk agent text or memories. This is the only allowed exception to [[ignore-other-repos]]. The no-commit rule still holds, and the guard hook now enforces it ([[agents-commit-owner-merges]]).
