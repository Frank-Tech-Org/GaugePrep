import unicodedata
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any

from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from . import verification
from .models import Consent, User

MINIMUM_AGE = 16
PROCESSING_POLICY_VERSION = "1"


class AccountRefused(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class EmailTaken(Exception):
    pass


class MailRateLimited(Exception):
    def __init__(self, wait: int) -> None:
        super().__init__(wait)
        self.wait = wait


@dataclass(frozen=True)
class AccountDetails:
    email: str
    date_of_birth: date
    interface_language: str
    processing_consent: bool
    display_name: str = ""


def normalize_email(raw: str) -> str:
    return unicodedata.normalize("NFKC", raw).strip().lower()


def age_on(born: date, today: date) -> int:
    had_birthday = (today.month, today.day) >= (born.month, born.day)
    return today.year - born.year - (0 if had_birthday else 1)


def is_old_enough(born: date, today: date | None = None) -> bool:
    return age_on(born, today or timezone.now().date()) >= MINIMUM_AGE


def ensure_eligible(date_of_birth: date, processing_consent: bool) -> None:
    if not is_old_enough(date_of_birth):
        raise AccountRefused("age_below_minimum")
    if not processing_consent:
        raise AccountRefused("consent_required")


def create_account(
    *,
    email: str,
    date_of_birth: date,
    interface_language: str,
    processing_consent: bool,
    display_name: str = "",
) -> User:
    """Create an account with no usable password, plus its processing consent row.

    Every sign-in method calls this. Raises AccountRefused (age_below_minimum,
    consent_required) before anything is stored, and EmailTaken for a used email.
    """
    ensure_eligible(date_of_birth, processing_consent)
    address = normalize_email(email)
    user = User(
        email=address,
        date_of_birth=date_of_birth,
        interface_language=interface_language,
        display_name=display_name.strip(),
    )
    user.set_unusable_password()
    try:
        with transaction.atomic():
            user.save(force_insert=True)
            Consent.objects.create(
                user=user,
                kind=Consent.Kind.PROCESSING,
                granted=True,
                policy_version=PROCESSING_POLICY_VERSION,
                source=Consent.Source.SIGNUP,
            )
    except IntegrityError:
        if User.objects.filter(email=address).exists():
            raise EmailTaken from None
        raise
    return user


def profile_of(user: User) -> dict[str, Any]:
    return dict(
        learner_id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        interface_language=user.interface_language,
        email_verified=user.email_verified,
    )


def decoy_profile(details: AccountDetails, learner_id: str) -> dict[str, Any]:
    """The profile shown for a used email, rebuilt from the request, never stored."""
    decoy = User(
        id=uuid.UUID(learner_id),
        email=normalize_email(details.email),
        display_name=details.display_name.strip(),
        interface_language=details.interface_language,
    )
    return profile_of(decoy)


def register(
    details: AccountDetails, password: str
) -> tuple[User | None, dict[str, Any]]:
    """Create an account with a password and queue its code mail.

    Returns the user and the profile to show. A used email gets the "account exists"
    mail and a made-up profile, so the answer looks the same. Raises AccountRefused or
    MailRateLimited before anything is kept. Call inside one transaction: the account,
    its consent, its hash and its mail commit together.
    """
    try:
        validate_password(password)
    except ValidationError:
        raise AccountRefused("weak_password") from None
    ensure_eligible(details.date_of_birth, details.processing_consent)
    # WHY: hash first so a used email takes the same time
    hashed = make_password(password)
    address = normalize_email(details.email)
    wait = verification.reserve_mail(address)
    if wait is not None:
        raise MailRateLimited(wait)
    try:
        user = create_account(
            email=details.email,
            date_of_birth=details.date_of_birth,
            interface_language=details.interface_language,
            processing_consent=details.processing_consent,
            display_name=details.display_name,
        )
    except EmailTaken:
        verification.queue_exists_mail(address)
        return None, decoy_profile(details, str(uuid.uuid4()))
    user.password = hashed
    user.save(update_fields=["password"])
    verification.queue_code_mail(user)
    return user, profile_of(user)
