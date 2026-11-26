#!/usr/bin/env bash
# Installs the photo credits PR check and shows the diff (script and test TESTED; workflow UNTESTED: it only runs in Actions).
# Usage: bash .claude/proposed/apply-photo-credits.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
src=.claude/proposed/photo-credits

install -m 755 "$src/check-photo-credits.sh" .github/scripts/check-photo-credits.sh
install -m 755 "$src/check-photo-credits.test.sh" .github/scripts/check-photo-credits.test.sh
install -m 644 "$src/photo-credits.yml" .github/workflows/photo-credits.yml

bash .github/scripts/check-photo-credits.test.sh
git add -N .github/scripts/check-photo-credits.sh .github/scripts/check-photo-credits.test.sh .github/workflows/photo-credits.yml
git --no-pager diff -- .github
echo "Read the diff, then commit it on feature/295-carousel-photos."
