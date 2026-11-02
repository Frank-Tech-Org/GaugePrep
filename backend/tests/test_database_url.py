import pytest
from config.database import parse_database_url
from django.core.exceptions import ImproperlyConfigured


def test_parses_all_parts() -> None:
    parsed = parse_database_url("postgres://user:pa%40ss@db.example:6543/lingua")
    assert parsed["ENGINE"] == "django.db.backends.postgresql"
    assert parsed["NAME"] == "lingua"
    assert parsed["USER"] == "user"
    assert parsed["PASSWORD"] == "pa@ss"
    assert parsed["HOST"] == "db.example"
    assert parsed["PORT"] == "6543"


def test_accepts_postgresql_scheme_and_defaults_the_port() -> None:
    parsed = parse_database_url("postgresql://u:p@localhost/db")
    assert parsed["PORT"] == "5432"


def test_query_string_becomes_connection_options() -> None:
    parsed = parse_database_url("postgres://u:p@h/db?sslmode=require")
    assert parsed["OPTIONS"]["sslmode"] == "require"


def test_default_connect_timeout_is_two_seconds() -> None:
    parsed = parse_database_url("postgres://u:p@h/db")
    assert parsed["OPTIONS"]["connect_timeout"] == 2


def test_connect_timeout_is_always_set() -> None:
    parsed = parse_database_url("postgres://u:p@h/db", connect_timeout=3)
    assert parsed["OPTIONS"]["connect_timeout"] == 3


@pytest.mark.parametrize(
    "url", ["", "mysql://u:p@h/db", "postgres://u:p@h", "not a url"]
)
def test_rejects_bad_urls_without_echoing_them(url: str) -> None:
    with pytest.raises(ImproperlyConfigured) as error:
        parse_database_url(url)
    assert "p@h" not in str(error.value)
