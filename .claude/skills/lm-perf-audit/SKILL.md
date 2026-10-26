---
name: lm-perf-audit
description: Measure LinguaMentor against its performance budgets (3G page load, per-route JS, simulation data size, grading and examiner latency, SQL plans, N+1) and open a ticket per breach. Use before a release or when something feels slow.
argument-hint: "[page, endpoint, flow or 'all']"
disable-model-invocation: true
---

# Performance audit: $ARGUMENTS

Delegate to `performance-engineer`. It measures before it touches anything. If `$ARGUMENTS` is empty, it covers everything changed since the last tag:
```
git diff --stat $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD) origin/develop
```

Say plainly which budgets can't be measured yet, because the surface or the environment doesn't exist (for example, no staging before ticket #11). Don't estimate them.

Require the table (surface · budget · before · after · guard) and the final `PERF: PASS` or `PERF: FAIL` line.

For each exceeded budget, draft a Bug ticket for `pm`. Don't fix inside the audit unless the fix is one line and the owner of that area agrees. Otherwise the fix goes through its own ticket.
