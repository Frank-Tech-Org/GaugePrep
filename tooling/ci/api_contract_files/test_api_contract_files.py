from pathlib import Path

from shell_test_support import (
    clean_env,
    commit_all,
    git,
    init_repo,
    read_outputs,
    run_script,
    write,
)

SPEC = "apps/backend/openapi.json"


def run(repo: Path, base: str, head: str) -> tuple[int, dict[str, str], Path]:
    temp = repo.parent / "tmp"
    temp.mkdir(exist_ok=True)
    out = repo.parent / "out"
    env = clean_env(
        repo.parent, BASE=base, HEAD=head, RUNNER_TEMP=str(temp), GITHUB_OUTPUT=str(out)
    )
    done = run_script("api_contract_files", repo, env)
    return done.returncode, read_outputs(out), temp


def test_changed_spec_is_extracted_for_comparison(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    write(repo, SPEC, '{"a": 1}\n')
    base = commit_all(repo)
    write(repo, SPEC, '{"a": 2}\n')
    head = commit_all(repo)
    code, outputs, temp = run(repo, base, head)
    assert code == 0
    assert outputs == {"compare": "true"}
    assert (temp / "openapi.base.json").read_text() == '{"a": 1}\n'
    assert (temp / "openapi.head.json").read_text() == '{"a": 2}\n'


def test_unchanged_spec_skips_the_comparison(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    write(repo, SPEC, "{}\n")
    base = commit_all(repo)
    write(repo, "x.txt", "x\n")
    head = commit_all(repo)
    assert run(repo, base, head)[:2] == (0, {"compare": "false"})


def test_removed_spec_fails_the_step(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    write(repo, SPEC, "{}\n")
    base = commit_all(repo)
    git(repo, "rm", "-q", SPEC)
    head = commit_all(repo)
    temp = tmp_path / "tmp"
    temp.mkdir()
    env = clean_env(
        tmp_path,
        BASE=base,
        HEAD=head,
        RUNNER_TEMP=str(temp),
        GITHUB_OUTPUT=str(tmp_path / "out"),
    )
    done = run_script("api_contract_files", repo, env)
    assert done.returncode == 1
    assert "::error title=API contract removed::" in done.stdout
