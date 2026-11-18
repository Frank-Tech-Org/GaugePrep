from config.problems import FieldProblem, problem_response
from django.http import HttpRequest, JsonResponse

from .messages import CATALOG, request_language


def problem_for(
    request: HttpRequest,
    status: int,
    code: str,
    *,
    language: str | None = None,
    errors: list[FieldProblem] | None = None,
    headers: dict[str, str] | None = None,
) -> JsonResponse:
    """A problem-details answer in the learner's language."""
    chosen = language or request_language(request)
    title, detail = CATALOG[code][chosen]
    response = problem_response(
        status, code, title, detail, errors=errors, headers=headers
    )
    response["Content-Language"] = chosen
    return response
