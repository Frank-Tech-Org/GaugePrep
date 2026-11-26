import hmac
import logging
import secrets
import uuid
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from . import throttle
from .models import EmailCode, MailOutbox, User
from .tasks import queue_mail

logger = logging.getLogger(__name__)

CODE_DIGITS = 6
CODE_LIFETIME = timedelta(minutes=10)
MAX_WRONG_ATTEMPTS = 5
_NO_ACCOUNT = uuid.UUID(int=0)


def code_for(nonce: str) -> str:
    """The six digits a nonce stands for; only the mail job ever computes them."""
    digest = salted_hmac("identity.email_code.digits", nonce, algorithm="sha256")
    number = int.from_bytes(digest.digest()[:8]) % 10**CODE_DIGITS
    return f"{number:0{CODE_DIGITS}d}"


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


def queue_code_mail(user: User) -> None:
    """Replace the learner's open codes with a new one and queue its mail."""
    now = timezone.now()
    EmailCode.objects.filter(user=user, closed_at__isnull=True).update(closed_at=now)
    # WHY: the job queue holds this nonce, not the code; the code needs the server key.
    nonce = secrets.token_urlsafe(16)
    EmailCode.objects.create(
        user=user,
        code_hash=_hash(user.id, code_for(nonce)),
        created_at=now,
        expires_at=now + CODE_LIFETIME,
    )
    queue_mail(
        MailOutbox.Kind.VERIFICATION_CODE, user.email, user.interface_language, nonce
    )
    logger.info("event=email_code_queued learner_id=%s", user.id)


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
    """Resend: a code for an unverified account, the notice for a verified one."""
    user = User.objects.filter(email=address).first()
    if user is None:
        return
    if user.email_verified:
        queue_exists_mail(address)
    else:
        queue_code_mail(user)


def _unusable(row: EmailCode | None, now: datetime) -> str | None:
    if row is None:
        return "none"
    if row.wrong_attempts >= MAX_WRONG_ATTEMPTS:
        return "exhausted"
    return "expired" if now >= row.expires_at else None


def verify_code(address: str, code: str) -> User | None:
    """Verify the address with the code; None for every kind of refusal.

    One answer for a wrong, expired, used, exhausted or unknown code, so the
    caller learns nothing about the account.
    """
    now = timezone.now()
    user = User.objects.filter(email=address).first()
    with transaction.atomic():
        row = _open_code(user)
        # WHY: hash and compare even with no code on file, so the time is the same.
        owner = user.id if user is not None else _NO_ACCOUNT
        expected = row.code_hash if row is not None else _hash(_NO_ACCOUNT, "")
        matches = hmac.compare_digest(expected, _hash(owner, code))
        reason = _unusable(row, now)
        if reason is None and not matches:
            reason = "wrong"
            assert row is not None
            row.wrong_attempts += 1
            row.save(update_fields=["wrong_attempts"])
        if reason is not None or user is None:
            logger.info("event=email_code_refused reason=%s", reason)
            return None
        EmailCode.objects.filter(user=user, closed_at__isnull=True).update(
            closed_at=now
        )
        if user.email_verified_at is None:
            user.email_verified_at = now
            user.save(update_fields=["email_verified_at"])
    logger.info("event=email_verified learner_id=%s", user.id)
    return user


def _open_code(user: User | None) -> EmailCode | None:
    if user is None:
        return None
    return (
        EmailCode.objects.select_for_update()
        .filter(user=user, closed_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
