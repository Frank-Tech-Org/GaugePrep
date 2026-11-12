from pathlib import Path

from shell_test_support import clean_env, commit_all, init_repo, run_script, stub, write


def setup(tmp_path: Path, exit_code: int) -> tuple[Path, dict[str, str]]:
    repo = init_repo(tmp_path / "repo")
    write(repo, ".gitleaks.toml", "[extend]\nuseDefault = true\n# base\n")
    write(repo, "a.txt", "a\n")
    base = commit_all(repo)
    write(repo, ".gitleaks.toml", "# head weakened\n")
    write(repo, ".gitleaksignore", "everything\n")
    head = commit_all(repo)
    temp = tmp_path / "tmp"
    stub(
        temp / "gitleaks-bin",
        "gitleaks",
        f'printf "%s\\n" "$@" > "{temp}/args"; exit {exit_code}\n',
    )
    env = clean_env(
        tmp_path,
        BASE=base,
        HEAD=head,
        GITHUB_EVENT_NAME="pull_request",
        RUNNER_TEMP=str(temp),
    )
    return repo, env


def test_clean_history_passes_with_the_base_config(tmp_path: Path) -> None:
    repo, env = setup(tmp_path, 0)
    done = run_script("scan_history", repo, env)
    assert done.returncode == 0, done.stderr
    assert "# base" in (tmp_path / "tmp" / "gl.toml").read_text()
    assert not (repo / ".gitleaksignore").exists()
    assert "--ignore-gitleaks-allow" in (tmp_path / "tmp" / "args").read_text()


def test_a_secret_fails_the_step_with_an_annotation(tmp_path: Path) -> None:
    repo, env = setup(tmp_path, 1)
    done = run_script("scan_history", repo, env)
    assert done.returncode == 1
    assert "::error title=Secret found::" in done.stdout
