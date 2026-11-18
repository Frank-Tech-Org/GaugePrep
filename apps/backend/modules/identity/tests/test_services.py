from datetime import date

import pytest
from django.db import IntegrityError, transaction

from modules.identity.models import Consent, User
from modules.identity.services import (
    AccountRefused,
    EmailTaken,
    age_on,
    create_account,
    is_old_enough,
    normalize_email,
)

BORN = date(2008, 6, 15)


def make(**overrides: object) -> User:
    details: dict[str, object] = {
        "email": "Ada@Example.com",
        "date_of_birth": date(1990, 1, 2),
        "interface_language": "fr",
        "processing_consent": True,
    }
    details.update(overrides)
    return create_account(**details)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Ada@Example.COM", "ada@example.com"),
        ("  ada@example.com \n", "ada@example.com"),
        ("ADA@EXAMPLE.COM", "ada@example.com"),
        ("ada@examplｅ.com", "ada@example.com"),
    ],
)
def test_email_is_normalised(raw: str, expected: str) -> None:
    assert normalize_email(raw) == expected


def test_the_day_before_the_16th_birthday_is_too_young() -> None:
    assert not is_old_enough(BORN, today=date(2024, 6, 14))
    assert age_on(BORN, date(2024, 6, 14)) == 15


def test_the_day_of_the_16th_birthday_is_old_enough() -> None:
    assert is_old_enough(BORN, today=date(2024, 6, 15))
    assert age_on(BORN, date(2024, 6, 15)) == 16


def test_a_leap_day_birthday_counts_on_the_leap_day() -> None:
    born = date(2008, 2, 29)
    assert not is_old_enough(born, today=date(2024, 2, 28))
    assert is_old_enough(born, today=date(2024, 2, 29))


def test_a_future_date_of_birth_is_too_young() -> None:
    assert not is_old_enough(date(2999, 1, 1), today=date(2024, 1, 1))


@pytest.mark.django_db
def test_create_account_stores_the_user_and_the_consent_row() -> None:
    user = make()
    assert user.email == "ada@example.com"
    assert not user.has_usable_password()
    consent = Consent.objects.get(user=user)
    assert (consent.kind, consent.granted, consent.source) == (
        "processing",
        True,
        "signup",
    )
    assert consent.policy_version
    assert consent.created_at is not None


@pytest.mark.django_db
def test_create_account_refuses_under_16_and_stores_nothing() -> None:
    with pytest.raises(AccountRefused) as refused:
        make(date_of_birth=date(2999, 1, 1))
    assert refused.value.code == "age_below_minimum"
    assert User.objects.count() == 0
    assert Consent.objects.count() == 0


@pytest.mark.django_db
def test_create_account_refuses_a_missing_consent_and_stores_nothing() -> None:
    with pytest.raises(AccountRefused) as refused:
        make(processing_consent=False)
    assert refused.value.code == "consent_required"
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_create_account_reports_a_taken_email_in_any_case() -> None:
    make()
    with pytest.raises(EmailTaken):
        make(email="ADA@example.com")
    assert User.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("bad", ["hunter2hunter2", "pbkdf2_sha256$1$salt$hash", ""])
def test_saving_a_weak_password_fails(bad: str) -> None:
    user = make(email=f"{abs(hash(bad))}@example.com")
    user.password = bad
    with pytest.raises(IntegrityError), transaction.atomic():
        user.save()


@pytest.mark.django_db
def test_an_argon2_hash_and_an_unusable_marker_are_accepted() -> None:
    user = make()
    user.set_password("a long enough passphrase")
    user.save()
    assert user.password.startswith("argon2$")
    user.set_unusable_password()
    user.save()


@pytest.mark.django_db
def test_the_database_refuses_an_email_that_is_not_lowercase() -> None:
    user = make()
    user.email = "Ada@Example.com"
    with pytest.raises(IntegrityError), transaction.atomic():
        user.save()
