def run(request):
    return eval(request.GET["expr"])
