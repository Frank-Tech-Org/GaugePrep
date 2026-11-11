FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim@sha256:e80c05a310400cfc90af00b5b7271ef9ad24816e3265e1162af8a678e1aad099 AS base

ENV UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# uv needs every workspace member's pyproject to resolve the lock.
COPY pyproject.toml uv.lock ./
COPY backend/pyproject.toml backend/pyproject.toml
COPY packages/examcore/pyproject.toml packages/examcore/pyproject.toml
COPY voice/pyproject.toml voice/pyproject.toml
RUN uv sync --frozen --no-dev --package gaugeprep-backend

COPY backend backend
WORKDIR /app/backend
RUN useradd --system --no-create-home app
USER app

# Deployed image: Kamal builds this target.
FROM base AS production
ENV DJANGO_SETTINGS_MODULE=config.settings.production
EXPOSE 8000
# Migrate before serving: a failed migration exits the container, so kamal-proxy never switches to it.
# Only migrate sees the migration role's URL; gunicorn starts without it.
# The app user has no home, so gunicorn's control socket is off.
CMD ["sh", "-c", "python manage.py migrate --noinput --settings=config.settings.migrate && exec env -u MIGRATION_DATABASE_URL gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --no-control-socket"]

# Last stage, so a plain build (compose, CI) stays the local image.
FROM base AS dev
