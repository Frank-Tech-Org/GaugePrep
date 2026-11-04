#!/usr/bin/env bash
# Checks a PR title and body. Inputs come only from env: PR_TITLE, PR_BODY; arg 1 is the template path.
# Heading Evidence is optional because the template says to delete it when unused.
set -u
template=${1:?usage: check-pr-description.sh <pull_request_template.md>}
title=${PR_TITLE-}
body=${PR_BODY-}
errors=()

re='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)\([a-z0-9._/-]+\)!?: .+'
if ! [[ "$title" =~ $re ]]; then
  errors+=("Title must be <type>(<scope>): <subject>; types: feat fix docs style refactor perf test build ci chore revert; the scope is required.")
fi

if ! [[ "$body" =~ Refs\ \#[0-9]+ ]]; then
  errors+=("Body must contain 'Refs #<number>'.")
fi

body_headings=$(printf '%s\n' "$body" | tr -d '\r' | sed -E 's/[[:space:]]+$//')
while IFS= read -r heading; do
  heading=$(printf '%s' "$heading" | tr -d '\r' | sed -E 's/[[:space:]]+$//')
  [ -z "$heading" ] && continue
  [ "$heading" = "## Evidence" ] && continue
  if ! printf '%s\n' "$body_headings" | grep -Fxq -- "$heading"; then
    errors+=("Body is missing the heading '$heading'.")
  fi
done < <(grep -E '^## ' "$template")

if [ "${#errors[@]}" -gt 0 ]; then
  for e in "${errors[@]}"; do printf '::error::%s\n' "$e"; done
  exit 1
fi
echo "PR title and description follow the template."
