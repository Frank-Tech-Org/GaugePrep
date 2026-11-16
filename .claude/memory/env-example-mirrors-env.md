---
name: env-example-mirrors-env
description: .env.example and .env hold exactly the same keys; a ticket that adds a setting adds it to both, and the owner only pastes the real values
metadata:
  type: feedback
---

`.env.example` is the mirror of `.env`: the same keys in the same order, with placeholders in the example and empty values in `.env`. A ticket that needs a new key or credential adds it to both in that ticket, so the owner sees exactly which keys to get and only pastes values. Accounts are created in #9, and keys come in the ticket that first uses them. Agents never read `.env` (deny rule), so `.env` is updated by key name only, never by reading values.

**Why:** owner, 2026-10-30.
**How to apply:** the PR of any ticket that adds configuration lists the new keys in its body under "Owner: paste values for". See [[cto-session-owns-delivery]].
