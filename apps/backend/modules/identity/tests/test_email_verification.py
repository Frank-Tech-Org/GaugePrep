import hmac
import logging
import uuid
from datetime import timedelta
from typing import Any

import pytest
from django.db import connection
from django.db.models import F
from django.utils import timezone

from modules.identity import throttle, verification
from modules.identity.mail import code_for
from modules.identity.models import EmailCode, MailOutbox, Throttle, User

from .conftest import (
    PASSWORD,
    RESEND,
    SIGNUP,
    VERIFY,
    Api,
    forget_mail_limits,
    queued_code,
    signup_body,
    verified_account,
)

pytestmark = pytest.mark.django_db

EMAIL = "ada@example.com"
WRONG = "000000"


def problem(response: Any) -> dict[str, Any]:
    assert response["Content-Type"].startswith("application/problem+json")
    return dict(response.json())


def enter(api: Api, code: str, email: str = EMAIL) -> Any:
    return api.post(VERIFY, {"email": email, "code": code, "password": PASSWORD})


def wrong_code() -> str:
    return "000000" if queued_code() != "000000" else "111111"


def age_code(seconds: int) -> None:
    """Make the open code `seconds` old."""
    delta = timedelta(seconds=seconds)
    EmailCode.objects.update(
        created_at=F("created_at") - delta, expires_at=F("expires_at") - delta
    )


def let_resend_through() -> None:
    forget_mail_limits()


@pytest.fixture
def pending(api: Api, db: None) -> Api:
    assert api.sign_up().status_code == 201
    return api


@pytest.mark.success("POST /api/v1/auth/verify-email")
def test_the_right_code_verifies_the_account_and_signs_the_learner_in(
    pending: Api,
) -> None:
    response = enter(pending, queued_code())
    assert response.status_code == 200
    assert response.json()["email_verified"] is True
    me = pending.get("/api/v1/me")
    assert me.status_code == 200
    assert me.json()["email_verified"] is True
    assert User.objects.get().email_verified_at is not None


@pytest.mark.not_found("POST /api/v1/auth/verify-email")
def test_an_unknown_email_and_a_bad_code_shape_are_refused(pending: Api) -> None:
    unknown = enter(pending, queued_code(), email="ghost@example.com")
    assert unknown.status_code == 422
    assert problem(unknown)["code"] == "invalid_code"
    for bad in ("12345", "1234567", "abcdef", " 12345", ""):
        shape = enter(pending, bad)
        assert shape.status_code == 422
        assert problem(shape)["code"] == "validation_error"
    assert not User.objects.get().email_verified


@pytest.mark.refused("POST /api/v1/auth/verify-email")
def test_another_learners_code_does_not_verify_this_account(pending: Api) -> None:
    other = Api()
    assert other.sign_up(email="grace@example.com").status_code == 201
    theirs = queued_code("grace@example.com")
    refused = enter(pending, theirs)
    assert refused.status_code == 422
    assert problem(refused)["code"] == "invalid_code"
    assert not User.objects.get(email=EMAIL).email_verified
    assert pending.get("/api/v1/me").status_code == 401


def test_a_code_works_at_9_59_and_not_at_10_01(pending: Api) -> None:
    age_code(9 * 60 + 59)
    assert enter(pending, queued_code()).status_code == 200

    other = Api()
    other.sign_up(email="grace@example.com")
    code = queued_code("grace@example.com")
    age_code(10 * 60 + 1)
    late = enter(other, code, email="grace@example.com")
    assert late.status_code == 422
    assert "new code" in problem(late)["detail"]
    assert not User.objects.get(email="grace@example.com").email_verified


def test_the_fifth_wrong_code_is_counted_and_the_sixth_try_is_refused_even_if_right(
    pending: Api,
) -> None:
    code, bad = queued_code(), wrong_code()
    for _ in range(5):
        assert enter(pending, bad).status_code == 422
    assert EmailCode.objects.get().wrong_attempts == 5
    assert enter(pending, code).status_code == 422
    assert not User.objects.get().email_verified


def test_four_wrong_codes_leave_the_right_one_working(pending: Api) -> None:
    code, bad = queued_code(), wrong_code()
    for _ in range(4):
        enter(pending, bad)
    assert enter(pending, code).status_code == 200


def test_a_used_code_is_refused(pending: Api) -> None:
    code = queued_code()
    assert enter(pending, code).status_code == 200
    again = enter(Api(), code)
    assert again.status_code == 422
    assert problem(again)["code"] == "invalid_code"


def test_a_new_code_cancels_the_old_one(pending: Api) -> None:
    old = queued_code()
    let_resend_through()
    assert pending.post(RESEND, {"email": EMAIL}).status_code == 202
    new = queued_code()
    assert new != old
    assert enter(pending, old).status_code == 422
    assert enter(pending, new).status_code == 200


def test_tries_with_an_old_code_count_against_the_new_one(pending: Api) -> None:
    old = queued_code()
    let_resend_through()
    pending.post(RESEND, {"email": EMAIL})
    new = queued_code()
    for _ in range(5):
        enter(pending, old)
    assert enter(pending, new).status_code == 422


def test_every_refusal_gets_the_same_answer(pending: Api) -> None:
    code = queued_code()
    answers = []
    answers.append(enter(pending, wrong_code()))
    answers.append(enter(pending, wrong_code(), email="ghost@example.com"))
    for _ in range(5):
        enter(pending, wrong_code())
    answers.append(enter(pending, code))
    shapes = {(a.status_code, a.content, a["Content-Language"]) for a in answers}
    assert len(shapes) == 1


def test_only_a_keyed_hash_of_the_code_is_stored(pending: Api) -> None:
    code = queued_code()
    row = EmailCode.objects.get()
    assert len(row.code_hash) == 64
    assert code not in row.code_hash
    with connection.cursor() as cursor:
        cursor.execute('SELECT t::text FROM "identity"."email_code" t')
        stored = cursor.fetchone()
        cursor.execute("SELECT args::text FROM procrastinate_jobs")
        jobs = " ".join(r[0] for r in cursor.fetchall())
    assert stored is not None
    assert code not in stored[0]
    assert code not in jobs
    assert EMAIL not in jobs


def test_the_code_is_compared_in_constant_time(
    pending: Api, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[tuple[str, str]] = []
    real = hmac.compare_digest

    def spy(a: str, b: str) -> bool:
        seen.append((a, b))
        return real(a, b)

    monkeypatch.setattr(hmac, "compare_digest", spy)
    enter(pending, wrong_code())
    enter(pending, wrong_code(), email="ghost@example.com")
    assert len(seen) == 2


def test_logs_never_hold_the_code_or_the_address(
    pending: Api, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    code = queued_code()
    enter(pending, wrong_code())
    enter(pending, code)
    let_resend_through()
    pending.post(RESEND, {"email": EMAIL})
    assert code not in caplog.text
    assert "ada@" not in caplog.text
    assert "reason=wrong" in caplog.text


def test_a_code_from_the_mail_matches_the_stored_hash(pending: Api) -> None:
    user = User.objects.get()
    row = MailOutbox.objects.get()
    assert row.recipient == EMAIL
    assert row.nonce
    assert EmailCode.objects.get().code_hash == verification._hash(
        user.id, code_for(row.nonce)
    )


@pytest.mark.success("POST /api/v1/auth/verify-email/resend")
def test_resend_mails_a_new_code(pending: Api) -> None:
    let_resend_through()
    response = pending.post(RESEND, {"email": EMAIL})
    assert response.status_code == 202
    assert response.json() == {"resend_available_in": 60}
    assert MailOutbox.objects.count() == 2
    assert EmailCode.objects.filter(closed_at__isnull=True).count() == 1


@pytest.mark.not_found("POST /api/v1/auth/verify-email/resend")
def test_resend_for_an_unknown_email_answers_alike_and_sends_nothing(
    pending: Api,
) -> None:
    let_resend_through()
    known = pending.post(RESEND, {"email": EMAIL})
    unknown = Api().post(RESEND, {"email": "ghost@example.com"})
    assert (known.status_code, known.json()) == (unknown.status_code, unknown.json())
    unsent = MailOutbox.objects.filter(recipient="ghost@example.com")
    assert [row.kind for row in unsent] == ["no_mail"]
    bad = pending.post(RESEND, {"email": "not-an-email"})
    assert bad.status_code == 422


@pytest.mark.refused("POST /api/v1/auth/verify-email/resend")
def test_resend_within_a_minute_of_the_last_mail_is_refused_with_the_wait(
    pending: Api,
) -> None:
    response = pending.post(RESEND, {"email": EMAIL})
    assert response.status_code == 429
    assert problem(response)["code"] == "rate_limited"
    assert 1 <= int(response["Retry-After"]) <= 60
    assert MailOutbox.objects.count() == 1


def test_resend_answers_429_for_an_unknown_email_too(db: None) -> None:
    first = Api().post(RESEND, {"email": "ghost@example.com"})
    second = Api().post(RESEND, {"email": "ghost@example.com"})
    assert first.status_code == 202
    assert second.status_code == 429
    assert "Retry-After" in second


def test_a_minute_later_the_next_mail_goes_out(pending: Api) -> None:
    key = throttle.key_for(throttle.MAILS_PER_MINUTE, EMAIL)
    Throttle.objects.filter(key=key).update(
        window_started_at=timezone.now() - timedelta(seconds=61)
    )
    assert pending.post(RESEND, {"email": EMAIL}).status_code == 202


def test_the_sixth_mail_in_an_hour_is_refused_and_the_wait_is_long(
    pending: Api,
) -> None:
    for _ in range(4):
        Throttle.objects.filter(
            key=throttle.key_for(throttle.MAILS_PER_MINUTE, EMAIL)
        ).delete()
        assert pending.post(RESEND, {"email": EMAIL}).status_code == 202
    Throttle.objects.filter(
        key=throttle.key_for(throttle.MAILS_PER_MINUTE, EMAIL)
    ).delete()
    sixth = pending.post(RESEND, {"email": EMAIL})
    assert sixth.status_code == 429
    assert int(sixth["Retry-After"]) > 60
    assert MailOutbox.objects.count() == 5


def test_a_refused_resend_keeps_the_open_code_working(pending: Api) -> None:
    code = queued_code()
    assert pending.post(RESEND, {"email": EMAIL}).status_code == 429
    assert enter(pending, code).status_code == 200


def test_resend_for_a_verified_account_sends_the_account_notice_without_a_code(
    pending: Api,
) -> None:
    enter(pending, queued_code())
    let_resend_through()
    assert Api().post(RESEND, {"email": EMAIL}).status_code == 202
    notice = MailOutbox.objects.get(kind=MailOutbox.Kind.ACCOUNT_EXISTS)
    assert notice.nonce == ""
    assert EmailCode.objects.filter(closed_at__isnull=True).count() == 0


def test_resend_replays_the_answer_for_the_same_key_without_a_second_mail(
    pending: Api,
) -> None:
    let_resend_through()
    key = str(uuid.uuid4())
    first = pending.post(RESEND, {"email": EMAIL}, HTTP_IDEMPOTENCY_KEY=key)
    second = pending.post(RESEND, {"email": EMAIL}, HTTP_IDEMPOTENCY_KEY=key)
    assert first.status_code == second.status_code == 202
    assert first.json() == second.json()
    assert MailOutbox.objects.count() == 2


def test_resend_key_reused_with_another_email_conflicts(pending: Api) -> None:
    let_resend_through()
    key = str(uuid.uuid4())
    pending.post(RESEND, {"email": EMAIL}, HTTP_IDEMPOTENCY_KEY=key)
    other = pending.post(
        RESEND, {"email": "grace@example.com"}, HTTP_IDEMPOTENCY_KEY=key
    )
    assert other.status_code == 409
    assert problem(other)["code"] == "idempotency_conflict"


def test_resend_key_must_be_a_uuid(pending: Api) -> None:
    response = pending.post(RESEND, {"email": EMAIL}, HTTP_IDEMPOTENCY_KEY="nope")
    assert response.status_code == 422


def test_the_idempotency_record_of_a_resend_holds_no_email(pending: Api) -> None:
    let_resend_through()
    pending.post(RESEND, {"email": EMAIL}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
    with connection.cursor() as cursor:
        cursor.execute('SELECT t::text FROM "identity"."idempotency_record" t')
        text = " ".join(row[0] for row in cursor.fetchall())
    assert "ada@" not in text


def test_signup_and_resend_share_one_mail_budget(pending: Api) -> None:
    again = Api().sign_up()
    assert again.status_code == 429
    assert "Retry-After" in again


def test_a_signup_refused_for_its_mail_limit_creates_nothing(db: None) -> None:
    Api().post(RESEND, {"email": "grace@example.com"})
    refused = Api().sign_up(email="grace@example.com")
    assert refused.status_code == 429
    assert User.objects.count() == 0
    assert MailOutbox.objects.exclude(kind="no_mail").count() == 0


def test_the_twentieth_signup_in_an_hour_passes_and_the_twenty_first_is_refused(
    db: None,
) -> None:
    api = Api()
    codes = [api.sign_up(email=f"user{n}@example.com").status_code for n in range(21)]
    assert codes == [201] * 20 + [429]
    assert User.objects.count() == 20
    key = throttle.key_for(throttle.SIGNUPS, "127.0.0.1")
    assert Throttle.objects.get(key=key).count == 21


def test_the_signup_limit_window_reopens_after_an_hour(db: None) -> None:
    api = Api()
    for n in range(21):
        api.sign_up(email=f"user{n}@example.com")
    key = throttle.key_for(throttle.SIGNUPS, "127.0.0.1")
    Throttle.objects.filter(key=key).update(
        window_started_at=timezone.now() - timedelta(hours=1, seconds=1)
    )
    assert api.sign_up(email="later@example.com").status_code == 201


def test_signup_limit_counts_a_request_that_fails_validation(db: None) -> None:
    api = Api()
    for _ in range(20):
        api.post(SIGNUP, signup_body(password="short"))
    assert api.sign_up(email="late@example.com").status_code == 429


def test_the_account_exists_mail_goes_to_a_known_address_and_has_no_code(
    db: None,
) -> None:
    verified_account("known@example.com", "fr")
    assert Api().sign_up(email="known@example.com").status_code == 201
    row = MailOutbox.objects.get()
    assert (row.kind, row.language, row.nonce) == ("account_exists", "fr", "")
    assert EmailCode.objects.count() == 0
