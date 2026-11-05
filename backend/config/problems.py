"""RFC 9457 problem details. `code` is a stable machine-readable error code."""

from django.http import JsonResponse
from ninja import Schema

PROBLEM_CONTENT_TYPE = "application/problem+json"


class Problem(Schema):
    type: str
    title: str
    status: int
    detail: str
    code: str


def problem_response(status: int, code: str, title: str, detail: str) -> JsonResponse:
    body = Problem(
        type=f"urn:gaugeprep:problem:{code.replace('_', '-')}",
        title=title,
        status=status,
        detail=detail,
        code=code,
    )
    return JsonResponse(
        body.model_dump(), status=status, content_type=PROBLEM_CONTENT_TYPE
    )
