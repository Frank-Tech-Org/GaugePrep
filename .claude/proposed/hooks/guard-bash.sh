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
import re, shlex, subprocess, sys

cmd = sys.stdin.read()

def block(why):
    print(f"Blocked: {why}. The owner runs this; hand it over instead.", file=sys.stderr)
    sys.exit(2)

# WHY: newlines split commands and only a quoted heredoc body is dropped as data; the lexer
# reads the "|" of ">|" as a pipe, so the word after it is kept as a written file.
HEREDOC = re.compile(
    r"(?<!<)(<<-?[ \t]*([\x22\x27])(\w+)\2[^\n]*)\n(?:.*?\n)??[ \t]*\3[ \t]*(?=\n|\)|$)", re.S
)
CODE_LINE = re.compile(r"\b(bash|sh|dash|zsh|ksh|python3?|node|perl|ruby|eval|xargs|source)\b")
SUBST = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")

def heredoc_head(m):
    line = m.string[m.string.rfind("\n", 0, m.start()) + 1:m.start()]
    return m.group(0) if CODE_LINE.search(line) else m.group(1)

def split(text):
    text = HEREDOC.sub(heredoc_head, text)
    lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    words, segs, clob, after_clobber = [], [], [], False
    for tok in lexer:
        if set(tok) <= set(";&|\n"):
            after_clobber = tok.startswith("|") and bool(words) and words[-1].endswith(">")
            segs.append(words); words = []
        else:
            if after_clobber:
                clob.append(tok); after_clobber = False
            words.append(tok)
    segs.append(words)
    for m in SUBST.finditer(text):
        inner, inner_clob = split(m.group(1) or m.group(2) or "")
        segs += inner; clob += inner_clob
    return segs, clob

try:
    segments, clobbered = split(cmd)
except ValueError:
    block("a command I cannot read safely (unbalanced quotes)")

def sub(words):
    """First non-option word after the tool name, skipping option values git/gh take."""
    i = 1
    while i < len(words):
        w = words[i]
        if w in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "-R", "--repo"):
            i += 2; continue
        if w.startswith("-"):
            i += 1; continue
        return w, words[i + 1:]
    return "", []

# gh api: the endpoint and whether the call writes (an explicit method, or a body, which makes gh POST).
API_VALUE_OPTS = {"-X", "--method", "-f", "-F", "--field", "--raw-field", "-H", "--header", "--input",
                  "-q", "--jq", "-t", "--template", "--hostname", "--cache", "-p", "--preview"}
API_PROTECTED = re.compile(r"/pulls/\d+/merge|/merges\b|/git/(refs|tags)|/releases|/tags/protection|/contents/")
GRAPHQL_PROTECTED = re.compile(r"\b(mergePullRequest|enablePullRequestAutoMerge|mergeBranch|createRef|updateRefs?|deleteRef|createCommitOnBranch)\b")

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

# WHY: a hook, script or workflow an agent can edit and run unprompted can hide a push in it.
# Scanner and npm config may change on a branch; merge.sh sends those PRs to the owner.
OWNER_ONLY = re.compile(r"\.claude/(hooks/|settings(\.local)?\.json|scripts/)|\.github/workflows/|\.husky/|\.git/(config|hooks/)")
READ_ONLY = {"cat", "head", "tail", "less", "more", "ls", "diff", "cmp", "grep", "rg", "wc", "sha256sum",
             "md5sum", "stat", "file", "echo", "printf", "jq", "test", "[", "shellcheck"}
GIT_READ = {"diff", "log", "show", "status", "add", "commit", "ls-files", "blame", "grep"}

if any(OWNER_ONLY.search(t) for t in clobbered):
    block("writing to an owner-only file")

# Secret files: .env and .env.<anything> except .env.example, and keys.
SECRET = re.compile(r"(^|[\s/\"\x27=@<])\.env(\.(?!example\b)[\w-]+)?($|[\s\"\x27])|\.(pem|key)\b")
READERS = {"cat", "less", "more", "head", "tail", "sed", "awk", "grep", "rg", "cp", "mv", "base64", "xxd",
           "od", "hexdump", "strings", "source", ".", "nl", "tac", "rev", "dd", "tee", "python", "python3",
           "node", "perl", "ruby", "bat", "vim", "vi", "nano", "openssl", "gpg", "scp", "rsync", "curl", "wget"}

ASSIGN = re.compile(r"[A-Za-z_]\w*=")
WRAPPERS = {"sudo", "doas", "env", "command", "builtin", "time", "nohup", "exec", "timeout", "nice",
            "ionice", "setsid", "stdbuf", "xargs", "find", "watch", "flock", "parallel", "busybox"}
SHELLS = {"bash", "sh", "dash", "zsh", "ksh", "ash", "fish"}
INTERPRETERS = {"python", "python3", "node", "perl", "ruby"}
GIT_ENV = re.compile(r"(GIT_CONFIG\w*|GIT_EXEC_PATH|HOME|XDG_CONFIG_HOME)=")
PUSH_IN_CODE = re.compile(r"\bgit\b.{0,80}?\b(push|send-pack)\b")
GIT_C_OK = re.compile(r"(user\.(name|email)|core\.quotepath|color\.[\w.-]+|advice\.\w+|safe\.directory"
                      r"|commit\.gpgsign|pull\.rebase)(=|$)", re.I)
GIT_CONFIG_FLAGS = {"--get", "--get-all", "--get-regexp", "--list", "-l", "--show-origin", "--show-scope",
                    "--name-only", "--local", "--global", "--system", "--worktree"}
GIT_BUILTIN = {"status", "diff", "log", "show", "add", "commit", "branch", "switch", "fetch", "pull",
               "worktree", "checkout", "merge", "rebase", "reset", "stash", "tag", "clean", "config",
               "rev-parse", "remote", "restore", "ls-files", "blame", "grep", "init", "clone", "describe",
               "cherry-pick", "revert", "mv", "rm", "apply", "am", "bisect", "submodule", "update-ref",
               "symbolic-ref", "for-each-ref", "cat-file", "rev-list", "shortlog", "reflog", "gc", "fsck",
               "notes", "archive", "bundle", "diff-tree"}

def lead(a):
    # WHY: a subshell or substitution glues ( $( or a backtick to a word, so they are stripped.
    return a.lstrip("$({`!").rstrip(")}`")

def program(a):
    return lead(a).rsplit("/", 1)[-1]

KEYWORDS = {"do", "then", "else", "elif", "if", "while", "until", "{", "!", "time"}

def dynamic(a):
    return "$" in a or "`" in a

def nested(text):
    # WHY: a command string given to a shell, eval, rebase --exec or an alias is read like the rest.
    try:
        segs, clob = split(text)
    except ValueError:
        block("a nested command I cannot read safely (unbalanced quotes)")
    if any(OWNER_ONLY.search(t) for t in clob):
        block("writing to an owner-only file")
    segments.extend(segs)

def alias_of(name):
    try:
        r = subprocess.run(["git", "config", "--get", "alias." + name], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        block("cannot read the git aliases")
    return r.stdout.strip() if r.returncode == 0 else None

budget = 300
for w in segments:
    budget -= 1
    if budget < 0:
        block("a command nested too deeply to check")
    while w and w[0] in KEYWORDS:
        w = w[1:]
    if not w:
        continue
    full = [lead(w[0])] + w[1:]
    start = 0
    while start < len(full) and ASSIGN.match(full[start]):
        start += 1
    cmdw = full[start:]
    if not cmdw:
        continue
    if dynamic(re.sub(r"^(\$\(|\(|\{|!|`)", "", w[start])):
        block("a command name built from a variable or substitution")
    head = program(cmdw[0])
    gitw = None
    if head == "git":
        gitw = cmdw
    elif head in WRAPPERS or head in SHELLS or head == "eval":
        for k, a in enumerate(cmdw):
            name = program(a)
            if gitw is None and name == "git":
                gitw = [lead(a)] + cmdw[k + 1:]
            if name in SHELLS:
                for m in range(k + 1, len(cmdw) - 1):
                    if re.fullmatch(r"-[a-zA-Z]*c[a-zA-Z]*", cmdw[m]):
                        nested(cmdw[m + 1]); break
            elif name == "eval":
                nested(" ".join(cmdw[k + 1:]))
    w = cmdw
    while w and (w[0] in ("sudo", "env", "command", "time", "nohup", "exec") or ASSIGN.match(w[0])):
        w = w[1:]
        while w and w[0].startswith("-"):
            w = w[1:]
    if not w:
        continue
    prog = w[0].rsplit("/", 1)[-1]
    if prog in INTERPRETERS and any(PUSH_IN_CODE.search(a) for a in w[1:]):
        block("a git push written inside interpreter code")

    if any(SECRET.search(a) for a in w) and (prog in READERS or any(a.startswith("<") for a in w)):
        block("reading secret files (.env, .pem, .key)")

    # WHY: helper scripts run as they are; any other command may only read an owner-only file.
    owner_args = [a for a in w[1:] if OWNER_ONLY.search(a)]
    if prog not in ("git", "gh"):  # their messages may contain ">" as text
        for i, a in enumerate(w):
            if ">" in a:
                target = a.split(">")[-1].lstrip("|&") or (w[i + 1] if i + 1 < len(w) else "")
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
        elif prog == "sed":
            plain = all(re.fullmatch(r"[\w./~-]+", a) for a in owner_args)
            if not plain or any(re.match(r"-[a-zA-Z]*i", a) or a.startswith("--in-place") for a in w[1:]):
                block("sed that edits an owner-only file")
        elif prog not in READ_ONLY and prog != "gh":
            block("changing an owner-only file (the owner copies it from .claude/proposed/)")

    if gitw:
        if any(GIT_ENV.match(a) for a in full):
            block("git settings passed through the environment (config, exec path, HOME)")
        j = 1
        while j < len(gitw):
            a, setting, step = gitw[j], None, 1
            if a in ("-c", "--config-env"):
                setting, step = (gitw[j + 1] if j + 1 < len(gitw) else ""), 2
            elif a.startswith("--config-env="):
                setting = a.split("=", 1)[1]
            elif a.startswith("-c") and not a.startswith("--"):
                setting = a[2:]
            elif a.startswith("--exec-path"):
                block("changing where git looks for its commands")
            if setting is not None:
                if not GIT_C_OK.match(setting):
                    block("git -c with a setting that can run commands (alias, core.*, hooksPath)")
            elif a in ("-C", "--git-dir", "--work-tree", "--namespace", "--super-prefix"):
                step = 2
            elif not a.startswith("-"):
                break
            j += step
        verb, rest = sub(gitw)
        if dynamic(verb):
            block("a git subcommand built from a variable or substitution")
        verb = lead(verb)
        if verb in ("push", "send-pack", "http-push"):
            block("a raw git push (use .claude/scripts/push.sh)")
        if verb == "config":
            flags = [a for a in rest if a.startswith("-")]
            if not set(flags) <= GIT_CONFIG_FLAGS or len(rest) - len(flags) > 1:
                block("changing git config (aliases and hooks can hide a push)")
        if verb == "rebase":
            for k, a in enumerate(rest):
                if a in ("-x", "--exec") and k + 1 < len(rest):
                    nested(rest[k + 1])
                elif a.startswith("--exec="):
                    nested(a[7:])
        if verb == "submodule" and "foreach" in rest:
            nested(" ".join(rest[rest.index("foreach") + 1:]))
        if verb == "tag" and any(not a.startswith("-") or a in ("-a", "-s", "-f", "-d") for a in rest):
            block("creating or deleting a tag")
        if verb == "commit" and "--amend" in rest:
            block("amending a commit")
        if verb == "reset" and "--hard" in rest:
            block("git reset --hard discards work")
        if verb == "clean" and any(re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", a) for a in rest):
            block("git clean -f deletes untracked files")
        if verb and verb not in GIT_BUILTIN:
            expansion = alias_of(verb)
            if expansion is not None:
                nested(expansion[1:] if expansion.startswith("!") else "git " + expansion)
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
        if verb == "alias" and action in ("set", "import"):
            block("creating a gh alias (it can run shell commands)")
        if verb == "extension" and action in ("install", "exec"):
            block("installing or running a gh extension")
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
