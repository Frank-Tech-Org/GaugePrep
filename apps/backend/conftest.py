# Database tests skip locally when PostgreSQL is down, and fail under CI=true.

import os

import psycopg
import pytest
from django.conf import settings


def pytest_configure(config: pytest.Config) -> None:
    for kind in ("success", "not_found", "refused"):
        config.addinivalue_line(
            "markers", f"{kind}(operation): test covers this API operation"
        )


_probe: dict[str, str | None] = {}


def _database_error() -> str | None:
    if "error" not in _probe:
        db = settings.DATABASES["default"]
        try:
            with psycopg.connect(
                dbname=db["NAME"],
                user=db["USER"],
                password=db["PASSWORD"],
                host=db["HOST"],
                port=db["PORT"],
                connect_timeout=2,
            ):
                _probe["error"] = None
        except psycopg.OperationalError as exc:
            _probe["error"] = type(exc).__name__
    return _probe["error"]


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    uses_db = item.get_closest_marker("django_db") is not None or "db" in getattr(
        item, "fixturenames", ()
    )
    if not uses_db:
        return
    error = _database_error()
    if error is None:
        return
    reason = (
        f"PostgreSQL is not reachable ({error}); "
        "start it with `docker compose up -d db` or set DATABASE_URL"
    )
    if os.environ.get("CI") == "true":
        pytest.fail(reason, pytrace=False)
    pytest.skip(reason)
