# ADR-010: In-house Rasch scoring engine verified against a reference

- Status: Accepted
- Date: 2026-10-22

## Context

Listening and reading predictions need item difficulties and learner ability on one scale, converted to the 699 scale.

## Decision

Implement the Rasch model in `examcore` with NumPy and SciPy: MAP ability estimates online, monthly marginal maximum likelihood calibration with stable items as anchors, fit statistics, and cut-point conversion. Verify with recovery tests on simulated data and comparison with an established statistics package in CI.

## Alternatives considered

- **GIRTH:** Rejected: last release November 2021, labelled alpha.
- **py-irt:** Rejected: described as research code, single maintainer, requires PyTorch.

## Consequences

A small, well-understood codebase under our control, checked against a reference on every change.

## Sources

- https://pypi.org/project/girth/
- https://pypi.org/project/py-irt/
