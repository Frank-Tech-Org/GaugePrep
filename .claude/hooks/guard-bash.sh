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

def sub(words):
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

# gh api: the endpoint and whether the call writes (an explicit method, or a body, which makes gh POST).
API_VALUE_OPTS = {"-X", "--method", "-f", "-F", "--field", "--raw-field", "-H", "--header", "--input",
                  "-q", "--jq", "-t", "--template", "--hostname", "--cache", "-p", "--preview"}
API_PROTECTED = re.compile(r"/pulls/\d+/merge|/merges\b|/git/(refs|tags)|/releases|/tags/protection")
GRAPHQL_PROTECTED = re.compile(r"\b(mergePullRequest|enablePullRequestAutoMerge|mergeBranch|createRef|updateRefs?|deleteRef)\b")

def gh_api(rest):
    method, endpoint, body, i = "", "", False, 0
    while i < len(rest):
        a = rest[i]
        if a in ("-X", "--method"):
            method = rest[i + 1].upper() if i + 1 < len(rest) else ""; i += 2; continue
        if a.startswith("--method=") or (a.startswith("-X") and len(a) > 2):
            method = a.split("=", 1)[-1].removeprefix("-X").upper(); i += 1; continue
        if a in ("-f", "-F", "--field", "--raw-field", "--input") or a.startswith(("--field=", "--raw-field=", "--input=")):
            body = True
        if a in API_VALUE_OPTS:
            i += 2; continue
        if not a.startswith("-") and not endpoint:
            endpoint = a
        i += 1
    writes = method in ("POST", "PUT", "PATCH", "DELETE") or (body and method in ("", "POST"))
    if method == "DELETE":
        block("a DELETE through the GitHub API")
    if endpoint == "graphql" and GRAPHQL_PROTECTED.search(" ".join(rest)):
        block("a merge or ref change through the GraphQL API")
    if writes and API_PROTECTED.search(endpoint):
        block("a merge, ref, tag or release write through the GitHub API (use .claude/scripts/merge.sh)")

# Owner-only files: hooks, settings, the push and merge scripts, CI workflows.
OWNER_ONLY = re.compile(r"\.claude/(hooks/|settings(\.local)?\.json|scripts/(push|merge)\.sh)|\.github/workflows/")
READ_ONLY = {"cat", "head", "tail", "less", "more", "ls", "diff", "cmp", "grep", "rg", "wc", "sha256sum",
             "md5sum", "stat", "file", "echo", "printf", "jq", "test", "["}
GIT_READ = {"diff", "log", "show", "status", "add", "commit", "ls-files", "blame", "grep"}

# Secret files: .env and .env.<anything> except .env.example, and keys.
SECRET = re.compile(r"(^|[\s/\"\x27=@<])\.env(\.(?!example\b)[\w-]+)?($|[\s\"\x27])|\.(pem|key)\b")
READERS = {"cat", "less", "more", "head", "tail", "sed", "awk", "grep", "rg", "cp", "mv", "base64", "xxd",
           "od", "hexdump", "strings", "source", ".", "nl", "tac", "rev", "dd", "tee", "python", "python3",
           "node", "perl", "ruby", "bat", "vim", "vi", "nano", "openssl", "gpg", "scp", "rsync", "curl", "wget"}

for w in segments:
    if not w:
        continue
    while w and w[0] in ("sudo", "env", "command", "time", "nohup", "exec"):
        w = w[1:]
    if not w:
        continue
    prog = w[0].rsplit("/", 1)[-1]

    if any(SECRET.search(a) for a in w) and (prog in READERS or any(a.startswith("<") for a in w)):
        block("reading secret files (.env, .pem, .key)")

    # Running push.sh or merge.sh is the intended path; anything else that names an owner-only file must only read it.
    owner_args = [a for a in w[1:] if OWNER_ONLY.search(a)]
    if prog not in ("git", "gh"):  # their messages may contain ">" as text
        for i, a in enumerate(w):
            if ">" in a:
                target = a.split(">")[-1] or (w[i + 1] if i + 1 < len(w) else "")
                if OWNER_ONLY.search(target):
                    block("writing to an owner-only file")
    if owner_args:
        if prog == "git":
            verb, _ = sub(w)
            if verb not in GIT_READ:
                block("changing an owner-only file through git")
        elif prog == "find":
            if any(a in ("-delete", "-exec", "-execdir", "-ok") for a in w):
                block("changing an owner-only file")
        elif prog in ("bash", "sh"):
            if "-c" in w:
                block("changing an owner-only file")
        elif prog not in READ_ONLY and prog != "gh":
            block("changing an owner-only file (the owner copies it from .claude/proposed/)")

    if prog == "git":
        verb, rest = sub(w)
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
        verb, rest = sub(w)
        action = rest[0] if rest else ""
        if verb == "pr" and action == "merge":
            block("merging a PR (use .claude/scripts/merge.sh)")
        if verb == "release" and action in ("create", "delete", "edit", "upload"):
            block("publishing a release")
        if verb in ("repo", "issue") and action == "delete":
            block("deleting a repository or issue")
        if verb == "api":
            gh_api(rest)
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
'
