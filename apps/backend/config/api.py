from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from modules.identity import public as identity
from ninja import NinjaAPI
from ninja.errors import AuthenticationError, ValidationError

from .health import router as health_router
from .problems import PROBLEM_CONTENT_TYPE, FieldProblem

RETRY_AFTER_HEADER = {
    "description": "Seconds to wait before the next attempt.",
    "required": True,
    "schema": {"type": "integer", "minimum": 1},
}


class ProblemAPI(NinjaAPI):
    """Declares every error answer as problem+json, the type the server sends."""

    def get_openapi_schema(self, **kwargs: Any) -> Any:
        schema = super().get_openapi_schema(**kwargs)
        for item in schema["paths"].values():
            for operation in item.values():
                for status, response in operation.get("responses", {}).items():
                    if int(status) == 429:
                        response["headers"] = {"Retry-After": RETRY_AFTER_HEADER}
                    content = response.get("content")
                    if int(status) >= 400 and content and "application/json" in content:
                        content[PROBLEM_CONTENT_TYPE] = content.pop("application/json")
        return schema


# The docs page is local only; openapi.json is served everywhere.
api = ProblemAPI(
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
