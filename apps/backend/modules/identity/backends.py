from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import make_password
from django.http import HttpRequest

from .models import User
from .services import normalize_email


class EmailBackend(BaseBackend):
    # WHY: unknown emails and passwordless accounts still pay for a hash.
    def authenticate(
        self,
        request: HttpRequest | None,
        email: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        if email is None or password is None:
            return None
        user = User.objects.filter(email=normalize_email(email)).first()
        if user is None or not user.has_usable_password():
            make_password(password)
            return None
        # SECURITY: an unconfirmed address cannot sign in, so right after sign-up a new
        # and a known email get the same refusal.
        return user if user.check_password(password) and user.email_verified else None

    def get_user(self, user_id: Any) -> User | None:
        return get_user_model().objects.filter(pk=user_id).first()
