import os

from django.http import HttpRequest


def run(request: HttpRequest) -> int:
    return os.system(request.GET["cmd"])
