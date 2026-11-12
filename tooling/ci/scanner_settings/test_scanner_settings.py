from pathlib import Path
from subprocess import CompletedProcess

from shell_test_support import clean_env, commit_all, init_repo, run_script, write


def check(tmp_path: Path, change: dict[str, str]) -> CompletedProcess[str]:
    repo = init_repo(tmp_path / "repo")
    write(repo, "app.py", "x = 1\n")
    write(repo, "package.json", '{"packageManager": "pnpm@1.0.0"}\n')
    base = commit_all(repo)
    for rel, text in change.items():
        write(repo, rel, text)
    head = commit_all(repo)
    temp = tmp_path / "tmp"
    temp.mkdir()
    env = clean_env(tmp_path, BASE=base, HEAD=head, RUNNER_TEMP=str(temp))
    return run_script("scanner_settings", repo, env)


def test_plain_code_change_passes(tmp_path: Path) -> None:
    done = check(tmp_path, {"app.py": "x = 2\n"})
    assert done.returncode == 0, done.stdout


def test_added_scanner_ignore_file_fails_and_is_named(tmp_path: Path) -> None:
    done = check(tmp_path, {".trivyignore": "CVE-1\n"})
    assert done.returncode == 1
    assert ".trivyignore" in done.stdout
    assert "::error title=Scanner settings::" in done.stdout


def test_added_inline_suppression_fails_with_file_and_line(tmp_path: Path) -> None:
    done = check(tmp_path, {"app.py": "x = 1\ny = 2  # nosemgrep: rule\n"})
    assert done.returncode == 1
    assert "app.py:2" in done.stdout
    assert "nosemgrep" not in done.stdout


def test_changed_package_manager_fails_with_the_field(tmp_path: Path) -> None:
    done = check(tmp_path, {"package.json": '{"packageManager": "pnpm@2.0.0"}\n'})
    assert done.returncode == 1
    assert "package.json: packageManager" in done.stdout


def test_rule_file_change_under_tooling_semgrep_fails(tmp_path: Path) -> None:
    done = check(tmp_path, {"tooling/semgrep/r.yaml": "rules: []\n"})
    assert done.returncode == 1
    assert "tooling/semgrep/r.yaml" in done.stdout
