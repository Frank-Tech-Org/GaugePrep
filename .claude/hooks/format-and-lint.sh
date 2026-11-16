#!/usr/bin/env bash
# PostToolUse(Edit|Write): format the edited file and report lint errors back to the agent.
# Tools are used only once installed (ticket #4 adds them), so this is a no-op until then.
set -uo pipefail

FILE=$(jq -r '.tool_input.file_path // empty')
[ -n "$FILE" ] && [ -f "$FILE" ] || exit 0
ROOT=${CLAUDE_PROJECT_DIR:-$(pwd)}
WEB="$ROOT/apps/web"
OUT=""

case "$FILE" in
  *.py)
    if [ -x "$ROOT/.venv/bin/ruff" ]; then
      "$ROOT/.venv/bin/ruff" format -q "$FILE"
      OUT=$("$ROOT/.venv/bin/ruff" check --fix -q "$FILE" 2>&1)
    fi ;;
  "$WEB"/*.ts|"$WEB"/*.tsx|"$WEB"/*.js|"$WEB"/*.jsx|"$WEB"/*.css|"$WEB"/*.json)
    [ -x "$WEB/node_modules/.bin/prettier" ] && "$WEB/node_modules/.bin/prettier" --write --log-level warn "$FILE" >/dev/null
    case "$FILE" in *.ts|*.tsx|*.js|*.jsx)
      [ -x "$WEB/node_modules/.bin/eslint" ] && OUT=$(cd "$WEB" && node_modules/.bin/eslint --fix "$FILE" 2>&1) ;;
    esac ;;
esac

# Exit 2 hands the remaining lint errors to the agent so it fixes them now.
[ -n "$OUT" ] && { printf 'Lint errors in %s:\n%s\n' "$FILE" "$OUT" | head -30 >&2; exit 2; }
exit 0
