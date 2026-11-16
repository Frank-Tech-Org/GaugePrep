#!/usr/bin/env bash
# Passes every module's app label explicitly: a bare makemigrations --check skips apps with no migrations package.
set -euo pipefail

cd "$(dirname "$0")/../../apps/backend"
export DJANGO_SETTINGS_MODULE=config.settings.test

# Fails on an empty label list or a module package on disk that is not installed.
labels=$(uv run python -c '
import sys
from pathlib import Path
import django
django.setup()
from django.apps import apps
found = {c.name: c.label for c in apps.get_app_configs() if c.name.startswith("modules.")}
if not found:
    sys.exit("check-migrations: no modules.* apps found in INSTALLED_APPS, so nothing would be checked")
on_disk = {p.parent.name for p in Path("modules").glob("*/__init__.py")}
missing = sorted(on_disk - {n.split(".", 1)[1] for n in found})
if missing:
    sys.exit("check-migrations: modules on disk but not in INSTALLED_APPS: " + ", ".join(missing))
print(*found.values())
')

# shellcheck disable=SC2086
if ! out=$(uv run python manage.py makemigrations --check --dry-run $labels 2>&1); then
  echo "$out" >&2
  if grep -q "Migrations for" <<<"$out"; then
    echo "Model changes without a migration (app named above). Run: cd apps/backend && python manage.py makemigrations <app>, then commit the file." >&2
  else
    echo "makemigrations --check failed (not a missing migration; see the error above)." >&2
  fi
  exit 1
fi
