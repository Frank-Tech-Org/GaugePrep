#!/usr/bin/env bash
# Board helper for org project #6, shared by the /lm-* commands.
#   board.sh list [Status]          issues on the board, optionally one column
#   board.sh wip                    tickets in flight (In progress, In review, In QA)
#   board.sh info <n>               type, area, priority, status, sprint, blockers
#   board.sh move <n> <Status>      set the Status column (adds the issue to the board if missing)
#   board.sh block <n> <blocker>    link "<n> blocked by <blocker>"; label unless it is resolved
#   board.sh unblock <n> <blocker>  remove that link; drops the label when no blocker is left
#   board.sh sweep                  drop the blocked label where the issue or its blockers are done
#   board.sh set <n> <Field> <Opt>  set an org issue field: Priority, Area or Effort
#   board.sh type <n> <Type>        set the issue type: Epic, Story, Task, Bug, Chore, Decision, ...
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

status_in() {
  jq -r --argjson n "$2" '.items[] | select(.content.number == $n) | .status // "-"' <<<"$1"
}

status_of() { status_in "$(items)" "$1"; }

# WHY: a blocker counts as resolved at Ready to deploy, so a closed or shipped one blocks nothing.
resolved() {
  local state=$1 status=$2
  [ "$state" = closed ] || [ "$state" = CLOSED ] \
    || [ "$status" = "Ready to deploy" ] || [ "$status" = Done ]
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
  local n=$1 blocker=$2 issue id state status
  issue=$(gh api "repos/$REPO/issues/$blocker" --jq '"\(.id) \(.state)"')
  read -r id state <<<"$issue"
  gh api -X POST "repos/$REPO/issues/$n/dependencies/blocked_by" -F issue_id="$id" >/dev/null
  status=$(status_of "$blocker")
  if resolved "$state" "$status"; then
    echo "#$n blocked by #$blocker, already $state and $status: no blocked label"
    return
  fi
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

# WARNING: every read is captured before its loop; a read in < <(...) fails silently under set -e.
sweep() {
  local board labelled deps n state b bstate open clear=()
  board=$(items)
  labelled=$(gh issue list --repo "$REPO" --label blocked --state all --limit 500 \
    --json number,state --jq '.[] | "\(.number) \(.state)"')
  while read -r n state; do
    [ -n "$n" ] || continue
    if [ "$state" = CLOSED ]; then
      echo "#$n: drop the label (issue closed)"; clear+=("$n"); continue
    fi
    deps=$(gh api "repos/$REPO/issues/$n/dependencies/blocked_by" --jq '.[] | "\(.number) \(.state)"')
    open=""
    while read -r b bstate; do
      [ -n "$b" ] || continue
      resolved "$bstate" "$(status_in "$board" "$b")" || open="$open #$b"
    done <<<"$deps"
    if [ -z "$open" ]; then
      echo "#$n: drop the label (no open blocker)"; clear+=("$n")
    else
      echo "#$n: keep the label, blocked by$open"
    fi
  done <<<"$labelled"
  [ "${#clear[@]}" -gt 0 ] || { echo "Nothing to change."; return; }
  for n in "${clear[@]}"; do
    gh issue edit "$n" --repo "$REPO" --remove-label blocked >/dev/null
  done
  echo "Dropped the blocked label from ${#clear[@]} issues."
}

issue_id() {
  gh api graphql -F n="$1" -f query='query($n: Int!) {
    repository(owner: "Frank-Tech-Org", name: "GaugePrep") { issue(number: $n) { id } } }' \
    --jq .data.repository.issue.id
}

set_field() {
  local n=$1 field=$2 value=$3 fields fid oid
  # WHY: REST lists org issue fields for the agents' token; GraphQL then gives the option IDs.
  fields=$(gh api "orgs/$OWNER/issue-fields") || { echo "could not read issue fields" >&2; exit 1; }
  fid=$(jq -r --arg f "$field" '.[] | select(.name == $f) | .node_id' <<<"$fields")
  [ -n "$fid" ] || { echo "No issue field named '$field'" >&2; exit 1; }
  oid=$(gh api graphql -f id="$fid" -f query='query($id: ID!) {
    node(id: $id) { ... on IssueFieldSingleSelect { options { id name } } } }' \
    | jq -r --arg v "$value" '.data.node.options[]? | select(.name == $v) | .id')
  [ -n "$oid" ] || { echo "No $field option named '$value'" >&2; exit 1; }
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
  sweep) sweep ;;
  set) set_field "$1" "$2" "$3" ;;
  type) set_type "$1" "$2" ;;
  sprint) sprint "$1" "$2" ;;
  *) sed -n '2,12p' "$0"; exit 1 ;;
esac
