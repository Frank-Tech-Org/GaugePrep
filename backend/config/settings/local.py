# Empty env values fall back to the defaults; the database is the compose db service.
import os

from config.database import parse_database_url

from .base import *  # noqa: F403
from .base import split_hosts

DEBUG = True
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or "local-only-insecure-key"
ALLOWED_HOSTS = split_hosts(
    os.environ.get("DJANGO_ALLOWED_HOSTS") or "localhost,127.0.0.1"
)

DATABASES = {
    "default": parse_database_url(
        os.environ.get("DATABASE_URL")
        or "postgres://postgres:postgres@localhost:5432/linguamentor"
    )
}
