#!/usr/bin/env bash
# Lets agents run merge.sh and stops infra and Kamal paths needing the owner's approval (untested).
# Usage: bash .claude/proposed/apply-merge-permissions.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
tmp=$(mktemp)
jq '.permissions.allow |= (if index("Bash(.claude/scripts/merge.sh:*)") then . else . + ["Bash(.claude/scripts/merge.sh:*)"] end)' \
  .claude/settings.json >"$tmp"
mv "$tmp" .claude/settings.json
sed -i 's/ (In progress, In review, In QA); limit 3/ (In progress, In review, In QA)/' .claude/scripts/board.sh
python3 -I - <<'PY'
import pathlib

old = r"|^infra/|^\.kamal/'"
for f in (".claude/scripts/merge.sh", ".github/workflows/develop-alarm.yml"):
    p = pathlib.Path(f)
    s = p.read_text()
    assert s.count(old) == 1, f
    p.write_text(s.replace(old, "'"))
PY
git --no-pager diff -- .claude/settings.json .claude/scripts .github/workflows/develop-alarm.yml
echo "Read the diff, then commit it on chore/memory-into-rules."
