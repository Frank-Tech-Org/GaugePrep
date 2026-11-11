# ADR-002: Python and Django for all backend processes, with a shared examcore package

- Status: Accepted
- Date: 2026-10-22

## Context

The voice examiner framework (LiveKit Agents) and the statistics engine are Python. Exam rules (word counts, rule checks, combination model, NCLC tables) must give identical results in practice, simulation, the examiner and prediction. The internal content and support consoles are large PRD requirements.

## Decision

Use Python 3.14 for every backend process, Django 6.1 (moving to 6.2 LTS in April 2027) with Django Ninja for the API, and a shared `examcore` package without Django dependencies that holds all exam rules and scoring maths. Use Django admin as the base of the internal consoles.

## Alternatives considered

- **NestJS core plus Python services:** Rejected: exam rules would exist twice and drift; every grading and prediction call would cross a network boundary; two toolchains.
- **FastAPI:** Rejected: no built-in admin, ORM migrations or authentication; more code for the consoles.

## Consequences

One language, one test suite and one rules library. The team learns Django and LiveKit. Python performance is not the bottleneck: the heavy work waits on AI providers, and Instagram runs Django at very large scale.

## Sources

- https://devguide.python.org/versions.html
- https://www.djangoproject.com/download/
- https://pypi.org/project/django-ninja/
- https://pypi.org/project/livekit-agents/
- https://instagram-engineering.com/web-service-efficiency-at-instagram-with-python-4976d078e366
