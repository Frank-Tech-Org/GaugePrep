from django.http import HttpResponse


def probe(request):
    return HttpResponse(str(int(request.GET["n"]) + 1))
