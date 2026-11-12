from pathlib import Path

from shell_test_support import (
    clean_env,
    commit_all,
    init_repo,
    read_outputs,
    run_script,
    write,
)


def two_commits(tmp_path: Path, changed: str) -> tuple[Path, str, str]:
    repo = init_repo(tmp_path / "repo")
    write(repo, "README.md", "x\n")
    base = commit_all(repo)
    write(repo, changed, "y\n")
    return repo, base, commit_all(repo)


def run(
    repo: Path, base: str, head: str, event: str = "pull_request"
) -> dict[str, str]:
    out = repo.parent / "out"
    env = clean_env(
        repo.parent,
        BASE=base,
        HEAD=head,
        GITHUB_EVENT_NAME=event,
        GITHUB_OUTPUT=str(out),
    )
    done = run_script("path_filter", repo, env)
    assert done.returncode == 0, done.stderr
    return read_outputs(out)


def test_docs_only_pull_request_skips_code_checks(tmp_path: Path) -> None:
    repo, base, head = two_commits(tmp_path, "docs/a.md")
    assert run(repo, base, head) == {"code": "false", "backend_image": "false"}


def test_code_and_image_inputs_turn_the_outputs_on(tmp_path: Path) -> None:
    repo, base, head = two_commits(tmp_path, "infra/docker/backend.Dockerfile")
    assert run(repo, base, head) == {"code": "true", "backend_image": "true"}


def test_push_always_runs_code_checks(tmp_path: Path) -> None:
    repo, base, head = two_commits(tmp_path, "docs/a.md")
    assert run(repo, base, head, event="push")["code"] == "true"


def test_missing_base_runs_everything(tmp_path: Path) -> None:
    repo, _, head = two_commits(tmp_path, "docs/a.md")
    assert run(repo, "", head) == {"code": "true", "backend_image": "true"}


def test_unreadable_head_fails_the_step(tmp_path: Path) -> None:
    repo, base, _ = two_commits(tmp_path, "docs/a.md")
    env = clean_env(
        repo.parent,
        BASE=base,
        HEAD="0" * 40,
        GITHUB_EVENT_NAME="pull_request",
        GITHUB_OUTPUT=str(repo.parent / "out"),
    )
    assert run_script("path_filter", repo, env).returncode != 0
