import hmac
import json
from datetime import timedelta
from typing import Any
from uuid import UUID

from django.db import connection
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import IdempotencyRecord, User

KEEP_FOR = timedelta(hours=24)


def parse_key(raw: str) -> UUID | None:
    try:
        return UUID(raw)
    except ValueError:
        return None


def fingerprint(payload: dict[str, Any]) -> str:
    # SECURITY: keyed, so a leaked table cannot be used to guess the password inside.
    body = json.dumps(payload, sort_keys=True, default=str)
    return salted_hmac("identity.idempotency", body, algorithm="sha256").hexdigest()


def lock(scope: str, key: UUID) -> None:
    """Hold a transaction lock so two requests with one key run one after the other."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", [f"{scope}:{key}"]
        )


def find(scope: str, key: UUID) -> IdempotencyRecord | None:
    cutoff = timezone.now() - KEEP_FOR
    IdempotencyRecord.objects.filter(
        scope=scope, key=key, created_at__lt=cutoff
    ).delete()
    return IdempotencyRecord.objects.filter(scope=scope, key=key).first()


def matches(record: IdempotencyRecord, request_hash: str) -> bool:
    return hmac.compare_digest(record.request_hash, request_hash)


def store(
    scope: str,
    key: UUID,
    request_hash: str,
    user: User | None,
    status_code: int,
    response: dict[str, Any],
) -> None:
    IdempotencyRecord.objects.create(
        scope=scope,
        key=key,
        request_hash=request_hash,
        user=user,
        status_code=status_code,
        response=response,
    )
