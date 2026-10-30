# Empty env values fall back to the defaults; the database is the compose db service.
import os

from config.database import parse_database_url

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or "local-only-insecure-key"
ALLOWED_HOSTS = (os.environ.get("DJANGO_ALLOWED_HOSTS") or "localhost,127.0.0.1").split(
    ","
)

DATABASES = {
    "default": parse_database_url(
        os.environ.get("DATABASE_URL")
        or "postgres://postgres:postgres@localhost:5432/linguamentor"
    )
}
