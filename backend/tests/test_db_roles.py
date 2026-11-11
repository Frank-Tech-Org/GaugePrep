import uuid
from collections.abc import Iterator

import psycopg.errors
import pytest
from config.append_only import append_only
from config.db_roles import main, role_sql
from django.db import ProgrammingError, connection, transaction


@pytest.fixture
def roles(db: None) -> Iterator[tuple[str, str]]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
        row = cursor.fetchone()
        if row is None or not row[0]:
            pytest.skip("needs a superuser to create roles")
        tag = uuid.uuid4().hex[:8]
        migrator, serving = f"t_migrator_{tag}", f"t_serving_{tag}"
        database = connection.settings_dict["NAME"]
        cursor.execute(f'CREATE ROLE "{migrator}"')
        cursor.execute(f'CREATE ROLE "{serving}"')
        cursor.execute(role_sql(migrator, serving))
        cursor.execute(f'GRANT CREATE ON DATABASE "{database}" TO "{migrator}"')
        cursor.execute(f'GRANT CREATE ON SCHEMA public TO "{migrator}"')
    yield migrator, serving


def _as(role: str, *statements: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(f'SET LOCAL ROLE "{role}"')
        for statement in statements:
            cursor.execute(statement)
        cursor.execute("RESET ROLE")


def _refused(role: str, sql: str) -> None:
    with pytest.raises(ProgrammingError) as caught, transaction.atomic():
        _as(role, sql)
    assert isinstance(caught.value.__cause__, psycopg.errors.InsufficientPrivilege)


def _create_table(migrator: str, table: str, *, locked: bool) -> None:
    _as(migrator, f"CREATE TABLE {table} (id serial PRIMARY KEY, body text)")
    if locked:
        sql = append_only(table).sql
        assert isinstance(sql, str)
        _as(migrator, sql)


def test_serving_role_cannot_change_the_schema(roles: tuple[str, str]) -> None:
    migrator, serving = roles
    _create_table(migrator, "public.t_ordinary", locked=False)
    _refused(serving, "CREATE TABLE public.t_forbidden (id int)")
    _refused(serving, "ALTER TABLE public.t_ordinary ADD COLUMN extra int")
    _refused(serving, "DROP TABLE public.t_ordinary")
    _refused(serving, "TRUNCATE public.t_ordinary")


def test_new_table_is_usable_by_serving_role_without_a_grant(
    roles: tuple[str, str],
) -> None:
    migrator, serving = roles
    _create_table(migrator, "public.t_ordinary", locked=False)
    _as(
        serving,
        "INSERT INTO public.t_ordinary (body) VALUES ('a')",
        "UPDATE public.t_ordinary SET body = 'b'",
        "SELECT * FROM public.t_ordinary",
        "DELETE FROM public.t_ordinary",
    )


def test_serving_role_cannot_update_or_delete_on_an_append_only_table(
    roles: tuple[str, str],
) -> None:
    migrator, serving = roles
    _create_table(migrator, "public.t_grades", locked=True)
    _as(
        serving,
        "INSERT INTO public.t_grades (body) VALUES ('a')",
        "SELECT * FROM public.t_grades",
    )
    _refused(serving, "UPDATE public.t_grades SET body = 'b'")
    _refused(serving, "DELETE FROM public.t_grades")
    _refused(serving, "TRUNCATE public.t_grades")


def test_tables_in_a_later_schema_are_granted_too(roles: tuple[str, str]) -> None:
    migrator, serving = roles
    schema = f"s_{uuid.uuid4().hex[:8]}"
    _as(migrator, f"CREATE SCHEMA {schema}", f"CREATE TABLE {schema}.t (id serial)")
    _as(serving, f"INSERT INTO {schema}.t DEFAULT VALUES")
    _refused(serving, f"CREATE TABLE {schema}.u (id int)")


def test_role_names_are_checked() -> None:
    with pytest.raises(ValueError):
        role_sql('x"; y', "ok")


def test_command_prints_the_sql(capsys: pytest.CaptureFixture[str]) -> None:
    main(["app_migrator", "app_serving"])
    assert (
        capsys.readouterr().out.strip()
        == role_sql("app_migrator", "app_serving").strip()
    )


def test_command_refuses_a_missing_role() -> None:
    with pytest.raises(SystemExit, match="usage"):
        main(["app_migrator"])
