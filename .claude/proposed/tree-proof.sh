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

run_id() {
  gh api "repos/$repo/actions/runs?head_sha=$1&event=push&per_page=50" \
    --jq "[.workflow_runs[] | select(.name == \"$workflow\")] | sort_by(.run_number) | last | .id // empty" 2>/dev/null
}

# WHY: a docs-only commit skips the code jobs, so its green run proves nothing about the code.
# Walks first parents to the nearest commit that ran them; fails closed on red or no answer.
code_checks_passed() {
  local c=$1 id r n=0
  while [ "$n" -lt 25 ]; do
    id=$(run_id "$c") || return 1
    if [ -n "$id" ]; then
      r=$(gh api "repos/$repo/actions/runs/$id/jobs?per_page=100" \
        --jq '[.jobs[] | select(.name == "checks / check")] | first | .conclusion // "none"' 2>/dev/null) || return 1
      case "$r" in
        success) return 0 ;;
        skipped|none) ;;
        *) return 1 ;;
      esac
    fi
    c=$(git rev-parse -q --verify "$c^1") || return 1
    n=$((n + 1))
  done
  return 1
}

# WHY: fails closed; any unreadable answer prints nothing and the caller runs full CI.
git log "origin/$branch" -n 300 --format='%H %T' | while read -r commit t; do
  [ "$t" = "$tree" ] || continue
  id=$(run_id "$commit") || continue
  [ -n "$id" ] || continue
  if [ "$mode" = run ]; then
    ok=$(gh api "repos/$repo/actions/runs/$id" --jq '.conclusion == "success"' 2>/dev/null) || continue
  else
    ok=$(gh api "repos/$repo/actions/runs/$id/jobs?per_page=100" --jq '
      [.jobs[] | select(.name | startswith("checks / "))] as $j
      | ($j | length) > 0 and ($j | all(.conclusion == "success" or .conclusion == "skipped"))
        and ($j | any(.conclusion == "success"))' 2>/dev/null) || continue
    [ "$ok" = true ] && { code_checks_passed "$commit" || ok=false; }
  fi
  if [ "$ok" = true ]; then echo "$commit"; break; fi
done
