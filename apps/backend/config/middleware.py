from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.http.response import HttpResponseBase
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.cache import patch_vary_headers

API_PREFIX = "/api/v1/"
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


CORS_METHODS = "GET, POST, PUT, PATCH, DELETE"
CORS_HEADERS = "Content-Type, X-CSRFToken, Idempotency-Key"
CORS_MAX_AGE = "7200"  # seconds; Chromium caps it there


# SECURITY: only the exact app origin gets a header, never a wildcard.
class CorsMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        origin = request.headers.get("Origin")
        allowed = origin is not None and origin == settings.WEB_APP_ORIGIN
        preflight = (
            request.method == "OPTIONS"
            and "Access-Control-Request-Method" in request.headers
        )
        if allowed and preflight:
            response = HttpResponse(status=204)
            response["Access-Control-Allow-Methods"] = CORS_METHODS
            response["Access-Control-Allow-Headers"] = CORS_HEADERS
            response["Access-Control-Max-Age"] = CORS_MAX_AGE
        else:
            response = self.get_response(request)
        if origin is not None:
            patch_vary_headers(response, ["Origin"])
        if allowed and origin is not None:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
        return response


# WHY: API answers hold personal data; a view that sets its own Cache-Control keeps it.
class NoStoreMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if request.path.startswith(API_PREFIX) and request.path != HEALTH_PATH:
            if "Cache-Control" not in response:
                response["Cache-Control"] = "no-store"
        return response


def _not_exempt(request: HttpRequest) -> HttpResponse:  # pragma: no cover
    raise AssertionError("the view is never called here")


# WHY: Ninja marks every view csrf_exempt; this checks every unsafe API call anyway.
class ApiCsrfMiddleware(CsrfViewMiddleware):
    def process_view(
        self,
        request: HttpRequest,
        callback: Callable[..., HttpResponseBase],
        callback_args: tuple[Any, ...],
        callback_kwargs: dict[str, Any],
    ) -> HttpResponseForbidden | None:
        if not request.path.startswith(API_PREFIX):
            return super().process_view(
                request, callback, callback_args, callback_kwargs
            )
        return super().process_view(
            request, _not_exempt, callback_args, callback_kwargs
        )
