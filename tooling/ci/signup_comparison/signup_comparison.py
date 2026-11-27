"""Fail when sign-up answers differently for a known and a new email.

Usage: python signup_comparison.py --base-url <url> --verified-email <address>

The address must belong to a verified account on that server and not have been
signed up with in the last hour, or the mail limits answer 429 for it.
"""

import argparse
import json
import secrets
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.cookiejar import CookieJar
from typing import Any

PASSWORD = "correct horse battery 9"
VARYING_HEADERS = {"date", "set-cookie", "x-request-id"}
VARYING_FIELDS = {"learner_id", "csrf_token", "email"}


@dataclass(frozen=True)
class Answer:
    status: int
    headers: dict[str, str]
    body: dict[str, Any]
    cookie_names: tuple[str, ...]


def shape(answer: Answer) -> dict[str, Any]:
    """What must match: status, stable headers, cookies, body minus account values."""
    headers = {k: v for k, v in answer.headers.items() if k not in VARYING_HEADERS}
    body = {
        k: ("<varies>" if k in VARYING_FIELDS else v) for k, v in answer.body.items()
    }
    return {
        "status": answer.status,
        "headers": headers,
        "cookies": answer.cookie_names,
        "body": body,
    }


def differences(known: Answer, new: Answer) -> list[str]:
    a, b = shape(known), shape(new)
    found = [f"{key}: {a[key]!r} != {b[key]!r}" for key in a if a[key] != b[key]]
    for key in VARYING_FIELDS & known.body.keys() & new.body.keys():
        if len(str(known.body[key])) != len(str(new.body[key])):
            found.append(f"body.{key}: length differs")
    return found


class Client:
    def __init__(self, base_url: str) -> None:
        self.base = base_url.rstrip("/") + "/api/v1"
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )
        self.csrf = ""

    def call(self, method: str, path: str, payload: dict[str, Any] | None) -> Answer:
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method)
        request.add_header("Content-Type", "application/json")
        request.add_header("Referer", self.base)
        if self.csrf:
            request.add_header("X-CSRFToken", self.csrf)
        try:
            response = self.opener.open(request, timeout=30)
        except urllib.error.HTTPError as error:
            response = error
        raw = response.read().decode()
        headers = {k.lower(): v for k, v in response.headers.items()}
        names = tuple(sorted(c.name for c in self.jar))
        return Answer(response.status, headers, json.loads(raw) if raw else {}, names)

    def sign_up(self, email: str) -> Answer:
        self.csrf = self.call("GET", "/auth/csrf", None).body["csrf_token"]
        return self.call(
            "POST",
            "/auth/signup",
            {
                "email": email,
                "password": PASSWORD,
                "date_of_birth": "1990-01-01",
                "interface_language": "en",
                "display_name": "Check",
                "processing_consent": True,
            },
        )


def address() -> str:
    return f"signup-check-{secrets.token_hex(6)}@example.invalid"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--verified-email", required=True)
    args = parser.parse_args()
    known = Client(args.base_url).sign_up(args.verified_email)
    new = Client(args.base_url).sign_up(address())
    found = differences(known, new)
    for line in found:
        print(f"differs - {line}", file=sys.stderr)
    print("sign-up answers identically" if not found else "sign-up answers differ")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
