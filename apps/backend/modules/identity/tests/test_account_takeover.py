import asyncio
import logging
import smtplib
from datetime import timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from django.db.models import F

from modules.identity import mail, services, tasks, throttle, verification
from modules.identity.models import Consent, EmailCode, MailOutbox, Throttle, User

from .conftest import (
    LOGIN,
    PASSWORD,
    RESEND,
    VERIFY,
    Api,
    queued_code,
)

pytestmark = pytest.mark.django_db

VICTIM = "victim@example.com"
ATTACKER_PASSWORD = "Attacker-Pelican-9911"


def enter(api: Api, code: str, email: str = VICTIM) -> Any:
    return api.post(VERIFY, {"email": email, "code": code, "password": PASSWORD})


def other_client(n: int) -> Api:
    return Api(REMOTE_ADDR=f"203.0.113.{n}", HTTP_X_FORWARDED_FOR="")


def test_an_earlier_stranger_does_not_keep_the_password_of_the_verified_owner() -> None:
    attacker, victim = other_client(1), other_client(2)
    assert attacker.sign_up(email=VICTIM, password=ATTACKER_PASSWORD).status_code == 201
    forget_mail_limits_for(VICTIM)
    assert victim.sign_up(email=VICTIM, password=PASSWORD).status_code == 201
    assert enter(victim, queued_code(VICTIM)).status_code == 200
    assert (
        other_client(3)
        .post(LOGIN, {"email": VICTIM, "password": ATTACKER_PASSWORD})
        .status_code
        == 401
    )
    assert (
        other_client(4).post(LOGIN, {"email": VICTIM, "password": PASSWORD}).status_code
        == 200
    )
    assert User.objects.filter(email=VICTIM).count() == 1


def test_the_attackers_old_code_stops_working_after_the_owner_signs_up() -> None:
    attacker = other_client(1)
    attacker.sign_up(email=VICTIM, password=ATTACKER_PASSWORD)
    stale = queued_code(VICTIM)
    forget_mail_limits_for(VICTIM)
    other_client(2).sign_up(email=VICTIM)
    assert enter(attacker, stale).status_code == 422
    assert EmailCode.objects.filter(closed_at__isnull=True).count() == 1


def test_a_verified_account_is_never_taken_over() -> None:
    api = other_client(1)
    api.sign_up(email=VICTIM)
    enter(api, queued_code(VICTIM))
    forget_mail_limits_for(VICTIM)
    other_client(2).sign_up(email=VICTIM, password=ATTACKER_PASSWORD)
    forget_mail_limits_for(VICTIM)
    response = other_client(3).post(
        LOGIN, {"email": VICTIM, "password": ATTACKER_PASSWORD}
    )
    assert response.status_code == 401
    owner = other_client(4).post(LOGIN, {"email": VICTIM, "password": PASSWORD})
    assert owner.status_code == 200


def test_the_takeover_answers_like_a_new_address() -> None:
    other_client(1).sign_up(email=VICTIM)
    forget_mail_limits_for(VICTIM)
    again = other_client(2).sign_up(email=VICTIM)
    fresh = other_client(3).sign_up(email="newxxx@example.com")
    assert again.status_code == fresh.status_code == 201
    assert set(again.json()) == set(fresh.json())


def forget_mail_limits_for(email: str) -> None:
    Throttle.objects.filter(
        key__in=[
            throttle.key_for(limit, email)
            for limit in (throttle.MAILS_PER_MINUTE, throttle.MAILS_PER_HOUR)
        ]
    ).delete()


def age_account(email: str, hours: int) -> None:
    User.objects.filter(email=email).update(
        created_at=F("created_at") - timedelta(hours=hours)
    )


def test_an_account_unverified_for_a_day_is_erased_at_the_next_signup() -> None:
    other_client(1).sign_up(email=VICTIM, display_name="Mallory")
    age_account(VICTIM, 25)
    assert other_client(2).sign_up(email="next@example.com").status_code == 201
    retired = User.objects.exclude(email__in=["next@example.com"]).get()
    assert retired.email.endswith(services.RETIRED_SUFFIX)
    assert (retired.display_name, retired.has_usable_password()) == ("", False)
    assert EmailCode.objects.filter(user=retired).count() == 0
    assert not User.objects.filter(email=VICTIM).exists()


def test_an_account_unverified_for_less_than_a_day_stays() -> None:
    other_client(1).sign_up(email=VICTIM)
    age_account(VICTIM, 23)
    other_client(2).sign_up(email="next@example.com")
    assert User.objects.filter(email=VICTIM).exists()


def test_a_verified_account_is_not_erased_whatever_its_age() -> None:
    api = other_client(1)
    api.sign_up(email=VICTIM)
    enter(api, queued_code(VICTIM))
    age_account(VICTIM, 100)
    other_client(2).sign_up(email="next@example.com")
    assert User.objects.filter(email=VICTIM).exists()


def test_wrong_tries_are_capped_per_account_across_all_codes() -> None:
    api = other_client(1)
    api.sign_up(email=VICTIM)
    for n in range(2):
        for _ in range(5):
            enter(other_client(10 + n), "000000" if n == 0 else "111111")
        forget_mail_limits_for(VICTIM)
        api.post(RESEND, {"email": VICTIM})
    right = queued_code(VICTIM)
    assert enter(other_client(30), right).status_code == 422
    assert not User.objects.get(email=VICTIM).email_verified


def test_the_cap_resets_after_a_day() -> None:
    api = other_client(1)
    api.sign_up(email=VICTIM)
    for n in range(2):
        for _ in range(5):
            enter(other_client(10 + n), "000000")
        forget_mail_limits_for(VICTIM)
        api.post(RESEND, {"email": VICTIM})
    EmailCode.objects.update(created_at=F("created_at") - timedelta(hours=25))
    forget_mail_limits_for(VICTIM)
    api.post(RESEND, {"email": VICTIM})
    assert enter(other_client(31), queued_code(VICTIM)).status_code == 200


@pytest.mark.parametrize("path", [VERIFY, RESEND])
def test_one_client_address_gets_429_after_ten_requests_a_minute(path: str) -> None:
    api = other_client(7)
    body = {"email": "ghost@example.com", "code": "123456", "password": PASSWORD}
    if path == RESEND:
        body = {"email": "ghost@example.com"}
    statuses = []
    for n in range(11):
        body = dict(body, email=f"ghost{n}@example.com")
        statuses.append(api.post(path, body).status_code)
    assert 429 not in statuses[:10]
    assert statuses[10] == 429


def test_the_limit_counts_a_known_and_an_unknown_email_alike() -> None:
    other_client(1).sign_up(email=VICTIM)
    known, unknown = other_client(8), other_client(9)
    for _ in range(10):
        known.post(VERIFY, {"email": VICTIM, "code": "123456", "password": PASSWORD})
        unknown.post(
            VERIFY,
            {"email": "ghost@example.com", "code": "123456", "password": PASSWORD},
        )
    a = known.post(VERIFY, {"email": VICTIM, "code": "123456", "password": PASSWORD})
    b = unknown.post(
        VERIFY, {"email": "ghost@example.com", "code": "123456", "password": PASSWORD}
    )
    assert a.status_code == b.status_code == 429


def test_resend_queues_one_outbox_row_and_one_job_for_every_address() -> None:
    other_client(1).sign_up(email=VICTIM)
    before = MailOutbox.objects.count()
    for n, email in enumerate((VICTIM, "ghost@example.com")):
        forget_mail_limits_for(email)
        assert other_client(20 + n).post(RESEND, {"email": email}).status_code == 202
    assert MailOutbox.objects.count() == before + 2


def test_a_no_mail_row_is_dropped_unsent_by_the_job() -> None:
    other_client(1).post(RESEND, {"email": "ghost@example.com"})
    row = MailOutbox.objects.get()
    assert row.kind == "no_mail"
    mail.deliver(str(row.id))
    assert MailOutbox.objects.count() == 0


def run_job(outbox_id: str) -> None:
    context = SimpleNamespace(
        task=SimpleNamespace(name="identity_send_mail"),
        job=SimpleNamespace(attempts=0),
    )
    asyncio.run(tasks.send_mail_job.func(context, outbox_id))  # type: ignore[arg-type]  # stand-in context


def test_a_refused_recipient_leaves_no_address_in_the_logs(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def refuse(*args: Any, **kwargs: Any) -> None:
        raise smtplib.SMTPRecipientsRefused({VICTIM: (550, b"no such user victim")})

    monkeypatch.setattr(mail, "deliver", refuse)
    caplog.set_level(logging.DEBUG)
    with pytest.raises(tasks.MailNotSent) as raised:
        run_job("outbox-id")
    assert "victim" not in caplog.text
    assert "victim" not in str(raised.value)
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__
    assert "SMTPRecipientsRefused" in str(raised.value)


def test_the_events_carry_the_ticket_names(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    api = other_client(1)
    api.sign_up(email=VICTIM)
    enter(api, "000000")
    forget_mail_limits_for(VICTIM)
    api.post(RESEND, {"email": VICTIM})
    enter(api, queued_code(VICTIM))
    for event in (
        "event=verification_mail_queued",
        "event=verification_failed reason=wrong",
        "event=verification_resent",
        "event=verification_succeeded",
    ):
        assert event in caplog.text
    assert "victim@" not in caplog.text


def test_a_closed_code_with_the_right_digits_is_still_refused() -> None:
    api = other_client(1)
    api.sign_up(email=VICTIM)
    first = queued_code(VICTIM)
    forget_mail_limits_for(VICTIM)
    api.post(RESEND, {"email": VICTIM})
    assert enter(other_client(2), first).status_code == 422


def test_a_later_stranger_does_not_decide_the_password_of_the_owner() -> None:
    owner, stranger = other_client(1), other_client(2)
    owner.sign_up(email=VICTIM, password=PASSWORD)
    forget_mail_limits_for(VICTIM)
    stranger.sign_up(email=VICTIM, password=ATTACKER_PASSWORD)
    assert enter(owner, queued_code(VICTIM)).status_code == 200
    stolen = other_client(3).post(
        LOGIN, {"email": VICTIM, "password": ATTACKER_PASSWORD}
    )
    assert stolen.status_code == 401
    assert (
        other_client(4).post(LOGIN, {"email": VICTIM, "password": PASSWORD}).status_code
        == 200
    )


def test_the_password_sent_with_a_wrong_code_is_not_kept() -> None:
    other_client(1).sign_up(email=VICTIM)
    refused = other_client(2).post(
        VERIFY, {"email": VICTIM, "code": "000000", "password": ATTACKER_PASSWORD}
    )
    assert refused.status_code == 422
    assert not User.objects.get(email=VICTIM).has_usable_password()


def test_a_weak_password_at_verification_is_refused_before_the_code_is_used() -> None:
    api = other_client(1)
    api.sign_up(email=VICTIM)
    weak = api.post(
        VERIFY, {"email": VICTIM, "code": queued_code(VICTIM), "password": "123"}
    )
    assert weak.status_code == 422
    assert weak.json()["code"] == "weak_password"
    assert enter(api, queued_code(VICTIM)).status_code == 200


def test_a_later_signup_changes_nothing_on_the_account_until_its_code_is_used() -> None:
    owner, stranger = other_client(1), other_client(2)
    owner.sign_up(email=VICTIM, display_name="Ada", interface_language="fr")
    forget_mail_limits_for(VICTIM)
    stranger.sign_up(email=VICTIM, display_name="Mallory", interface_language="en")
    before = User.objects.get(email=VICTIM)
    assert (before.display_name, before.interface_language) == ("Ada", "fr")
    assert Consent.objects.count() == 0
    assert enter(owner, queued_code(VICTIM)).status_code == 200
    user = User.objects.get(email=VICTIM)
    assert (user.display_name, user.interface_language) == ("Mallory", "en")
    assert Consent.objects.filter(user=user).count() == 1


def test_the_owners_own_signup_wins_when_the_owner_signs_up_last() -> None:
    other_client(1).sign_up(email=VICTIM, display_name="Mallory")
    forget_mail_limits_for(VICTIM)
    owner = other_client(2)
    owner.sign_up(email=VICTIM, display_name="Ada")
    assert enter(owner, queued_code(VICTIM)).status_code == 200
    assert User.objects.get(email=VICTIM).display_name == "Ada"
    assert Consent.objects.filter(user__email=VICTIM).count() == 1


def test_a_resent_code_keeps_the_details_of_its_signup() -> None:
    api = other_client(1)
    api.sign_up(email=VICTIM, display_name="Ada", interface_language="fr")
    forget_mail_limits_for(VICTIM)
    api.post(RESEND, {"email": VICTIM})
    assert enter(api, queued_code(VICTIM)).status_code == 200
    user = User.objects.get(email=VICTIM)
    assert (user.display_name, user.interface_language) == ("Ada", "fr")


def test_the_sweep_skips_accounts_it_already_retired() -> None:
    other_client(1).sign_up(email=VICTIM)
    age_account(VICTIM, 25)
    assert services.retire_stale_accounts() == 1
    assert services.retire_stale_accounts() == 0


def test_the_unverified_index_leaves_out_the_retired_suffix() -> None:
    index = next(
        i for i in User._meta.indexes if i.name == "identity_user_unverified_idx"
    )
    assert services.RETIRED_SUFFIX in str(index.condition)


def test_after_a_right_code_no_code_row_or_detail_is_left_for_the_account() -> None:
    owner = other_client(1)
    owner.sign_up(email=VICTIM, display_name="Ada")
    forget_mail_limits_for(VICTIM)
    other_client(2).sign_up(email=VICTIM, display_name="Mallory")
    assert enter(owner, queued_code(VICTIM)).status_code == 200
    assert EmailCode.objects.filter(user__email=VICTIM).count() == 0


@pytest.mark.parametrize("known", [True, False])
def test_resend_and_verify_retire_stale_accounts_for_any_address(known: bool) -> None:
    other_client(1).sign_up(email=VICTIM)
    age_account(VICTIM, 25)
    email = VICTIM if known else "ghost@example.com"
    forget_mail_limits_for(email)
    assert other_client(2).post(RESEND, {"email": email}).status_code == 202
    assert not User.objects.filter(email=VICTIM).exists()
    other_client(3).sign_up(email="second@example.com")
    age_account("second@example.com", 25)
    enter(other_client(4), "000000", email)
    assert not User.objects.filter(email="second@example.com").exists()


def test_an_account_verified_after_the_pick_is_not_wiped() -> None:
    api = other_client(1)
    api.sign_up(email=VICTIM, display_name="Ada")
    age_account(VICTIM, 25)
    stale = list(User.objects.filter(email=VICTIM).values_list("id", flat=True))
    code = queued_code(VICTIM)
    assert verification.verify_code(VICTIM, code, PASSWORD) is not None
    assert services._retire(stale) == 0
    user = User.objects.get(email=VICTIM)
    assert (user.display_name, user.has_usable_password()) == ("Ada", True)


def test_verify_locks_the_user_row_before_its_code_rows() -> None:
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    other_client(1).sign_up(email=VICTIM)
    code = queued_code(VICTIM)
    with CaptureQueriesContext(connection) as queries:
        verification.verify_code(VICTIM, code, PASSWORD)
    locks = [q["sql"] for q in queries if "FOR UPDATE" in q["sql"]]
    assert '"identity"."user"' in locks[0]
    assert '"identity"."email_code"' in locks[1]
