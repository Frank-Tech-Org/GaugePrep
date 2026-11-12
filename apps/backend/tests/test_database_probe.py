import os
import socket
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def test_db_test_fails_instead_of_skipping_under_ci(tmp_path: Path) -> None:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    (tmp_path / "test_tiny.py").write_text("def test_uses_db(db):\n    pass\n")
    env = {
        **os.environ,
        "CI": "true",
        "DATABASE_URL": f"postgres://u:p@127.0.0.1:{port}/db",
        "PYTHONPATH": str(BACKEND),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "conftest",
            "-p",
            "no:cacheprovider",
            "-c",
            str(BACKEND / "pyproject.toml"),
            "--rootdir",
            str(BACKEND),
            str(tmp_path / "test_tiny.py"),
        ],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0, result.stdout
    assert "skipped" not in result.stdout
    assert "PostgreSQL is not reachable" in result.stdout
