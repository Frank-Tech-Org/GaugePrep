import json
from pathlib import Path

from django.test import Client

COMMITTED = Path(__file__).resolve().parent.parent / "openapi.json"


def test_openapi_document_is_served(client: Client) -> None:
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert "/api/v1/health" in response.json()["paths"]


def test_committed_openapi_file_matches_the_api(client: Client) -> None:
    served = client.get("/api/v1/openapi.json").json()
    assert json.loads(COMMITTED.read_text()) == served, (
        "run: uv run python backend/manage.py export_openapi_schema "
        "--api config.api.api --indent 2 --output backend/openapi.json"
    )
