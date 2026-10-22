# Project management and working standards

Applies to every change in this repository. Nothing is merged outside this process.

## 1. Branches and environments

| Branch | Purpose | Deploys to |
|---|---|---|
| `develop` | Default branch. Integration and staging. | Staging, automatically, after checks pass |
| `main` | Production-ready code only | Nothing. Production deploys only from a version tag |
| `feat/*`, `fix/*`, `chore/*`, `docs/*`, `refactor/*`, `test/*` | One issue each, branched from `develop` | Nothing |
| `hotfix/*` | Urgent production fix, branched from `main` | Nothing |

Rules:
- Nobody commits or pushes directly to `develop` or `main`. Husky blocks it locally.
- Pull requests use `Refs #n`, never `Closes #n`, so the issue stays open through Testing. It is closed by hand once staging is verified.
- Merging into `main` never deploys. Only a tag `vX.Y.Z` on `main` deploys to production, and the workflow refuses a tag whose commit is not on `main`.

## 2. Work item workflow

Every change to behaviour, data or infrastructure starts as an issue. Typo fixes may go through a `chore` commit in a pull request without an issue.

1. **Backlog**: issue created from a template.
2. **Ready**: the issue meets the ticket standard (section 3). Only Ready issues are started.
3. **In progress**: branch created from `develop`. Limit: 2 issues at a time.
4. **In review**: pull request opened, self-review done in the GitHub diff.
5. **Testing**: pull request squash-merged into `develop` and staging deployed. The acceptance criteria are checked on staging and the result is written as a comment on the issue. If staging shows the ticket does not meet its criteria, it goes back to In progress. If staging shows a different problem outside the ticket, a new bug issue is opened.
6. **Done**: every acceptance criterion verified on staging, and the issue closed by hand.

A bug is not a column: it goes through the same stages as any other issue. It is an issue with the `bug` label and the `fix:` prefix, and a P0 or P1 bug goes to the top of Ready. A board view filtered on Type = Bug shows them together.

Project board fields: Status (Backlog, Ready, In progress, In review, Testing, Done), Type (Feature, Bug, Task, Decision), Milestone (M0 to M8), Area (`web`, `api`, `examcore`, `voice`, `infra`, `docs`), Priority (P0 urgent, P1 high, P2 normal, P3 low).

## 3. Ticket standards

| Type | Use it for | Title prefix | Label |
|---|---|---|---|
| Feature | New behaviour | `feat:` | `feature` |
| Bug | Something is wrong | `fix:` | `bug` |
| Task | Technical or operational work | `chore:` | `task` |
| Decision | A choice that needs a record | `decision:` | `decision` |

A ticket is **Ready** when:
- The title says the outcome in the imperative: `feat: add NCLC conversion to examcore`.
- It has context, scope and acceptance criteria written as testable checkboxes.
- It states what is out of scope and what it depends on.
- It fits in two days of work. Larger work is split into sub-issues under a parent feature issue.
- It has a milestone, an area and a priority.

Additional rules:
- A bug includes steps to reproduce, expected and actual behaviour, and the environment.
- A decision ends with an ADR in `docs/adr/`. The ADR number is referenced in the pull request that delivers it.
- Other labels: `blocked` (with a comment naming the blocker) and `hotfix`.
- Scope changes are written as a comment on the issue, never silently in code.

## 4. Commits and pull requests

**Branch name**: `<type>/<issue-number>-<short-slug>`, for example `feat/42-nclc-conversion`.

**Commits** follow Conventional Commits: `<type>(<scope>): <description>`.
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`, `perf`.
- Scope: the module or area, for example `examcore`, `api`, `web`, `voice`, `infra`.
- Description: lowercase, imperative, no final full stop.
- Footer: `Refs #42`. Breaking changes add `!` after the scope and a `BREAKING CHANGE:` footer.

**Pull requests**
- One issue per pull request. Title follows the commit format, because it becomes the commit on `develop`.
- Body uses the template and contains `Refs #42`.
- Feature, fix and chore branches into `develop`: **squash merge**.
- `develop` into `main` (release) and `hotfix/*` into `main`: **merge commit**, so history is kept.
- Never merge with a failing check. GitHub cannot enforce this on a free private repository, so it is a rule.
- Review your own diff in the GitHub pull request page before merging. Changes to scoring and `examcore`, billing, authentication, and migrations or append-only data also get an AI review pass and the failure modes written in the pull request.

## 5. Release and hotfix

**Release**
1. Verify the staging deployment from `develop`.
2. Open a pull request `develop` to `main` with the release template, titled `release: vX.Y.Z`.
3. Merge it with a merge commit.
4. Tag `main`: `git tag vX.Y.Z && git push origin vX.Y.Z`. The tag deploys to production.
5. Publish the GitHub release with notes generated from the merged pull requests.

Versions follow SemVer. Before launch they stay at `v0.x.y`.

**Hotfix**
1. Branch `hotfix/<issue>-slug` from `main`, label the issue `hotfix`.
2. Pull request into `main`, merge commit, tag a patch version.
3. Open a pull request from `main` back into `develop` the same day.

## 6. Definition of done

- Every acceptance criterion is covered by an automated test, or by a written manual check in the pull request.
- A bug fix starts with a test that fails before the fix.
- `pnpm check` passes locally and CI is green.
- Documentation changes in the same pull request (OpenAPI, runbook, ADR, README).
- Database changes follow expand then contract and state their rollback.
- No secrets in the diff. New settings are documented and added to the example env file.

## 7. Local checks (Husky)

Everything CI runs must run locally first. There is one command, `pnpm check`, that runs formatting, linting, type checks, Import Linter, unit and integration tests and the frontend tests. CI calls the same command, so the two cannot drift.

Tools: Husky, lint-staged, commitlint (`@commitlint/config-conventional`), gitleaks.

| Hook | What it does |
|---|---|
| `pre-commit` | Refuses commits on `develop` and `main`. Runs lint-staged (format and lint changed files) and gitleaks on staged changes |
| `commit-msg` | commitlint rejects messages that are not Conventional Commits |
| `pre-push` | Refuses pushes to `develop` and `main`. Runs `pnpm check` |

`.husky/pre-commit` (branch guard, then the checks):
```sh
branch=$(git rev-parse --abbrev-ref HEAD)
case "$branch" in
  main|develop) echo "Direct commits to $branch are not allowed. Create a branch."; exit 1;;
esac
pnpm exec lint-staged
gitleaks protect --staged --redact
```

`.husky/commit-msg`:
```sh
pnpm exec commitlint --edit "$1"
```

`.husky/pre-push`:
```sh
while read local_ref local_sha remote_ref remote_sha; do
  case "$remote_ref" in
    refs/heads/main|refs/heads/develop) echo "Direct pushes to ${remote_ref#refs/heads/} are not allowed. Open a pull request."; exit 1;;
  esac
done
pnpm check
```

Skipping hooks with `--no-verify` is not allowed. CI repeats every check, so a skipped hook is caught there.

## 8. CI

| Trigger | Steps |
|---|---|
| Pull request to `develop` or `main` | `pnpm check`, pull request title check, gitleaks, API contract check |
| Push to `develop` | Same checks, then build ARM images, deploy to staging, publish the PWA to staging |
| Tag `vX.Y.Z` | Verify the commit is on `main`, run migrations, deploy to production, publish the PWA |

## 9. One-time repository setup

1. Create `develop` from `main` and set it as the default branch (Settings, Branches).
2. Settings, General, Pull Requests: allow squash merging and merge commits, disable rebase merging, enable automatic deletion of merged branches.
3. Add the files in section 10.
4. Install Husky only after the first commits on `develop` are pushed, otherwise the guards block the setup itself.
5. Create the labels from section 3, the milestones M0 to M8 and the project board with the fields in section 2.

## 10. Templates

### `.github/ISSUE_TEMPLATE/config.yml`
```yaml
blank_issues_enabled: false
```

### `.github/ISSUE_TEMPLATE/feature.yml`
```yaml
name: Feature
description: New behaviour for learners, admins or operators
title: "feat: "
labels: ["feature"]
body:
  - type: textarea
    id: context
    attributes:
      label: Context
      description: Why this is needed and who it is for.
    validations:
      required: true
  - type: textarea
    id: scope
    attributes:
      label: Scope
      description: What will be built.
    validations:
      required: true
  - type: textarea
    id: acceptance
    attributes:
      label: Acceptance criteria
      description: Testable statements, one checkbox each.
      value: "- [ ] "
    validations:
      required: true
  - type: textarea
    id: out-of-scope
    attributes:
      label: Out of scope
    validations:
      required: true
  - type: textarea
    id: dependencies
    attributes:
      label: Dependencies
      description: Issues or decisions this depends on, or "none".
    validations:
      required: true
```

### `.github/ISSUE_TEMPLATE/bug.yml`
```yaml
name: Bug
description: Something does not work as intended
title: "fix: "
labels: ["bug"]
body:
  - type: textarea
    id: summary
    attributes:
      label: Summary
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Steps to reproduce
      value: "1. "
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Expected behaviour
    validations:
      required: true
  - type: textarea
    id: actual
    attributes:
      label: Actual behaviour
    validations:
      required: true
  - type: dropdown
    id: environment
    attributes:
      label: Environment
      options: [Local, Staging, Production]
    validations:
      required: true
  - type: textarea
    id: evidence
    attributes:
      label: Evidence
      description: Logs, screenshots, request IDs, Sentry link.
  - type: textarea
    id: acceptance
    attributes:
      label: Acceptance criteria
      description: How we know it is fixed. Includes a regression test.
      value: "- [ ] A test reproduces the bug and now passes\n- [ ] "
    validations:
      required: true
```

### `.github/ISSUE_TEMPLATE/task.yml`
```yaml
name: Task
description: Technical or operational work
title: "chore: "
labels: ["task"]
body:
  - type: textarea
    id: context
    attributes:
      label: Context
    validations:
      required: true
  - type: textarea
    id: scope
    attributes:
      label: Scope
    validations:
      required: true
  - type: textarea
    id: acceptance
    attributes:
      label: Acceptance criteria
      value: "- [ ] "
    validations:
      required: true
  - type: textarea
    id: dependencies
    attributes:
      label: Dependencies
      description: Issues or decisions this depends on, or "none".
    validations:
      required: true
```

### `.github/ISSUE_TEMPLATE/decision.yml`
```yaml
name: Decision
description: A choice that needs a decision record
title: "decision: "
labels: ["decision"]
body:
  - type: textarea
    id: question
    attributes:
      label: Question
      description: What must be decided, and why now.
    validations:
      required: true
  - type: textarea
    id: constraints
    attributes:
      label: Constraints
    validations:
      required: true
  - type: textarea
    id: options
    attributes:
      label: Options considered
      description: Each option with evidence and sources.
    validations:
      required: true
  - type: textarea
    id: acceptance
    attributes:
      label: Done when
      value: "- [ ] ADR written in docs/adr and linked here\n- [ ] Affected documents updated"
    validations:
      required: true
```

### `.github/pull_request_template.md`
```markdown
## Summary

Refs #

## What changed

-

## How it was tested

- [ ] `pnpm check` passes locally
- [ ] Manual check (describe, or write "not needed"):

## Acceptance criteria

Copy from the issue.

- [ ]

## Checklist

- [ ] Title follows Conventional Commits
- [ ] Docs updated (OpenAPI, runbook, ADR, README) or not needed
- [ ] Database change follows expand then contract, rollback noted below
- [ ] No secrets, new settings documented
- [ ] High-risk area (scoring and examcore, billing, authentication, migrations or append-only data): failure modes written below and AI review done

## Risk and rollback

How this could fail, and how to undo it.
```

### `.github/PULL_REQUEST_TEMPLATE/release.md`
Use it with `?template=release.md` on the pull request URL.
```markdown
## Release vX.Y.Z

## Included

List the merged pull requests and issues.

## Checks

- [ ] Staging verified from `develop`
- [ ] Migrations reviewed and reversible
- [ ] Rollback plan written below
- [ ] Merge with a merge commit, then tag `main`

## Rollback
```