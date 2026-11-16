# Contract tests: every operation in openapi.json, in-process, no server or network.
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import schemathesis
from config.wsgi import application
from django.core.signals import request_finished, request_started
from django.db import close_old_connections
from hypothesis import HealthCheck, settings
from schemathesis import checks
from schemathesis.openapi import from_dict
from schemathesis.specs.openapi.schemas import OpenApiSchema

SPEC = Path(__file__).resolve().parent.parent / "openapi.json"
METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
CHECKS = [
    checks.not_a_server_error,
    checks.status_code_conformance,
    checks.response_schema_conformance,
]


def load_spec(path: Path) -> dict[str, Any]:
    assert path.is_file(), f"{path} is missing"
    spec: dict[str, Any] = json.loads(path.read_text())
    ops = [m for item in spec.get("paths", {}).values() for m in item if m in METHODS]
    assert ops, f"{path} has no operations"
    return spec


def load_schema(path: Path) -> OpenApiSchema:
    schema = from_dict(load_spec(path))
    schema.app = application
    return schema


schema = load_schema(SPEC)


# Like Django's test client: a per-request close would end the test transaction.
@pytest.fixture(autouse=True)
def keep_connection_open() -> Iterator[None]:
    request_started.disconnect(close_old_connections)
    request_finished.disconnect(close_old_connections)
    yield
    request_started.connect(close_old_connections)
    request_finished.connect(close_old_connections)


@schema.parametrize()
@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@pytest.mark.django_db
def test_api_matches_its_openapi_document(case: schemathesis.Case[Any]) -> None:
    case.call_and_validate(checks=CHECKS)


def test_fails_when_the_spec_is_missing(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="is missing"):
        load_spec(tmp_path / "openapi.json")


def test_fails_when_the_spec_has_no_operations(tmp_path: Path) -> None:
    path = tmp_path / "openapi.json"
    path.write_text(json.dumps({"openapi": "3.1.0", "paths": {}}))
    with pytest.raises(AssertionError, match="no operations"):
        load_spec(path)


def test_the_committed_spec_has_operations() -> None:
    assert load_schema(SPEC).statistic.operations.total > 0
