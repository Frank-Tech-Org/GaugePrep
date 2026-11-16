# ADR-015: GitHub Actions and Kamal for delivery

- Status: Accepted
- Date: 2026-10-22

## Context

Deployments must be automated, zero-downtime, and portable between Oracle (staging) and Hetzner (production).

## Decision

Use GitHub Actions with arm64 runners (available in private repositories since 29 January 2026) for CI and image builds, GitHub Container Registry for images, and Kamal 2.12 to deploy containers over SSH with zero-downtime switching through kamal-proxy. Migrations follow expand-then-contract.

## Alternatives considered

- **Kubernetes:** Rejected: control plane and complexity unjustified at this scale.
- **Self-hosted PaaS:** Rejected: an extra server and component to operate.

## Consequences

CI stays within the free plan's included minutes through path filters and caching.

## Sources

- https://github.blog/changelog/2026-01-29-arm64-standard-runners-are-now-available-in-private-repositories
- https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/
- https://rubygems.org/gems/kamal
