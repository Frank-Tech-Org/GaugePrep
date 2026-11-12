# Every API operation needs a test marked success, not_found and refused.
import ast
import json
from collections.abc import Mapping
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[3] / "apps" / "backend"
KINDS = ("success", "not_found", "refused")
DISABLING = {"skip", "skipif", "xfail"}
EXEMPT = {"GET /api/v1/health", "GET /api/v1/openapi.json"}
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}

Mark = tuple[str, ast.Call | None]


def operations(spec_path: Path) -> list[tuple[str, str]]:
    assert spec_path.is_file(), f"{spec_path} is missing"
    paths = json.loads(spec_path.read_text())["paths"]
    found = [
        (f"{method.upper()} {path}", op.get("operationId", ""))
        for path, item in paths.items()
        for method, op in item.items()
        if method in HTTP_METHODS
    ]
    assert found, f"{spec_path} has no operations"
    return found


def _mark(node: ast.expr) -> Mark | None:
    call = node if isinstance(node, ast.Call) else None
    target = call.func if call else node
    if (
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Attribute)
        and target.value.attr == "mark"
        and isinstance(target.value.value, ast.Name)
        and target.value.value.id == "pytest"
    ):
        return target.attr, call
    return None


def _marks(nodes: list[ast.expr]) -> list[Mark]:
    return [m for node in nodes if (m := _mark(node))]


def _module_marks(tree: ast.Module) -> list[Mark]:
    nodes: list[ast.expr] = []
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "pytestmark" for t in stmt.targets
        ):
            value = stmt.value
            nodes += value.elts if isinstance(value, ast.List | ast.Tuple) else [value]
    return _marks(nodes)


Function = ast.FunctionDef | ast.AsyncFunctionDef


def _tests(tree: ast.Module) -> list[tuple[Function, list[Mark]]]:
    base = _module_marks(tree)
    found: list[tuple[Function, list[Mark]]] = []
    for stmt in tree.body:
        if isinstance(stmt, Function):
            found.append((stmt, base))
        elif isinstance(stmt, ast.ClassDef):
            inherited = base + _marks(stmt.decorator_list)
            found += [(m, inherited) for m in stmt.body if isinstance(m, Function)]
    return [(f, m) for f, m in found if f.name.startswith("test_")]


def marked(root: Path, skip: Path) -> tuple[dict[str, set[str]], list[str]]:
    """Operation names per kind, plus malformed markers as `file:line` errors."""
    names: dict[str, set[str]] = {kind: set() for kind in KINDS}
    errors: list[str] = []
    for file in sorted(root.rglob("test_*.py")):
        if file == skip:
            continue
        for func, inherited in _tests(ast.parse(file.read_text())):
            found = inherited + _marks(func.decorator_list)
            if any(name in DISABLING for name, _ in found):
                continue
            for name, call in found:
                if name not in KINDS:
                    continue
                args = call.args if call else []
                if (
                    call is None
                    or len(args) != 1
                    or call.keywords
                    or not isinstance(args[0], ast.Constant)
                    or not isinstance(args[0].value, str)
                ):
                    line = call.lineno if call else func.lineno
                    errors.append(
                        f"{file.name}:{line}: {name} marker needs one string argument"
                    )
                else:
                    names[name].add(args[0].value)
    return names, sorted(set(errors))


def missing(spec_path: Path, root: Path, skip: Path) -> list[str]:
    ops = operations(spec_path)
    names, errors = marked(root, skip)
    gaps = [
        f"{key}: missing {kind} test"
        for key, operation_id in ops
        if key not in EXEMPT
        for kind in KINDS
        if key not in names[kind] and operation_id not in names[kind]
    ]
    return errors + gaps


def test_every_operation_has_success_not_found_and_refused_tests() -> None:
    gaps = missing(BACKEND / "openapi.json", BACKEND, Path(__file__).resolve())
    assert not gaps, "\n".join(gaps)


def write_spec(tmp_path: Path, paths: Mapping[str, object]) -> Path:
    spec = tmp_path / "openapi.json"
    spec.write_text(json.dumps({"paths": paths}))
    return spec


def write_tests(tmp_path: Path, kinds: tuple[str, ...]) -> Path:
    root = tmp_path / "tests"
    root.mkdir()
    body = "".join(
        f'@pytest.mark.{kind}("GET /api/v1/items")\ndef test_{kind}(): ...\n'
        for kind in kinds
    )
    (root / "test_items.py").write_text("import pytest\n" + body)
    return root


ITEMS = {"/api/v1/items": {"get": {"operationId": "items_list"}}}


def test_passes_when_all_three_kinds_are_present(tmp_path: Path) -> None:
    spec = write_spec(tmp_path, ITEMS)
    root = write_tests(tmp_path, KINDS)
    assert missing(spec, root, Path()) == []


def test_names_the_operation_and_the_missing_kind(tmp_path: Path) -> None:
    spec = write_spec(tmp_path, ITEMS)
    root = write_tests(tmp_path, ("success", "not_found"))
    assert missing(spec, root, Path()) == ["GET /api/v1/items: missing refused test"]


def test_operation_id_satisfies_a_marker(tmp_path: Path) -> None:
    spec = write_spec(tmp_path, ITEMS)
    root = tmp_path / "tests"
    root.mkdir()
    (root / "test_items.py").write_text(
        "import pytest\n"
        + "".join(
            f'@pytest.mark.{k}("items_list")\ndef test_{k}(): ...\n' for k in KINDS
        )
    )
    assert missing(spec, root, Path()) == []


def test_exempt_operations_need_no_tests(tmp_path: Path) -> None:
    spec = write_spec(
        tmp_path,
        {
            "/api/v1/health": {"get": {}},
            "/api/v1/openapi.json": {"get": {}},
            "/api/v1/other": {"get": {}},
        },
    )
    root = tmp_path / "tests"
    root.mkdir()
    assert missing(spec, root, Path()) == [
        f"GET /api/v1/other: missing {kind} test" for kind in KINDS
    ]


def test_malformed_markers_are_reported_by_missing(tmp_path: Path) -> None:
    spec = write_spec(tmp_path, ITEMS)
    root = write_tests(tmp_path, KINDS)
    (root / "test_bad.py").write_text(
        "import pytest\n@pytest.mark.success()\ndef test_a(): ...\n"
    )
    assert missing(spec, root, Path()) == [
        "test_bad.py:2: success marker needs one string argument"
    ]


def test_fails_when_the_spec_is_missing(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="is missing"):
        operations(tmp_path / "openapi.json")


def test_fails_when_the_spec_has_no_operations(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="no operations"):
        operations(write_spec(tmp_path, {}))


def test_counts_exempt_operations_as_operations(tmp_path: Path) -> None:
    assert operations(write_spec(tmp_path, {"/api/v1/health": {"get": {}}}))


def scan(tmp_path: Path, source: str) -> tuple[dict[str, set[str]], list[str]]:
    (tmp_path / "test_x.py").write_text("import pytest\n" + source)
    return marked(tmp_path, Path())


def test_scan_counts_a_decorator(tmp_path: Path) -> None:
    names, errors = scan(tmp_path, '@pytest.mark.success("A")\ndef test_a(): ...\n')
    assert names["success"] == {"A"}
    assert errors == []


def test_scan_counts_a_class_marker_on_its_tests(tmp_path: Path) -> None:
    src = '@pytest.mark.refused("A")\nclass TestA:\n    def test_a(self): ...\n'
    assert scan(tmp_path, src)[0]["refused"] == {"A"}


def test_scan_counts_module_pytestmark(tmp_path: Path) -> None:
    src = 'pytestmark = [pytest.mark.not_found("A")]\ndef test_a(): ...\n'
    assert scan(tmp_path, src)[0]["not_found"] == {"A"}


def test_scan_counts_a_parametrized_test(tmp_path: Path) -> None:
    src = (
        '@pytest.mark.success("A")\n@pytest.mark.parametrize("n", [1, 2])\n'
        "def test_a(n): ...\n"
    )
    assert scan(tmp_path, src)[0]["success"] == {"A"}


def test_scan_ignores_comments_and_strings(tmp_path: Path) -> None:
    src = '# @pytest.mark.success("A")\nX = \'@pytest.mark.success("B")\'\n'
    names, errors = scan(tmp_path, src)
    assert names["success"] == set()
    assert errors == []


def test_scan_ignores_an_unknown_kind(tmp_path: Path) -> None:
    src = '@pytest.mark.succes("A")\ndef test_a(): ...\n'
    assert scan(tmp_path, src)[0] == {kind: set() for kind in KINDS}


def test_scan_ignores_a_marker_on_a_non_test_function(tmp_path: Path) -> None:
    src = '@pytest.mark.success("A")\ndef helper(): ...\n'
    assert scan(tmp_path, src)[0]["success"] == set()


@pytest.mark.parametrize("extra", ['skip("no")', 'skipif(True, reason="no")', "xfail"])
def test_scan_ignores_a_disabled_test(tmp_path: Path, extra: str) -> None:
    src = f'@pytest.mark.success("A")\n@pytest.mark.{extra}\ndef test_a(): ...\n'
    assert scan(tmp_path, src)[0]["success"] == set()


@pytest.mark.parametrize("args", ["", '"A", "B"', "1", 'op="A"'])
def test_scan_reports_a_malformed_marker(tmp_path: Path, args: str) -> None:
    src = f"@pytest.mark.success({args})\ndef test_a(): ...\n"
    names, errors = scan(tmp_path, src)
    assert errors == ["test_x.py:2: success marker needs one string argument"]
    assert names["success"] == set()


ASYNC_KINDS = (
    '@pytest.mark.success("A")\nasync def test_s(): ...\n'
    '@pytest.mark.not_found("A")\nasync def test_n(): ...\n'
)


def test_scan_counts_an_async_test_function(tmp_path: Path) -> None:
    src = '@pytest.mark.success("A")\nasync def test_a(): ...\n'
    assert scan(tmp_path, src)[0]["success"] == {"A"}


def test_scan_counts_an_async_test_method(tmp_path: Path) -> None:
    src = (
        '@pytest.mark.refused("A")\nclass TestA:\n'
        '    @pytest.mark.success("A")\n    async def test_a(self): ...\n'
    )
    names = scan(tmp_path, src)[0]
    assert names["success"] == {"A"}
    assert names["refused"] == {"A"}


def test_missing_flags_an_async_test_without_the_refused_marker(
    tmp_path: Path,
) -> None:
    spec = write_spec(tmp_path, ITEMS)
    root = tmp_path / "tests"
    root.mkdir()
    (root / "test_items.py").write_text(
        "import pytest\n"
        + ASYNC_KINDS.replace("A", "GET /api/v1/items")
        + "async def test_r(): ...\n"
    )
    assert missing(spec, root, Path()) == ["GET /api/v1/items: missing refused test"]
