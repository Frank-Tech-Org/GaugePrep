import logging
from collections.abc import Iterator

import pytest
from config.jobs import RETRY, RUNS, mail_health, retry_stalled_jobs
from django.core import mail
from django.core.management import call_command
from django.db import connection, transaction
from procrastinate.contrib.django import app

pytestmark = pytest.mark.django_db(transaction=True)


def _run_worker(*queues: str) -> None:
    call_command("procrastinate", "worker", "--one-shot", "--queues", ",".join(queues))


def _rows(sql: str) -> list[tuple[object, ...]]:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall() if cursor.description else []


@pytest.fixture(autouse=True)
def clean_queue() -> Iterator[None]:
    yield
    _rows("DELETE FROM procrastinate_periodic_defers")
    _rows("DELETE FROM procrastinate_jobs")
    _rows("DROP TABLE IF EXISTS t_marker")


def _mine(columns: str) -> list[tuple[object, ...]]:
    return _rows(f"SELECT {columns} FROM procrastinate_jobs WHERE queue_name = 'test'")


@app.task(name="test_always_fails", queue="test", retry=RETRY)
def always_fails() -> None:
    raise RuntimeError("boom")


@app.task(name="test_marker", queue="test")
def marker() -> None:
    _rows("CREATE TABLE IF NOT EXISTS t_marker (n int)")
    _rows("INSERT INTO t_marker VALUES (1)")


def test_a_committed_job_runs_and_a_rolled_back_one_does_not() -> None:
    with pytest.raises(RuntimeError), transaction.atomic():
        marker.defer()
        raise RuntimeError("rolled back")
    assert _rows("SELECT count(*) FROM procrastinate_jobs") == [(0,)]

    with transaction.atomic():
        marker.defer()
    _run_worker("test")
    assert _mine("status") == [("succeeded",)]
    assert _rows("SELECT count(*) FROM t_marker") == [(1,)]


def test_a_failing_job_backs_off_then_stops_after_the_set_attempts(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    always_fails.defer()
    for attempt in range(1, RUNS + 1):
        _run_worker("test")
        status, attempts = _mine("status, attempts")[0]
        assert attempts == attempt
        if attempt < RUNS:
            assert status == "todo"
            seconds = _mine("extract(epoch FROM scheduled_at - now())")[0][0]
            assert 0 < float(seconds) <= 2**attempt  # type: ignore[arg-type]
            _rows("UPDATE procrastinate_jobs SET scheduled_at = now()")
    assert status == "failed"
    assert caplog.text.count("ended with status: Error") == RUNS


def test_a_job_left_doing_by_a_dead_worker_runs_once_more() -> None:
    marker.defer()
    _rows("UPDATE procrastinate_jobs SET status = 'doing', worker_id = NULL")
    _run_worker("test")
    assert _mine("status") == [("doing",)]
    assert _rows("SELECT count(*) FROM pg_tables WHERE tablename = 't_marker'") == [
        (0,)
    ]

    retry_stalled_jobs.configure(queueing_lock="test").defer(timestamp=1)
    _run_worker("default")
    _run_worker("test")
    assert _mine("status") == [("succeeded",)]
    assert _rows("SELECT count(*) FROM t_marker") == [(1,)]


def test_the_health_job_sends_one_message_and_logs_no_address(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    mail_health.defer()
    _run_worker("default")
    assert len(mail.outbox) == 1
    assert "health@gaugeprep.test" not in caplog.text
    assert "job_succeeded job=mail_health attempt=1" in caplog.text
    assert "mail_sent template=health" in caplog.text
