import os

from django.core.asgi import get_asgi_application

os.environ["DJANGO_SETTINGS_MODULE"] = (
    os.environ.get("DJANGO_SETTINGS_MODULE") or "config.settings.local"
)
application = get_asgi_application()
