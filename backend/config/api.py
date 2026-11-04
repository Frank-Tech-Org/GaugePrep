from django.conf import settings
from ninja import NinjaAPI

from .health import router as health_router

# The docs page is local only; openapi.json is served everywhere.
api = NinjaAPI(
    title="LinguaMentor API",
    version="1",
    description="Public HTTP API. Errors are RFC 9457 problem details.",
    docs_url="/docs" if settings.DEBUG else None,
)
api.add_router("", health_router)

x = 1  # nosemgrep: some-rule
