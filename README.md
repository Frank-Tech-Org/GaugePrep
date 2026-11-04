# LinguaMentor

Exam preparation platform. This repository holds the web app, the backend, the voice examiner and the shared exam rules.

## Layout

| Folder | What it is |
|---|---|
| `apps/web` | Next.js progressive web app (pnpm workspace) |
| `backend` | Django application; each module is a package under `backend/modules/` |
| `packages/examcore` | Exam rules, rule checks and scoring maths. No Django dependency |
| `voice` | Voice examiner worker |
| `infra` | `docker`, `kamal` and `staging` deployment files |
| `docs` | Architecture, decision records and exam specifications |

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs Python 3.14 if you do not have it)
- Node 24 or newer and pnpm 11 (`corepack enable` picks the pinned version)

## Setup

```sh
uv sync
pnpm install
cp .env.example .env
```

## Check that it works

```sh
uv run python -c "import examcore"
pnpm --version
```

`examcore` must import without Django installed.

## Run locally

Needs Docker with Compose. Starts PostgreSQL 18 and the backend (it migrates, then serves on port 8000):

```sh
docker compose up -d --build
curl -i http://localhost:8000/api/v1/health      # 200 {"status": "ok", "database": "ok"}
curl http://localhost:8000/api/v1/openapi.json   # the OpenAPI document
docker compose down                              # add -v to drop the database volume
```

To run Django on your machine against the compose database instead:

```sh
docker compose up -d db
uv run python backend/manage.py migrate
uv run python backend/manage.py runserver
```

Unset settings use safe local defaults (see `.env.example`). Hosted settings (`dev`, `staging`, `production`) refuse to start without `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` and `DATABASE_URL`. A down database answers 503 within 2 seconds.

Regenerate the committed OpenAPI file after changing the API (a test fails when it is stale):

```sh
uv run python backend/manage.py export_openapi_schema --api config.api.api --indent 2 --output backend/openapi.json
```

## Checks

`pnpm check` is the single command that defines "passes". Git hooks and CI run the same command, and CI adds the `gate` job and the security scans below. It stops at the first failure and prints `check failed: <tool>`.

| Tool | What it does |
|---|---|
| `ruff format --check` | Python formatting |
| `ruff check` | Python lint |
| `mypy` | Python types (strict) |
| `lint-imports` (Import Linter) | Module boundaries; zero contracts for now |
| `makemigrations --check` | Fails when a model change has no migration, naming the app. Every module under `backend/modules/` is passed by app label (`.github/scripts/check-migrations.sh`), because a bare check skips apps that have no migrations package yet. Fix: run `python manage.py makemigrations <app>` in `backend/` and commit the file |
| `pytest` | Python tests in random order (pytest-randomly prints the seed; replay with `--randomly-seed=N`), 30 s timeout per test; collecting none fails, and an unregistered marker fails collection (`--strict-markers`). Database tests skip with a reason when PostgreSQL is unreachable, and fail when `CI=true` |
| `coverage report` | Branch coverage per package, floors set in each package pyproject.toml: `examcore` 95%, backend 85%. Fails below the floor. `voice` has no code yet and is not measured |
| `prettier --check` | TypeScript and JSON formatting |
| `eslint` | TypeScript lint (`apps/web/eslint.config.js`) |
| `tsc --noEmit` | TypeScript types (`apps/web/tsconfig.json`) |
| `vitest` | TypeScript tests in random order (seed printed), 10 s timeout per test; passes when there are none. Branch coverage of `apps/web/src` (v8), floor 80%; fails below it, and an empty report passes while there is no measured code |

No skips: with `CI=true` any skipped or xfail test (pytest or Vitest) fails the run and is named; locally it only warns. Floors only go up.

### Gate job in CI

One `gate` job runs first on every pull request, in this order: the path filter (which decides whether the code jobs, pip-audit, pnpm audit, Trivy and the backend image run), the gitleaks secret scan over the full git history, the API breaking-change check, and last the title and description check (its script comes from the pull request, so it runs after the scan and the API check and cannot change them). It fails red with a message naming the bad title or description rule, the file holding the secret, or the breaking API change. When it fails, the jobs that need it are skipped; a skipped job counts as passing for merge, so a red `gate` is what blocks, and a grey job is not a pass.

### API breaking changes

When a pull request changes `backend/openapi.json`, the `API breaking changes` step of `gate` compares it with the base branch copy (both read with `git show`, never from the checkout) using [oasdiff](https://github.com/oasdiff/oasdiff) v1.35.0 (Apache-2.0, built from source with `go install -trimpath` at the pinned module version and Go 1.27.3, cached, and run only when its SHA256 matches the pinned value). It runs `oasdiff breaking --match-path '^/api/v1/' --fail-on ERR` and fails on a removed operation, a removed response property (required or optional), a request property that became required, a changed property type or an added enum value in a response, naming each one. Adding an optional field or a new operation passes. oasdiff reads no config from the checkout (it gets an empty config file and its own severity file) and refuses external `$ref`s. Installed copies of the web app keep calling the old contract for days, so a breaking change needs a new API version, not an edit. To run it locally, build oasdiff as the `API breaking changes` step does, then: `: > empty.yaml; echo 'response-optional-property-removed err' > severity.txt; oasdiff breaking base.json head.json --config empty.yaml --severity-levels severity.txt --allow-external-refs=false --match-path '^/api/v1/' --fail-on ERR`. Without the severity file, removing an optional response property passes. The step runs with `contents: read` and no secret.

### API contract tests

`backend/tests/test_contract.py` runs inside `pytest`. [Schemathesis](https://schemathesis.readthedocs.io) (MIT, dev dependency only) generates requests for every operation in `backend/openapi.json` and calls the Django app in-process: no server, no network. Each response must use a documented status, never be a 5xx, and match its documented schema; a failure names the operation and the status. The tests also fail when `backend/openapi.json` is missing or has no operations. Response content types are not checked yet. After an API change, regenerate the document (the command is in the `test_openapi.py` failure message) and run `uv run pytest backend/tests/test_contract.py`.

### Backend image build in CI

The `backend image` check runs `docker build -f infra/docker/backend.Dockerfile .` (no push, no login) only when a pull request changes `infra/docker/`, `uv.lock`, a `pyproject.toml` or `.dockerignore`; otherwise it shows as skipped and does not block the merge. It catches a Dockerfile, lockfile or workspace change that breaks the image, which `pnpm check` never builds. It builds for x64, so ARM-only problems still show at deploy.

### Security scans in CI

Each pull request also runs these checks (gitleaks inside `gate`, the rest as separate jobs). A HIGH or CRITICAL finding fails the check and blocks the merge (pip-audit fails on any advisory, as it has no severity filter). All are free and open source, with no token or account.

| Check | What it scans |
|---|---|
| Semgrep | Source code, community rules (pinned `semgrep/semgrep-rules` for Python, TypeScript and generic, metrics off), ERROR findings fail, except two vendored dev tools that never ship: `.claude/skills/semgrep/scripts` and `.claude/skills/webapp-testing/scripts/with_server.py` |
| pip-audit | The `uv.lock` dependencies; it has no severity filter, so any known advisory fails |
| pnpm audit | The `pnpm-lock.yaml` dependencies, audited in a rebuilt directory with no pull request settings or hooks (`pnpm audit --audit-level high`) |
| Trivy | The repository files (`trivy fs --severity HIGH,CRITICAL`) |
| gitleaks (in `gate`) | The full git history, not only the pull request's commits |

Documentation-only pull requests skip pip-audit, pnpm audit and Trivy. The only secret-scan allowlist entry is the placeholder key in `api-design.md`, in `.gitleaks.toml`.

### Scanner settings

The `Scanner settings` step of `gate` compares the pull request with its merge base and fails when the pull request:

- adds or edits a scanner or package-manager settings file: `.semgrepignore`, `.trivyignore*`, `trivy.yaml`, `.gitleaks.toml`, `.gitleaksignore`, `.npmrc` or `.pnpmfile.*`, at any depth; the log names each file
- adds a line to `pnpm-workspace.yaml` that sets an `audit*` key, `ignoreCves`, `ignoreGhsas`, `onlyBuiltDependencies`, `overrides`, `pnpmfile`, `globalPnpmfile` or `ignorePnpmfile`
- adds a line containing `nosem` (also `nosemgrep`), `trivy:`, `tfsec:` or `--ignore-vuln`; the log names each file and line

Markdown files and the owner-only CI workflow are not searched, since they only describe these markers. Deleting a settings file is not flagged, because it can only widen what the scans see.

The check flags; it does not decide. When the suppression is justified, the owner merges over the red check. The free plan cannot make checks required, so nothing stops that merge but `merge.sh`, which reads the gate and refuses a red one: the owner merges by hand, after reading the named files and lines.

### Pull request description

The title and description check, a step of `gate` (script `.github/scripts/check-pr-description.sh`, local cases in `check-pr-description.test.sh`) fails when:

- the title is not `<type>(<scope>): <subject>` with a scope, using the commitlint types (feat fix docs style refactor perf test build ci chore revert)
- the body has no `Refs #<number>`
- the body lacks any `## ` heading of `.github/pull_request_template.md`, read from the base branch; `## Evidence` is optional

The failure names each broken rule. Editing the body re-runs the check.

### Git hooks

`pnpm install` installs the hooks (Husky, through the `prepare` script). They need [gitleaks](https://github.com/gitleaks/gitleaks) 8.19 or newer on your PATH, because `gitleaks git --staged` replaces the deprecated `gitleaks protect`. With gitleaks missing, `pre-commit` refuses.

| Hook | Refuses |
|---|---|
| `pre-commit` | A commit on `develop`, `stage` or `main`; staged files that fail lint-staged (ruff, prettier); a staged secret found by gitleaks (rules in `.gitleaks.toml`) |
| `commit-msg` | A message that is not Conventional Commits with a scope, `<type>(<area>): <subject>` (commitlint, `commitlint.config.mjs`) |
| `pre-push` | A push to `develop`, `stage` or `main`; then runs `pnpm check` and refuses on failure (skipped when nothing is pushed or the push only deletes branches) |

Run one tool with `pnpm run check:<name>`, for example `pnpm run check:mypy`. Fix formatting with `uv run ruff format backend packages voice` and `pnpm exec prettier --write <file>`.
