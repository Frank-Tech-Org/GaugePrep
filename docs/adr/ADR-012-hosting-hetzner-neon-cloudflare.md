# ADR-012: Hosting: Hetzner Germany, Neon Frankfurt, Cloudflare edge

- Status: Accepted
- Date: 2026-10-22

## Context

Traffic from French-speaking Central Africa routes through European hubs; Cloudflare has a data centre in Douala. Non-production environments must be free.

## Decision

Run application and voice servers on Hetzner Cloud ARM servers in Germany, the database on Neon (PostgreSQL 18) in Frankfurt, and static files, audio and object storage on Cloudflare (R2 has no egress fees). Staging runs on Oracle Cloud Always Free ARM, Neon Free, LiveKit Cloud free and Cloudflare free, fully scripted. A latency test from Douala in milestone 0 confirms the region.

## Alternatives considered

- **African cloud regions:** Rejected: traffic still routes through Europe.
- **Hetzner x86 plans:** Rejected: prices more than doubled in June 2026; ARM rose about 30%.

## Consequences

Infrastructure about €90 to €100 a month at launch. Staging can be rebuilt in under an hour if a free tier changes, as Oracle's did in June 2026.

## Sources

- https://blog.cloudflare.com/african-traffic-growth-and-predictions-for-the-future/
- https://getdeploying.com/datacenters-in-cameroon
- https://neon.com/pricing
- https://neon.com/docs/introduction/regions
- https://developers.cloudflare.com/r2/pricing/
- https://privatedevops.com/news/hetzner-june-2026-cloud-price-increase-what-to-do
- https://infoq.com/news/2026/07/oracle-cloud-free-tier-limits/
