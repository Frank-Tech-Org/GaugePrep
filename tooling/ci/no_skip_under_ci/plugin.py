"""Pytest plugin: under CI=true a skipped or xfail test or module fails, named."""

import os
from collections.abc import Generator

import pytest


def _fail_skips(report: pytest.TestReport | pytest.CollectReport, what: str) -> None:
    if os.environ.get("CI") != "true" or report.outcome not in ("skipped", "passed"):
        return
    if report.outcome == "passed" and not hasattr(report, "wasxfail"):
        return
    kind = "xfail" if hasattr(report, "wasxfail") else "skipped"
    # WHY: pytest does not count a failed report that still carries wasxfail.
    if hasattr(report, "wasxfail"):
        del report.wasxfail
    report.outcome = "failed"
    report.longrepr = f"{what} is {kind}: no skips or xfail allowed under CI"


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    report = yield
    _fail_skips(report, item.nodeid)
    return report


@pytest.hookimpl(wrapper=True)
def pytest_make_collect_report(
    collector: pytest.Collector,
) -> Generator[None, pytest.CollectReport, pytest.CollectReport]:
    report = yield
    if report.outcome == "skipped":
        _fail_skips(report, collector.nodeid)
    return report
