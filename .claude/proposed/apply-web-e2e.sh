#!/usr/bin/env bash
# Adds the web browser tests to the check job of the CI workflow and shows the diff to read.
# Usage: bash .claude/proposed/apply-web-e2e.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
wf=.github/workflows/ci.yml
step=.claude/proposed/web-e2e-step.yml
if grep -q 'name: Web browser tests' "$wf"; then echo "already applied"; exit 0; fi
[ "$(grep -c '^      - run: pnpm check$' "$wf")" = 1 ] || { echo "expected one 'pnpm check' step"; exit 1; }

tmp=$(mktemp)
awk -v step="$step" '{ print } /^      - run: pnpm check$/ { while ((getline line < step) > 0) print line }' "$wf" > "$tmp"
cat "$tmp" > "$wf"
rm -f "$tmp"
git --no-pager diff -- "$wf"
echo "Read the diff, then commit it on the ticket branch."
