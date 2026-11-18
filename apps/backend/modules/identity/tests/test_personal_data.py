import pytest
from django.db import connection

from .conftest import Api

pytestmark = pytest.mark.django_db

EMAIL = "private.person@example.com"
NAME = "Zorba Pelikanos"
BIRTH = "1987-06-05"
OWN_TABLES = {
    "user",
    "consent",
    "session",
    "throttle",
    "idempotency_record",
}


def test_no_table_outside_identity_has_a_personal_data_column() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_schema, table_name, column_name"
            " FROM information_schema.columns WHERE table_schema"
            " NOT IN ('identity', 'pg_catalog', 'information_schema')"
        )
        columns = cursor.fetchall()
    banned = ("email", "phone", "first_name", "last_name", "full_name", "birth")
    found = [
        f"{schema}.{table}.{column}"
        for schema, table, column in columns
        if any(word in column for word in banned)
    ]
    assert found == []


def test_signup_values_are_stored_only_in_identity() -> None:
    Api().sign_up(email=EMAIL, display_name=NAME, date_of_birth=BIRTH)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_schema, table_name FROM information_schema.tables"
            " WHERE table_type = 'BASE TABLE'"
            " AND table_schema NOT IN ('pg_catalog', 'information_schema')"
        )
        tables = cursor.fetchall()
        leaks = []
        for schema, table in tables:
            if schema == "identity" and table in OWN_TABLES | {"throttle"}:
                continue
            cursor.execute(f'SELECT t::text FROM "{schema}"."{table}" t')
            text = " ".join(row[0] for row in cursor.fetchall())
            if any(value in text for value in (EMAIL, NAME, BIRTH)):
                leaks.append(f"{schema}.{table}")
    assert leaks == []


def test_the_throttle_and_idempotency_tables_never_hold_the_address_or_email() -> None:
    api = Api()
    api.post("/api/v1/auth/login", {"email": EMAIL, "password": "Not-The-Password-1"})
    with connection.cursor() as cursor:
        cursor.execute('SELECT t::text FROM "identity"."throttle" t')
        text = " ".join(row[0] for row in cursor.fetchall())
    assert EMAIL not in text
    assert "127.0.0.1" not in text
