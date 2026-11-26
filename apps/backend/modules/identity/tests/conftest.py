import json
from datetime import date, timedelta
from typing import Any

import pytest
from django.conf import settings
from django.test import Client

from modules.identity import throttle
from modules.identity.models import MailOutbox, Throttle
from modules.identity.verification import code_for

PASSWORD = "Sturdy-Pelican-4821"
ADULT = "1990-01-02"
SIGNUP = "/api/v1/auth/signup"
LOGIN = "/api/v1/auth/login"
LOGOUT = "/api/v1/auth/logout"
CSRF = "/api/v1/auth/csrf"
ME = "/api/v1/me"
VERIFY = "/api/v1/auth/verify-email"
RESEND = "/api/v1/auth/verify-email/resend"


def too_young() -> str:
    return (date.today() - timedelta(days=365 * 15)).isoformat()


def signup_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "email": "ada@example.com",
        "password": PASSWORD,
        "date_of_birth": ADULT,
        "interface_language": "en",
        "display_name": "Ada",
        "processing_consent": True,
    }
    body.update(overrides)
    return body


class Api:
    """A browser stand-in: keeps cookies, enforces CSRF and follows token rotation."""

    def __init__(self, **defaults: Any) -> None:
        self.client = Client(
            enforce_csrf_checks=True,
            HTTP_ORIGIN=settings.WEB_APP_ORIGIN,
            **defaults,
        )
        self.token: str | None = None

    def fetch_token(self) -> str:
        self.token = self.client.get(CSRF).json()["csrf_token"]
        return self.token

    def send(
        self, method: str, path: str, body: Any = None, csrf: bool = True, **extra: Any
    ) -> Any:
        if csrf and self.token is None:
            self.fetch_token()
        headers = {"HTTP_X_CSRFTOKEN": self.token} if csrf else {}
        response = getattr(self.client, method)(
            path,
            data=json.dumps(body) if body is not None else None,
            content_type="application/json",
            **headers,
            **extra,
        )
        if response.content and response["Content-Type"].startswith("application/json"):
            data = response.json()
            if isinstance(data, dict) and "csrf_token" in data:
                self.token = data["csrf_token"]
        return response

    def post(self, path: str, body: Any = None, **kw: Any) -> Any:
        return self.send("post", path, body, **kw)

    def patch(self, path: str, body: Any = None, **kw: Any) -> Any:
        return self.send("patch", path, body, **kw)

    def get(self, path: str, **kw: Any) -> Any:
        return self.client.get(path, **kw)

    def sign_up(self, **overrides: Any) -> Any:
        return self.post(SIGNUP, signup_body(**overrides))


def queued_code(email: str = "ada@example.com") -> str:
    """The code in the newest verification mail waiting for this address."""
    row = (
        MailOutbox.objects.filter(
            recipient=email, kind=MailOutbox.Kind.VERIFICATION_CODE
        )
        .order_by("-created_at")
        .first()
    )
    assert row is not None, "no verification mail is waiting"
    return code_for(row.nonce)


def forget_mail_limits() -> None:
    """Let the next mail through, as if an hour had passed."""
    keys = [
        throttle.key_for(limit, "ada@example.com")
        for limit in (throttle.MAILS_PER_MINUTE, throttle.MAILS_PER_HOUR)
    ]
    Throttle.objects.filter(key__in=keys).delete()


@pytest.fixture
def api() -> Api:
    return Api()


@pytest.fixture
def learner(api: Api, db: None) -> Api:
    assert api.sign_up().status_code == 201
    assert (
        api.post(
            VERIFY, {"email": "ada@example.com", "code": queued_code()}
        ).status_code
        == 200
    )
    forget_mail_limits()
    return api
