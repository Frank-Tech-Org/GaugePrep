# Dev, staging and production: no defaults, a missing value stops startup.

from config.database import parse_database_url

from .base import *  # noqa: F403
from django.core.exceptions import ImproperlyConfigured

from .base import required_env, split_hosts

DEBUG = False
SECRET_KEY = required_env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = split_hosts(required_env("DJANGO_ALLOWED_HOSTS"))
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list at least one host")
DATABASES = {"default": parse_database_url(required_env("DATABASE_URL"))}

# TLS ends at the proxy, which sets this header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
