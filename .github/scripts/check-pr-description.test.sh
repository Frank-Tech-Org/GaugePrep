#!/usr/bin/env bash
# Local cases for check-pr-description.sh: bash .github/scripts/check-pr-description.test.sh
cd "$(dirname "$0")/../.." || exit 1
S=.github/scripts/check-pr-description.sh
T=.github/pull_request_template.md
fail=0
out=$(mktemp)
run() { PR_TITLE="$2" PR_BODY="$3" bash "$S" "$T" >"$out" 2>&1; echo $?; }
expect() { # name want title body [grep]
  got=$(run "$1" "$3" "$4")
  if [ "$got" != "$2" ] || { [ -n "${5-}" ] && ! grep -Fq -- "$5" "$out"; }; then echo "FAIL $1 (exit $got)"; cat "$out"; fail=1; else echo "ok   $1"; fi
}
full=$(sed 's/^Refs #$/Refs #12/' "$T")
noevid=$(printf '%s\n' "$full" | awk '/^## Evidence/{s=1;next} /^## /{s=0} !s')
expect green-full 0 'feat(api): add x' "$full"
expect green-no-evidence 0 'feat(api): add x' "$noevid"
expect green-crlf 0 'fix(web): y' "$(printf '%s\n' "$full" | sed 's/$/\r/')"
expect red-heading 1 'feat(api): add x' "${full//## How it was tested/## Testing}" "How it was tested"
expect red-refs 1 'feat(api): add x' "${full//Refs #12/Refs}" "Refs #"
expect red-scope 1 'feat: add x' "$full" "scope is required"
expect red-empty 1 '' ''
expect inject-title 1 '$(id) `id` "; echo pwned' "$full"
expect inject-title-ok 0 'fix(ci): $(id) `id`' "$full"
if grep -q 'uid=' "$out"; then echo "FAIL injection executed"; fail=1; fi
exit $fail
