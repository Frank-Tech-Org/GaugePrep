import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def required_env(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        raise ImproperlyConfigured(f"{key} must be set in the environment")
    return value


def split_hosts(raw: str) -> list[str]:
    return [host.strip() for host in raw.split(",") if host.strip()]


HOST_PORT = re.compile(r"[A-Za-z0-9.-]+(:\d{1,5})?")


# WHY: CORS compares this string with the Origin header, so it must be one bare origin.
def web_app_origin(raw: str, *, https_only: bool) -> str:
    parts = urlsplit(raw)
    schemes = {"https"} if https_only else {"http", "https"}
    bare = f"{parts.scheme}://{parts.netloc}"
    valid_host = HOST_PORT.fullmatch(parts.netloc)
    if parts.scheme not in schemes or raw != bare or not valid_host:
        raise ImproperlyConfigured(
            "WEB_APP_ORIGIN must be one origin like https://app.example.com, no path"
        )
    return raw


INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "ninja",
    "procrastinate.contrib.django",
    "modules.identity",
    "modules.learner",
    "modules.curriculum",
    "modules.content",
    "modules.exammodels",
    "modules.practice",
    "modules.simulation",
    "modules.assessment",
    "modules.prediction",
    "modules.calibration",
    "modules.billing",
    "modules.engagement",
    "modules.reporting",
    "modules.admin",
]

MIDDLEWARE = [
    "config.middleware.HealthCheckHostMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "config.middleware.CorsMiddleware",
    "config.middleware.NoStoreMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "config.middleware.ApiCsrfMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en"

# Needed for the Swagger docs page; no context processors, no sessions or admin.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    }
]

# Serves the Swagger assets while DEBUG is on; the docs page is off elsewhere.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 63072000  # two years

# Accounts
AUTH_USER_MODEL = "identity.User"
AUTHENTICATION_BACKENDS = ["modules.identity.backends.EmailBackend"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher"]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Sessions and cookies
SESSION_ENGINE = "modules.identity.session_store"
SESSION_COOKIE_AGE = 14 * 24 * 3600  # seconds
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_DOMAIN = None
CSRF_FAILURE_VIEW = "config.problems.csrf_failure"

# Mail
_mail_key = os.environ.get("MAIL_API_KEY", "")
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": os.environ.get("MAIL_HOST") or "localhost",
            "port": int(os.environ.get("MAIL_PORT") or 1025),
            "username": "resend" if _mail_key else "",
            "password": _mail_key,
            "use_tls": bool(_mail_key),
            "timeout": 10,  # seconds
        },
    }
}
DEFAULT_FROM_EMAIL = os.environ.get("MAIL_FROM") or "GaugePrep <no-reply@localhost>"
MAIL_HEALTH_TO = os.environ.get("MAIL_HEALTH_TO", "")

# Jobs
PROCRASTINATE_IMPORT_PATHS = ["config.jobs", "modules.identity.tasks"]
PROCRASTINATE_AUTODISCOVER_MODULE_NAME = ""
PROCRASTINATE_WORKER_DEFAULTS = {
    "wait": True,
    "concurrency": 2,
    "fetch_job_polling_interval": 5,  # seconds
    "shutdown_graceful_timeout": 20,  # seconds
}

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "line": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "line"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
