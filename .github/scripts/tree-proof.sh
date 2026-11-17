#!/usr/bin/env bash
# Prints a commit on <branch> with tree <tree> whose checks passed, or nothing.
# Usage: tree-proof.sh <branch> <tree> <jobs|run>
set -uo pipefail

branch=${1:?branch} tree=${2:?tree} mode=${3:?jobs|run}
repo=${GITHUB_REPOSITORY:?}
case "$branch:$mode" in
  develop:jobs) workflow=deploy-dev ;;
  stage:run) workflow=deploy-staging ;;
  *) echo "tree-proof.sh: unsupported $branch:$mode" >&2; exit 2 ;;
esac

# WHY: the checkout fetched every branch with full history, so no credentials are needed here.
git rev-parse -q --verify "refs/remotes/origin/$branch" >/dev/null || exit 0

# WHY: fails closed; any unreadable answer prints nothing and the caller runs full CI.
git log "origin/$branch" -n 300 --format='%H %T' | while read -r commit t; do
  [ "$t" = "$tree" ] || continue
  id=$(gh api "repos/$repo/actions/runs?head_sha=$commit&event=push&per_page=50" \
    --jq "[.workflow_runs[] | select(.name == \"$workflow\")] | sort_by(.run_number) | last | .id // empty" 2>/dev/null) || continue
  [ -n "$id" ] || continue
  if [ "$mode" = run ]; then
    ok=$(gh api "repos/$repo/actions/runs/$id" --jq '.conclusion == "success"' 2>/dev/null) || continue
  else
    ok=$(gh api "repos/$repo/actions/runs/$id/jobs?per_page=100" --jq '
      [.jobs[] | select(.name | startswith("checks / "))] as $j
      | ($j | length) > 0 and ($j | all(.conclusion == "success" or .conclusion == "skipped"))
        and ($j | any(.conclusion == "success"))' 2>/dev/null) || continue
  fi
  if [ "$ok" = true ]; then echo "$commit"; break; fi
done
