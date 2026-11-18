from django.apps import apps
from django.contrib.sessions.backends.db import SessionStore as DatabaseSessionStore


class SessionStore(DatabaseSessionStore):
    @classmethod
    def get_model_class(cls) -> type:
        return apps.get_model("identity", "Session")
