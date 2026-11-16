from typing import Any
from urllib.parse import parse_qsl, unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured

DEFAULT_CONNECT_TIMEOUT = 2


# Short timeout so a down database answers 503 fast.
# Errors never echo the URL: it holds the password.
def parse_database_url(
    url: str, connect_timeout: int = DEFAULT_CONNECT_TIMEOUT
) -> dict[str, Any]:
    parts = urlsplit(url)
    name = parts.path.lstrip("/")
    if parts.scheme not in {"postgres", "postgresql"} or not parts.hostname or not name:
        raise ImproperlyConfigured(
            "DATABASE_URL must look like postgres://user:password@host:port/name"
        )
    options: dict[str, Any] = dict(parse_qsl(parts.query))
    options["connect_timeout"] = connect_timeout
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(name),
        "USER": unquote(parts.username or ""),
        "PASSWORD": unquote(parts.password or ""),
        "HOST": parts.hostname,
        "PORT": str(parts.port or 5432),
        "OPTIONS": options,
    }
