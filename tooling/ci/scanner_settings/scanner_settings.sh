#!/usr/bin/env bash
# Fails when a pull request changes scanner or pnpm settings or adds an inline suppression.
# Usage: scanner_settings.sh   (env: BASE, HEAD, RUNNER_TEMP)
set -e

# SECURITY: prints file names, field names and line numbers, never values or line contents.
# WHY: separate files, so a failing git diff stops the step.
d=(git -c core.quotepath=off diff --no-renames --diff-filter=d "$BASE...$HEAD")
"${d[@]}" -z --name-only >"$RUNNER_TEMP/scanner.names"
"${d[@]}" -U0 --text --no-textconv --no-ext-diff -- . ':!*.md' ':!.github/workflows/ci.yml' ':!.claude/proposed/ci.yml' ':!tooling/ci/scanner_settings' ':!tooling/ci/semgrep_scan' >"$RUNNER_TEMP/scanner.diff"
strip() { awk '/^[[:space:]]*(#|$)/ {next} /^packages:[[:space:]]*$/ {s=1; next} s && /^[[:space:]]*-/ {next} {s=0; print}'; }
files=
while IFS= read -r -d '' f; do
  case "${f##*/}" in
    .semgrepignore | .trivyignore* | trivy.yaml | trivy.yml | .gitleaks.toml | .gitleaksignore | .npmrc | .pnpmfile.*) ;;
    pnpm-workspace.yaml) [ "$(git ls-tree "$HEAD" -- "$f" | cut -c1-6)" = 100644 ] && [ "$(git show "$BASE:$f" 2>/dev/null | strip)" = "$(git show "$HEAD:$f" | strip)" ] && continue ;;
    *) continue ;;
  esac
  files+="  $(printf %s "$f" | tr -d '[:cntrl:]')"$'\n'
done <"$RUNNER_TEMP/scanner.names"
# WHY: local rules are read from the base, so a merged edit becomes the next base; flag deletions.
git -c core.quotepath=off diff --no-renames -z --name-only "$BASE...$HEAD" -- tooling/semgrep/ >"$RUNNER_TEMP/semgrep.names"
while IFS= read -r -d '' f; do
  files+="  $(printf %s "$f" | tr -d '[:cntrl:]')"$'\n'
done <"$RUNNER_TEMP/semgrep.names"
pkg=
mb=$(git merge-base "$BASE" "$HEAD")
while IFS= read -r -d '' f; do
  [ "${f##*/}" = package.json ] || continue
  if git cat-file -e "$mb:$f" 2>/dev/null; then git show "$mb:$f" >"$RUNNER_TEMP/pkg.base"; else echo '{}' >"$RUNNER_TEMP/pkg.base"; fi
  git show "$HEAD:$f" >"$RUNNER_TEMP/pkg.head"
  name=$(printf %s "$f" | tr -d '[:cntrl:]')
  if ! changed=$(jq -nr --slurpfile b "$RUNNER_TEMP/pkg.base" --slurpfile h "$RUNNER_TEMP/pkg.head" 'if ($b[0]|type) == "object" and ($h[0]|type) == "object" then ["packageManager","devEngines","pnpm","resolutions"][] | select($b[0][.] != $h[0][.]) else error("not an object") end' 2>/dev/null); then
    pkg+="  $name: not readable as a JSON object"$'\n'
    continue
  fi
  for field in $changed; do pkg+="  $name: $field"$'\n'; done
done <"$RUNNER_TEMP/scanner.names"
hits=$(tr '\0' ' ' <"$RUNNER_TEMP/scanner.diff" | awk '
  /^diff / { hdr = 1; next }
  hdr && /^\+\+\+ / { f = substr($0, 5); sub(/^"?b\//, "", f); next }
  /^@@ / { hdr = 0; match($0, /\+[0-9]+/); n = substr($0, RSTART + 1, RLENGTH - 1); next }
  !hdr && /^\+/ { if (tolower($0) ~ /nosem|trivy:|tfsec:|--ignore-vuln|gitleaks:allow/) print "  " f ":" n; n++ }' | tr -d '\000-\011\013-\037')
if [ -n "$files$pkg$hits" ]; then
  [ -z "$files" ] || printf 'Scanner or package-manager settings changed (pnpm-workspace.yaml: anything beyond the packages list):\n%s' "$files"
  [ -z "$pkg" ] || printf 'pnpm version or settings changed in package.json (file: field):\n%s' "$pkg"
  [ -z "$hits" ] || printf 'Inline suppression added at file:line:\n%s\n' "$hits"
  echo "::error title=Scanner settings::This pull request changes scanner settings, the pnpm version or its settings, or adds a suppression (listed above). The code and scanner jobs still run. Remove it, or the owner merges over this check when it is justified."
  exit 1
fi
