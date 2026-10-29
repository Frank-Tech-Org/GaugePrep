#!/usr/bin/env bash
# PreToolUse(Bash): blocks the few destructive or release actions agents must never take. Everything else passes.
# It parses the command into real words, so a commit message that mentions "push" or a "$" in a script is fine.
# The strong limits are the deny rules in settings.json and the GitHub workflows; this hook is a second net.
set -uo pipefail

command -v jq >/dev/null 2>&1 || { echo "guard-bash: jq is required (sudo apt install -y jq)" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "guard-bash: python3 is required" >&2; exit 2; }
CMD=$(jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

printf '%s' "$CMD" | python3 -I -c '
import re, shlex, sys

cmd = sys.stdin.read()

def block(why):
    print(f"Blocked: {why}. The owner runs this; hand it over instead.", file=sys.stderr)
    sys.exit(2)

# Split on shell separators outside quotes, then read each simple command as words.
lexer = shlex.shlex(cmd, posix=True, punctuation_chars=";&|\n")
lexer.whitespace_split = True
words, segments = [], []
try:
    for tok in lexer:
        if set(tok) <= set(";&|\n"):
            segments.append(words); words = []
        else:
            words.append(tok)
    segments.append(words)
except ValueError:
    block("a command I cannot read safely (unbalanced quotes)")

def sub(words, tool):
    """First non-option word after the tool name, skipping option values git/gh take."""
    i = 1
    while i < len(words):
        w = words[i]
        if w in ("-C", "-c", "--git-dir", "--work-tree", "-R", "--repo"):
            i += 2; continue
        if w.startswith("-"):
            i += 1; continue
        return w, words[i + 1:]
    return "", []

for w in segments:
    if not w:
        continue
    if w[0] in ("sudo", "env", "command", "time", "nohup"):
        w = w[1:]
        if not w:
            continue
    prog = w[0].rsplit("/", 1)[-1]
    if prog == "git":
        verb, rest = sub(w, "git")
        if verb == "push":
            block("a raw git push (use .claude/scripts/push.sh)")
        if verb == "tag" and any(not a.startswith("-") or a in ("-a", "-s", "-f", "-d") for a in rest):
            block("creating or deleting a tag")
        if verb == "commit" and "--amend" in rest:
            block("amending a commit")
        if verb == "reset" and "--hard" in rest:
            block("git reset --hard discards work")
        if verb == "clean" and any(re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", a) for a in rest):
            block("git clean -f deletes untracked files")
    elif prog == "gh":
        verb, rest = sub(w, "gh")
        action = rest[0] if rest else ""
        if verb == "pr" and action == "merge":
            block("merging a PR (use .claude/scripts/merge.sh)")
        if verb == "release" and action in ("create", "delete", "edit"):
            block("publishing a release")
        if verb in ("repo", "issue") and action == "delete":
            block("deleting a repository or issue")
        if verb == "api" and any(a.upper() in ("DELETE",) for a in rest):
            block("a DELETE through the GitHub API")
    elif prog == "rm":
        flags = "".join(a for a in w[1:] if a.startswith("-"))
        targets = [a for a in w[1:] if not a.startswith("-")]
        if "r" in flags or "R" in flags:
            for t in targets:
                if t in ("/", "~", "$HOME", "/*", "~/*") or re.fullmatch(r"/home/[^/]+/?", t):
                    block("recursive delete of / or home")

# Whole-line checks that need the raw text.
flat = cmd.replace("\n", " ")
if re.search(r"(curl|wget)[^|]*\|\s*(ba|z)?sh\b", flat):
    block("piping a download into a shell")
if re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", flat, re.I):
    block("destructive SQL")
if re.search(r"(^|[\s/\"\x27=])\.env(\.(local|development|test|staging|production))?(\s|$|[\"\x27])|\.(pem|key)\b", flat.replace(".env.example", "")) \
        and re.search(r"\b(cat|less|more|head|tail|sed|awk|grep|cp|mv|base64|xxd|strings|source)\b", flat):
    block("reading secret files (.env, .pem, .key)")
'
