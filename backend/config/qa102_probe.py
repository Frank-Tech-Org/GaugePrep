from django.http import HttpRequest, HttpResponse


def probe(request: HttpRequest) -> HttpResponse:
    return HttpResponse(str(int(request.GET["n"]) + 1))
