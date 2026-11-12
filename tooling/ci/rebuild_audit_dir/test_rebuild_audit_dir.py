import json
from pathlib import Path

from shell_test_support import clean_env, commit_all, init_repo, run_script, stub, write

YQ_STUB = 'cat "$2"\n'


def setup(tmp_path: Path, lockfile: bool = True) -> tuple[Path, dict[str, str]]:
    repo = init_repo(tmp_path / "repo")
    if lockfile:
        write(repo, "pnpm-lock.yaml", "lockfileVersion: 9\n")
    manifest = {"name": "root", "dependencies": {"a": "1"}, "scripts": {"x": "evil"}}
    write(repo, "package.json", json.dumps(manifest))
    write(repo, "apps/web/package.json", json.dumps({"devDependencies": {"b": "2"}}))
    commit_all(repo)
    bin_dir = tmp_path / "bin"
    stub(bin_dir, "yq", YQ_STUB)
    temp = tmp_path / "tmp"
    temp.mkdir()
    env = clean_env(tmp_path, RUNNER_TEMP=str(temp))
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    return repo, env


def test_audit_directory_holds_only_dependency_fields(tmp_path: Path) -> None:
    repo, env = setup(tmp_path)
    done = run_script("rebuild_audit_dir", repo, env)
    assert done.returncode == 0, done.stderr
    audit = tmp_path / "tmp" / "audit"
    root = json.loads((audit / "package.json").read_text())
    assert root == {
        "dependencies": {"a": "1"},
        "devDependencies": None,
        "optionalDependencies": None,
    }
    assert (audit / "pnpm-workspace.yaml").read_text() == 'packages:\n  - "apps/web"\n'
    assert (audit / "pnpm-lock.yaml").read_text() == "lockfileVersion: 9\n"


def test_missing_lockfile_fails(tmp_path: Path) -> None:
    repo, env = setup(tmp_path, lockfile=False)
    assert run_script("rebuild_audit_dir", repo, env).returncode != 0
