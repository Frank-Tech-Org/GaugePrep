"""Every CI shell script passes shellcheck and starts with a usage header."""

import shutil
import subprocess
from pathlib import Path

import pytest
from shell_test_support import CI_DIR

SCRIPTS = sorted(CI_DIR.glob("*/*.sh"))


def shellcheck_bin() -> str:
    found = shutil.which("shellcheck")
    if found is None:
        pytest.fail("shellcheck is not installed")
    return found


def test_scripts_exist() -> None:
    assert SCRIPTS


def test_shellcheck_is_clean() -> None:
    done = subprocess.run(
        [shellcheck_bin(), *map(str, SCRIPTS)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stdout


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_script_has_a_usage_header(script: Path) -> None:
    lines = script.read_text().splitlines()
    assert any(line.startswith("# Usage: ") for line in lines[:5])


def test_shellcheck_flags_a_bad_script(tmp_path: Path) -> None:
    bad = tmp_path / "bad.sh"
    bad.write_text("#!/usr/bin/env bash\nrm -rf $1/*\n")
    done = subprocess.run(
        [shellcheck_bin(), str(bad)], capture_output=True, text=True, check=False
    )
    assert done.returncode != 0
