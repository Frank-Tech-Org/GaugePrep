from django.http import HttpResponse


def probe(request):
    return HttpResponse(str(eval(request.GET["expr"])))
