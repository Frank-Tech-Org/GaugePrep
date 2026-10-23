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
