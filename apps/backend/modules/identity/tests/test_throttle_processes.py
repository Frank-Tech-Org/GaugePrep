import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from django.db import connection

from modules.identity import throttle
from modules.identity.models import Throttle

BACKEND = Path(__file__).resolve().parents[3]
ADDRESS = "203.0.113.77"

WORKER = (
    "import django; django.setup();"
    "from modules.identity import throttle;"
    f"[throttle.record(throttle.LOGIN_FAILURES, '{ADDRESS}') for _ in range(3)]"
)


@pytest.fixture
def committed_throttle(
    django_db_setup: None, django_db_blocker: pytest.FixtureRequest
) -> Iterator[None]:
    with django_db_blocker.unblock():  # type: ignore[attr-defined]  # pytest-django API
        key = throttle.key_for(throttle.LOGIN_FAILURES, ADDRESS)
        Throttle.objects.filter(key=key).delete()
        yield
        Throttle.objects.filter(key=key).delete()


def test_two_worker_processes_share_one_failed_login_counter(
    committed_throttle: None, django_db_blocker: pytest.FixtureRequest
) -> None:
    with django_db_blocker.unblock():  # type: ignore[attr-defined]  # pytest-django API
        db = connection.settings_dict
        env = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "config.settings.test",
            "DATABASE_URL": (
                f"postgres://{db['USER']}:{db['PASSWORD']}"
                f"@{db['HOST']}:{db['PORT']}/{db['NAME']}"
            ),
        }
        workers = [
            subprocess.Popen(
                [sys.executable, "-c", WORKER],
                cwd=BACKEND,
                env=env,
                stderr=subprocess.PIPE,
                text=True,
            )
            for _ in range(2)
        ]
        errors = [w.communicate(timeout=60)[1] for w in workers]
        assert [w.returncode for w in workers] == [0, 0], errors
        row = Throttle.objects.get(
            key=throttle.key_for(throttle.LOGIN_FAILURES, ADDRESS)
        )
        assert row.count == 6
        assert throttle.retry_after(throttle.LOGIN_FAILURES, ADDRESS) is not None
        assert throttle.retry_after(throttle.LOGIN_FAILURES, "203.0.113.78") is None
