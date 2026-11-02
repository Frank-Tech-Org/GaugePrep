# Database tests skip locally when PostgreSQL is down, and fail under CI=true.

import os
from collections.abc import Generator

import psycopg
import pytest
from django.conf import settings

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


# Under CI=true a skipped or xfail test (or module) fails and is named.
def _ci_no_skips(report: pytest.TestReport | pytest.CollectReport, what: str) -> None:
    if os.environ.get("CI") != "true" or report.outcome not in ("skipped", "passed"):
        return
    if report.outcome == "passed" and not hasattr(report, "wasxfail"):
        return
    kind = "xfail" if hasattr(report, "wasxfail") else "skipped"
    report.outcome = "failed"
    report.longrepr = f"{what} is {kind}: no skips or xfail allowed under CI"


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    report = yield
    _ci_no_skips(report, item.nodeid)
    return report


@pytest.hookimpl(wrapper=True)
def pytest_make_collect_report(
    collector: pytest.Collector,
) -> Generator[None, pytest.CollectReport, pytest.CollectReport]:
    report = yield
    if report.outcome == "skipped":
        _ci_no_skips(report, collector.nodeid)
    return report
