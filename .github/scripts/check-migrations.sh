#!/usr/bin/env bash
# Passes every module's app label explicitly: a bare makemigrations --check skips apps with no migrations package.
set -euo pipefail

cd "$(dirname "$0")/../../backend"
export DJANGO_SETTINGS_MODULE=config.settings.test

labels=$(uv run python -c '
import django
django.setup()
from django.apps import apps
print(*(c.label for c in apps.get_app_configs() if c.name.startswith("modules.")))
')

# shellcheck disable=SC2086
if ! out=$(uv run python manage.py makemigrations --check --dry-run $labels 2>&1); then
  echo "$out" >&2
  echo "Model changes without a migration (app named above). Run: cd backend && python manage.py makemigrations <app>, then commit the file." >&2
  exit 1
fi
