from pathlib import Path

from shell_test_support import clean_env, commit_all, init_repo, run_script, write


def env_for(
    tmp_path: Path, base: str, head: str, event: str = "pull_request"
) -> dict[str, str]:
    return clean_env(tmp_path, BASE=base, HEAD=head, GITHUB_EVENT_NAME=event)


def test_head_ignore_files_are_replaced_by_the_base_copies(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    write(repo, "pkg/.semgrepignore", "base-rule\n")
    base = commit_all(repo)
    write(repo, "pkg/.semgrepignore", "ignore-everything\n")
    write(repo, "other/.semgrepignore", "new\n")
    head = commit_all(repo)
    done = run_script("semgrep_base_ignore", repo, env_for(tmp_path, base, head))
    assert done.returncode == 0, done.stderr
    assert (repo / "pkg/.semgrepignore").read_text() == "base-rule\n"
    assert not (repo / "other/.semgrepignore").exists()


def test_push_without_a_base_leaves_no_ignore_files(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    write(repo, ".semgrepignore", "x\n")
    head = commit_all(repo)
    env = env_for(tmp_path, "0" * 40, head, event="push")
    assert run_script("semgrep_base_ignore", repo, env).returncode == 0
    assert not (repo / ".semgrepignore").exists()


def test_missing_base_variable_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    done = run_script("semgrep_base_ignore", repo, clean_env(tmp_path))
    assert done.returncode != 0
    assert "BASE is not set" in done.stderr
