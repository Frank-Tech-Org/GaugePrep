import json
import socket
from collections.abc import Iterator

import pytest
from django.db import connection
from django.test import Client
from pytest_django.plugin import DjangoDbBlocker


def test_health_returns_200_when_the_database_is_up(db: None, client: Client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.fixture
def unreachable_database(
    django_db_blocker: DjangoDbBlocker,
) -> Iterator[None]:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        free_port = str(sock.getsockname()[1])
    with django_db_blocker.unblock():
        connection.close()
        original = dict(connection.settings_dict)
        connection.settings_dict.update(HOST="127.0.0.1", PORT=free_port)
        try:
            yield
        finally:
            connection.close()
            connection.settings_dict.update(original)


def test_health_returns_503_problem_details_when_the_database_is_down(
    client: Client, unreachable_database: None
) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 503
    assert response["Content-Type"] == "application/problem+json"
    body = response.json()
    assert body["status"] == 503
    assert body["code"] == "database_unavailable"
    assert {"type", "title", "detail"} <= body.keys()
    leaked = json.dumps(body).lower()
    assert "127.0.0.1" not in leaked
    assert "refused" not in leaked
    assert "postgres" not in leaked
