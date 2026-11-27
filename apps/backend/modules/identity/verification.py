import hmac
import logging
import secrets
import uuid
from datetime import datetime, timedelta

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone
from django.utils.crypto import salted_hmac

from . import throttle
from .mail import code_for
from .models import EmailCode, MailOutbox, User
from .tasks import queue_mail

logger = logging.getLogger(__name__)

CODE_LIFETIME = timedelta(minutes=10)
MAX_WRONG_ATTEMPTS = 5
MAX_WRONG_PER_DAY = 10
WRONG_TRIES_WINDOW = timedelta(hours=24)
_NO_ACCOUNT = uuid.UUID(int=0)


def _hash(user_id: uuid.UUID, code: str) -> str:
    # SECURITY: keyed, so a leaked table cannot be brute-forced over a million codes.
    return salted_hmac(
        "identity.email_code.hash", f"{user_id}:{code}", algorithm="sha256"
    ).hexdigest()


def reserve_mail(address: str) -> int | None:
    """Count one mail to this address; seconds to wait when it is over a limit."""
    for limit in (throttle.MAILS_PER_MINUTE, throttle.MAILS_PER_HOUR):
        wait = throttle.wait_if_over(limit, throttle.record(limit, address))
        if wait is not None:
            return wait
    return None


def close_open_codes(owner: uuid.UUID) -> None:
    EmailCode.objects.filter(user_id=owner, closed_at__isnull=True).update(
        closed_at=timezone.now()
    )


def _new_code(user: User) -> str:
    """Store a fresh code for the learner; the nonce it comes from is returned."""
    now = timezone.now()
    # WHY: the job queue holds this nonce, not the code; the code needs the server key.
    nonce = secrets.token_urlsafe(16)
    EmailCode.objects.create(
        user=user,
        code_hash=_hash(user.id, code_for(nonce)),
        created_at=now,
        expires_at=now + CODE_LIFETIME,
    )
    return nonce


def queue_code_mail(user: User) -> None:
    """Replace the learner's open codes with a new one and queue its mail."""
    close_open_codes(user.id)
    nonce = _new_code(user)
    queue_mail(
        MailOutbox.Kind.VERIFICATION_CODE, user.email, user.interface_language, nonce
    )
    logger.info("event=verification_mail_queued learner_id=%s", user.id)


def queue_exists_mail(address: str) -> None:
    """Tell the owner of a registered address that someone tried to sign up with it."""
    language = (
        User.objects.filter(email=address)
        .values_list("interface_language", flat=True)
        .first()
    )
    if language is not None:
        queue_mail(MailOutbox.Kind.ACCOUNT_EXISTS, address, language)


def queue_for_address(address: str) -> None:
    """Resend. Every address runs the same statements and queues one outbox row.

    The row's kind says what the worker does: a code, the account notice, or nothing.
    """
    user = User.objects.filter(email=address).first()
    close_open_codes(user.id if user is not None else _NO_ACCOUNT)
    if user is None:
        EmailCode.objects.filter(user_id=_NO_ACCOUNT).exists()
        queue_mail(MailOutbox.Kind.NO_MAIL, address, "en")
    elif user.email_verified:
        EmailCode.objects.filter(user_id=_NO_ACCOUNT).exists()
        queue_mail(MailOutbox.Kind.ACCOUNT_EXISTS, address, user.interface_language)
    else:
        nonce = _new_code(user)
        queue_mail(
            MailOutbox.Kind.VERIFICATION_CODE,
            address,
            user.interface_language,
            nonce,
        )
        logger.info("event=verification_mail_queued learner_id=%s", user.id)


def _unusable(row: EmailCode | None, wrong_today: int, now: datetime) -> str | None:
    if row is None:
        return "wrong"
    if wrong_today >= MAX_WRONG_PER_DAY or row.wrong_attempts >= MAX_WRONG_ATTEMPTS:
        return "locked"
    return "expired" if now >= row.expires_at else None


def _wrong_tries_today(owner: uuid.UUID, now: datetime) -> int:
    total = EmailCode.objects.filter(
        user_id=owner, created_at__gt=now - WRONG_TRIES_WINDOW
    ).aggregate(total=Sum("wrong_attempts"))["total"]
    return int(total or 0)


def verify_code(address: str, code: str, password: str) -> User | None:
    """Verify the address with the code and set the password; None for a refusal.

    The password is hashed for every address and stored only on a right code.

    One answer for a wrong, expired, used, exhausted or unknown code, so the
    caller learns nothing about the account. Known and unknown addresses run the
    same statements.
    """
    now = timezone.now()
    hashed = make_password(password)
    user = User.objects.filter(email=address).first()
    owner = user.id if user is not None else _NO_ACCOUNT
    with transaction.atomic():
        row = _open_code(owner)
        wrong_today = _wrong_tries_today(owner, now)
        # WHY: hash and compare even with no code on file, so the time is the same.
        expected = row.code_hash if row is not None else _hash(_NO_ACCOUNT, "")
        matches = hmac.compare_digest(expected, _hash(owner, code))
        reason = _unusable(row, wrong_today, now)
        if reason is None and not matches:
            reason = "wrong"
        EmailCode.objects.filter(user_id=owner, closed_at__isnull=True).update(
            wrong_attempts=F("wrong_attempts") + (1 if reason == "wrong" else 0)
        )
        if reason is not None or user is None:
            logger.info("event=verification_failed reason=%s", reason)
            return None
        close_open_codes(user.id)
        if user.email_verified_at is None:
            user.email_verified_at = now
            user.password = hashed
            user.save(update_fields=["email_verified_at", "password"])
    logger.info("event=verification_succeeded learner_id=%s", user.id)
    return user


def _open_code(owner: uuid.UUID) -> EmailCode | None:
    return (
        EmailCode.objects.select_for_update()
        .filter(user_id=owner, closed_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
