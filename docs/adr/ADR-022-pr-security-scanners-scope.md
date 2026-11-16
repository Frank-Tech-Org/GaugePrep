# ADR-022: PR security scanners catch accidents, not a deliberate bypass

- Status: Accepted
- Date: 2026-11-02

## Context

The pull request workflow runs Semgrep, pip-audit, pnpm audit, Trivy and gitleaks. The same workflow installs and runs the PR's own code, so a PR author controls part of what the scanners see. We harden the obvious switches (ignore files and configs come from the base commit, inline suppression markers are neutralised, pnpm audit runs on a rebuilt directory), but that cannot be made complete.

## Decision

The scanners catch accidental vulnerabilities, not a deliberate bypass by the PR author. The owner and agents are the only authors, and every diff gets a review.

- A bypass that needs deliberate hiding is LOW and goes to a follow-up.
- A bypass an honest change could trigger by accident blocks the PR.

## Residual risks

- A hand-crafted lockfile or a suppression comment in a form we do not neutralise.
- A tampered tarball URL in the lockfile. The check job's frozen install fails on it.

## Follow-up

A chore for a tripwire check that fails or flags a PR changing scanner settings or adding suppression markers.
