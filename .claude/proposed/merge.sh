#!/usr/bin/env bash
# The only way an agent merges, and only the CTO (the main Claude Code session) runs it. It squash-merges a reviewed work-branch PR into develop.
#   .claude/scripts/merge.sh <pr-number>
# Releases, tags and anything into main stay with the owner. The review verdict is the last line of a PR comment:
#   REVIEW: PASS <full head sha>      or      REVIEW: CHANGES <full head sha>
# The owner's GitHub approval of that same commit is required too.
set -euo pipefail

pr=${1:-}
[ $# -eq 1 ] && [[ "$pr" =~ ^[0-9]+$ ]] || { echo "merge.sh: usage: merge.sh <pr-number>" >&2; exit 2; }
repo=LinguaMentor/linguamentor-v3
owner=KefouegFrank
[ "$(git remote get-url origin)" = "https://github.com/$repo.git" ] \
  || { echo "merge.sh: origin is not the LinguaMentor repository" >&2; exit 2; }

fail() { echo "merge.sh: refused, $1" >&2; exit 1; }
# gh --paginate prints one JSON array per page; slurp and join them so no page is skipped.
all() { gh api --paginate "$1" | jq -s 'map(if type == "array" then . else [.] end) | add // []'; }

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
[ "$(field .head.sha)" = "$sha" ] || fail "the branch moved while checking; run again"

# Guardrail, CI, secret-scan config and settings files belong to the owner.
owner_files=$(all "repos/$repo/pulls/$pr/files?per_page=100" | jq -r '[.[] | .filename, (.previous_filename // "") | select(test("^\\.claude/(hooks/|settings|scripts/(push|merge)\\.sh)|^\\.github/workflows/|^\\.gitleaks(\\.toml|ignore)$"))] | join(", ")')
[ -z "$owner_files" ] || fail "it changes owner-only files ($owner_files); the owner merges this one"

# CI fails closed: at least one check must exist on the head commit and all must have passed.
# Workflow runs, not check runs: the agent's fine-grained token cannot be given the Checks permission.
runs=$(all "repos/$repo/actions/runs?head_sha=$sha&per_page=100" | jq '[.[] | .workflow_runs[]?]')
statuses=$(gh api "repos/$repo/commits/$sha/status")
[ "$(printf '%s' "$runs" | jq length)" -gt 0 ] || [ "$(printf '%s' "$statuses" | jq '.statuses | length')" -gt 0 ] \
  || fail "no CI checks exist on this commit; the owner merges until CI is in place"
# A run cancelled because a newer run of the same workflow superseded it is not a failure: only the newest run of each workflow counts.
bad=$(printf '%s' "$runs" | jq -r 'group_by(.workflow_id) | map(max_by(.run_number)) | [.[] | select(.status != "completed" or (.conclusion | IN("success","neutral","skipped") | not)) | .name] | join(", ")')
[ -z "$bad" ] || fail "checks not green: $bad"
if [ "$(printf '%s' "$statuses" | jq '.statuses | length')" -gt 0 ]; then
  [ "$(printf '%s' "$statuses" | jq -r .state)" = success ] || fail "commit statuses are not all success"
fi

# The newest verdict must be PASS for this exact commit. A verdict is the final line of a comment, nothing quoted.
verdict=$(all "repos/$repo/issues/$pr/comments?per_page=100" | jq -r '
  [.[] | {t: .created_at, last: (.body | rtrimstr("\n") | split("\n") | last // "" | gsub("\\s+$"; ""))}
       | select(.last | test("^REVIEW: (PASS|CHANGES) [0-9a-f]{40}$"))]
  | sort_by(.t) | last // empty | .last')
[ -n "$verdict" ] || fail "no review verdict comment; run /lm-next"
[ "$verdict" = "REVIEW: PASS $sha" ] || fail "the latest verdict is '$verdict', not a PASS for $sha; review again"

# The owner's latest decisive review must approve this exact commit; a later push makes it stale.
approval=$(all "repos/$repo/pulls/$pr/reviews?per_page=100" | jq -r --arg o "$owner" '
  [.[] | select(.user.login == $o and (.state | IN("APPROVED", "CHANGES_REQUESTED", "DISMISSED")))]
  | sort_by(.submitted_at) | last // empty | "\(.state) \(.commit_id)"')
[ "$approval" = "APPROVED $sha" ] || fail "the owner has not approved $sha; ask them to approve PR #$pr"

# The squash commit carries the PR body's ticket refs, so `git log --grep "#<n>"` finds every change of a ticket.
refs=$(field .body | grep -oE 'Refs #[0-9]+' | sort -u || true)
msg=(-f commit_title="$(field .title) (#$pr)")
[ -z "$refs" ] || msg+=(-f commit_message="$refs")

# Merge exactly the reviewed commit; GitHub rejects it if the branch moved since.
gh api -X PUT "repos/$repo/pulls/$pr/merge" -f merge_method=squash -f sha="$sha" "${msg[@]}" --jq .message
# The repository may delete merged branches itself; only a branch that still exists after a failed delete is an error.
if ! gh api -X DELETE "repos/$repo/git/refs/heads/$head" >/dev/null 2>&1 \
  && gh api "repos/$repo/branches/$head" >/dev/null 2>&1; then
  echo "merge.sh: merged #$pr but could not delete $head" >&2; exit 1
fi
echo "merge.sh: merged #$pr; $head is deleted"
