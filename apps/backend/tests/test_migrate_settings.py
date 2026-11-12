import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
ENV = {
    "DJANGO_SECRET_KEY": "x" * 50,
    "DJANGO_ALLOWED_HOSTS": "api.example.test",
    "DATABASE_URL": "postgres://app:p@h/db",
}


def _users(**extra: str) -> subprocess.CompletedProcess[str]:
    clean = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    clean.pop("MIGRATION_DATABASE_URL", None)
    clean.update(ENV, **extra)
    code = (
        "from config.settings import hosted, migrate;"
        "print(migrate.DATABASES['default']['USER'],"
        " hosted.DATABASES['default']['USER'])"
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND,
        env=clean,
        capture_output=True,
        text=True,
        check=False,
    )


def test_migration_settings_connect_as_the_migration_role() -> None:
    result = _users(MIGRATION_DATABASE_URL="postgres://owner:p@h/db")
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["owner", "app"]


def test_migration_settings_stop_when_the_migration_url_is_missing() -> None:
    result = _users()
    assert result.returncode != 0
    assert "MIGRATION_DATABASE_URL" in result.stderr
