---
name: lm-verify-claims
description: Verify every LinguaMentor public claim against the code and its tests, and refresh docs/CLAIMS.md. Use before any release, any public-page change, and any README or release-notes change.
argument-hint: "[surface or path, default: all public surfaces]"
disable-model-invocation: true
---

# Claim check: $ARGUMENTS

Delegate to `product-verifier`. If `$ARGUMENTS` is empty, the scope is:
- the public pages under `apps/web` (landing, pricing, accuracy page, help)
- onboarding and notification copy in the message catalogues
- `README.md`
- the draft release notes, if any
- the tickets reaching Ready to deploy since the last tag

Require the full classification table and the final `CLAIMS: GO` or `CLAIMS: NO-GO` line.

List every `MOCKED` and `ABSENT` claim first, above the summary, with the surface and the exact line to remove or rewrite. For each one, draft a Bug ticket for `product-owner` with priority High and Area docs or web.

If `docs/CLAIMS.md` changed, commit it on the current work branch (or on `chore/claims-<date>`) and open a PR into `develop`.
