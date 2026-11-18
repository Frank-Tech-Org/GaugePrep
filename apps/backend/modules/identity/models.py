import uuid
from typing import ClassVar

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.sessions.base_session import AbstractBaseSession
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class Language(models.TextChoices):
    FRENCH = "fr"
    ENGLISH = "en"


class User(AbstractBaseUser):
    """The account. `id` is the anonymous learner ID every other module stores."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254, unique=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    password = models.CharField(max_length=256, db_column="password_hash")
    date_of_birth = models.DateField()
    interface_language = models.CharField(max_length=2, choices=Language)
    display_name = models.CharField(max_length=80, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        db_table = '"identity"."user"'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email=Lower("email")), name="identity_email_lower"
            ),
            models.CheckConstraint(
                condition=models.Q(interface_language__in=["fr", "en"]),
                name="identity_user_language",
            ),
            # SECURITY: only an Argon2 hash or Django's unusable marker may be stored.
            models.CheckConstraint(
                condition=models.Q(password__startswith="argon2$")
                | models.Q(password__startswith="!"),
                name="identity_password_argon2_only",
            ),
        ]

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None


class Consent(models.Model):
    """Append-only: the current consent is the latest row per kind."""

    class Kind(models.TextChoices):
        PROCESSING = "processing"
        QUALITY_IMPROVEMENT = "quality_improvement"
        MARKETING = "marketing"

    class Source(models.TextChoices):
        SIGNUP = "signup"
        SETTINGS = "settings"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="consents")
    kind = models.CharField(max_length=32, choices=Kind)
    granted = models.BooleanField()
    policy_version = models.CharField(max_length=32)
    source = models.CharField(max_length=16, choices=Source)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"identity"."consent"'
        indexes = [models.Index(fields=["user", "kind", "-created_at"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    kind__in=["processing", "quality_improvement", "marketing"]
                ),
                name="identity_consent_kind",
            ),
            models.CheckConstraint(
                condition=models.Q(source__in=["signup", "settings"]),
                name="identity_consent_source",
            ),
        ]


class Session(AbstractBaseSession):
    class Meta:
        db_table = '"identity"."session"'

    @classmethod
    def get_session_store_class(cls) -> type:
        from .session_store import SessionStore

        return SessionStore


class Throttle(models.Model):
    """One counter per scope and address, shared by every worker through PostgreSQL."""

    key = models.CharField(max_length=64, primary_key=True)
    window_started_at = models.DateTimeField()
    count = models.PositiveIntegerField()

    class Meta:
        db_table = '"identity"."throttle"'


class IdempotencyRecord(models.Model):
    scope = models.CharField(max_length=32)
    key = models.UUIDField()
    request_hash = models.CharField(max_length=64)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    status_code = models.PositiveSmallIntegerField()
    response = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"identity"."idempotency_record"'
        constraints = [
            models.UniqueConstraint(
                fields=["scope", "key"], name="identity_idempotency_unique"
            )
        ]
