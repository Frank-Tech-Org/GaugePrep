---
name: lm-release
description: Release LinguaMentor. With "check", run only the release gate (security, performance budgets, public claims) on staging. With no argument or a version, merge the changelog into develop, open the promotion PR develop → stage, run the gate and regression on staging, then open the release PR stage → main. With "<version> done", after the owner has merged, tagged and published, move the released tickets to Done.
argument-hint: "[version] [done] | check"
arguments: [version, phase]
disable-model-invocation: true
---

# Release v$version $phase

Follow `docs/process/branching-and-release.md` section 7. `platform-engineer` is the release manager: it prepares every branch and PR. Only the owner merges into `stage` and `main`, pushes the tag and publishes the GitHub release.

## State now

!`.claude/scripts/board.sh list "Ready to deploy" || true`
!`.claude/scripts/board.sh list "In QA" || true`
!`git fetch -q origin develop stage main && git log --oneline origin/stage..origin/develop | head -30 || true`
!`gh api "repos/LinguaMentor/linguamentor-v3/pulls?state=open" --jq '.[] | select(.base.ref=="stage" or .base.ref=="main") | "#\(.number) \(.head.ref) -> \(.base.ref)"' || true`

## Version

No version given: take the last tag (`git describe --tags --abbrev=0 origin/main`, or `v0.0.0` if none) and bump MINOR if any Ready to deploy ticket is a Story or Task that adds a capability, else PATCH. Say the version and why in one line, and use it below as `$version`. Nothing Ready to deploy: stop and name `/pm`.

## Check (version is "check")

Run the gate below on staging, on what changed since the last tag, and stop after the table. Use it before a release, after a public-page change, or when something feels slow.

## Prepare (no phase given)

Resume from where the release stands: an open promotion PR means step 2 is waiting on the owner; `stage` equal to `develop` with no release PR means step 3.

### 1. Changelog

Nothing may be In QA, so `develop` holds only QA-passed work. `platform-engineer` checks that the Ready to deploy list matches `git log <last-tag>..origin/develop` (a commit without a ticket, or a ticket without a commit, stops the release) and that CI is green on the head of `develop`. A ticket whose commits are on `develop` but which is back In progress after a failed QA stops the release: ask the owner whether to wait for its fix or revert its squash commits (`git log --grep "#<n>"`, newest first) on `chore/revert-<n>`, merged with `/lm-next`, and send the ticket back to Ready. Never cherry-pick a subset into `stage`. It writes the `CHANGELOG.md` entry on `chore/release-$version` (Added, Changed, Fixed; one line per ticket), pushes it with `push.sh` and opens the PR into `develop`. Review and merge it with `/lm-next`.

### 2. Promote to staging

`platform-engineer` opens the promotion PR through `gh api`: base `stage`, head `develop`, title `chore(release): promote v$version to staging`, body listing the tickets. Tell the owner to merge it with a **merge commit**, then rerun `/lm-release $version`.

### 3. Gate and regression on staging: every item runs, and any failure stops the release

Wait until the staging deploy of `stage` includes the promotion (`gh run list --branch stage`).

| # | Check | Who |
|---|---|---|
| 1 | Staging runs the head of `stage`, and `stage` equals `develop` at the changelog merge | `platform-engineer` |
| 2 | CI green on the head of `stage` | `platform-engineer` |
| 3 | Security pass on `git diff <last-tag>..origin/stage`: no CRITICAL or HIGH | `security-engineer` |
| 4 | Dependencies: `uvx pip-audit` and `pnpm audit --audit-level high`, no high or critical | `security-engineer` |
| 4b | Attack test on staging (never production): the permanent attack tests, ZAP active scan, Nuclei and Schemathesis against the OpenAPI contract (all free), no open HIGH or CRITICAL | `security-engineer` |
| 5 | Performance: every budget measured on staging at phone and desktop sizes, including the k6 load run; the table surface · budget · before · after · guard; budgets that can't be measured yet are named, never estimated; `PERF: PASS` | `performance-engineer` |
| 6 | Claims: every statement on the public pages, onboarding and notification copy, `README.md`, the draft release notes and the tickets since the last tag, checked against code and tests; `MOCKED` and `ABSENT` claims listed first with the line to fix; `docs/CLAIMS.md` refreshed on a `chore/*` PR into `develop`; `CLAIMS: GO` | `qa-engineer` |
| 7 | Regression of the released tickets, and UX and accessibility on every changed screen | `qa-engineer`, `product-designer` |
| 8 | Privacy: no new personal data flow without a ruling | `privacy-compliance` (only if data flows changed) |
| 9 | Migrations are expand-then-contract, with a rollback written down | `code-reviewer` |
| 10 | Grader changes have a stored, passing release-check report | `ai-engineer` (only if grading changed) |
| 11 | Rollback command documented for this deploy | `platform-engineer` |

Show the table with each result. If any check fails, stop with `RELEASE: NO-GO — <check>` and hand a draft ticket for each failure to `product-manager`. The fix is built on `develop` with `/lm-next`, then promoted again from step 2. Nothing is fixed on `stage`.

### 4. Release PR and hand-over

`platform-engineer` opens the release PR through `gh api`: base `main`, head `stage`, title `Release v$version`, body from the release PR template. `content-marketer` writes `release-notes.md`, in French then English, in the scratchpad, starting from GitHub's generated notes (`gh api repos/LinguaMentor/linguamentor-v3/releases/generate-notes -f tag_name=v$version -f target_commitish=stage -f previous_tag_name=<last tag> --jq .body`; it creates nothing) and rewriting them in learner terms with no ticket numbers. Tell the owner:

```
Merge the release PR (stage → main) with a merge commit, not a squash, then:
git switch main && git pull && git tag -a v$version -m "Release v$version" && git push origin v$version
gh release create v$version --title "v$version" --notes-file <path to release-notes.md>
Then run: /lm-release $version done
```

## Close (phase = done)

1. Confirm the tag and the release exist: `git ls-remote --tags origin v$version` and `gh release view v$version`. If either is missing, stop.
2. Delegate to `product-manager`, for each released ticket:
   ```
   .claude/scripts/board.sh move <n> Done
   gh issue comment <n> --body "Released in v$version."
   gh issue close <n>    # skip if its merge already closed it
   ```
3. Report the closed tickets in one line, then `/pm`.
