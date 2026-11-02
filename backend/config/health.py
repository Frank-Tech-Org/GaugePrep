import logging

from django.db import DatabaseError, InterfaceError, connection
from django.http import HttpRequest, HttpResponse
from ninja import Router, Schema, Status

from .problems import Problem, problem_response

logger = logging.getLogger(__name__)
router = Router(tags=["health"])


class Health(Schema):
    status: str
    database: str


# The 2 s connect timeout comes from parse_database_url.
def database_is_up() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except (DatabaseError, InterfaceError) as exc:
        logger.warning("health check: database unreachable (%s)", type(exc).__name__)
        connection.close()
        return False
    return True


@router.get(
    "/health", auth=None, response={200: Health, 503: Problem}, summary="Health"
)
def health(request: HttpRequest) -> Status[Health] | HttpResponse:
    if database_is_up():
        return Status(200, Health(status="ok", database="ok"))
    return problem_response(
        503,
        "database_unavailable",
        "Database unavailable",
        "The service cannot reach its database right now.",
    )
