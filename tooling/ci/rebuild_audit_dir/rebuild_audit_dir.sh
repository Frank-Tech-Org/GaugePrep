#!/usr/bin/env bash
# Rebuilds a clean directory for pnpm audit: the allowlisted lockfile fields and fresh manifests.
# Usage: rebuild_audit_dir.sh   (env: RUNNER_TEMP; needs yq, jq and a git checkout in the cwd)
set -euo pipefail

# SECURITY: no PR setting, hook or .npmrc is read; only dependency fields reach the audit.
d="$RUNNER_TEMP/audit"
mkdir "$d"
yq '{"lockfileVersion": .lockfileVersion, "settings": .settings, "importers": .importers, "packages": .packages, "snapshots": .snapshots}' pnpm-lock.yaml >"$d/pnpm-lock.yaml"
printf 'packages:\n' >"$d/pnpm-workspace.yaml"
git ls-files -z '*package.json' | while IFS= read -r -d '' f; do
  dir=$(dirname "$f")
  mkdir -p "$d/$dir"
  jq '{dependencies, devDependencies, optionalDependencies}' "$f" >"$d/$dir/package.json.tmp"
  mv "$d/$dir/package.json.tmp" "$d/$dir/package.json"
  if [ "$dir" != . ]; then printf '  - "%s"\n' "$dir" >>"$d/pnpm-workspace.yaml"; fi
done
