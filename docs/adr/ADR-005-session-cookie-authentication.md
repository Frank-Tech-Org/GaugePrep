# ADR-005: Session cookie authentication

- Status: Accepted
- Date: 2026-10-22

## Context

The PWA on app.<domain> calls the API on api.<domain>. The PRD requires sign-out of all devices.

## Decision

Use Django sessions with HttpOnly, Secure, SameSite Lax cookies shared across the same site, CSRF tokens on writes, Argon2 password hashing, and short-lived room tokens for LiveKit.

## Alternatives considered

- **JWT in browser storage:** Rejected: tokens readable by scripts and harder revocation.

## Consequences

Instant revocation and no token storage in the browser. The PWA and API must stay on the same registrable domain.
