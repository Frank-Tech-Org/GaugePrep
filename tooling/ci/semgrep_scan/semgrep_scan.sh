#!/usr/bin/env bash
# Runs Semgrep with the pinned community rules and our own rules read from the base commit.
# Usage: semgrep_scan.sh   (env: BASE, HEAD, GITHUB_EVENT_NAME, RUNNER_TEMP, RULES_SHA)
set -e

if [ "$GITHUB_EVENT_NAME" != pull_request ] && ! git cat-file -e "$BASE^{commit}" 2>/dev/null; then
  BASE=$(git rev-parse -q --verify "$HEAD^" || true)
fi
git init -q "$RUNNER_TEMP/semgrep-rules"
git -C "$RUNNER_TEMP/semgrep-rules" fetch -q --depth 1 https://github.com/semgrep/semgrep-rules "$RULES_SHA"
git -C "$RUNNER_TEMP/semgrep-rules" checkout -q FETCH_HEAD
r="$RUNNER_TEMP/semgrep-rules"
mkdir "$RUNNER_TEMP/local-rules"
# SECURITY: our rules come from the base commit, so a PR cannot weaken them.
if [ -n "$BASE" ]; then
  git ls-tree -r -z --name-only "$BASE" -- tooling/semgrep | { grep -zE '^tooling/semgrep/[^/]+\.yaml$' || true; } | while IFS= read -r -d '' f; do
    git show "$BASE:$f" >"$RUNNER_TEMP/local-rules/${f##*/}"
  done
fi
args=(--config "$r/python" --config "$r/typescript" --config "$r/generic")
if [ -n "$(ls -A "$RUNNER_TEMP/local-rules")" ]; then
  args+=(--config "$RUNNER_TEMP/local-rules")
else
  echo "::notice title=Local rules::No tooling/semgrep/*.yaml on the base commit; scanning with the pinned community rules only."
fi
# WHY: the test snippets hold unsafe calls on purpose, so those files are excluded from the scan.
uvx --no-config --exclude-newer 2026-10-30 semgrep==1.183.0 scan --max-target-bytes 0 --metrics=off --disable-nosem --error --severity ERROR --quiet --exclude .claude/skills/semgrep/scripts --exclude .claude/skills/webapp-testing/scripts/with_server.py --exclude tooling/semgrep/request-eval-exec.py \
  "${args[@]}" .
