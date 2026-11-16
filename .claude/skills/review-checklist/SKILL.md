---
name: review-checklist
description: Order of work for reviewing a local diff before its first push: scope, invariants, behaviour, tests, silent failures, then the verdict line. Use when reviewing any GaugePrep diff.
---

# Review checklist

1. Run the mechanical script first and fix its findings; don't repeat them by hand.
2. Read `git diff develop...HEAD`, then only the callers of what changed.
3. Check the architecture invariants in `CLAUDE.md`; a breach is `issue (blocking)`.
4. For each acceptance criterion and Definition of Done item on the ticket, find the code and the test that proves it. A missing proof is blocking.
5. Look where an error would hide a wrong grade, score or charge: defaults on failure, log-and-continue, retries that never surface.
6. Check the tests assert behaviour: success, not-found and other-learner-refused for each endpoint.
7. Check the PR text matches the diff and names no path, tool or step the diff lacks.
8. Verdict first: `REVIEW: PASS <head sha>` or `REVIEW: CHANGES`, then at most 10 findings as `label: file:line - problem - fix`. Say what you could not verify.
