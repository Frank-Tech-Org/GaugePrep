import os
import subprocess
import sys
from pathlib import Path

from django.test import Client

BACKEND = Path(__file__).resolve().parent.parent


def test_docs_page_is_not_served_when_debug_is_off(client: Client) -> None:
    assert client.get("/api/v1/docs").status_code == 404


def test_docs_page_renders_when_debug_is_on() -> None:
    # api.py reads DEBUG at import, so this needs a fresh process on the local settings.
    code = (
        "import django; django.setup();"
        "from django.test import Client;"
        "client = Client(raise_request_exception=False);"
        "print(client.get('/api/v1/docs', HTTP_HOST='localhost').status_code)"
    )
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings.local"}
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "200"
