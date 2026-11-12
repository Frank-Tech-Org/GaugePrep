#!/usr/bin/env bash
# Replaces the Trivy ignore and config files with the base commit's and disarms inline markers.
# Usage: trivy_base_ignore.sh   (env: BASE, HEAD, GITHUB_EVENT_NAME)
set -e

: "${BASE?BASE is not set}" "${HEAD?HEAD is not set}"
# WHY: with no base on a push, none are used and the scan is stricter.
if [ "$GITHUB_EVENT_NAME" != pull_request ] && ! git cat-file -e "$BASE^{commit}" 2>/dev/null; then
  BASE=$(git rev-parse -q --verify "$HEAD^" || true)
fi
# SECURITY: ignore files and config come from the base, so a PR cannot switch off its own scan.
for f in .trivyignore .trivyignore.yaml .trivyignore.yml trivy.yaml trivy.yml; do
  rm -f "$f"
  if [ -n "$BASE" ]; then git show "$BASE:$f" >"$f" 2>/dev/null || rm -f "$f"; fi
done
# WHY: rewrite the markers so Trivy no longer reads them as ignores; git grep exits 1 on no match.
{ git grep -lzE '(trivy|tfsec):(ignore|exp)' || true; } | xargs -0 -r sed -i -E 's/(trivy|tfsec):(ignore|exp)/\1-\2/g'
