#!/usr/bin/env bash
# Usage: worker-role.sh <dev|stg>
# Creates or rotates the worker database role, grants it the job tables only and stores its URL in Doppler.
set -euo pipefail

env="${1:?usage: worker-role.sh <dev|stg>}"
case "$env" in dev | stg) ;; *) echo "environment must be dev or stg" >&2; exit 1 ;; esac
cfg=(--project gaugeprep --config "$env")
role="gaugeprep_${env}_worker"
migrator="gaugeprep_${env}_migrator"
serving="gaugeprep_${env}_app"

owner_url=$(doppler secrets get DATABASE_OWNER_URL --plain "${cfg[@]}")
password=$(openssl rand -hex 24)

psql "$owner_url" -v ON_ERROR_STOP=1 -q <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$role') THEN
    CREATE ROLE "$role" LOGIN;
  END IF;
END \$\$;
ALTER ROLE "$role" PASSWORD '$password';
SQL

(cd "$(git rev-parse --show-toplevel)/apps/backend" && uv run python -m config.db_roles "$migrator" "$serving" "$role") |
  psql "$owner_url" -v ON_ERROR_STOP=1 -q

# WHY: only the user, password and database part of the serving URL change.
app_url=$(doppler secrets get DATABASE_URL --plain "${cfg[@]}")
worker_url=$(python3 - "$app_url" "$role" "$password" <<'PY'
import sys
from urllib.parse import urlsplit, urlunsplit

url, role, password = sys.argv[1:]
p = urlsplit(url)
print(urlunsplit(p._replace(netloc=f"{role}:{password}@{p.hostname}" + (f":{p.port}" if p.port else ""))))
PY
)
printf '%s' "$worker_url" | doppler secrets set WORKER_DATABASE_URL "${cfg[@]}" --silent > /dev/null
echo "worker role $role ready; WORKER_DATABASE_URL set in gaugeprep/$env"
