# Local development image; production images come with the deploy work.
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

ENV UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# uv needs every workspace member's pyproject to resolve the lock.
COPY pyproject.toml uv.lock ./
COPY backend/pyproject.toml backend/pyproject.toml
COPY packages/examcore/pyproject.toml packages/examcore/pyproject.toml
COPY voice/pyproject.toml voice/pyproject.toml
RUN uv sync --frozen --no-dev --package linguamentor-backend

COPY backend backend
WORKDIR /app/backend
