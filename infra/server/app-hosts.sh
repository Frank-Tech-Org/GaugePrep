#!/usr/bin/env bash
# Attaches the dev and staging app hosts to their Pages projects and points DNS at them, or undoes it.
# Usage: app-hosts.sh <attach|detach> <dev|staging|both>   (asks for a DNS-edit token, never echoed)
set -euo pipefail

ACTION="${1:-}"
TARGET="${2:-}"
ZONE_NAME=gaugeprep.com
API=https://api.cloudflare.com/client/v4
SNAP_DIR="${SNAP_DIR:-./dns-snapshots}"

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
[[ "$ACTION" =~ ^(attach|detach)$ && "$TARGET" =~ ^(dev|staging|both)$ ]] || die "usage: app-hosts.sh <attach|detach> <dev|staging|both>"

# Args: token, method, path, then any curl options.
cf() {
  local token="$1" method="$2" path="$3"
  shift 3
  curl -fsS -X "$method" -H "Authorization: Bearer $token" -H 'Content-Type: application/json' "$API$path" "$@"
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
  snap="$SNAP_DIR/$env-$ACTION-$(date -u +%Y%m%dT%H%M%SZ)"
  recs=$(cf "$DNS_TOKEN" GET "/zones/$ZONE_ID/dns_records?name=$host")
  printf '%s\n' "$recs" | jq '[.result[] | {type, name, content, proxied}]' > "$snap-before.json"
  echo "$host before: $(jq -c . "$snap-before.json")"
  ids=$(printf '%s\n' "$recs" | jq -r '.result[] | select(.type=="A" or .type=="AAAA" or .type=="CNAME") | .id')

  if [ "$ACTION" = attach ]; then
    cf "$pages_token" POST "/accounts/$account_id/pages/projects/$project/domains" \
      --data "{\"name\":\"$host\"}" > /dev/null || echo "domain already attached to $project"
    for id in $ids; do cf "$DNS_TOKEN" DELETE "/zones/$ZONE_ID/dns_records/$id" > /dev/null; done
    cf "$DNS_TOKEN" POST "/zones/$ZONE_ID/dns_records" \
      --data "{\"type\":\"CNAME\",\"name\":\"$host\",\"content\":\"$project.pages.dev\",\"proxied\":true,\"ttl\":1}" > /dev/null
  else
    saved=$(printf "%s\n" "$SNAP_DIR/$env-attach-"*-before.json | sort | tail -1)
    [ -f "$saved" ] || die "no attach snapshot for $env in $SNAP_DIR"
    # SECURITY: without an A or AAAA record to restore, detach would leave the host with no DNS.
    jq -e 'any(.[]; .type=="A" or .type=="AAAA")' "$saved" > /dev/null || die "no A or AAAA record in $saved"
    cf "$pages_token" DELETE "/accounts/$account_id/pages/projects/$project/domains/$host" > /dev/null || echo "domain not attached"
    for id in $ids; do cf "$DNS_TOKEN" DELETE "/zones/$ZONE_ID/dns_records/$id" > /dev/null; done
    jq -c '.[] | select(.type=="A" or .type=="AAAA") | {type, name, content, proxied, ttl: 1}' "$saved" | while read -r rec; do
      cf "$DNS_TOKEN" POST "/zones/$ZONE_ID/dns_records" --data "$rec" > /dev/null
    done
  fi
  cf "$DNS_TOKEN" GET "/zones/$ZONE_ID/dns_records?name=$host" | jq '[.result[] | {type, name, content, proxied}]' > "$snap-after.json"
  echo "$host after: $(jq -c . "$snap-after.json")"
done
unset DNS_TOKEN

for env in "${hosts[@]}"; do
  host="$env.$ZONE_NAME"
  code=000
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
    code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' "https://$host/" || true)
    if [ "$ACTION" = attach ] && [ "$code" = 200 ]; then break; fi
    sleep 10
  done
  echo "$host status $code, answers: $(dig +short "$host" | tr '\n' ' ')"
done
for api in api.dev api.staging; do
  echo "$api.$ZONE_NAME health: $(curl -s -m 10 "https://$api.$ZONE_NAME/api/v1/health")"
done
