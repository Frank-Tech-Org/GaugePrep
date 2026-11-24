#!/usr/bin/env bash
# Adds the app host page check to the deploy health step (UNTESTED: it only runs in Actions).
# Usage: bash .claude/proposed/apply-app-host-check.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
f=.github/workflows/deploy-backend.yml
python3 - "$f" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = '''          echo "$body" | jq -e '.database == "ok"' > /dev/null
'''
new = old + '''      - name: Check the app host
        run: curl -sS --fail --retry 10 --retry-delay 3 --retry-all-errors -o /dev/null "https://${ENVIRONMENT}.gaugeprep.com/"
'''
if new in s:
    sys.exit("already applied")
if s.count(old) != 1:
    sys.exit("health step not found")
open(p, "w").write(s.replace(old, new))
PY
git --no-pager diff -- "$f"
echo "Read the diff, then commit it on feature/258-app-hosts-pages."
