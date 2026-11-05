#!/usr/bin/env bash
# Compares the keys of .env.example and .env. Prints key names only, never a value, so agents can run it.
#   env-check.sh          list keys missing from .env, keys missing from .env.example, and keys still empty in .env
#   env-check.sh --add    also append each key missing from .env with an empty value, for the owner to fill
# Exits 1 while .env lacks a key that .env.example has.
set -euo pipefail

# .env.example comes from this checkout; .env lives only in the main checkout, which ticket worktrees share.
EXAMPLE="$(git rev-parse --show-toplevel)/.env.example"
LOCAL="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/.env"

[ -f "$EXAMPLE" ] || { echo "No $EXAMPLE in the repository root" >&2; exit 2; }
[ "${1:-}" = "--add" ] && [ ! -f "$LOCAL" ] && touch "$LOCAL" && chmod 600 "$LOCAL"
[ -f "$LOCAL" ] || { echo "No $LOCAL yet: run with --add to create it from $EXAMPLE"; exit 1; }

# KEY=value lines, with or without "export"; comments and blank lines are skipped.
keys() { sed -nE 's/^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)=.*/\2/p' "$1"; }
empty_keys() {
  sed -nE 's/^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)=[[:space:]]*(""|'"''"')?[[:space:]]*$/\2/p' "$1"
}

missing=$(comm -23 <(keys "$EXAMPLE" | sort -u) <(keys "$LOCAL" | sort -u))
extra=$(comm -13 <(keys "$EXAMPLE" | sort -u) <(keys "$LOCAL" | sort -u))
empty=$(empty_keys "$LOCAL" | sort -u)

if [ "${1:-}" = "--add" ] && [ -n "$missing" ]; then
  # Appended in .env.example order so the two files read alike.
  [ -s "$LOCAL" ] && [ -n "$(tail -c1 "$LOCAL")" ] && echo >> "$LOCAL"
  keys "$EXAMPLE" | grep -Fxf <(echo "$missing") | sed 's/$/=/' >> "$LOCAL"
  echo "Added to $LOCAL with empty values: $(echo $missing | tr ' ' ',' | sed 's/,/, /g')"
  empty=$(empty_keys "$LOCAL" | sort -u); missing=""
fi

list() { [ -n "$1" ] && echo "$1" | paste -sd, - | sed 's/,/, /g' || echo "(none)"; }
echo "In $EXAMPLE but missing from $LOCAL: $(list "$missing")"
echo "In $LOCAL but missing from $EXAMPLE: $(list "$extra")"
echo "Empty in $LOCAL (owner pastes the value): $(list "$empty")"
[ -z "$missing" ]
