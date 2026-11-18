from dataclasses import dataclass
from uuid import UUID

from django.conf import settings
from django.http import HttpRequest
from ninja.security.base import AuthBase

from .models import User


@dataclass(frozen=True)
class Learner:
    """What other modules see of a signed-in learner: no personal data."""

    learner_id: UUID
    interface_language: str


class LearnerAuth(AuthBase):
    """Access: learner. The session middleware has already read the cookie."""

    openapi_type = "apiKey"
    openapi_in = "cookie"
    openapi_name = settings.SESSION_COOKIE_NAME

    def __call__(self, request: HttpRequest) -> Learner | None:
        user = request.user
        if not isinstance(user, User) or not user.is_authenticated:
            return None
        return Learner(user.id, user.interface_language)


learner_auth = LearnerAuth()
