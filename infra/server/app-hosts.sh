#!/usr/bin/env bash
# Attaches the dev and staging app hosts to their Pages projects, or puts the old DNS back.
# Usage: app-hosts.sh <attach|detach> <dev|staging|both>   (reads a DNS-edit token, never echoed)
set -euo pipefail

ACTION="${1:-}"
TARGET="${2:-}"
ZONE_NAME=gaugeprep.com
API=https://api.cloudflare.com/client/v4
SNAP_DIR="${SNAP_DIR:-./dns-snapshots}"

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
[[ "$ACTION" =~ ^(attach|detach)$ && "$TARGET" =~ ^(dev|staging|both)$ ]] || die "usage: app-hosts.sh <attach|detach> <dev|staging|both>"

cf() {
  local token="$1" method="$2" path="$3"
  shift 3
  curl -fsS -X "$method" -H "Authorization: Bearer $token" -H 'Content-Type: application/json' "$API$path" "$@"
}

# Recreates the A and AAAA records of the snapshot file given, with their proxied flag and ttl.
restore_records() {
  jq -c '.[] | select(.type=="A" or .type=="AAAA") | {type, name, content, proxied, ttl: (.ttl // 1)}' "$1" |
    while read -r rec; do
      cf "$DNS_TOKEN" POST "/zones/$ZONE_ID/dns_records" --data "$rec" > /dev/null || return 1
    done
}

read -rs -p "Cloudflare token with DNS edit on $ZONE_NAME: " DNS_TOKEN
echo
ZONE_ID=$(cf "$DNS_TOKEN" GET "/zones?name=$ZONE_NAME" | jq -r '.result[0].id // empty')
[ -n "$ZONE_ID" ] || die "token sees no zone $ZONE_NAME"

mkdir -p "$SNAP_DIR"
hosts=(dev staging)
if [ "$TARGET" != both ]; then hosts=("$TARGET"); fi

for env in "${hosts[@]}"; do
  host="$env.$ZONE_NAME"
  project="gaugeprep-$env"
  config=dev
  if [ "$env" = staging ]; then config=stg; fi
  pages_token=$(doppler secrets get CLOUDFLARE_API_TOKEN --project gaugeprep --config "$config" --plain)
  account_id=$(doppler secrets get CLOUDFLARE_ACCOUNT_ID --project gaugeprep --config "$config" --plain)
  domains="/accounts/$account_id/pages/projects/$project/domains"
  snap="$SNAP_DIR/$env-$ACTION-$(date -u +%Y%m%dT%H%M%SZ)"
  recs=$(cf "$DNS_TOKEN" GET "/zones/$ZONE_ID/dns_records?name=$host")
  before=$(printf '%s\n' "$recs" | jq -c '[.result[] | {type, name, content, proxied, ttl}]')
  echo "$host before: $before"
  ids=$(printf '%s\n' "$recs" | jq -r '.result[] | select(.type=="A" or .type=="AAAA" or .type=="CNAME") | .id')
  attached_dns=$(printf '%s\n' "$before" | jq --arg t "$project.pages.dev" 'any(.[]; .type=="CNAME" and .content==$t)')

  if [ "$ACTION" = attach ]; then
    # WHY: a repeat attach must not overwrite the snapshot of the original A records.
    if [ "$attached_dns" = false ]; then printf '%s\n' "$before" > "$snap-before.json"; fi
    if ! cf "$pages_token" GET "$domains/$host" > /dev/null 2>&1; then
      cf "$pages_token" POST "$domains" --data "{\"name\":\"$host\"}" > /dev/null || die "Pages refused the domain $host"
    fi
    if [ "$attached_dns" = false ]; then
      for id in $ids; do
        cf "$DNS_TOKEN" DELETE "/zones/$ZONE_ID/dns_records/$id" > /dev/null ||
          { restore_records "$snap-before.json"; die "deleting records for $host failed, old records restored"; }
      done
      cf "$DNS_TOKEN" POST "/zones/$ZONE_ID/dns_records" \
        --data "{\"type\":\"CNAME\",\"name\":\"$host\",\"content\":\"$project.pages.dev\",\"proxied\":true,\"ttl\":1}" > /dev/null ||
        { restore_records "$snap-before.json"; die "CNAME for $host failed, old records restored"; }
    fi
  else
    # WHY: the newest snapshot with an A or AAAA record is the one worth restoring.
    saved=""
    for f in $(printf '%s\n' "$SNAP_DIR/$env-attach-"*-before.json | sort -r); do
      if [ -f "$f" ] && jq -e 'any(.[]; .type=="A" or .type=="AAAA")' "$f" > /dev/null; then saved="$f"; break; fi
    done
    [ -n "$saved" ] || die "no attach snapshot with an A or AAAA record for $env in $SNAP_DIR"
    printf '%s\n' "$before" > "$snap-before.json"
    cf "$pages_token" DELETE "$domains/$host" > /dev/null 2>&1 || echo "domain was not attached to $project"
    for id in $ids; do
      cf "$DNS_TOKEN" DELETE "/zones/$ZONE_ID/dns_records/$id" > /dev/null || die "deleting records for $host failed; rerun detach"
    done
    restore_records "$saved" || die "restoring $host from $saved failed; the host has no DNS until it is rerun"
  fi
  after=$(cf "$DNS_TOKEN" GET "/zones/$ZONE_ID/dns_records?name=$host" | jq -c '[.result[] | {type, name, content, proxied, ttl}]')
  printf '%s\n' "$after" > "$snap-after.json"
  echo "$host after: $after"
done
unset DNS_TOKEN

failed=0
for env in "${hosts[@]}"; do
  host="$env.$ZONE_NAME"
  code=000
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
    code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' "https://$host/" || true)
    if [ "$ACTION" = attach ] && [ "$code" = 200 ]; then break; fi
    sleep 10
  done
  echo "$host status $code, answers: $(dig +short "$host" | tr '\n' ' ')"
  if [ "$ACTION" = attach ] && [ "$code" != 200 ]; then failed=1; fi
done
for env in "${hosts[@]}"; do
  health=$(curl -s -m 10 "https://api.$env.$ZONE_NAME/api/v1/health" || true)
  echo "api.$env.$ZONE_NAME health: $health"
  if ! printf '%s' "$health" | jq -e '.status == "ok"' > /dev/null 2>&1; then failed=1; fi
done
exit "$failed"
