import statistics
import time
from typing import Any

import pytest

from .conftest import RESEND, VERIFY, Api, signup_body, verified_account

pytestmark = pytest.mark.django_db

SKIPPED_HEADERS = {"date", "set-cookie"}


def known_account(email: str, language: str = "en") -> None:
    verified_account(email, language)


def shape(response: Any) -> dict[str, Any]:
    body = response.json() if response.content else None
    if isinstance(body, dict):
        body = {
            k: v
            for k, v in body.items()
            if k not in ("learner_id", "csrf_token", "email")
        }
    headers = {
        k.lower(): v for k, v in response.items() if k.lower() not in SKIPPED_HEADERS
    }
    return {
        "status": response.status_code,
        "body": body,
        "headers": headers,
        "cookies": sorted(response.cookies.keys()),
    }


def test_signup_answers_alike_for_a_known_and_a_new_email() -> None:
    known_account("known@example.com")
    known, fresh = Api(), Api()
    a = known.sign_up(email="known@example.com", display_name="X")
    b = fresh.sign_up(email="newxx@example.com", display_name="X")
    assert shape(a) == shape(b)
    assert a.status_code == 201


def test_the_follow_up_account_details_are_byte_identical() -> None:
    known_account("known@example.com")
    known, fresh = Api(), Api()
    known.sign_up(email="known@example.com")
    fresh.sign_up(email="newxx@example.com")
    a, b = known.get("/api/v1/me"), fresh.get("/api/v1/me")
    assert a.status_code == b.status_code == 401
    assert a.content == b.content
    assert shape(a) == shape(b)


def test_a_second_signup_within_the_minute_is_refused_alike() -> None:
    known_account("known@example.com")
    for email in ("known@example.com", "newxx@example.com"):
        assert Api().sign_up(email=email).status_code == 201
    a = Api().sign_up(email="known@example.com")
    b = Api().sign_up(email="newxx@example.com")
    assert a.status_code == b.status_code == 429
    keys = {"status", "body", "cookies"}
    assert {k: shape(a)[k] for k in keys} == {k: shape(b)[k] for k in keys}


def test_resend_and_verify_answer_alike_for_known_and_unknown() -> None:
    known_account("known@example.com")
    api = Api()
    a = api.post(RESEND, {"email": "known@example.com"})
    b = Api().post(RESEND, {"email": "ghost@example.com"})
    assert shape(a) == shape(b)
    c = api.post(VERIFY, {"email": "known@example.com", "code": "123456"})
    d = Api().post(VERIFY, {"email": "ghost@example.com", "code": "123456"})
    assert shape(c) == shape(d)


def median_gap(call_known: Any, call_unknown: Any) -> float:
    """Median of paired differences, each pair run back to back in alternating order."""
    gaps: list[float] = []
    for n in range(200):
        timed: dict[str, float] = {}
        order = (("known", call_known), ("unknown", call_unknown))
        for label, call in order if n % 2 == 0 else order[::-1]:
            started = time.perf_counter()
            call(n)
            timed[label] = time.perf_counter() - started
        gaps.append(timed["known"] - timed["unknown"])
    print(f"paired median gap {statistics.median(gaps) * 1000:.3f} ms")
    return abs(statistics.median(gaps))


@pytest.mark.timeout(600)
def test_signup_timing_gap_is_under_5_ms() -> None:
    for n in range(200):
        known_account(f"known{n}@example.com")

    def signup(email: str, n: int) -> None:
        api = Api(REMOTE_ADDR=f"203.0.113.{n % 250 + 1}", HTTP_X_FORWARDED_FOR="")
        api.post("/api/v1/auth/signup", signup_body(email=email))

    gap = median_gap(
        lambda n: signup(f"known{n}@example.com", n),
        lambda n: signup(f"fresh{n}@example.com", n + 100),
    )
    assert gap < 0.005


@pytest.mark.timeout(600)
def test_resend_and_verify_timing_gaps_are_under_1_ms() -> None:
    known_account("known@example.com")
    from modules.identity import throttle
    from modules.identity.models import Throttle

    def clear() -> None:
        Throttle.objects.filter(
            key__in=[
                throttle.key_for(limit, "known@example.com")
                for limit in (throttle.MAILS_PER_MINUTE, throttle.MAILS_PER_HOUR)
            ]
        ).delete()

    def resend(email: str) -> None:
        clear()
        Api().post(RESEND, {"email": email})

    assert (
        median_gap(
            lambda n: resend("known@example.com"), lambda n: resend("ghost@example.com")
        )
        < 0.001
    )

    def verify(email: str) -> None:
        Api().post(VERIFY, {"email": email, "code": "123456"})

    assert (
        median_gap(
            lambda n: verify("known@example.com"), lambda n: verify("ghost@example.com")
        )
        < 0.001
    )
