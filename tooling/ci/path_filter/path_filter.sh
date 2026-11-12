#!/usr/bin/env bash
# Sets the code and backend_image step outputs from the files a pull request changes.
# Usage: path_filter.sh   (env: BASE, HEAD, GITHUB_EVENT_NAME, GITHUB_OUTPUT)
set -e

# WHY: a separate assignment, so a failing git diff stops the step instead of skipping the checks.
if [ -n "$BASE" ] && git cat-file -e "$BASE^{commit}" 2>/dev/null; then
  diff=$(git diff --name-only --no-renames "$BASE...$HEAD")
  other=$(printf '%s\n' "$diff" | grep -Ev '^(docs/|\.claude/(agents|rules|memory)/|\.claude/skills/.*\.md$|.*\.md$)' || true)
  if [ -n "$other" ]; then code=true; else code=false; fi
  image=$(printf '%s\n' "$diff" | grep -E '^(infra/docker/|uv\.lock$|\.dockerignore$|(.*/)?pyproject\.toml$)' || true)
  if [ -n "$image" ]; then backend_image=true; else backend_image=false; fi
else
  echo "no usable base commit, running everything"
  code=true
  backend_image=true
fi
if [ "$GITHUB_EVENT_NAME" != pull_request ]; then code=true; fi
echo "code=$code" >>"$GITHUB_OUTPUT"
echo "backend_image=$backend_image" >>"$GITHUB_OUTPUT"
echo "code checks: $code"
echo "backend image: $backend_image"
