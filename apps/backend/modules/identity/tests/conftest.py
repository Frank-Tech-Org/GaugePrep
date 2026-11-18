import json
from datetime import date, timedelta
from typing import Any

import pytest
from django.conf import settings
from django.http import HttpResponse
from django.test import Client

PASSWORD = "Sturdy-Pelican-4821"
ADULT = "1990-01-02"
SIGNUP = "/api/v1/auth/signup"
LOGIN = "/api/v1/auth/login"
LOGOUT = "/api/v1/auth/logout"
CSRF = "/api/v1/auth/csrf"
ME = "/api/v1/me"


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
    ) -> HttpResponse:
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

    def post(self, path: str, body: Any = None, **kw: Any) -> HttpResponse:
        return self.send("post", path, body, **kw)

    def patch(self, path: str, body: Any = None, **kw: Any) -> HttpResponse:
        return self.send("patch", path, body, **kw)

    def get(self, path: str, **kw: Any) -> HttpResponse:
        return self.client.get(path, **kw)

    def sign_up(self, **overrides: Any) -> HttpResponse:
        return self.post(SIGNUP, signup_body(**overrides))


@pytest.fixture
def api() -> Api:
    return Api()


@pytest.fixture
def learner(api: Api, db: None) -> Api:
    assert api.sign_up().status_code == 201
    return api
