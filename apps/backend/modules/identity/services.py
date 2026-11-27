import logging
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import CharField, Value
from django.db.models.functions import Cast, Concat
from django.utils import timezone

from . import verification
from .models import Consent, EmailCode, User

MINIMUM_AGE = 16
PROCESSING_POLICY_VERSION = "1"
UNVERIFIED_LIFETIME = timedelta(hours=24)
RETIRED_SUFFIX = "@retired.invalid"
RETIRED_BIRTH_DATE = date(1900, 1, 1)

logger = logging.getLogger(__name__)


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


def ensure_strong_password(password: str) -> None:
    try:
        validate_password(password)
    except ValidationError:
        raise AccountRefused("weak_password") from None


def register(
    details: AccountDetails, password: str
) -> tuple[User | None, dict[str, Any]]:
    """Create an account and queue its code mail; the password is set at verification.

    The password is checked here and never stored, so who signed up first or last
    never decides who owns the account. Returns the user and the profile to show. A
    used email gets the "account exists" mail and a made-up profile, so the answer
    looks the same. Raises AccountRefused or MailRateLimited before anything is kept.
    Call inside one transaction: the account, its consent and its mail commit together.
    """
    ensure_strong_password(password)
    ensure_eligible(details.date_of_birth, details.processing_consent)
    address = normalize_email(details.email)
    wait = verification.reserve_mail(address)
    if wait is not None:
        raise MailRateLimited(wait)
    retire_stale_accounts()
    try:
        user = create_account(
            email=details.email,
            date_of_birth=details.date_of_birth,
            interface_language=details.interface_language,
            processing_consent=details.processing_consent,
            display_name=details.display_name,
        )
    except EmailTaken:
        taken = _take_over_unverified(address, details)
        if taken is None:
            verification.queue_exists_mail(address)
            return None, decoy_profile(details, str(uuid.uuid4()))
        user = taken
    verification.queue_code_mail(user)
    return user, profile_of(user)


# SECURITY: nobody holds an unverified address, so the newest sign-up wins; else an
# earlier stranger would keep a password on the account the real owner verifies.
def _take_over_unverified(address: str, details: AccountDetails) -> User | None:
    user = (
        User.objects.select_for_update()
        .filter(email=address, email_verified_at__isnull=True)
        .first()
    )
    if user is None:
        return None
    user.date_of_birth = details.date_of_birth
    user.interface_language = details.interface_language
    user.display_name = details.display_name.strip()
    user.save(update_fields=["date_of_birth", "interface_language", "display_name"])
    Consent.objects.create(
        user=user,
        kind=Consent.Kind.PROCESSING,
        granted=True,
        policy_version=PROCESSING_POLICY_VERSION,
        source=Consent.Source.SIGNUP,
    )
    return user


def retire_stale_accounts(batch: int = 20) -> int:
    """Erase accounts still unverified after a day and free their address.

    The consent rows are append-only, so the row stays under its learner ID with its
    personal fields overwritten. Runs at sign-up, because the worker role cannot read
    accounts.
    """
    ids = list(
        User.objects.filter(
            email_verified_at__isnull=True,
            created_at__lt=timezone.now() - UNVERIFIED_LIFETIME,
        )
        .exclude(email__endswith=RETIRED_SUFFIX)
        .order_by("created_at")
        .values_list("id", flat=True)[:batch]
    )
    if not ids:
        return 0
    EmailCode.objects.filter(user_id__in=ids).delete()
    User.objects.filter(id__in=ids).update(
        email=Concat(Value("retired-"), Cast("id", CharField()), Value(RETIRED_SUFFIX)),
        display_name="",
        date_of_birth=RETIRED_BIRTH_DATE,
        password=make_password(None),
    )
    logger.info("event=unverified_accounts_retired count=%d", len(ids))
    return len(ids)
