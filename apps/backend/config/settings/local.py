# Empty env values fall back to the defaults; the database is the compose db service.
import os

from config.database import parse_database_url

from .base import *  # noqa: F403
from .base import split_hosts, web_app_origin

DEBUG = True
MAIL_HEALTH_TO = os.environ.get("MAIL_HEALTH_TO") or "health@gaugeprep.test"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or "local-only-insecure-key"
ALLOWED_HOSTS = split_hosts(os.environ.get("DJANGO_ALLOWED_HOSTS", "")) or [
    "localhost",
    "127.0.0.1",
]

DATABASES = {
    "default": parse_database_url(
        os.environ.get("DATABASE_URL")
        or "postgres://postgres:postgres@localhost:5432/gaugeprep"
    )
}

# Web app and cookies
WEB_APP_ORIGIN = web_app_origin(
    os.environ.get("WEB_APP_ORIGIN") or "http://localhost:3000", https_only=False
)
CSRF_TRUSTED_ORIGINS = [WEB_APP_ORIGIN]
SESSION_COOKIE_NAME = "gp_session"
CSRF_COOKIE_NAME = "gp_csrf"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
