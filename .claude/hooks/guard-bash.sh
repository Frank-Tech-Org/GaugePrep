#!/usr/bin/env bash
# PreToolUse(Bash): agents may commit, push work branches and open PRs; merging, tagging and releasing stay with the owner.
set -uo pipefail

command -v jq >/dev/null 2>&1 || { echo "guard-bash: jq is required (sudo apt install -y jq)" >&2; exit 2; }
CMD=$(jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

block() { echo "Blocked: $1. The owner runs this; hand it over instead." >&2; exit 2; }
has() { printf '%s' "$CMD" | grep -qE "$1"; }

GIT='\bgit[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?'
# A regex guard catches mistakes, not a determined bypass; GitHub branch protection would be the real backstop.
# Indirect git (built subcommand, eval, sh -c, xargs, new aliases) is refused so the checks below see real commands.
has "${GIT}[\$\`(]"                                     && block "git with a computed subcommand"
has '\b(eval|xargs)\b.*\bgit\b|\b(ba|z)?sh[[:space:]]+-c\b.*\bgit\b' && block "git run indirectly"
has "${GIT}config\b.*\balias\b"                         && block "creating a git alias"
# Push is allowlisted: if "push" appears anywhere (quotes and backslashes removed), the whole command must be exactly
# git push [-u] [--force-with-lease] origin <feature|release|hotfix|chore>/<name>, run on its own.
if printf '%s' "$CMD" | tr -d "\"'\\\\" | grep -qE 'push'; then
  printf '%s' "$CMD" | grep -qxE 'git push( -u| --set-upstream)?( --force-with-lease)? origin (feature|release|hotfix|chore)/[A-Za-z0-9._-]+' \
    || block "push must run on its own as: git push [-u] [--force-with-lease] origin feature/<n>-<slug> (or release/*, hotfix/*, chore/*)"
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
