#!/usr/bin/env bash
# Copies the board helper fix into place and shows the diff to read.
# Usage: bash .claude/proposed/apply-board-sweep.sh
# Tested: sweep, block and set with gh stubbed (a failed read stops the run; no label is dropped).
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
install -m 755 .claude/proposed/board-sweep/board.sh .claude/scripts/board.sh
git --no-pager diff -- .claude/scripts/board.sh
echo "Read the diff, then commit it on chore/cto-decision-rights."
