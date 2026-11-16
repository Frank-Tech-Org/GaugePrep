#!/usr/bin/env bash
# Board helper for org project #6, shared by the /lm-* commands.
#   board.sh list [Status]          issues on the board, optionally one column
#   board.sh wip                    tickets in flight (In progress, In review, In QA); the limit is 2, or 3 once CI exists
#   board.sh info <n>               type, area, priority, status, sprint, blockers
#   board.sh move <n> <Status>      set the Status column (adds the issue to the board if missing)
#   board.sh block <n> <blocker>    record "<n> is blocked by <blocker>" and add the blocked label
#   board.sh unblock <n> <blocker>  remove that link; drops the label when no blocker is left
#   board.sh set <n> <Field> <Opt>  set an org issue field: Priority, Area or Effort
#   board.sh type <n> <Type>        set the issue type: Epic, Story, Task, Bug, Chore, Decision, Spike, Refactor
#   board.sh sprint <n> <Sprint>    put the issue in a sprint, e.g. "Sprint 2"
set -euo pipefail

OWNER=Frank-Tech-Org
PROJECT=6
REPO=Frank-Tech-Org/GaugePrep
WIP_COLUMNS='["In progress","In review","In QA"]'

items() { gh project item-list "$PROJECT" --owner "$OWNER" --limit 500 --format json; }

list() {
  items | jq -r --arg s "${1:-}" '.items[]
    | select(.content.type == "Issue" and ($s == "" or .status == $s))
    | "#\(.content.number)\t\(.status // "-")\t\(.sprint.title // "-")\t\(.title)"'
}

wip() {
  items | jq -r --argjson w "$WIP_COLUMNS" '.items[]
    | select(.content.type == "Issue" and (.status as $s | $w | index($s)))
    | "#\(.content.number)\t\(.status)\t\(.title)"'
}

status_of() {
  items | jq -r --argjson n "$1" '.items[] | select(.content.number == $n) | .status // "-"'
}

info() {
  local n=$1
  gh api graphql -F n="$n" -f query='query($n: Int!) {
    repository(owner: "Frank-Tech-Org", name: "GaugePrep") { issue(number: $n) {
      number title state issueType { name } milestone { title }
      issueFieldValues(first: 10) { nodes { ... on IssueFieldSingleSelectValue { name field { ... on IssueFieldSingleSelect { name } } } } }
    } } }' | jq -r '.data.repository.issue
      | "#\(.number) \(.title)\nstate: \(.state)  type: \(.issueType.name // "-")  milestone: \(.milestone.title // "-")",
        (.issueFieldValues.nodes[] | select(.field) | "\(.field.name | ascii_downcase): \(.name)")'
  echo "status: $(status_of "$n")"
  local blockers
  blockers=$(gh api "repos/$REPO/issues/$n/dependencies/blocked_by" --jq '.[].number')
  for b in $blockers; do echo "blocked by: #$b ($(status_of "$b"))"; done
}

move() {
  local n=$1 target=$2 pid fid oid item
  pid=$(gh project view "$PROJECT" --owner "$OWNER" --format json --jq .id)
  read -r fid oid < <(gh project field-list "$PROJECT" --owner "$OWNER" --format json \
    | jq -r --arg t "$target" '.fields[] | select(.name == "Status")
        | "\(.id) \(.options[] | select(.name == $t) | .id)"') || true
  [ -n "${oid:-}" ] || { echo "No Status column named '$target'" >&2; exit 1; }
  item=$(gh project item-add "$PROJECT" --owner "$OWNER" --url "https://github.com/$REPO/issues/$n" --format json --jq .id)
  gh project item-edit --id "$item" --project-id "$pid" --field-id "$fid" --single-select-option-id "$oid" >/dev/null
  echo "#$n -> $target"
}

sprint() {
  local n=$1 title=$2 pid fid iid item
  pid=$(gh project view "$PROJECT" --owner "$OWNER" --format json --jq .id)
  read -r fid iid < <(gh api graphql -f query='{ organization(login: "Frank-Tech-Org") { projectV2(number: 6) {
      field(name: "Sprint") { ... on ProjectV2IterationField { id configuration { iterations { id title } } } } } } }' \
    | jq -r --arg t "$title" '.data.organization.projectV2.field
        | "\(.id) \(.configuration.iterations[] | select(.title == $t) | .id)"') || true
  [ -n "${iid:-}" ] || { echo "No open sprint named '$title'" >&2; exit 1; }
  item=$(gh project item-add "$PROJECT" --owner "$OWNER" --url "https://github.com/$REPO/issues/$n" --format json --jq .id)
  gh project item-edit --id "$item" --project-id "$pid" --field-id "$fid" --iteration-id "$iid" >/dev/null
  echo "#$n -> $title"
}

block() {
  local n=$1 blocker=$2 id
  id=$(gh api "repos/$REPO/issues/$blocker" --jq .id)
  gh api -X POST "repos/$REPO/issues/$n/dependencies/blocked_by" -F issue_id="$id" >/dev/null
  gh issue edit "$n" --repo "$REPO" --add-label blocked >/dev/null
  echo "#$n blocked by #$blocker"
}

unblock() {
  local n=$1 blocker=$2 id
  id=$(gh api "repos/$REPO/issues/$blocker" --jq .id)
  gh api -X DELETE "repos/$REPO/issues/$n/dependencies/blocked_by/$id" >/dev/null
  if [ -z "$(gh api "repos/$REPO/issues/$n/dependencies/blocked_by" --jq '.[].number')" ]; then
    gh issue edit "$n" --repo "$REPO" --remove-label blocked >/dev/null
  fi
  echo "#$n no longer blocked by #$blocker"
}

issue_id() {
  gh api graphql -F n="$1" -f query='query($n: Int!) {
    repository(owner: "Frank-Tech-Org", name: "GaugePrep") { issue(number: $n) { id } } }' \
    --jq .data.repository.issue.id
}

set_field() {
  local n=$1 field=$2 value=$3 fid oid pages
  # The agents' token can't list org issue fields, so the field and its options are read from issues that use it.
  pages=$(gh api graphql --paginate -f query='query($endCursor: String) { repository(owner: "Frank-Tech-Org", name: "GaugePrep") {
      issues(first: 100, after: $endCursor, states: [OPEN, CLOSED]) { pageInfo { hasNextPage endCursor } nodes { issueFieldValues(first: 10) { nodes {
        ... on IssueFieldSingleSelectValue { field { ... on IssueFieldSingleSelect { id name options { id name } } } } } } } } } }')
  read -r fid oid < <(jq -rs --arg f "$field" --arg v "$value" '[.[].data.repository.issues.nodes[].issueFieldValues.nodes[].field
        | select(. and .name == $f)] | first // empty | "\(.id) \(.options[] | select(.name == $v) | .id)"' <<<"$pages") || true
  [ -n "${oid:-}" ] || { echo "No $field option named '$value' (or no issue uses $field yet)" >&2; exit 1; }
  gh api graphql -f i="$(issue_id "$n")" -f f="$fid" -f o="$oid" -f query='mutation($i: ID!, $f: ID!, $o: ID!) {
    setIssueFieldValue(input: { issueId: $i, issueFields: [{ fieldId: $f, singleSelectOptionId: $o }] }) { clientMutationId } }' >/dev/null
  echo "#$n $field: $value"
}

set_type() {
  local n=$1 type=$2 got
  # REST takes the type by name; the agents' token can't list org issue types through GraphQL.
  got=$(gh api -X PATCH "repos/$REPO/issues/$n" -f type="$type" --jq '.type.name // empty' 2>&1) || true
  [ "$got" = "$type" ] || { echo "Could not set #$n to type '$type' (unknown type, or: $got)" >&2; exit 1; }
  echo "#$n type: $type"
}

cmd=${1:-}; shift || true
case "$cmd" in
  list) list "${1:-}" ;;
  wip) wip ;;
  info) info "$1" ;;
  move) move "$1" "$2" ;;
  block) block "$1" "$2" ;;
  unblock) unblock "$1" "$2" ;;
  set) set_field "$1" "$2" "$3" ;;
  type) set_type "$1" "$2" ;;
  sprint) sprint "$1" "$2" ;;
  *) sed -n '2,11p' "$0"; exit 1 ;;
esac
