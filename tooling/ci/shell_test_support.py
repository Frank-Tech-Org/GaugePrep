"""Helpers for the shell script tests: scratch repos, stub commands, clean env."""

import os
import subprocess
from pathlib import Path

CI_DIR = Path(__file__).parent


def script_path(name: str) -> Path:
    return CI_DIR / name / f"{name}.sh"


def clean_env(home: Path, **extra: str) -> dict[str, str]:
    # WHY: git hooks export GIT_DIR; leaving it out keeps the temp repos separate.
    base = {"PATH": os.environ["PATH"], "HOME": str(home), "LC_ALL": "C.UTF-8"}
    return base | extra


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        [
            "git",
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=repo,
        env=clean_env(repo.parent),
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    return path


def write(repo: Path, rel: str, text: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def commit_all(repo: Path, message: str = "c") -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--allow-empty", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def stub(bin_dir: Path, name: str, body: str) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / name
    target.write_text("#!/usr/bin/env bash\n" + body)
    target.chmod(0o755)


def run_script(
    name: str, cwd: Path, env: dict[str, str], timeout: int = 20
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script_path(name))],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def read_outputs(path: Path) -> dict[str, str]:
    pairs = (
        line.split("=", 1) for line in path.read_text().splitlines() if "=" in line
    )
    return {key: value for key, value in pairs}
