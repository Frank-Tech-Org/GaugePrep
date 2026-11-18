from django.conf import settings
from django.http import HttpRequest, HttpResponse
from modules.identity import public as identity
from ninja import NinjaAPI
from ninja.errors import AuthenticationError, ValidationError

from .health import router as health_router
from .problems import FieldProblem

# The docs page is local only; openapi.json is served everywhere.
api = NinjaAPI(
    title="GaugePrep API",
    version="1",
    description="Public HTTP API. Errors are RFC 9457 problem details.",
    docs_url="/docs" if settings.DEBUG else None,
)
api.add_router("", health_router)
api.add_router("", identity.router)


@api.exception_handler(AuthenticationError)
def not_authenticated(request: HttpRequest, exc: AuthenticationError) -> HttpResponse:
    return identity.problem_for(request, 401, "not_authenticated")


# SECURITY: only field names and error types go out; the submitted values never do.
@api.exception_handler(ValidationError)
def invalid_request(request: HttpRequest, exc: ValidationError) -> HttpResponse:
    errors = [
        FieldProblem(
            field=".".join(str(part) for part in item["loc"][2:]) or "body",
            code=str(item["type"]),
        )
        for item in exc.errors
    ]
    return identity.problem_for(request, 422, "validation_error", errors=errors)
