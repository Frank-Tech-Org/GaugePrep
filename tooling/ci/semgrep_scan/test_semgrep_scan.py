import shutil
from pathlib import Path

from shell_test_support import clean_env, commit_all, init_repo, run_script, stub, write


def setup(tmp_path: Path, uvx_exit: int, rules: bool) -> tuple[Path, dict[str, str]]:
    repo = init_repo(tmp_path / "repo")
    if rules:
        write(repo, "tooling/semgrep/r.yaml", "rules: []\n")
    write(repo, "a.py", "x = 1\n")
    base = commit_all(repo)
    write(repo, "a.py", "x = 2\n")
    head = commit_all(repo)
    bin_dir = tmp_path / "bin"
    real_git = shutil.which("git")
    stub(
        bin_dir,
        "git",
        'if [ "$1" = -C ] && [ "$3" = fetch -o "$3" = checkout ]; then exit 0; fi\n'
        f'exec "{real_git}" "$@"\n',
    )
    stub(
        bin_dir,
        "uvx",
        f'printf "%s\\n" "$@" > "{tmp_path}/uvx.args"; exit {uvx_exit}\n',
    )
    temp = tmp_path / "tmp"
    temp.mkdir()
    env = clean_env(
        tmp_path,
        BASE=base,
        HEAD=head,
        GITHUB_EVENT_NAME="pull_request",
        RUNNER_TEMP=str(temp),
        RULES_SHA="abc",
    )
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    return repo, env


def test_clean_scan_uses_the_base_rules(tmp_path: Path) -> None:
    repo, env = setup(tmp_path, 0, rules=True)
    done = run_script("semgrep_scan", repo, env)
    assert done.returncode == 0, done.stderr
    args = (tmp_path / "uvx.args").read_text()
    assert str(tmp_path / "tmp" / "local-rules") in args
    assert "--disable-nosem" in args
    assert (tmp_path / "tmp" / "local-rules" / "r.yaml").read_text() == "rules: []\n"


def test_without_base_rules_it_says_so(tmp_path: Path) -> None:
    repo, env = setup(tmp_path, 0, rules=False)
    done = run_script("semgrep_scan", repo, env)
    assert "::notice title=Local rules::" in done.stdout


def test_a_finding_fails_the_step(tmp_path: Path) -> None:
    repo, env = setup(tmp_path, 1, rules=True)
    assert run_script("semgrep_scan", repo, env).returncode == 1
