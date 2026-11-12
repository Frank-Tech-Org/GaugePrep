#!/usr/bin/env bash
# Replaces every .semgrepignore in the checkout with the copies from the base commit.
# Usage: semgrep_base_ignore.sh   (env: BASE, HEAD, GITHUB_EVENT_NAME)
set -e

: "${BASE?BASE is not set}" "${HEAD?HEAD is not set}"
# WHY: with no base on a push, none are restored and the scan is stricter.
if [ "$GITHUB_EVENT_NAME" != pull_request ] && ! git cat-file -e "$BASE^{commit}" 2>/dev/null; then
  BASE=$(git rev-parse -q --verify "$HEAD^" || true)
fi
# SECURITY: Semgrep reads .semgrepignore in every folder, so drop all and restore only the base's.
find . -name .semgrepignore -not -path './.git/*' -delete
if [ -n "$BASE" ]; then
  git ls-tree -r -z --name-only "$BASE" | { grep -zE '(^|/)\.semgrepignore$' || true; } | while IFS= read -r -d '' f; do
    mkdir -p "$(dirname "$f")"
    git show "$BASE:$f" >"$f"
  done
fi
