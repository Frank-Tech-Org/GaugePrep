import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent

CASES = {
    "skip": 'import pytest\n\ndef test_a():\n    pytest.skip("later")\n',
    "skip marker": "import pytest\n\n@pytest.mark.skip\ndef test_a(): ...\n",
    "xfail": "import pytest\n\n@pytest.mark.xfail\ndef test_a():\n    assert False\n",
    "skipped module": 'import pytest\n\npytest.skip("no", allow_module_level=True)\n',
}


def _run(
    tmp_path: Path, source: str, ci: str | None
) -> subprocess.CompletedProcess[str]:
    (tmp_path / "test_tiny.py").write_text(source)
    env = {k: v for k, v in os.environ.items() if k != "CI"}
    if ci is not None:
        env["CI"] = ci
    env["PYTHONPATH"] = str(HERE.parent)
    # WHY: fixed argv list from our own interpreter; no shell and no external input.
    return subprocess.run(  # nosemgrep: dangerous-subprocess-use-audit
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no_skip_under_ci.plugin",
            "-p",
            "no:cacheprovider",
            "-p",
            "no:randomly",
            "-p",
            "no:django",
            "-c",
            os.devnull,
            "--rootdir",
            str(tmp_path),
            str(tmp_path / "test_tiny.py"),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("source", CASES.values(), ids=CASES.keys())
def test_a_skip_fails_under_ci(tmp_path: Path, source: str) -> None:
    result = _run(tmp_path, source, "true")
    assert result.returncode != 0, result.stdout
    assert "no skips or xfail allowed under CI" in result.stdout


@pytest.mark.parametrize("source", CASES.values(), ids=CASES.keys())
def test_a_skip_stays_a_skip_locally(tmp_path: Path, source: str) -> None:
    result = _run(tmp_path, source, None)
    assert result.returncode in (0, 5), result.stdout  # 5: no tests collected
    assert "allowed under CI" not in result.stdout


def test_a_passing_test_passes_under_ci(tmp_path: Path) -> None:
    result = _run(tmp_path, "def test_a(): ...\n", "true")
    assert result.returncode == 0, result.stdout
