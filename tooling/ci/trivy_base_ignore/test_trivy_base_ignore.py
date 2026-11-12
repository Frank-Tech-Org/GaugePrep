from pathlib import Path

from shell_test_support import clean_env, commit_all, init_repo, run_script, write

MARKER = "tri" + "vy:ignore"


def test_base_files_win_and_inline_markers_are_disarmed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    write(repo, ".trivyignore", "CVE-base\n")
    base = commit_all(repo)
    write(repo, ".trivyignore", "CVE-everything\n")
    write(repo, "trivy.yaml", "added: true\n")
    write(repo, "main.tf", f"# {MARKER}=AVD-1\n")
    head = commit_all(repo)
    env = clean_env(tmp_path, BASE=base, HEAD=head, GITHUB_EVENT_NAME="pull_request")
    done = run_script("trivy_base_ignore", repo, env)
    assert done.returncode == 0, done.stderr
    assert (repo / ".trivyignore").read_text() == "CVE-base\n"
    assert not (repo / "trivy.yaml").exists()
    assert MARKER not in (repo / "main.tf").read_text()
    assert "tri" + "vy-ignore" in (repo / "main.tf").read_text()


def test_missing_head_variable_fails(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    done = run_script("trivy_base_ignore", repo, clean_env(tmp_path, BASE="x"))
    assert done.returncode != 0
    assert "HEAD is not set" in done.stderr
