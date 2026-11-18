#!/usr/bin/env bash
# Copies the board sweep and the issue template changes into place and shows the diff to read.
# Usage: bash .claude/proposed/apply-ticket-practice.sh
# Tested: board.sh (sweep, block and set run against the live board with every write stubbed).
# Untested: the issue templates (YAML parses; GitHub renders them only once they are on develop).
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
src=.claude/proposed/ticket-practice
tpl=.github/ISSUE_TEMPLATE

install -m 755 "$src/board.sh" .claude/scripts/board.sh
for f in story task chore bug decision spike; do
  install -m 644 "$src/$f.yml" "$tpl/$f.yml"
done

git add -N "$tpl/spike.yml"
git --no-pager diff -- .claude/scripts/board.sh "$tpl"
echo "Read the diff, then commit it on chore/cto-decision-rights."
