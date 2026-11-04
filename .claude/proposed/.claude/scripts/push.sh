#!/usr/bin/env bash
# The only way agents push. The guard hook refuses raw `git push`, so the branch is checked here in code, not by regex.
#   .claude/scripts/push.sh <branch> [--force-with-lease]
set -euo pipefail

branch=${1:-}
mode=${2:-}
[ $# -le 2 ] || { echo "push.sh: too many arguments" >&2; exit 2; }
[ -z "$mode" ] || [ "$mode" = "--force-with-lease" ] || { echo "push.sh: only --force-with-lease is allowed as a second argument" >&2; exit 2; }

if ! [[ "$branch" =~ ^(feature|hotfix|chore)/[A-Za-z0-9._-]+$ ]] || [[ "$branch" == *..* ]]; then
  echo "push.sh: '$branch' is not a work branch (feature/*, hotfix/*, chore/*)" >&2; exit 2
fi
git rev-parse --verify --quiet "refs/heads/$branch" >/dev/null || { echo "push.sh: no local branch '$branch'" >&2; exit 2; }
[ "$(git remote get-url origin)" = "https://github.com/LinguaMentor/linguamentor-v3.git" ] \
  || { echo "push.sh: origin is not LinguaMentor/linguamentor-v3" >&2; exit 2; }

# An explicit refs/heads -> refs/heads refspec, so the target can only be the branch of the same name.
args=(push --set-upstream)
[ -n "$mode" ] && args+=("--force-with-lease=refs/heads/$branch")
exec git "${args[@]}" origin "refs/heads/$branch:refs/heads/$branch"
