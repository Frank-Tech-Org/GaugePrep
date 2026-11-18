from datetime import date
from typing import Literal
from uuid import UUID

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from ninja import Schema
from pydantic import Field, field_validator

LanguageCode = Literal["fr", "en"]


class SignUpIn(Schema):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)
    date_of_birth: date = Field(ge=date(1900, 1, 1))
    interface_language: LanguageCode
    display_name: str = Field(default="", max_length=80)
    processing_consent: bool = False

    @field_validator("email")
    @classmethod
    def email_has_a_valid_shape(cls, value: str) -> str:
        try:
            validate_email(value.strip())
        except DjangoValidationError:
            raise ValueError("invalid email") from None
        return value


class LoginIn(Schema):
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class ProfilePatch(Schema):
    interface_language: LanguageCode | None = None
    display_name: str | None = Field(default=None, max_length=80)


class Profile(Schema):
    learner_id: UUID
    email: str
    display_name: str
    interface_language: LanguageCode
    email_verified: bool


class AccountSession(Profile):
    csrf_token: str


class CsrfToken(Schema):
    csrf_token: str
