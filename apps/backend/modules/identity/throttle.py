import hashlib
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.http import HttpRequest
from django.utils import timezone

from .models import Throttle

LOGIN = "login"
SIGNUP = "signup"


@dataclass(frozen=True)
class Limit:
    scope: str
    attempts: int
    window_seconds: int


LOGIN_FAILURES = Limit(LOGIN, attempts=5, window_seconds=60)
SIGNUPS = Limit(SIGNUP, attempts=20, window_seconds=3600)

# WHY: one statement, so two workers counting at once never lose an increment.
_UPSERT = """
INSERT INTO "identity"."throttle" (key, window_started_at, count)
VALUES (%(key)s, clock_timestamp(), 1)
ON CONFLICT (key) DO UPDATE SET
  count = CASE WHEN "identity"."throttle".window_started_at
                    <= clock_timestamp() - make_interval(secs => %(window)s)
               THEN 1 ELSE "identity"."throttle".count + 1 END,
  window_started_at = CASE WHEN "identity"."throttle".window_started_at
                    <= clock_timestamp() - make_interval(secs => %(window)s)
               THEN clock_timestamp() ELSE "identity"."throttle".window_started_at END
"""


def client_address(request: HttpRequest) -> str:
    """Behind the proxy the last X-Forwarded-For entry; otherwise the peer address."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if settings.SECURE_PROXY_SSL_HEADER and forwarded:
        return forwarded.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR", "")


def key_for(limit: Limit, address: str) -> str:
    return hashlib.sha256(f"{limit.scope}:{address}".encode()).hexdigest()


def record(limit: Limit, address: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            _UPSERT, {"key": key_for(limit, address), "window": limit.window_seconds}
        )


def retry_after(limit: Limit, address: str) -> int | None:
    """Seconds until the address may try again, or None when it is not blocked."""
    row = Throttle.objects.filter(key=key_for(limit, address)).first()
    if row is None or row.count < limit.attempts:
        return None
    ends = row.window_started_at + timedelta(seconds=limit.window_seconds)
    remaining = (ends - timezone.now()).total_seconds()
    return max(1, int(remaining) + 1) if remaining > 0 else None
