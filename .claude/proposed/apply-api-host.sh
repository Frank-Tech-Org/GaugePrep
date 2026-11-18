#!/usr/bin/env bash
# Points the deploy workflow's health check at the API hosts (UNTESTED: it only runs in Actions).
# Usage: bash .claude/proposed/apply-api-host.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
sed -i 's/HOST=\${ENVIRONMENT}\.gaugeprep\.com/HOST=api.${ENVIRONMENT}.gaugeprep.com/' \
  .github/workflows/deploy-backend.yml
git --no-pager diff -- .github/workflows/deploy-backend.yml
echo "Read the diff, then commit it on feature/245-worker-mail-api-host."
