#!/usr/bin/env bash
# Copies the staged CI, merge and board changes into place and shows the diff to read.
# Usage: bash .claude/proposed/apply.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
src=.claude/proposed

for f in ci pages deploy-dev deploy-staging develop-alarm pr-title; do
  install -m 644 "$src/$f.yml" ".github/workflows/$f.yml"
done
install -m 755 "$src/tree-proof.sh" .github/scripts/tree-proof.sh
install -m 755 "$src/merge.sh" .claude/scripts/merge.sh
sed -i 's/the limit is 2, or 3 once CI exists/the limit is 3/' .claude/scripts/board.sh

git add -N .github/workflows/pr-title.yml .github/scripts/tree-proof.sh
git --no-pager diff --stat -- .github .claude/scripts
git --no-pager diff -- .github .claude/scripts
echo "Read the diff, then commit it on chore/team-flow."
