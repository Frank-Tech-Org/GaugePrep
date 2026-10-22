# ADR-013: Self-hosted LiveKit in production, LiveKit Cloud free in staging

- Status: Accepted
- Date: 2026-10-22

## Context

LiveKit Cloud's paid plan is $50 a month with 5,000 agent minutes, then $0.01 per minute, which would add about a third to the speaking cost.

## Decision

Use LiveKit Cloud's free Build plan in staging and the open-source LiveKit server on a dedicated Hetzner server in production, using LiveKit's single-server setup (Caddy TLS, built-in TURN on 443).

## Alternatives considered

- **LiveKit Cloud in production:** Rejected at launch volume above about 5,000 minutes a month on cost.

## Consequences

We operate the media server, its certificates and ports; switching to LiveKit Cloud remains a configuration change.

## Sources

- https://livekit.com/pricing
- https://docs.livekit.io/home/self-hosting/vm/
- https://docs.livekit.io/home/self-hosting/deployment/
