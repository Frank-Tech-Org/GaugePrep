"""RFC 9457 problem details. `code` is a stable machine-readable error code."""

from collections.abc import Mapping

from django.http import HttpRequest, JsonResponse
from ninja import Schema

PROBLEM_CONTENT_TYPE = "application/problem+json"


class FieldProblem(Schema):
    field: str
    code: str


class Problem(Schema):
    type: str
    title: str
    status: int
    detail: str
    code: str
    errors: list[FieldProblem] | None = None


def problem_response(
    status: int,
    code: str,
    title: str,
    detail: str,
    *,
    errors: list[FieldProblem] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JsonResponse:
    body = Problem(
        type=f"urn:gaugeprep:problem:{code.replace('_', '-')}",
        title=title,
        status=status,
        detail=detail,
        code=code,
        errors=errors,
    )
    response = JsonResponse(
        body.model_dump(exclude_none=True),
        status=status,
        content_type=PROBLEM_CONTENT_TYPE,
    )
    for name, value in (headers or {}).items():
        response[name] = value
    return response


def csrf_failure(request: HttpRequest, reason: str = "") -> JsonResponse:
    # WHY: imported late because settings name this view before apps are ready.
    from modules.identity.public import problem_for

    return problem_for(request, 403, "csrf_failed")
