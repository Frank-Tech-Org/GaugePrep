#!/usr/bin/env bash
# PreToolUse(Bash): agents may commit, push work branches and open PRs; merging, tagging and releasing stay with the owner.
set -uo pipefail

command -v jq >/dev/null 2>&1 || { echo "guard-bash: jq is required (sudo apt install -y jq)" >&2; exit 2; }
INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty')
[ -z "$CMD" ] && exit 0
ROOT=${CLAUDE_PROJECT_DIR:-}
# Fingerprint of the committed .claude/scripts/push.sh; the owner updates it when the script changes.
PUSH_SHA=e45f1949af438cd48627e0262421f9426a24b184ed8bf1ad6696681822977f10

block() { echo "Blocked: $1. The owner runs this; hand it over instead." >&2; exit 2; }
# Checks run on one flattened line, so continuations and newlines can't split a command across grep's lines.
FLAT=$(printf '%s' "$CMD" | sed -e ':a' -e 'N' -e '$!ba' -e 's/\\\n/ /g' | tr '\n\r' '  ')
# NORM drops quotes and backslashes and turns $IFS into spaces, so "gi"t, g\it and git${IFS}tag read as written.
NORM=$(printf '%s' "$FLAT" | sed -E 's/\$\{?IFS\}?/ /g' | tr -d "\"'\\\\")
has() { printf '%s' "$NORM" | grep -qE "$1"; }

# A regex guard catches mistakes, not a determined bypass; GitHub branch protection would be the real backstop.
# Git rules match the subcommand anywhere after "git", so global options can't be used to hide it.
GIT='\bgit\b.*\b'
# Expansions are checked on the raw text: any $ or backtick in a command that mentions git or push is refused.
printf '%s' "$FLAT" | tr -d "\"'\\\\" | grep -qE '\b(git|push)\b' && printf '%s' "$FLAT" | grep -qE '[$`]' \
  && block "git with a shell expansion; write the command out literally"
has '\b(eval|xargs)\b.*\bgit\b|\b(ba|z)?sh[[:space:]]+-c\b.*\bgit\b' && block "git run indirectly"
has '\bgit\b.*(\balias\b|(^|[[:space:]=])--(git-dir|work-tree|namespace)\b)' && block "git alias or repository override"
# Raw git push is never allowed; agents push only through .claude/scripts/push.sh, which checks the branch in code.
# If "push" appears anywhere, the whole command must be exactly that script call, on its own.
re='^\.claude/scripts/push\.sh (feature|release|hotfix|chore)/[A-Za-z0-9._-]+( --force-with-lease)?$'
if printf '%s' "$NORM" | grep -qE 'push'; then
  [[ "$CMD" =~ $re ]] \
    || block "push only via: .claude/scripts/push.sh <feature|release|hotfix|chore>/<name> [--force-with-lease], run on its own"
  # The script that runs must be the pinned one: run from the repo root, file unchanged.
  [ -n "$ROOT" ] && [ "$CWD" = "$ROOT" ] || block "run push.sh from the repository root"
  [ "$(sha256sum "$ROOT/.claude/scripts/push.sh" 2>/dev/null | cut -d' ' -f1)" = "$PUSH_SHA" ] \
    || block "push.sh does not match its pinned fingerprint; the owner must review the change and update PUSH_SHA"
fi
# The guardrail files belong to the owner: no shell command may touch them (reading is done with the Read tool).
has '\.claude/(hooks|settings|scripts/push)' && ! [[ "$CMD" =~ $re ]] \
  && block "the guard hook, settings and push script are owner-only"
has "${GIT}commit\b.*--amend"                           && block "amending a commit"
has "${GIT}tag[[:space:]]+(-a|-s|-f|-d|[^-[:space:]])"  && block "creating or deleting a tag"
has "${GIT}reset[[:space:]]+--hard"                     && block "git reset --hard discards work"
has "${GIT}clean[[:space:]]+-[a-zA-Z]*f"                && block "git clean -f deletes untracked files"
has '\bgh[[:space:]]+pr[[:space:]]+merge\b'             && block "merging a PR"
has '\bgh[[:space:]]+release[[:space:]]+(create|delete|edit)\b' && block "publishing a release"
has '\bgh[[:space:]]+(repo|issue)[[:space:]]+delete\b'  && block "deleting a repository or issue"
has '\brm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*[[:space:]]+(/|~|\$HOME)([[:space:]]|$)' && block "recursive delete of / or home"
printf '%s' "${FLAT//.env.example/}" | grep -qE '(^|[[:space:]/"'"'"'=])\.env([.[:space:]"'"'"']|$)|\.(pem|key)\b' \
  && block "reading secret files (.env, .pem, .key)"
has '(curl|wget)[^|]*\|[[:space:]]*(ba|z)?sh\b'         && block "piping a download into a shell"
printf '%s' "$FLAT" | grep -qiE '\bDROP[[:space:]]+(TABLE|DATABASE|SCHEMA)\b' && block "destructive SQL"
exit 0
