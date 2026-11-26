#!/usr/bin/env bash
# Checks that every photo in a folder has a complete row in its CREDITS.md and fits the size limit.
# Usage: check-photo-credits.sh [photos-dir]   (default apps/web/public/photos)
set -u
dir=${1:-apps/web/public/photos}
credits="$dir/CREDITS.md"
limit=120000 # bytes
errors=()
declare -A ids=()

trim() {
  local s=$1
  s=${s#"${s%%[![:space:]]*}"}
  printf '%s' "${s%"${s##*[![:space:]]}"}"
}
safe() { printf '%q' "$1"; }

photos=()
if [ -d "$dir" ]; then
  mapfile -d '' photos < <(find "$dir" -type f ! -name CREDITS.md -print0 | sort -z)
fi

if [ -r "$credits" ]; then
  while IFS='|' read -r _ id src author lic terms checked altfr alten _; do
    id=$(trim "$id")
    case "$id" in "" | Id | -*) continue ;; esac
    src=$(trim "$src")
    author=$(trim "$author")
    lic=$(trim "$lic")
    terms=$(trim "$terms")
    checked=$(trim "$checked")
    altfr=$(trim "$altfr")
    alten=$(trim "$alten")
    if [ -n "${ids[$id]+x}" ]; then
      errors+=("Credits list has two rows for $(safe "$id").")
    fi
    ids[$id]=1
    [[ "$src" =~ ^https://[^[:space:]]+$ ]] || errors+=("$(safe "$id"): source must be an https link.")
    [ -n "$author" ] || errors+=("$(safe "$id"): author is empty.")
    [ -n "$lic" ] || errors+=("$(safe "$id"): licence is empty.")
    [[ "$terms" =~ ^\".+\"$ ]] || errors+=("$(safe "$id"): commercial-use terms must be quoted from the licence page.")
    [[ "$checked" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || errors+=("$(safe "$id"): check date must be YYYY-MM-DD.")
    [ -n "$altfr" ] || errors+=("$(safe "$id"): French alt text is empty.")
    [ -n "$alten" ] || errors+=("$(safe "$id"): English alt text is empty.")
  done < <(tr -d '\r' <"$credits" | grep '^|')
elif [ "${#photos[@]}" -gt 0 ]; then
  errors+=("$(safe "$credits") is missing but $dir holds photos.")
fi

for f in "${photos[@]}"; do
  name=${f#"$dir"/}
  if ! [[ "$name" =~ ^[A-Za-z0-9._/-]+$ ]]; then
    errors+=("Photo $(safe "$name") has characters other than letters, digits, dot, dash, underscore.")
    continue
  fi
  base=${name##*/}
  id=${base%.*}
  id=${id%-[sml]}
  [ -n "${ids[$id]+x}" ] || errors+=("Photo $name has no entry in CREDITS.md (expected a row with Id $id).")
  size=$(stat -c %s "$f")
  [ "$size" -le "$limit" ] || errors+=("Photo $name is $size bytes; the limit is $limit.")
done

if [ "${#errors[@]}" -gt 0 ]; then
  printf 'Photo credits check failed:\n'
  printf ' - %s\n' "${errors[@]}"
  exit 1
fi
echo "Photo credits check passed (${#photos[@]} files)."
