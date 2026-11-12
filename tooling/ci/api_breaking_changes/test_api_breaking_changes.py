import hashlib
from pathlib import Path

from shell_test_support import clean_env, run_script, stub


def setup(tmp_path: Path, exit_code: int) -> dict[str, str]:
    temp = tmp_path / "tmp"
    stub(
        temp / "oasdiff-bin",
        "oasdiff",
        f'echo "$@" > "{temp}/args"; exit {exit_code}\n',
    )
    digest = hashlib.sha256((temp / "oasdiff-bin" / "oasdiff").read_bytes()).hexdigest()
    (temp / "openapi.base.json").write_text("{}")
    (temp / "openapi.head.json").write_text("{}")
    return clean_env(
        tmp_path,
        RUNNER_TEMP=str(temp),
        OASDIFF_SHA256=digest,
        OASDIFF_VERSION="0",
        OASDIFF_GO_VERSION="0",
    )


def test_compatible_change_passes_with_our_own_settings(tmp_path: Path) -> None:
    env = setup(tmp_path, 0)
    done = run_script("api_breaking_changes", tmp_path, env)
    assert done.returncode == 0, done.stderr
    args = (tmp_path / "tmp" / "args").read_text()
    assert "--allow-external-refs=false" in args
    assert "--fail-on ERR" in args


def test_breaking_change_fails_with_an_annotation(tmp_path: Path) -> None:
    env = setup(tmp_path, 1)
    done = run_script("api_breaking_changes", tmp_path, env)
    assert done.returncode == 1
    assert "::error title=Breaking API change::" in done.stdout
