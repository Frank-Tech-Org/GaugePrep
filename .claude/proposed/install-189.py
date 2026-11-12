#!/usr/bin/env python3
# Usage: python3 .claude/proposed/install-189.py (from the repo root)
# Copies the staged guard, settings, merge script and alarm into place, then self-tests.
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

root = pathlib.Path.cwd()
staged = root / ".claude/proposed"
MAP = {
    "hooks/guard-bash.sh": ".claude/hooks/guard-bash.sh",
    "settings.json": ".claude/settings.json",
    "scripts/merge.sh": ".claude/scripts/merge.sh",
    "workflows/develop-alarm.yml": ".github/workflows/develop-alarm.yml",
}
guard = root / MAP["hooks/guard-bash.sh"]
settings = root / MAP["settings.json"]
alarm = root / MAP["workflows/develop-alarm.yml"]

for rel in MAP:
    if not (staged / rel).is_file():
        sys.exit(f"stopped: {rel} is not staged; nothing written")
if not (root / ".git").exists():
    sys.exit("stopped: run this from the repository root; nothing written")

originals = {}
for rel, dest in MAP.items():
    p = root / dest
    originals[p] = p.read_text() if p.exists() else None


def rollback(msg: str) -> None:
    for path, text in originals.items():
        if text is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(text)
    sys.exit(f"stopped: {msg}; originals restored")


def install() -> None:
    try:
        for rel, dest in MAP.items():
            target = root / dest
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(staged / rel, target)
            if dest.endswith(".sh"):
                target.chmod(0o755)
    except OSError as e:
        rollback(f"copy failed ({e})")

    for sh in (guard, root / ".claude/scripts/merge.sh"):
        if subprocess.run(["bash", "-n", str(sh)]).returncode:
            rollback(f"bash -n failed on {sh.name}")
    try:
        json.loads(settings.read_text())
    except ValueError as e:
        rollback(f"settings.json is not valid JSON ({e})")
    try:
        import yaml

        for wf in (alarm,):
            yaml.safe_load(wf.read_text())
        ALARM_SH = yaml.safe_load(alarm.read_text())["jobs"]["check"]["steps"][0]["run"]
    except ImportError:
        rollback("PyYAML is needed to read the alarm script")
    except yaml.YAMLError as e:
        rollback(f"workflow YAML does not parse ({e})")
    if shutil.which("actionlint"):
        for wf in (alarm,):
            r = subprocess.run(["actionlint", str(wf)], capture_output=True, text=True)
            print("actionlint:", wf.name, "PASS" if r.returncode == 0 else "FAIL")
            if r.returncode:
                print(r.stdout, r.stderr)
                rollback("actionlint failed")
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not common.startswith("/"):
        rollback("cannot find the shared git directory")
    anchor = '      "MultiEdit(./.git/**)",\n'
    text = settings.read_text()
    if text.count(anchor) != 1:
        rollback("settings.json has no single git deny anchor")
    extra = "".join(f'      "{tool}(/{common}/**)",\n' for tool in ("Edit", "Write", "MultiEdit"))
    settings.write_text(text.replace(anchor, anchor + extra))
    json.loads(settings.read_text())
    GIT_PATHS = ["./.husky/**", "./.git/**", f"/{common}/**", "~/.gitconfig", "~/.config/git/**"]
    tmp = pathlib.Path(tempfile.mkdtemp())
    gitcfg = tmp / "gitconfig"
    gitcfg.write_text("[alias]\n\tzz = push\n\tyy = !git push origin HEAD:develop\n")
    env = dict(os.environ, GIT_CONFIG_GLOBAL=str(gitcfg), GIT_CONFIG_NOSYSTEM="1")


    def guard_exit(cmd: str) -> int:
        return subprocess.run(
            [str(guard)],
            input=json.dumps({"tool_input": {"command": cmd}}),
            text=True,
            capture_output=True,
            env=env,
        ).returncode


    refused = [
        (
            "helper script: append push to board helper",
            "echo 'git push origin HEAD:develop' >> .claude/scripts/board.sh",
        ),
        (
            "helper script: sed -i on env check",
            "sed -i 's/x/git push origin HEAD:develop/' .claude/scripts/env-check.sh",
        ),
        ("helper script: cp over board helper", "cp /tmp/x .claude/scripts/board.sh"),
        ("helper script: tee", "printf x | tee .claude/scripts/env-check.sh"),
        ("helper script: new file by redirect", "cat > .claude/scripts/new.sh"),
        (
            "helper script: python write",
            "python3 -c \"open('.claude/scripts/board.sh','a')\"",
        ),
        ("git hook: husky pre-push", "echo true > .husky/pre-push"),
        ("git hook: .git/hooks", "echo x > .git/hooks/pre-commit"),
        ("alias: git -c alias", "git -c alias.p=push p"),
        ("alias: attached -c", "git -calias.p=push p"),
        ("alias: shell alias", "git -c 'alias.p=!git push' p"),
        ("alias: config-env", "git --config-env=alias.p=VAR p"),
        (
            "alias: env config",
            "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=alias.p GIT_CONFIG_VALUE_0=push git p",
        ),
        ("alias: git config write", "git config alias.p push"),
        ("alias: global config write", "git config --global alias.p push"),
        ("alias: existing push alias", "git zz origin HEAD:develop"),
        ("alias: existing shell alias", "git yy"),
        ("git -c core.pager runs a command", "git -c core.pager='git push' log"),
        ("bash -c", "bash -c 'git push origin HEAD:develop'"),
        ("bash -c double quotes", 'bash -c "git push"'),
        ("bash -lc", 'bash -lc "git push"'),
        ("sh -c", "sh -c 'git push'"),
        ("sudo bash -c", "sudo bash -c 'git push'"),
        ("xargs sh -c", "echo x | xargs sh -c 'git push'"),
        ("eval", 'eval "git push"'),
        ("nested bash -c", "bash -c \"bash -c 'git push'\""),
        ("env git", "env git push"),
        ("env -i git", "env -i git push"),
        ("env -u git", "env -u FOO git push"),
        ("assignment git", "FOO=1 git push"),
        ("full path git", "/usr/bin/git push origin HEAD:develop"),
        ("command git", "command git push"),
        ("quoted git", '"git" push'),
        ("subshell", "(git push)"),
        ("command substitution", "echo $(git push)"),
        ("backticks", "echo `git push`"),
        ("timeout", "timeout 5 git push"),
        ("find -exec", "find . -maxdepth 0 -exec git push {} +"),
        ("git -C", "git -C . push"),
        ("rebase --exec", "git rebase -x 'git push' HEAD~1"),
        ("submodule foreach", "git submodule foreach 'git push'"),
        ("send-pack", "git send-pack origin HEAD:refs/heads/develop"),
        ("interpreter", "python3 -c \"import subprocess; subprocess.run(['git','push'])\""),
        ("gh alias", "gh alias set p 'api repos/x'"),
        ("plain push", "git push"),
        ("newline then push", "true\ngit push origin HEAD:develop"),
        ("unquoted heredoc substitution", "cat <<EOF\n$(git push)\nEOF"),
        ("unquoted heredoc then push", "cat <<EOF\nEOF\ngit push"),
        ("quoted heredoc then push", "cat <<'EOF'\nhello\nEOF\ngit push"),
        ("quoted empty heredoc then push", "cat <<'EOF'\nEOF\ngit push"),
        ("two heredocs hide a push", "cat <<'EOF'\nEOF\ngit push\ncat <<'EOF'\nx\nEOF"),
        ("heredoc fed to bash", "bash <<'EOF'\ngit push origin HEAD:develop\nEOF"),
        ("do keyword", "for i in 1; do git push; done"),
        ("negated push", "! git push"),
        ("variable as git", "$GIT push"),
        ("braced variable as git", "${GIT} push"),
        ("variable as subcommand", "git $VERB origin HEAD:develop"),
        ("substitution as subcommand", 'git "$(echo push)"'),
        ("git --namespace", "git --namespace x push"),
        ("git --super-prefix", "git --super-prefix x push"),
        (
            "api contents write",
            "gh api -X PUT repos/o/r/contents/f.txt -f message=x -f content=eA==",
        ),
        ("api contents write by body", "gh api repos/o/r/contents/f.txt -f message=x -f content=y"),
        (
            "graphql commit on branch",
            "gh api graphql -f query=\"mutation { createCommitOnBranch(input: {}) { commit { oid } } }\"",
        ),
        ("sed w flag into a script", "sed -n 's/x/y/w .claude/scripts/board.sh' f"),
        ("sed -i with suffix", "sed -i.bak p .claude/scripts/board.sh"),
        ('gh pr merge after repo flag', 'gh pr -R o/r merge 201 --squash'),
        ('gh workflow disable after repo flag', 'gh workflow -R o/r disable alarm.yml'),
        ('gh release create after repo flag', 'gh release -R o/r create v9'),
        ('graphql attached file query', 'gh api graphql -Fquery=@/tmp/q.graphql'),
        ('graphql long field file query', 'gh api graphql --field=query=@/tmp/q.graphql'),
        ('graphql query from a variable', 'Q="mutation { x }"; gh api graphql -f query="$Q"'),
        ('graphql other mutation', "gh api graphql -f query='mutation { deleteBranchProtectionRule(input:{}) { clientMutationId } }'"),
        ('gh auth show token', 'gh auth status --show-token'),
        ('gh auth token', 'gh auth token'),
        ('git credential fill', 'git credential fill'),
        ('curl PUT to the GitHub API', "curl -X PUT -H 'Authorization: token x' https://api.github.com/repos/o/r/pulls/1/merge"),
        ('curl data to the GitHub API', 'curl -d @/tmp/b https://api.github.com/repos/o/r/contents/f'),
        ('api PATCH on the full repo URL', 'gh api -X PATCH https://api.github.com/repos/o/r -f default_branch=x'),
        ('api PATCH with a query string', "gh api -X PATCH 'repos/o/r?a=1' -f default_branch=x"),
        ('export GIT_EDITOR', "export GIT_EDITOR='git push origin HEAD:develop; true'; git commit --allow-empty"),
        ('declare -x GIT_SSH_COMMAND', "declare -x GIT_SSH_COMMAND='git push origin HEAD:develop'"),
        ('env assignment of GIT_CONFIG_COUNT', 'GIT_CONFIG_COUNT=1 git status'),
        ('EDITOR on a command', "EDITOR='git push origin HEAD:develop' git commit"),
        ('rebase -x attached', "git rebase -x'git push origin HEAD:develop' HEAD~1"),
        ('rebase abbreviated --exe', "git rebase --exe='git push origin HEAD:develop' HEAD~1"),
        ('fetch abbreviated --upload-pac', "git fetch --upload-pac='git push origin HEAD:develop' ."),
        ('difftool abbreviated --extc', "git difftool --extc='git push origin HEAD:develop' HEAD~1"),
        ('git subtree push', "git subtree push --prefix=a origin develop"),
        ('curl -sXPUT', "curl -sXPUT https://api.github.com/repos/o/r/pulls/1/merge"),
        ('curl -sX PUT', "curl -sX PUT https://api.github.com/repos/o/r/pulls/1/merge"),
        ('filter-branch', "git filter-branch --tree-filter 'git push origin HEAD:develop' HEAD~1..HEAD"),
        ('grep -O pager', "git grep -O'git push origin HEAD:develop' foo"),
        ('grep open-files-in-pager', "git grep --open-files-in-pager='git push origin HEAD:develop' foo"),
        ('archive --exec', "git archive --remote=. --exec='git push origin HEAD:develop' HEAD"),
        ('clone template with hooks', 'git clone --template=/tmp/t o /tmp/c'),
        ('cd -', 'cd /tmp; cd -; cp /tmp/x board.sh'),
        ('popd', 'pushd .claude/scripts; popd; cp /tmp/x board.sh'),
        ('CDPATH', 'CDPATH=.claude cd scripts'),
        ('cd into a variable', 'cd $D && cp /tmp/x board.sh'),
        ('copy tree into the claude folder', 'cp -r /tmp/stage/. .claude/'),
        ('rsync into the claude folder', 'rsync -a /tmp/stage/ .claude/'),
        ('tar into the claude folder', 'tar -xf /tmp/x.tar -C .claude'),
        ('symlink to the claude folder', 'ln -s "$PWD/.claude" /tmp/c'),
        ('checkout a folder from a ref', 'git checkout evil -- .claude'),
        ('checkout-index', 'git checkout-index -f -a'),
        ('subshell cd then copy', 'cd .claude/scripts && (cd /tmp) && cp /tmp/x board.sh'),
        ('heredoc marker inside quotes', 'echo "<<\'EOF\'"\ngit push origin HEAD:develop\nEOF'),
        ('heredoc marker in a comment', "# <<'EOF'\ngit push origin HEAD:develop\nEOF"),
        ('comment ending in a backslash', 'echo hi # \\\ngit push origin HEAD:develop'),
        ('brace expansion as command', '{git,push} origin HEAD:develop'),
        ('glob as command', '/usr/bin/gi? push origin HEAD:develop'),
        ('glob as git subcommand', 'git pu?h origin HEAD:develop'),
        ('source from stdin', "source /dev/stdin <<< 'git push origin HEAD:develop'"),
        ('dot from stdin', "echo 'git push origin HEAD:develop' | . /dev/stdin"),
        ('bash from stdin path', "bash /dev/stdin <<< 'git push origin HEAD:develop'"),
        ('hash -p', 'hash -p /usr/bin/git g; g push origin HEAD:develop'),
        ('time -p', 'time -p git push origin HEAD:develop'),
        ('coproc with a name', 'coproc X { git push origin HEAD:develop; }'),
        ('nested parens in a substitution', 'echo $(git push origin HEAD:develop; (true))'),
        ('subshell in a substitution', 'echo "$( (git push origin HEAD:develop) )"'),
        ('pipe into bash', "echo 'git push origin HEAD:develop' | bash"),
        ('here-string into sh', "sh <<< 'git push origin HEAD:develop'"),
        ('bash -c after double dash', "bash -c -- 'git push origin HEAD:develop'"),
        ('comment before newline', 'echo hi # note\ngit push origin HEAD:develop'),
        ('backslash newline in verb', 'git \\\npush origin HEAD:develop'),
        ('process substitution', "bash <(echo 'git push origin HEAD:develop')"),
        ('function body', 'f() { git push origin HEAD:develop; }; f'),
        ('case arm', 'case x in x) git push origin HEAD:develop;; esac'),
        ('trap', "trap 'git push origin HEAD:develop' EXIT"),
        ('coproc', 'coproc git push origin HEAD:develop'),
        ('shell alias', "alias p='git push origin HEAD:develop'; p"),
        ('env split string', "env -S 'git push origin HEAD:develop'"),
        ('xargs supplies verb', 'echo push | xargs git'),
        ('git helper program', 'git-push origin HEAD:develop'),
        ('copied git binary', 'cp /usr/bin/git /tmp/g'),
        ('GIT_EDITOR names a program', "GIT_EDITOR='git push' git commit"),
        ('GIT_SEQUENCE_EDITOR', "GIT_SEQUENCE_EDITOR='git push' git rebase -i HEAD~1"),
        ('fetch upload-pack', "git fetch --upload-pack='git push' origin"),
        ('pull short upload-pack', "git pull -u 'git push' origin"),
        ('clone upload-pack', "git clone --upload-pack 'git push' o /tmp/c"),
        ('difftool extcmd', "git difftool -x 'git push' HEAD~1"),
        ('submodule foreach recursive', "git submodule foreach --recursive 'git push origin HEAD:develop'"),
        ('bisect run', "git bisect run sh -c 'git push origin HEAD:develop'"),
        ('uv run git', 'uv run git push origin HEAD:develop'),
        ('pnpm exec git', 'pnpm exec git push origin HEAD:develop'),
        ('doppler run git', 'doppler run -- git push origin HEAD:develop'),
        ('script -c', "script -c 'git push origin HEAD:develop' /dev/null"),
        ('awk system', 'awk \'BEGIN{system("git push origin HEAD:develop")}\''),
        ('global git config', 'printf x >> ~/.gitconfig'),
        ('cd into .git', 'cd .git && printf x >> config'),
        ('cd then copy over a helper', 'cd .claude && cp /tmp/x scripts/board.sh'),
        ('double slash path', 'cp /tmp/x .claude//scripts/board.sh'),
        ('dot segment path', 'cp /tmp/x .claude/./scripts/board.sh'),
        ('glob path', 'cp /tmp/x .claude/scr*/board.sh'),
        ('git apply', 'git apply /tmp/p.patch'),
        ('patch command', 'patch -p1 < /tmp/p.patch'),
        ('graphql query from file', 'gh api graphql -F query=@/tmp/q.graphql'),
        ('graphql input file', 'gh api graphql --input /tmp/q.json'),
        ('branch rename', 'gh api -X POST repos/o/r/branches/develop/rename -f new_name=old'),
        ('workflow disable', 'gh workflow disable develop-alarm.yml'),
        ('actions permissions off', 'gh api -X PUT repos/o/r/actions/permissions -F enabled=false'),
    ]
    allowed = [
        ("board helper runs", ".claude/scripts/board.sh list"),
        ("env check runs", ".claude/scripts/env-check.sh --add"),
        ("push helper runs", ".claude/scripts/push.sh feature/189-x"),
        ("merge helper runs", ".claude/scripts/merge.sh 12"),
        ("bash n on a script", "bash -n .claude/scripts/board.sh"),
        ("shellcheck on a script", "shellcheck .claude/scripts/board.sh"),
        ("read a script", "cat .claude/scripts/board.sh"),
        ("git status", "git status"),
        ("git log", "git log --oneline -3"),
        ("commit message mentions push", 'git commit -m "fix: git push guard"'),
        (
            "commit by heredoc mentions push",
            "git commit -m \"$(cat <<'EOF'\nfix(infra): catch git push behind aliases\n\nRefs #189\nEOF\n)\"",
        ),
        ("git -c plain setting", "git -c core.quotepath=off diff --stat"),
        ("git config read", "git config --get user.name"),
        ("git config read key", "git config user.name"),
        ("worktree", "git worktree add ../x"),
        ("fetch", "git fetch origin"),
        ("echo mentions push", "echo git push is blocked"),
        ("grep mentions push", 'grep -rn "git push" docs'),
        ("env without git", "env FOO=1 ls"),
        ("bash -c harmless", "bash -c 'echo hi'"),
        ("pr create", "gh pr create --title x --body y"),
        ("pytest", "uv run pytest -q"),
        (
            "commit by quoted heredoc with an apostrophe",
            "git commit -F - <<'EOF'\nfix: it's a guard, it doesn't push\n\nRefs #189\nEOF",
        ),
        ("quoted heredoc to cat", "cat <<'EOF'\ndon't git push\nEOF"),
        ("two plain commands on lines", "git status\ngit log --oneline -3"),
        ("for loop", "for f in a b; do echo $f; done"),
        ("read-only sed on a script", "sed -n 1,5p .claude/scripts/board.sh"),
        ("api contents read", "gh api repos/o/r/contents/README.md"),
        ('gh pr view', 'gh pr view 201'),
        ('gh repo flag on a view', 'gh pr -R o/r view 201'),
        ('gh auth status', 'gh auth status'),
        ('graphql plain query', "gh api graphql -f query='{ viewer { login } }'"),
        ('author variables on a commit', 'GIT_AUTHOR_NAME=x git commit -m x'),
        ('checkout discarding changes', 'git checkout -- .'),
        ('restore working tree', 'git restore .'),
        ('checkout a branch', 'git checkout feature/189-x'),
        ('curl a public page', 'curl -s https://example.com'),
        ('curl get from GitHub', 'curl -s https://api.github.com/repos/o/r'),
        ('list the claude folder', 'ls .claude'),
        ('tar a folder up', 'tar czf /tmp/x.tgz .claude'),
        ('rm a build folder', 'rm -rf node_modules'),
        ('copy a file next to the code', 'cp /tmp/x apps/backend/x.py'),
        ('cd then read', 'cd .claude/scripts && cat board.sh'),
        ('comment mentioning push', 'ls # git push later'),
        ('time without a git', 'time -p ls'),
        ('test with brackets', '[ -f README.md ] && echo yes'),
        ("git apply check only", "git apply --check /tmp/p.patch"),
        ("cd into a subfolder", "cd apps/backend && git status"),
        ("xargs on a file list", "ls | xargs wc -l"),
    ]
    bad = total = 0
    for label, cmd in refused:
        code = guard_exit(cmd)
        ok = code == 2
        bad += not ok
        total += 1
        print(f"{'PASS' if ok else 'FAIL'}  refused  {label}")
    for label, cmd in allowed:
        code = guard_exit(cmd)
        ok = code == 0
        bad += not ok
        total += 1
        print(f"{'PASS' if ok else 'FAIL'}  allowed  {label}")

    deny = json.loads(settings.read_text())["permissions"]["deny"]
    for tool in ("Edit", "Write", "MultiEdit"):
        for path in (
            "./.claude/scripts/**",
            "./.claude/hooks/**",
            "./.github/workflows/**",
            *GIT_PATHS,
        ):
            ok = f"{tool}({path})" in deny
            bad += not ok
            if not ok:
                print(f"FAIL  deny rule missing  {tool}({path})")
    total += 1

    SHA = "a" * 40
    fake = tmp / "bin"
    fake.mkdir()
    (fake / "gh").write_text(
        "#!/usr/bin/env bash\n"
        'fail() { case ",${GH_FAIL:-}," in *",$1,"*) exit 1 ;; esac; }\n'
        "issue_list() {\n"
        '  local a="" q="" prev=""\n'
        '  for x in "$@"; do\n'
        '    [ "$prev" = --author ] && a=${x#app/}\n'
        '    [ "$prev" = --jq ] && q=$x\n'
        '    prev=$x\n'
        "  done\n"
        '  jq --arg a "$a" "[.[] | select(.author.login == \\$a)]" "$FX/issues.json" | jq "$q"\n'
        "}\n"
        'case "$*" in\n'
        '  *"/activity"*"heads/stage"*) fail activity; cat "$FX/activity-stage.json" ;;\n'
        '  *"/activity"*) fail activity; cat "$FX/activity-develop.json" ;;\n'
        '  *"/commits/"*"/pulls"*) fail pulls; cat "$FX/pulls.json" ;;\n'
        '  *"/reviews"*) fail reviews; cat "$FX/reviews.json" ;;\n'
        '  "api repos/"*"/commits/"*) fail files; cat "$FX/files.txt" ;;\n'
        '  "api repos/"*"/pulls/"*) fail pr; cat "$FX/pr.json" ;;\n'
        '  "issue list"*) fail issuelist; issue_list "$@" ;;\n'
        '  "issue create"*) echo "$*" >> "$FX/issues.log" ;;\n'
        "esac\n"
    )
    (fake / "sleep").write_text("#!/usr/bin/env bash\nexit 0\n")
    for f in fake.iterdir():
        f.chmod(0o755)
    script = tmp / "alarm.sh"
    script.write_text(ALARM_SH)

    NOW = datetime.now(timezone.utc)
    STAMP = "%Y-%m-%dT%H:%M:%SZ"


    def pulls(branch="develop", merged=True, sha=SHA):
        return [
            {
                "number": 7,
                "merged_at": "t" if merged else None,
                "merge_commit_sha": sha,
                "base": {"ref": branch},
            }
        ]


    def pr(head, merger):
        return {
            "head": {"ref": head, "sha": "h1"},
            "merged_by": {"login": merger} if merger else None,
        }


    def review(state="APPROVED", commit="h1"):
        return [
            {
                "user": {"login": "frankkefoueg"},
                "state": state,
                "commit_id": commit,
                "submitted_at": "1",
            }
        ]


    def push_log(kind="push", age=timedelta(minutes=3)):
        return [
            {
                "activity_type": kind,
                "after": SHA,
                "timestamp": (NOW - age).strftime(STAMP),
                "actor": {"login": "someone"},
            }
        ]


    AGENT, OWNER = "KefouegFrank", "frankkefoueg"
    GOOD = dict(pl=pulls(), prj=pr("feature/189-x", AGENT), rv=review())
    alarm_cases = []


    def case(label, issue, code, **kw):
        alarm_cases.append((label, issue, code, kw))


    case("direct push, no PR", True, 1, pl=[], prj=None, rv=[])
    case("squash merge by merge step, owner approved", False, 0, **GOOD)
    case("squash merge, no approval", True, 1, **dict(GOOD, rv=[]))
    case("squash merge, stale approval", True, 1, **dict(GOOD, rv=review(commit="old")))
    case(
        "squash merge, approval withdrawn",
        True,
        1,
        **dict(
            GOOD, rv=review() + [dict(review("CHANGES_REQUESTED")[0], submitted_at="2")]
        ),
    )
    case(
        "owner merged a feature PR",
        False,
        0,
        **dict(GOOD, prj=pr("feature/189-x", OWNER), rv=[]),
    )
    case(
        "unmerged PR head pushed",
        True,
        1,
        pl=pulls(merged=False, sha="b" * 40),
        prj=pr("feature/x", None),
        rv=review(),
    )
    case("develop from an unknown branch", True, 1, **dict(GOOD, prj=pr("rogue/x", OWNER)))
    case(
        "back-merge main to develop by owner",
        False,
        0,
        **dict(GOOD, prj=pr("main", OWNER), rv=[]),
    )
    case(
        "back-merge main to develop by agent", True, 1, **dict(GOOD, prj=pr("main", AGENT))
    )
    case(
        "promotion to stage by owner",
        False,
        0,
        branch="stage",
        pl=pulls("stage"),
        prj=pr("develop", OWNER),
        rv=[],
    )
    case(
        "promotion to stage by agent",
        True,
        1,
        branch="stage",
        pl=pulls("stage"),
        prj=pr("develop", AGENT),
        rv=review(),
    )
    case(
        "feature straight into stage",
        True,
        1,
        branch="stage",
        pl=pulls("stage"),
        prj=pr("feature/x", OWNER),
        rv=[],
    )
    case("direct push to stage", True, 1, branch="stage", pl=[], prj=None, rv=[])
    case("forced push", True, 1, forced="true", **dict(GOOD, prj=pr("feature/x", OWNER)))
    case(
        "owner merged a PR that changes a workflow",
        False,
        0,
        files=".github/workflows/ci.yml\n",
        **dict(GOOD, prj=pr("chore/x", OWNER)),
    )
    case(
        "agent merged a PR that changes a workflow",
        True,
        1,
        files="a.py\n.github/workflows/ci.yml\n",
        **GOOD,
    )
    def issue(title, login):
        return [{"title": title, "author": {"login": login}}]


    TITLE = f"develop changed outside the merge step: {SHA}"
    ALARM_ISSUE = issue(TITLE, "github-actions")
    case("existing issue is not opened twice", False, 1, issues=ALARM_ISSUE, pl=[], prj=None, rv=[])

    case("issue with the title made by a person", True, 1, issues=issue(TITLE, "someone"), pl=[], prj=None, rv=[])
    case("bot issue whose title only holds the sha", True, 1, issues=issue(f"note {SHA}", "github-actions"), pl=[], prj=None, rv=[])
    case("pre-made issue with the sha in the title", True, 1, issues=issue(f"x {TITLE}", "someone"), pl=[], prj=None, rv=[])

    for step in ("pulls", "pr", "reviews", "files"):
        case(f"{step} lookup fails", True, 1, fail=step, **GOOD)
    case("issue search fails", True, 1, fail="issuelist", pl=[], prj=None, rv=[])
    case("every lookup fails", True, 1, fail="pulls,pr,reviews,files,issuelist", **GOOD)

    case(
        "manual: direct commit",
        True,
        1,
        event="workflow_dispatch",
        in_branch="develop",
        in_sha=SHA,
        pl=[],
        prj=None,
        rv=[],
    )
    case(
        "manual: merged commit",
        False,
        0,
        event="workflow_dispatch",
        in_branch="develop",
        in_sha=SHA,
        **GOOD,
    )
    case(
        "manual: bad commit id",
        False,
        2,
        event="workflow_dispatch",
        in_branch="develop",
        in_sha="xyz",
        **GOOD,
    )
    case(
        "manual: branch main refused",
        False,
        2,
        event="workflow_dispatch",
        in_branch="main",
        in_sha=SHA,
        **GOOD,
    )

    case(
        "scan: unmerged push",
        True,
        1,
        event="schedule",
        dev=push_log(),
        pl=[],
        prj=None,
        rv=[],
    )
    case("scan: force push", True, 1, event="schedule", dev=push_log("force_push"), **GOOD)
    case(
        "scan: branch deleted",
        True,
        1,
        event="schedule",
        dev=push_log("branch_deletion"),
        **GOOD,
    )
    case("scan: merged push", False, 0, event="schedule", dev=push_log(), **GOOD)
    case(
        "scan: pr_merge entry", False, 0, event="schedule", dev=push_log("pr_merge"), **GOOD
    )
    case(
        "scan: old push is ignored",
        False,
        0,
        event="schedule",
        dev=push_log(age=timedelta(hours=3)),
        pl=[],
        prj=None,
        rv=[],
    )
    case(
        "scan: stage promotion by owner",
        False,
        0,
        event="schedule",
        stg=push_log(),
        pl=pulls("stage"),
        prj=pr("develop", OWNER),
        rv=[],
    )
    case(
        "scan: stage direct push",
        True,
        1,
        event="schedule",
        stg=push_log(),
        pl=[],
        prj=None,
        rv=[],
    )
    case("scan: push log unreadable", False, 1, event="schedule", fail="activity", **GOOD)
    case(
        "scan: existing issue",
        False,
        0,
        event="schedule",
        dev=push_log(),
        issues=ALARM_ISSUE,
        pl=[],
        prj=None,
        rv=[],
    )
    case(
        "manual: no commit id rescans",
        True,
        1,
        event="workflow_dispatch",
        dev=push_log(),
        pl=[],
        prj=None,
        rv=[],
    )

    for label, issue, code, kw in alarm_cases:
        fx = pathlib.Path(tempfile.mkdtemp(dir=tmp))
        (fx / "pulls.json").write_text(json.dumps(kw.get("pl", [])))
        (fx / "pr.json").write_text(json.dumps(kw.get("prj")))
        (fx / "reviews.json").write_text(json.dumps(kw.get("rv", [])))
        (fx / "files.txt").write_text(kw.get("files", "backend/a.py\n"))
        (fx / "issues.json").write_text(json.dumps(kw.get("issues", [])))
        (fx / "activity-develop.json").write_text(json.dumps(kw.get("dev", [])))
        (fx / "activity-stage.json").write_text(json.dumps(kw.get("stg", [])))
        r = subprocess.run(
            ["bash", "-e", str(script)],
            env=dict(
                os.environ,
                PATH=f"{fake}:{os.environ['PATH']}",
                FX=str(fx),
                GH_FAIL=kw.get("fail", ""),
                REPO="o/r",
                EVENT=kw.get("event", "push"),
                SHA=SHA,
                BRANCH=kw.get("branch", "develop"),
                ACTOR="someone",
                FORCED=kw.get("forced", "false"),
                IN_BRANCH=kw.get("in_branch", ""),
                IN_SHA=kw.get("in_sha", ""),
                OWNER=OWNER,
            ),
            capture_output=True,
            text=True,
        )
        fired = (fx / "issues.log").exists()
        ok = fired == issue and r.returncode == code
        bad += not ok
        total += 1
        kind = "fires" if issue else "quiet"
        print(f"{'PASS' if ok else 'FAIL'}  alarm {kind} (exit {code})  {label}")
        if not ok:
            print(
                f"  got issue={fired} exit={r.returncode}", r.stdout[-300:], r.stderr[-300:]
            )
    shutil.rmtree(tmp, ignore_errors=True)

    if bad:
        rollback(f"{bad} self-test checks failed")
    print(f"checks: PASS ({total} passed)")


try:
    install()
except SystemExit:
    raise
except BaseException as e:
    rollback(f"{type(e).__name__}: {e}")
