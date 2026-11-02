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

`pnpm check` is the single command that defines "passes". Git hooks and CI run the same command, and CI runs nothing else for checks except the pull request title check (Conventional Commits) and gitleaks. It stops at the first failure and prints `check failed: <tool>`.

| Tool | What it does |
|---|---|
| `ruff format --check` | Python formatting |
| `ruff check` | Python lint |
| `mypy` | Python types (strict) |
| `lint-imports` (Import Linter) | Module boundaries; zero contracts for now |
| `pytest` | Python tests; collecting none fails. Database tests skip with a reason when PostgreSQL is unreachable, and fail when `CI=true` |
| `prettier --check` | TypeScript and JSON formatting |
| `eslint` | TypeScript lint (`apps/web/eslint.config.js`) |
| `tsc --noEmit` | TypeScript types (`apps/web/tsconfig.json`) |
| `vitest` | TypeScript tests; passes when there are none |

### Git hooks

`pnpm install` installs the hooks (Husky, through the `prepare` script). They need [gitleaks](https://github.com/gitleaks/gitleaks) 8.19 or newer on your PATH, because `gitleaks git --staged` replaces the deprecated `gitleaks protect`. With gitleaks missing, `pre-commit` refuses.

| Hook | Refuses |
|---|---|
| `pre-commit` | A commit on `develop`, `stage` or `main`; staged files that fail lint-staged (ruff, prettier); a staged secret found by gitleaks (rules in `.gitleaks.toml`) |
| `commit-msg` | A message that is not Conventional Commits with a scope, `<type>(<area>): <subject>` (commitlint, `commitlint.config.mjs`) |
| `pre-push` | A push to `develop`, `stage` or `main`; then runs `pnpm check` and refuses on failure (skipped when nothing is pushed or the push only deletes branches) |

Run one tool with `pnpm run check:<name>`, for example `pnpm run check:mypy`. Fix formatting with `uv run ruff format backend packages voice` and `pnpm exec prettier --write <file>`.
