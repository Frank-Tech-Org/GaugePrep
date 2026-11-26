# GaugePrep

Exam preparation platform. This repository holds the backend, the shared exam rules and the placeholder pages; the web app and the voice examiner are still to build.

## Layout

| Folder              | What it is                                                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/web`          | Placeholder pages for dev and staging; the Next.js app comes with the first web feature. [Photo credits](apps/web/public/photos/CREDITS.md) |
| `apps/backend`      | Django application; each module is a package under `apps/backend/modules/`                                                                  |
| `apps/voice`        | Voice examiner (not built yet)                                                                                                              |
| `packages/examcore` | Exam rules, rule checks and scoring maths. No Django dependency                                                                             |
| `tooling`           | Shared lint and type configs, our own CI checks with their tests, Semgrep rules                                                             |
| `infra`             | `docker` images, `kamal` deploy configs, `server` rebuild script                                                                            |
| `docs`              | Product, architecture, decision records, exam specs, content guide, process, runbooks                                                       |
| `.github`           | CI workflows, their helper scripts, issue and PR templates                                                                                  |
| `.kamal`            | Kamal secrets files; they read values from the deploying shell, never hold them                                                             |
| `.claude`           | AI team tooling: agents, rules, commands. Nothing in it runs in the product                                                                 |

A new top-level folder or a moved one updates this table in the same PR.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs Python 3.14 if you do not have it)
- Node 24 or newer and pnpm 11 (`corepack enable` picks the pinned version)
- Docker with Compose
- [gitleaks](https://github.com/gitleaks/gitleaks) 8.19 or newer, for the commit hooks

## Setup

```sh
uv sync
pnpm install          # also installs the git hooks
cp .env.example .env
uv run python -c "import examcore"   # must import with no Django installed
```

## Run locally

Starts PostgreSQL 18 and the backend, which migrates and then serves. The host ports are fixed so they stay out of the way of other projects: API 18000, database 15432, Mailpit UI 18025. Override them with `BACKEND_PORT`, `POSTGRES_PORT` or `MAILPIT_UI_PORT` in `.env`; `pnpm dev:up` prints the API address and the database URL.

```sh
pnpm dev:up                                      # prints API: http://127.0.0.1:<port>
curl -i http://127.0.0.1:<port>/api/v1/health    # 200 {"status": "ok", "database": "ok"}
docker compose down                              # add -v to drop the database volume
```

If you ran the stack before this rename, drop the old database volume once with `docker compose down -v` (the data is synthetic), or confirm you don't need it; the new volume creates `gaugeprep`.

To run Django on your machine against the compose database, start only `db`, then `uv run python apps/backend/manage.py migrate` and `runserver`.

Unset settings fall back to safe local defaults. Hosted settings refuse to start without `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` and `DATABASE_URL`.

## Checks

```sh
pnpm check                    # everything the hooks and CI run; stops at the first failure
pnpm run check:mypy           # one tool
pnpm run check:shellcheck     # the CI "Lint shell scripts" step; needs shellcheck installed
uv run ruff format backend packages voice
pnpm exec prettier --write <file>
```

What each check does, the CI jobs, the security scans and the git hooks: [CI and checks](docs/process/ci-and-checks.md).

## Docs

- [Product requirements](docs/product/PRD.md)
- [System architecture](docs/architecture/system-architecture.md) and [decision records](docs/adr/)
- [TCF Canada exam rules](docs/exam-specs/TCF-Canada.md)
- [Branching and release](docs/process/branching-and-release.md)
- [Runbooks](docs/runbooks/)
