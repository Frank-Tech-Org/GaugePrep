import ipaddress
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.db import connection
from django.http import HttpRequest
from django.utils import timezone
from django.utils.crypto import salted_hmac

LOGIN = "login"
LOGIN_EMAIL = "login_email"
SIGNUP = "signup"
MAIL_MINUTE = "mail_minute"
MAIL_HOUR = "mail_hour"


@dataclass(frozen=True)
class Limit:
    scope: str
    attempts: int
    window_seconds: int


LOGIN_FAILURES = Limit(LOGIN, attempts=6, window_seconds=60)
LOGIN_EMAIL_FAILURES = Limit(LOGIN_EMAIL, attempts=10, window_seconds=3600)
SIGNUPS = Limit(SIGNUP, attempts=20, window_seconds=3600)
MAILS_PER_MINUTE = Limit(MAIL_MINUTE, attempts=1, window_seconds=60)
MAILS_PER_HOUR = Limit(MAIL_HOUR, attempts=5, window_seconds=3600)

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
RETURNING count, window_started_at
"""

_RELEASE = """
UPDATE "identity"."throttle" SET count = GREATEST(count - 1, 0) WHERE key = %(key)s
"""


@dataclass(frozen=True)
class Tally:
    count: int
    window_started_at: datetime


def normalize_address(raw: str) -> str:
    """IPv4 as is, IPv4-mapped IPv6 as its IPv4 address, other IPv6 as its /64 range."""
    text = raw.strip().split("%")[0]
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return raw.strip()
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            return str(ip.ipv4_mapped)
        return str(ipaddress.ip_network((ip, 64), strict=False))
    return str(ip)


def client_address(request: HttpRequest) -> str:
    """Behind the proxy the last X-Forwarded-For entry; otherwise the peer address."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if settings.SECURE_PROXY_SSL_HEADER and forwarded:
        return normalize_address(forwarded.split(",")[-1])
    return normalize_address(str(request.META.get("REMOTE_ADDR", "")))


def key_for(limit: Limit, subject: str) -> str:
    # SECURITY: keyed, so a leaked table cannot confirm a guessed email or address.
    return salted_hmac(
        "gaugeprep.identity.throttle",
        f"{limit.scope}:{subject}",
        secret=settings.THROTTLE_KEY_SECRET,
        algorithm="sha256",
    ).hexdigest()


def record(limit: Limit, address: str) -> Tally:
    with connection.cursor() as cursor:
        cursor.execute(
            _UPSERT, {"key": key_for(limit, address), "window": limit.window_seconds}
        )
        count, started = cursor.fetchone()
    return Tally(count, started)


def release(limit: Limit, subject: str) -> None:
    """Take back one counted attempt, for a login that turned out to be right."""
    with connection.cursor() as cursor:
        cursor.execute(_RELEASE, {"key": key_for(limit, subject)})


def wait_if_over(limit: Limit, tally: Tally) -> int | None:
    """Seconds to wait when this attempt went past the limit, else None."""
    if tally.count <= limit.attempts:
        return None
    ends = tally.window_started_at + timedelta(seconds=limit.window_seconds)
    return max(1, int((ends - timezone.now()).total_seconds()) + 1)
