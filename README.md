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

## Checks

`pnpm check` is the single command that defines "passes". Git hooks and CI run the same command, and CI runs nothing else for checks except the pull request title check (Conventional Commits) and gitleaks. It stops at the first failure and prints `check failed: <tool>`.

| Tool | What it does |
|---|---|
| `ruff format --check` | Python formatting |
| `ruff check` | Python lint |
| `mypy` | Python types (strict) |
| `lint-imports` (Import Linter) | Module boundaries; zero contracts for now |
| `pytest` | Python tests; exit code 5 (nothing collected) counts as a pass |
| `prettier --check` | TypeScript and JSON formatting |
| `eslint` | TypeScript lint (`apps/web/eslint.config.js`) |
| `tsc --noEmit` | TypeScript types (`apps/web/tsconfig.json`) |
| `vitest` | TypeScript tests; passes when there are none |

Run one tool with `pnpm run check:<name>`, for example `pnpm run check:mypy`. Fix formatting with `uv run ruff format backend packages voice` and `pnpm exec prettier --write <file>`.
