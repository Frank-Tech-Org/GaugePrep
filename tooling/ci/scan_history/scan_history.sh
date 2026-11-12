#!/usr/bin/env bash
# Scans the git history reachable from HEAD for secrets with the gitleaks binary.
# Usage: scan_history.sh   (env: BASE HEAD GITHUB_EVENT_NAME RUNNER_TEMP)
set -e

# WHY: on a push the base may be gone (new branch, force push), so fall back to the first parent.
if [ "$GITHUB_EVENT_NAME" != pull_request ] && ! git cat-file -e "$BASE^{commit}" 2>/dev/null; then
  BASE=$(git rev-parse -q --verify "$HEAD^" || true)
fi
# SECURITY: allow comments and the checkout's .gitleaksignore would let a PR skip its own secret.
args=(git --redact --verbose --ignore-gitleaks-allow --log-opts="HEAD")
rm -f .gitleaksignore
# SECURITY: the config and ignore list come from the base, never from the head's own files.
{ [ -n "$BASE" ] && git show "$BASE:.gitleaks.toml" >"$RUNNER_TEMP/gl.toml" 2>/dev/null; } || printf '[extend]\nuseDefault = true\n' >"$RUNNER_TEMP/gl.toml"
args+=(--config "$RUNNER_TEMP/gl.toml")
{ [ -n "$BASE" ] && git show "$BASE:.gitleaksignore" >"$RUNNER_TEMP/gl.ignore" 2>/dev/null; } || : >"$RUNNER_TEMP/gl.ignore"
args+=(--gitleaks-ignore-path "$RUNNER_TEMP/gl.ignore")
if ! "$RUNNER_TEMP/gitleaks-bin/gitleaks" "${args[@]}"; then
  echo "::error title=Secret found::gitleaks found a secret in the history; the File line in the output above names the file. Remove it from every commit and rotate it."
  exit 1
fi
