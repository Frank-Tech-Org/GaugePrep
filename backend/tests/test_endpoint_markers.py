# Every API operation needs a test marked success, not_found and refused.
import ast
import json
from collections.abc import Mapping
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
KINDS = ("success", "not_found", "refused")
EXEMPT = {"GET /api/v1/health", "GET /api/v1/openapi.json"}
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


def operations(spec_path: Path) -> list[tuple[str, str]]:
    """(key, operationId) for every operation; fails on a missing or empty spec."""
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


def marked(root: Path, skip: Path) -> dict[str, set[str]]:
    """Operation names per marker kind, read from `pytest.mark.<kind>("...")` calls."""
    names: dict[str, set[str]] = {kind: set() for kind in KINDS}
    for file in root.rglob("*.py"):
        if file == skip:
            continue
        for node in ast.walk(ast.parse(file.read_text())):
            if not (
                isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            ):
                continue
            mark = node.func.value
            if (
                node.func.attr in KINDS
                and isinstance(mark, ast.Attribute)
                and mark.attr == "mark"
            ):
                names[node.func.attr].update(
                    arg.value
                    for arg in node.args
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                )
    return names


def missing(spec_path: Path, root: Path, skip: Path) -> list[str]:
    ops = operations(spec_path)
    names = marked(root, skip)
    return [
        f"{key}: missing {kind} test"
        for key, operation_id in ops
        if key not in EXEMPT
        for kind in KINDS
        if key not in names[kind] and operation_id not in names[kind]
    ]


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


def test_fails_when_the_spec_is_missing(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="is missing"):
        operations(tmp_path / "openapi.json")


def test_fails_when_the_spec_has_no_operations(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="no operations"):
        operations(write_spec(tmp_path, {}))


def test_counts_exempt_operations_as_operations(tmp_path: Path) -> None:
    assert operations(write_spec(tmp_path, {"/api/v1/health": {"get": {}}}))
