# Test snippets for request-eval-exec.yaml; run with `semgrep --test semgrep/`.
import ast
import builtins

from ninja import NinjaAPI, Router

api = NinjaAPI()
router = Router()


def eval_get(request):
    # ruleid: lm-django-request-eval
    return eval(request.GET["expr"])


def eval_body(request):
    expr = request.body.decode()
    # ruleid: lm-django-request-eval
    return eval(expr)


def eval_cbv(self):
    # ruleid: lm-django-request-eval
    return builtins.eval(self.request.POST.get("expr"))


def eval_ok(request):
    # ok: lm-django-request-eval
    return eval("1 + 1")


def eval_parsed_ok(request):
    # ok: lm-django-request-eval
    return eval(str(int(request.GET["n"])))


def eval_literal_ok(request):
    # ok: lm-django-request-eval
    return ast.literal_eval(request.GET["expr"])


def exec_post(request):
    # ruleid: lm-django-request-exec
    exec(request.POST["code"])


def exec_header(request):
    code = request.headers.get("X-Code")
    # ruleid: lm-django-request-exec
    exec(code)


def exec_ok(request):
    # ok: lm-django-request-exec
    exec("x = 1")


def exec_parsed_ok(request):
    # ok: lm-django-request-exec
    exec(f"x = {int(request.GET['n'])}")


@api.get("/calc")
def ninja_eval(request, expr: str):
    # ruleid: lm-ninja-param-eval
    return eval(expr)


@api.get("/calc-ok")
def ninja_eval_ok(request, expr: str):
    # ok: lm-ninja-param-eval
    return eval("1 + 1")


@router.post("/run")
def ninja_exec(request, payload: str):
    # ruleid: lm-ninja-param-exec
    exec(payload)


@router.post("/run-ok")
def ninja_exec_ok(request, payload: str):
    # ok: lm-ninja-param-exec
    exec("x = 1")
