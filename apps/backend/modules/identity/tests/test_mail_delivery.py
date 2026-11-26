from datetime import date

import pytest
from django.core import mail
from django.db import connection, transaction

from modules.identity.mail import code_for, deliver, purge_unsent
from modules.identity.models import MailOutbox
from modules.identity.services import create_account
from modules.identity.tasks import queue_mail

from .conftest import Api

pytestmark = pytest.mark.django_db


def jobs() -> list[tuple[str, str]]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT task_name, args::text FROM procrastinate_jobs"
            " WHERE task_name = 'identity_send_mail'"
        )
        return list(cursor.fetchall())


def test_a_rolled_back_signup_leaves_no_mail_and_no_job() -> None:
    with pytest.raises(RuntimeError), transaction.atomic():
        queue_mail("verification_code", "ada@example.com", "en", "n")
        raise RuntimeError("rolled back")
    assert MailOutbox.objects.count() == 0
    assert jobs() == []


def test_a_committed_signup_leaves_the_mail_and_the_job_together() -> None:
    assert Api().sign_up().status_code == 201
    row = MailOutbox.objects.get()
    [(name, args)] = jobs()
    assert str(row.id) in args
    assert "ada@example.com" not in args


@pytest.mark.parametrize(
    ("language", "word"), [("en", "Your GaugePrep code is"), ("fr", "Votre code")]
)
def test_delivery_sends_the_code_in_the_learners_language(
    language: str, word: str
) -> None:
    Api().sign_up(interface_language=language)
    row = MailOutbox.objects.get()
    deliver(str(row.id))
    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.to == ["ada@example.com"]
    assert word in sent.body
    assert code_for(row.nonce) in sent.body
    assert MailOutbox.objects.count() == 0


def test_a_known_address_gets_the_notice_without_a_code() -> None:
    create_account(
        email="ada@example.com",
        date_of_birth=date(1990, 1, 2),
        interface_language="fr",
        processing_consent=True,
    )
    Api().sign_up()
    deliver(str(MailOutbox.objects.get().id))
    assert "déjà" in mail.outbox[0].subject
    assert not any(ch.isdigit() for ch in str(mail.outbox[0].body))


def test_a_job_run_twice_sends_once() -> None:
    Api().sign_up()
    row_id = str(MailOutbox.objects.get().id)
    deliver(row_id)
    deliver(row_id)
    assert len(mail.outbox) == 1


def test_unsent_rows_older_than_an_hour_are_purged() -> None:
    queue_mail("account_exists", "ada@example.com", "en")
    queue_mail("account_exists", "grace@example.com", "en")
    old = MailOutbox.objects.get(recipient="grace@example.com")
    MailOutbox.objects.filter(id=old.id).update(
        created_at=old.created_at.replace(year=2020)
    )
    assert purge_unsent() == 1
    assert MailOutbox.objects.get().recipient == "ada@example.com"
