# ADR-003: PostgreSQL 18 as database and job queue (Procrastinate), no Redis at launch

- Status: Accepted
- Date: 2026-10-22

## Context

The system needs a relational store, durable background jobs with retries and schedules, and a guarantee that a job is created only when its triggering change commits. Fewer components suit free-tier environments and single-person operation.

## Decision

Use PostgreSQL 18 (uuidv7 identifiers, numeric scores, one schema per module) and Procrastinate 3.10 as the job queue in the same database. Jobs are enqueued in the same transaction as the domain change. Rate limits and usage counters also live in PostgreSQL. No Redis or Valkey until measurements require a cache.

## Alternatives considered

- **Django 6 tasks framework:** Rejected: no worker, retries or scheduling; described as not a queue, worker system or scheduler.
- **Celery with Redis:** Rejected for launch: an extra component in every environment and no transactional enqueue.
- **PostgreSQL 19:** Deferred: still in beta in September 2026; managed providers lag major versions.

## Consequences

A transactional outbox for free. One database to back up. When job volume contends with application load, the queue moves to its own database or a dedicated system behind the same task interface.

## Sources

- https://pypi.org/pypi/procrastinate
- https://www.loopwerk.io/articles/2026/django-tasks-review/
- https://wz-it.com/en/blog/postgresql-14-end-of-life-upgrade-guide/
