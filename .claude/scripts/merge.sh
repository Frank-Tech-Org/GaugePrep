#!/usr/bin/env bash
# The only way an agent merges, and only the tech-lead runs it. It squash-merges a reviewed work-branch PR into develop.
#   .claude/scripts/merge.sh <pr-number>
# Releases, tags and anything into main stay with the owner.
set -euo pipefail

pr=${1:-}
[ $# -eq 1 ] && [[ "$pr" =~ ^[0-9]+$ ]] || { echo "merge.sh: usage: merge.sh <pr-number>" >&2; exit 2; }
repo=LinguaMentor/linguamentor-v3
[ "$(git remote get-url origin)" = "https://github.com/$repo.git" ] \
  || { echo "merge.sh: origin is not the LinguaMentor repository" >&2; exit 2; }

fail() { echo "merge.sh: refused, $1" >&2; exit 1; }

info=$(gh api "repos/$repo/pulls/$pr")
field() { printf '%s' "$info" | jq -r "$1"; }

[ "$(field .state)" = open ] || fail "PR #$pr is not open"
[ "$(field .draft)" = false ] || fail "PR #$pr is a draft"
[ "$(field .base.ref)" = develop ] || fail "base is '$(field .base.ref)', only develop is allowed"
head=$(field .head.ref)
[[ "$head" =~ ^(feature|chore)/[A-Za-z0-9._-]+$ ]] || fail "'$head' is not a feature or chore branch"
[ "$(field .head.repo.full_name)" = "$repo" ] || fail "the branch comes from a fork"
sha=$(field .head.sha)

# Mergeability is computed lazily by GitHub, so ask a few times before giving up.
for _ in 1 2 3 4 5; do
  [ "$(field .mergeable)" != null ] && break
  sleep 2; info=$(gh api "repos/$repo/pulls/$pr")
done
[ "$(field .mergeable)" = true ] || fail "PR #$pr has conflicts or its mergeability is unknown"

# Every check on the head commit must have passed. With no checks at all (before CI exists) it merges, and says so.
runs=$(gh api "repos/$repo/commits/$sha/check-runs" --jq '.check_runs')
bad=$(printf '%s' "$runs" | jq -r '[.[] | select(.status != "completed" or (.conclusion | IN("success","neutral","skipped") | not)) | .name] | join(", ")')
[ -z "$bad" ] || fail "checks not green: $bad"
if [ "$(printf '%s' "$runs" | jq length)" = 0 ]; then echo "merge.sh: note, no CI checks exist on this commit"; fi

# The latest review verdict must be PASS and must come after the last commit.
verdict=$(gh api "repos/$repo/issues/$pr/comments" --paginate --jq '[.[] | select(.body | test("REVIEW: (PASS|CHANGES)")) | {t: .created_at, v: (.body | capture("REVIEW: (?<v>PASS|CHANGES)").v)}] | last // empty | "\(.v) \(.t)"')
[ -n "$verdict" ] || fail "no 'REVIEW: PASS' comment from /lm-review"
[ "${verdict%% *}" = PASS ] || fail "the latest review verdict is CHANGES"
committed=$(gh api "repos/$repo/commits/$sha" --jq .commit.committer.date)
[[ "${verdict#* }" > "$committed" ]] || fail "the PASS verdict is older than the last commit; review again"

# Pinned to the reviewed sha, so a push after the review cannot slip in.
gh api -X PUT "repos/$repo/pulls/$pr/merge" -f merge_method=squash -f sha="$sha" --jq .message
gh api -X DELETE "repos/$repo/git/refs/heads/$head" >/dev/null && echo "merge.sh: merged #$pr and deleted $head"
