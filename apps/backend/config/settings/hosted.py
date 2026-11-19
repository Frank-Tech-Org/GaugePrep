# Dev, staging and production: no defaults, a missing value stops startup.

from django.core.exceptions import ImproperlyConfigured

from config.database import parse_database_url

from .base import *  # noqa: F403
from .base import required_env, split_hosts, web_app_origin

DEBUG = False
SECRET_KEY = required_env("DJANGO_SECRET_KEY")
THROTTLE_KEY_SECRET = required_env("THROTTLE_KEY_SECRET")
if len(THROTTLE_KEY_SECRET) < 32:
    raise ImproperlyConfigured("THROTTLE_KEY_SECRET must be at least 32 characters")
ALLOWED_HOSTS = split_hosts(required_env("DJANGO_ALLOWED_HOSTS"))
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list at least one host")
for _key in ("MAIL_HOST", "MAIL_PORT", "MAIL_FROM", "MAIL_HEALTH_TO"):
    required_env(_key)
DATABASES = {"default": parse_database_url(required_env("DATABASE_URL"))}

# TLS ends at the proxy, which sets this header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Web app and cookies
WEB_APP_ORIGIN = web_app_origin(required_env("WEB_APP_ORIGIN"), https_only=True)
CSRF_TRUSTED_ORIGINS = [WEB_APP_ORIGIN]
SESSION_COOKIE_NAME = "__Host-gp_session"
CSRF_COOKIE_NAME = "__Host-gp_csrf"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
