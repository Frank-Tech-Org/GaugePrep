#!/usr/bin/env bash
# Local cases for check-photo-credits.sh: bash .github/scripts/check-photo-credits.test.sh
cd "$(dirname "$0")/../.." || exit 1
check=.github/scripts/check-photo-credits.sh
fail=0
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
d="$tmp/d"
hdr=$'| Id | Source | Author | Licence | Commercial-use terms | Checked | Alt FR | Alt EN |\n| --- | --- | --- | --- | --- | --- | --- | --- |'

row() { printf '| %s | https://example.org/p/1 | A. Author | Example Licence | "free for commercial use" | 2026-11-26 | Un chronomètre | A stopwatch |\n' "$1"; }
photo() { head -c "${2:-5000}" /dev/zero >"$d/$1"; }
fresh() {
  rm -rf "$d"
  mkdir -p "$d"
  printf '%s\n' "$hdr" >"$d/CREDITS.md"
}
expect() { # name want [grep]
  out=$(bash "$check" "$d" 2>&1)
  got=$?
  if [ "$got" != "$2" ] || { [ -n "${3-}" ] && ! grep -Fq -- "$3" <<<"$out"; }; then
    echo "FAIL $1 (exit $got)"
    echo "$out"
    fail=1
  else
    echo "ok   $1"
  fi
}

fresh; row a-one >>"$d/CREDITS.md"; photo a-one-m.webp; photo a-one-l.webp
expect green 0
fresh
expect green-empty 0
rm -rf "$d"
expect green-no-folder 0
fresh; row a-one >>"$d/CREDITS.md"; photo a-one-m.webp; photo planted-m.webp
expect red-planted-photo 1 "Photo planted-m.webp has no entry"
fresh; photo lone.webp; rm "$d/CREDITS.md"
expect red-no-credits-file 1 "is missing"
fresh; row a-one >>"$d/CREDITS.md"; photo a-one-l.webp 120001
expect red-too-big 1 "a-one-l.webp is 120001 bytes"
fresh; row a-one >>"$d/CREDITS.md"; photo a-one-l.webp 120000
expect green-at-limit 0
fresh; row a-one | sed 's/ | Un chronomètre | / |  | /' >>"$d/CREDITS.md"; photo a-one-l.webp
expect red-no-alt-fr 1 "French alt text is empty"
fresh; row a-one | sed 's/ | A stopwatch |/ |  |/' >>"$d/CREDITS.md"; photo a-one-l.webp
expect red-no-alt-en 1 "English alt text is empty"
fresh; row a-one | sed 's/2026-11-26/26/' >>"$d/CREDITS.md"; photo a-one-l.webp
expect red-bad-date 1 "YYYY-MM-DD"
fresh; row a-one | sed 's/"free for commercial use"/free/' >>"$d/CREDITS.md"; photo a-one-l.webp
expect red-unquoted-terms 1 "quoted"
fresh; row a-one | sed 's#https://example.org/p/1#example.org#' >>"$d/CREDITS.md"; photo a-one-l.webp
expect red-source 1 "https link"
fresh; row a-one | sed 's/A. Author/ /' >>"$d/CREDITS.md"; photo a-one-l.webp
expect red-author 1 "author is empty"
fresh; row a-one >>"$d/CREDITS.md"; row a-one >>"$d/CREDITS.md"; photo a-one-l.webp
expect red-duplicate 1 "two rows"
fresh; row a-one >>"$d/CREDITS.md"; photo 'a one.webp'
expect red-unsafe-name 1 "characters other than"
fresh; row a-one >>"$d/CREDITS.md"; mkdir "$d/sub"; head -c 10 /dev/zero >"$d/sub/a-one-s.png"
expect green-subfolder 0
fresh; row a-one >>"$d/CREDITS.md"; photo a-one.tiff
expect green-any-format 0
fresh; row a-one >>"$d/CREDITS.md"; photo other.tiff
expect red-any-format 1 "other.tiff has no entry"
exit $fail
