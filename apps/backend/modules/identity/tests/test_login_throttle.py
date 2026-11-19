import statistics
import time
from datetime import timedelta
from typing import Any

import pytest
from django.contrib.auth import authenticate
from django.db import connection
from django.utils import timezone

from modules.identity import throttle
from modules.identity.models import Throttle

from .conftest import LOGIN, PASSWORD, Api

WRONG = "Wrong-Pass-1"


def attempt(email: str = "ada@example.com", password: str = WRONG, **extra: Any) -> Any:
    return Api(**extra).post(LOGIN, {"email": email, "password": password})


def from_address(address: str) -> dict[str, str]:
    return {"REMOTE_ADDR": address}


def test_address_limit_passes_the_sixth_and_refuses_the_seventh(learner: Api) -> None:
    codes = [attempt(**from_address("203.0.113.5")).status_code for _ in range(7)]
    assert codes == [401] * 6 + [429]


def test_two_addresses_in_one_64_share_a_limit_and_another_64_counts_apart(
    learner: Api,
) -> None:
    for n in range(3):
        attempt(**from_address(f"2001:db8:aa:1::{n + 1}"))
        attempt(**from_address(f"2001:db8:aa:1:ffff::{n + 1}"))
    for address in ("2001:db8:aa:1::99", "2001:db8:aa:1:1::99"):
        assert attempt(password=PASSWORD, **from_address(address)).status_code == 429
    elsewhere = attempt(password=PASSWORD, **from_address("2001:db8:aa:2::1"))
    assert elsewhere.status_code == 200


def test_a_mapped_address_counts_with_the_ipv4_address(learner: Api) -> None:
    for n in range(6):
        attempt(**from_address("::ffff:198.51.100.9" if n % 2 else "198.51.100.9"))
    assert attempt(**from_address("198.51.100.9")).status_code == 429
    assert attempt(**from_address("::ffff:198.51.100.9")).status_code == 429


def fail_from_many_addresses(email: str, times: int) -> list[int]:
    return [
        attempt(email, **from_address(f"192.0.2.{n + 1}")).status_code
        for n in range(times)
    ]


def test_email_limit_passes_the_tenth_and_refuses_the_eleventh(learner: Api) -> None:
    codes = fail_from_many_addresses("ada@example.com", 11)
    assert codes == [401] * 10 + [429]


def test_email_limit_counts_the_trimmed_lower_cased_email(learner: Api) -> None:
    spellings = ["ada@example.com", " ADA@example.com ", "Ada@Example.com"]
    codes = [
        attempt(spellings[n % 3], **from_address(f"192.0.2.{n + 1}")).status_code
        for n in range(11)
    ]
    assert codes[-1] == 429


def test_email_limit_refuses_the_right_password_too(learner: Api) -> None:
    fail_from_many_addresses("ada@example.com", 10)
    good = attempt(password=PASSWORD, **from_address("192.0.2.200"))
    assert good.status_code == 429


def test_the_429_is_the_same_for_known_and_unknown_emails(
    learner: Api, monkeypatch: pytest.MonkeyPatch
) -> None:
    fail_from_many_addresses("ada@example.com", 10)
    fail_from_many_addresses("ghost@example.com", 10)
    same_start = timezone.now() - timedelta(minutes=5)
    Throttle.objects.all().update(window_started_at=same_start)
    known = attempt("ada@example.com", **from_address("192.0.2.201"))
    unknown = attempt("ghost@example.com", **from_address("192.0.2.202"))
    assert known.status_code == unknown.status_code == 429
    assert known.content == unknown.content
    assert known["Retry-After"] == unknown["Retry-After"]
    assert dict(known.headers).keys() == dict(unknown.headers).keys()
    assert known["Content-Type"] == unknown["Content-Type"]
    assert known["Content-Language"] == unknown["Content-Language"]


@pytest.mark.parametrize(
    ("language", "title"), [("fr", "Trop de tentatives"), ("en", "Too many attempts")]
)
def test_the_429_follows_the_language_of_the_request(
    learner: Api, language: str, title: str
) -> None:
    for _ in range(6):
        attempt(**from_address("203.0.113.9"))
    refused = attempt(**from_address("203.0.113.9"), HTTP_ACCEPT_LANGUAGE=language)
    assert refused.status_code == 429
    assert refused.json()["title"] == title
    assert refused["Content-Type"] == "application/problem+json"
    assert int(refused["Retry-After"]) >= 1


def test_an_attempt_is_counted_when_the_password_check_raises(
    learner: Api, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("hasher down")

    monkeypatch.setattr("modules.identity.api.authenticate", boom)
    api = Api(raise_request_exception=False, **from_address("203.0.113.44"))
    response = api.post(LOGIN, {"email": "ada@example.com", "password": WRONG})
    assert response.status_code == 500
    monkeypatch.undo()
    for limit, subject in (
        (throttle.LOGIN_FAILURES, "203.0.113.44"),
        (throttle.LOGIN_EMAIL_FAILURES, "ada@example.com"),
    ):
        assert Throttle.objects.get(key=throttle.key_for(limit, subject)).count == 1


def test_a_right_login_gives_its_counted_attempt_back(learner: Api) -> None:
    attempt(**from_address("203.0.113.60"))
    assert attempt(password=PASSWORD, **from_address("203.0.113.60")).status_code == 200
    row = Throttle.objects.get(
        key=throttle.key_for(throttle.LOGIN_FAILURES, "203.0.113.60")
    )
    assert row.count == 1


def test_throttle_keys_are_not_plain_hashes(learner: Api) -> None:
    import hashlib

    attempt(**from_address("203.0.113.70"))
    plain = {
        hashlib.sha256(text.encode()).hexdigest()
        for subject in ("ada@example.com", "203.0.113.70")
        for text in (subject, f"login:{subject}", f"login_email:{subject}")
    }
    with connection.cursor() as cursor:
        cursor.execute('SELECT key FROM "identity"."throttle"')
        keys = {row[0] for row in cursor.fetchall()}
    assert keys
    assert not keys & plain


def test_an_unknown_email_still_pays_for_a_password_hash(
    db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    from django.contrib.auth import hashers

    real = hashers.make_password

    def spy(password: str, *args: Any, **kwargs: Any) -> str:
        calls.append(password)
        return real(password, *args, **kwargs)

    monkeypatch.setattr("modules.identity.backends.make_password", spy)
    assert authenticate(None, email="ghost@example.com", password=WRONG) is None
    assert calls == [WRONG]


def test_median_time_of_a_wrong_password_does_not_tell_known_from_unknown(
    learner: Api,
) -> None:
    def timed(email: str, n: int) -> float:
        Throttle.objects.all().delete()
        started = time.perf_counter()
        response = attempt(email, **from_address("198.18.0." + str(n % 250 + 1)))
        elapsed = time.perf_counter() - started
        assert response.status_code == 401
        return elapsed

    known, unknown = [], []
    for n in range(200):
        known.append(timed("ada@example.com", n))
        unknown.append(timed("ghost@example.com", n))
    assert abs(statistics.median(known) - statistics.median(unknown)) < 0.05
