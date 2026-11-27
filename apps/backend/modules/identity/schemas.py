from datetime import date
from typing import Literal
from uuid import UUID

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from ninja import Schema
from pydantic import Field, field_validator

LanguageCode = Literal["fr", "en"]


class EmailIn(Schema):
    email: str = Field(
        max_length=254, description="Email address; compared without case."
    )

    @field_validator("email")
    @classmethod
    def email_has_a_valid_shape(cls, value: str) -> str:
        try:
            validate_email(value.strip())
        except DjangoValidationError:
            raise ValueError("invalid email") from None
        return value


class SignUpIn(EmailIn):
    password: str = Field(
        min_length=1,
        max_length=128,
        description="Password, checked now and set when the email is verified.",
    )
    date_of_birth: date = Field(
        ge=date(1900, 1, 1),
        description="Date of birth; the learner must be 16 or older.",
    )
    interface_language: LanguageCode = Field(
        description="Interface language, fr or en."
    )
    display_name: str = Field(
        default="",
        max_length=80,
        description="Name shown in the app, up to 80 characters.",
    )
    processing_consent: bool = Field(
        default=False, description="Must be true: consent to process learning data."
    )


class VerifyEmailIn(EmailIn):
    code: str = Field(
        pattern=r"^\d{6}$", description="The six digits from the verification mail."
    )
    password: str = Field(
        min_length=1,
        max_length=128,
        description=(
            "The password for the account. It is set only when the code is right, "
            "so whoever owns the mailbox owns the password."
        ),
    )


class ResendAccepted(Schema):
    resend_available_in: int = Field(
        description="Seconds before another code can be requested."
    )


class LoginIn(Schema):
    email: str = Field(
        min_length=1, max_length=254, description="Email address of the account."
    )
    password: str = Field(
        min_length=1, max_length=256, description="Password of the account."
    )


class ProfilePatch(Schema):
    interface_language: LanguageCode | None = Field(
        default=None, description="New interface language, fr or en."
    )
    display_name: str | None = Field(
        default=None,
        max_length=80,
        description="New display name, up to 80 characters.",
    )


class Profile(Schema):
    learner_id: UUID = Field(
        description="Anonymous learner ID that every other part of the product stores."
    )
    email: str = Field(description="Account email, lower case.")
    display_name: str = Field(
        description="Name shown in the app; empty when none was given."
    )
    interface_language: LanguageCode = Field(
        description="Interface language, fr or en."
    )
    email_verified: bool = Field(
        description="True once the email address is confirmed."
    )


class AccountSession(Profile):
    csrf_token: str = Field(description="Token to send as X-CSRFToken on every write.")


class CsrfToken(Schema):
    csrf_token: str = Field(description="Token to send as X-CSRFToken on every write.")
