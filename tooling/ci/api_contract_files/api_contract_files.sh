#!/usr/bin/env bash
# Extracts the base and head OpenAPI files from git and sets the compare step output.
# Usage: api_contract_files.sh   (env: BASE, HEAD, RUNNER_TEMP, GITHUB_OUTPUT)
set -e

# SECURITY: both specs come from git objects, so nothing in the checkout can touch the API check.
compare=false
if [ -z "$BASE" ] || ! git cat-file -e "$BASE^{commit}" 2>/dev/null; then
  echo "no usable base commit, skipping the API comparison"
else
  changed=$(git diff --name-only --no-renames "$BASE...$HEAD" -- apps/backend/openapi.json)
  if [ -z "$changed" ]; then
    echo "apps/backend/openapi.json unchanged, skipping"
  elif ! git show "$BASE:apps/backend/openapi.json" >"$RUNNER_TEMP/openapi.base.json" 2>/dev/null; then
    echo "apps/backend/openapi.json is new on this PR, nothing to compare"
  elif ! git show "$HEAD:apps/backend/openapi.json" >"$RUNNER_TEMP/openapi.head.json" 2>/dev/null; then
    echo "::error title=API contract removed::apps/backend/openapi.json exists on the base branch and is missing on this PR. Restore it."
    exit 1
  else
    compare=true
  fi
fi
echo "compare=$compare" >>"$GITHUB_OUTPUT"
