# ADR-001: Modular monolith with four process types

- Status: Accepted
- Date: 2026-10-22

## Context

The product combines short web requests, a live speaking examiner, asynchronous AI grading and a monthly statistics batch. The expected load for release 1 is 10,000 registered and 1,000 daily active learners. The system must be runnable by one person and must not depend on team size.

## Decision

Build one codebase deployed as one application, divided into modules with enforced boundaries (public interface per module, one database schema per module, Import Linter contracts in CI). Run four process types from this codebase: core application, job worker, scoring engine, voice examiner. Modules communicate in-process through public interfaces; asynchronous work goes through a transactional outbox.

## Alternatives considered

- **Microservices:** Rejected: network calls, distributed consistency and several deployments for no benefit at the planned scale. Shopify reached the same conclusion and kept a modular monolith.
- **Unstructured monolith:** Rejected: without enforced boundaries modules couple over time, which is the problem Shopify describes.

## Consequences

One deployment and one database to operate. Boundaries are checked by tooling, so modules can later be extracted if a real need appears. Workloads with different behaviour scale independently as separate process types.

## Sources

- https://www.infoq.com/news/2019/07/shopify-modular-monolith
