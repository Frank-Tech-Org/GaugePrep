#!/usr/bin/env bash
# PreToolUse(Bash): agents may commit, push work branches and open PRs; merging, tagging and releasing stay with the owner.
set -uo pipefail

command -v jq >/dev/null 2>&1 || { echo "guard-bash: jq is required (sudo apt install -y jq)" >&2; exit 2; }
CMD=$(jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

block() { echo "Blocked: $1. The owner runs this; hand it over instead." >&2; exit 2; }
has() { printf '%s' "$CMD" | grep -qE "$1"; }

GIT='\bgit[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?'
if has "${GIT}push\b"; then
  has "${GIT}push\b.*[[:space:]](-f|--force[a-z-]*|--mirror|--all|--tags|--delete|-d)\b" && block "force, mirror, tag or delete push"
  has "${GIT}push\b.*[[:space:]:+](main|develop)([[:space:]]|$)" && block "pushing straight to main or develop"
  has "${GIT}push\b.*[[:space:]](feature|release|hotfix|chore)/[^[:space:]]+" \
    || block "push names no work branch; use git push -u origin feature/<n>-<slug> (or release/*, hotfix/*)"
fi
has "${GIT}commit\b.*--amend"                           && block "amending a commit"
has "${GIT}tag[[:space:]]+(-a|-s|-f|-d|[^-[:space:]])"  && block "creating or deleting a tag"
has "${GIT}reset[[:space:]]+--hard"                     && block "git reset --hard discards work"
has "${GIT}clean[[:space:]]+-[a-zA-Z]*f"                && block "git clean -f deletes untracked files"
has '\bgh[[:space:]]+pr[[:space:]]+merge\b'             && block "merging a PR"
has '\bgh[[:space:]]+release[[:space:]]+(create|delete|edit)\b' && block "publishing a release"
has '\bgh[[:space:]]+(repo|issue)[[:space:]]+delete\b'  && block "deleting a repository or issue"
has '\brm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*[[:space:]]+(/|~|\$HOME)([[:space:]]|$)' && block "recursive delete of / or home"
printf '%s' "${CMD//.env.example/}" | grep -qE '(^|[[:space:]/"'"'"'=])\.env([.[:space:]"'"'"']|$)|\.(pem|key)\b' \
  && block "reading secret files (.env, .pem, .key)"
has '(curl|wget)[^|]*\|[[:space:]]*(ba|z)?sh\b'         && block "piping a download into a shell"
printf '%s' "$CMD" | grep -qiE '\bDROP[[:space:]]+(TABLE|DATABASE|SCHEMA)\b' && block "destructive SQL"
exit 0
