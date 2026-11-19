#!/usr/bin/env bash
# Lets agents run the merge script and drops the cap wording from the board helper (tested: jq, sed).
# Usage: bash .claude/proposed/apply-merge-permissions.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
tmp=$(mktemp)
jq '.permissions.allow |= (if index("Bash(.claude/scripts/merge.sh:*)") then . else . + ["Bash(.claude/scripts/merge.sh:*)"] end)' \
  .claude/settings.json >"$tmp"
mv "$tmp" .claude/settings.json
sed -i 's/ (In progress, In review, In QA); limit 3/ (In progress, In review, In QA)/' .claude/scripts/board.sh
git --no-pager diff -- .claude/settings.json .claude/scripts/board.sh
echo "Read the diff, then commit it on chore/memory-into-rules."
