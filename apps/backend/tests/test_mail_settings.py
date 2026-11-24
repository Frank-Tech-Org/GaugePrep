import os
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent

PROBE = (
    "import django; django.setup();"
    "from django.core import mail;"
    "b = mail.mailers['default'];"
    "print(type(b).__name__, b.host, b.port, repr(b.username), repr(b.password),"
    " b.use_tls, b.timeout)"
)


def _probe(**env: str) -> list[str]:
    clean = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("DJANGO_", "MAIL_")) and k != "DATABASE_URL"
    }
    clean["DJANGO_SETTINGS_MODULE"] = "config.settings.local"
    clean.update(env)
    result = subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c", PROBE],
        cwd=BACKEND,
        env=clean,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.split()


def test_mailpit_settings_reach_the_smtp_backend_without_tls_or_login() -> None:
    out = _probe(MAIL_HOST="mailpit", MAIL_PORT="1025", MAIL_API_KEY="")
    assert out == ["EmailBackend", "mailpit", "1025", "''", "''", "False", "10"]


def test_resend_settings_reach_the_smtp_backend_with_tls_and_the_key() -> None:
    out = _probe(MAIL_HOST="smtp.resend.com", MAIL_PORT="587", MAIL_API_KEY="re_x")
    assert out == [
        "EmailBackend",
        "smtp.resend.com",
        "587",
        "'resend'",
        "'re_x'",
        "True",
        "10",
    ]


class _Smtp(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        self.wfile.write(b"220 stub\r\n")
        data = False
        for raw in self.rfile:
            line = raw.decode().strip()
            if data:
                if line == ".":
                    data = False
                    self.wfile.write(b"250 ok\r\n")
                else:
                    self.server.received.append(line)  # type: ignore[attr-defined]
                continue
            cmd = line.split(" ")[0].upper()
            if cmd == "EHLO":
                self.wfile.write(b"250 stub\r\n")
            elif cmd == "DATA":
                data = True
                self.wfile.write(b"354 go\r\n")
            elif cmd == "QUIT":
                self.wfile.write(b"221 bye\r\n")
                return
            else:
                self.wfile.write(b"250 ok\r\n")


def test_a_message_sent_through_the_configured_backend_reaches_the_smtp_host() -> None:
    server = socketserver.TCPServer(("127.0.0.1", 0), _Smtp)
    server.received = []  # type: ignore[attr-defined]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    code = (
        "import django; django.setup();"
        "from django.core.mail import send_mail;"
        "send_mail('Subject-probe', 'body', None, ['to@example.test'])"
    )
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("DJANGO_", "MAIL_")) and k != "DATABASE_URL"
    }
    env.update(
        DJANGO_SETTINGS_MODULE="config.settings.local",
        MAIL_HOST="127.0.0.1",
        MAIL_PORT=str(server.server_address[1]),
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=BACKEND,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
    assert result.returncode == 0, result.stderr
    assert any("Subject: Subject-probe" in line for line in server.received)  # type: ignore[attr-defined]


@pytest.mark.parametrize("module", ["dev", "staging", "production"])
def test_hosted_settings_have_no_health_inbox_default(module: str) -> None:
    code = f"import importlib; importlib.import_module('config.settings.{module}')"
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("DJANGO_", "MAIL_")) and k != "DATABASE_URL"
    }
    env.update(
        DJANGO_SECRET_KEY="x" * 50,
        THROTTLE_KEY_SECRET="y" * 50,
        DJANGO_ALLOWED_HOSTS="a.test",
        DATABASE_URL="postgres://u:p@h/db",
        MAIL_HOST="h",
        MAIL_PORT="25",
        MAIL_FROM="a <a@a.test>",
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "MAIL_HEALTH_TO" in result.stderr
