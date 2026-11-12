from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

HEALTH_PATH = "/api/v1/health"


# kamal-proxy probes the container by its ID, which is never an allowed host.
# Only the health path gets the first allowed host; every other path is still checked.
class HealthCheckHostMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path == HEALTH_PATH and settings.ALLOWED_HOSTS:
            request.META["HTTP_HOST"] = settings.ALLOWED_HOSTS[0].lstrip(".")
        return self.get_response(request)
