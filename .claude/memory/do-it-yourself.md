---
name: do-it-yourself
description: Agents run dev and staging setup themselves (Doppler, psql, Kamal, Neon, Chrome); the owner gets one command at most, never a step list
metadata:
  type: feedback
---

Agents run environment work themselves with the logged-in CLIs and connectors: database roles, Doppler values, Kamal deploys to dev and staging, migrations and the checks after them. Secrets are generated and piped between tools, never printed. If a permission check blocks a command, the whole job goes in one script and the owner gets one command in the chat reply.

**Why:** on 2026-11-11 the owner got a 4-step list for the dev database role split, though we had agreed the team does this work, and said the agreed rules had never reached the team's files.

**How to apply:** the rule lives in CLAUDE.md ("Do it; don't hand it over", "Names", "Where code goes") and every agent's "House rules". The owner is asked only for decisions, approvals, merges to stage and main, tags, owner-only files, accounts and money. See [[cto-session-owns-delivery]].
