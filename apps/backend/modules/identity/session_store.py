from django.contrib.sessions.backends.db import SessionStore as DatabaseSessionStore


class SessionStore(DatabaseSessionStore):
    @classmethod
    def get_model_class(cls) -> type:
        from .models import Session

        return Session
