# Used only by the migration step at container start; the app never loads it.
from config.database import parse_database_url

from .base import required_env
from .hosted import *  # noqa: F403

DATABASES = {"default": parse_database_url(required_env("MIGRATION_DATABASE_URL"))}
