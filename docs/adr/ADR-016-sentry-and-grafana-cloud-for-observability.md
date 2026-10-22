# ADR-016: Sentry and Grafana Cloud for observability

- Status: Accepted
- Date: 2026-10-22

## Context

One operator must see errors, latency, queue health, costs and accuracy, within free tiers at launch.

## Decision

Use Sentry (free Developer plan: 5,000 errors, 5 million spans) for errors and traces, and Grafana Cloud (free: 10,000 series, 50 GB logs and traces, 3 users) for logs, metrics, dashboards and alerts, with the alert list in the architecture document.

## Alternatives considered

- **Self-hosted monitoring stack:** Rejected: more to operate.

## Consequences

Upgrade to paid plans when limits are reached (Sentry Team $29 a month; Grafana Pro $19 plus usage).

## Sources

- https://sentry.io/pricing/
- https://last9.io/blog/grafana-cloud-pricing/
