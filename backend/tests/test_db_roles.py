import os
import uuid
from collections.abc import Iterator

import psycopg.errors
import pytest
from config.append_only import append_only
from config.db_roles import main, role_sql
from django.db import ProgrammingError, connection, migrations, transaction
from django.db.migrations.state import ProjectState


@pytest.fixture
def roles(db: None) -> Iterator[tuple[str, str]]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
        row = cursor.fetchone()
        if row is None or not row[0]:
            reason = "needs a superuser to create roles"
            if os.environ.get("CI") == "true":
                pytest.fail(reason)
            pytest.skip(reason)
        tag = uuid.uuid4().hex[:8]
        migrator, serving = f"t_migrator_{tag}", f"t_serving_{tag}"
        cursor.execute(f'CREATE ROLE "{migrator}"')
        cursor.execute(f'CREATE ROLE "{serving}"')
        cursor.execute(role_sql(migrator, serving))
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


def _run(op: migrations.operations.base.Operation, *, backwards: bool = False) -> None:
    with connection.schema_editor() as editor:
        step = op.database_backwards if backwards else op.database_forwards
        step("t", editor, ProjectState(), ProjectState())


def _create_table(migrator: str, table: str, *, locked: bool) -> None:
    _as(migrator, f"CREATE TABLE {table} (id serial PRIMARY KEY, body text)")
    if locked:
        _run(append_only(table))


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


def test_rerunning_the_role_sql_keeps_an_append_only_table_closed(
    roles: tuple[str, str],
) -> None:
    migrator, serving = roles
    _create_table(migrator, "public.t_grades", locked=True)
    _as(serving, "INSERT INTO public.t_grades (body) VALUES ('a')")
    with connection.cursor() as cursor:
        cursor.execute(role_sql(migrator, serving))
    _as(serving, "INSERT INTO public.t_grades (body) VALUES ('b')")
    _refused(serving, "UPDATE public.t_grades SET body = 'c'")
    _refused(serving, "DELETE FROM public.t_grades")
    _refused(serving, "TRUNCATE public.t_grades")


def test_trigger_refuses_even_when_the_privilege_is_granted(
    roles: tuple[str, str],
) -> None:
    migrator, serving = roles
    _create_table(migrator, "public.t_grades", locked=True)
    _as(serving, "INSERT INTO public.t_grades (body) VALUES ('a')")
    with connection.cursor() as cursor:
        cursor.execute(
            f'GRANT UPDATE, DELETE, TRUNCATE ON public.t_grades TO "{serving}"'
        )
    _refused(serving, "UPDATE public.t_grades SET body = 'b'")
    _refused(serving, "DELETE FROM public.t_grades")
    _refused(serving, "TRUNCATE public.t_grades")


def test_reversing_append_only_gives_update_and_delete_back_to_serving_only(
    roles: tuple[str, str],
) -> None:
    migrator, serving = roles
    op = append_only("public.t_grades")
    _create_table(migrator, "public.t_grades", locked=False)
    _run(op)
    _run(op, backwards=True)
    _as(
        serving,
        "INSERT INTO public.t_grades (body) VALUES ('a')",
        "UPDATE public.t_grades SET body = 'b'",
        "DELETE FROM public.t_grades",
    )
    _refused(serving, "TRUNCATE public.t_grades")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM pg_trigger "
            "WHERE tgrelid = 'public.t_grades'::regclass"
        )
        assert cursor.fetchone() == (0,)


def test_other_grantees_lose_their_table_rights(roles: tuple[str, str]) -> None:
    migrator, serving = roles
    stray = f"t_stray_{uuid.uuid4().hex[:8]}"
    _create_table(migrator, "public.t_ordinary", locked=False)
    with connection.cursor() as cursor:
        cursor.execute(f'CREATE ROLE "{stray}"')
        cursor.execute(f'GRANT SELECT ON public.t_ordinary TO "{stray}", PUBLIC')
        cursor.execute(role_sql(migrator, serving))
    _refused(stray, "SELECT * FROM public.t_ordinary")


def test_append_only_checks_the_table_name() -> None:
    with pytest.raises(ValueError):
        append_only("public.t; SELECT 1")


def test_serving_role_can_read_but_not_write_the_migration_history(
    roles: tuple[str, str],
) -> None:
    _, serving = roles
    _as(serving, "SELECT * FROM public.django_migrations")
    _refused(
        serving,
        "INSERT INTO public.django_migrations (app, name, applied) "
        "VALUES ('x', '0001_x', now())",
    )


def test_a_branch_copied_from_another_split_is_handed_over(
    roles: tuple[str, str],
) -> None:
    old_migrator, old_serving = roles
    _create_table(old_migrator, "public.t_ordinary", locked=False)
    tag = uuid.uuid4().hex[:8]
    migrator, serving = f"t_migrator_{tag}", f"t_serving_{tag}"
    with connection.cursor() as cursor:
        cursor.execute(f'CREATE ROLE "{migrator}"')
        cursor.execute(f'CREATE ROLE "{serving}"')
        cursor.execute(role_sql(migrator, serving))
    _as(serving, "INSERT INTO public.t_ordinary (body) VALUES ('a')")
    _as(migrator, "ALTER TABLE public.t_ordinary ADD COLUMN extra int")
    _refused(old_serving, "SELECT * FROM public.t_ordinary")


def test_role_sql_works_as_a_non_superuser_owner(roles: tuple[str, str]) -> None:
    owner = f"t_owner_{uuid.uuid4().hex[:8]}"
    tag = uuid.uuid4().hex[:8]
    migrator, serving = f"t_migrator_{tag}", f"t_serving_{tag}"
    with connection.cursor() as cursor:
        cursor.execute(f'CREATE ROLE "{owner}" NOSUPERUSER CREATEROLE')
        cursor.execute(
            "DO $$ DECLARE r record; BEGIN "
            "FOR r IN SELECT schemaname, tablename FROM pg_tables "
            "WHERE schemaname = 'public' LOOP "
            "EXECUTE format('ALTER TABLE %I.%I OWNER TO " + f'"{owner}"' + "', "
            "r.schemaname, r.tablename); END LOOP; END $$"
        )
        cursor.execute(f'ALTER SCHEMA public OWNER TO "{owner}"')
        cursor.execute(
            f'ALTER DATABASE "{connection.settings_dict["NAME"]}" OWNER TO "{owner}"'
        )
        cursor.execute(f'SET LOCAL ROLE "{owner}"')
        cursor.execute(f'CREATE ROLE "{migrator}"')
        cursor.execute(f'CREATE ROLE "{serving}"')
        cursor.execute("CREATE TABLE public.t_owned (id serial PRIMARY KEY)")
        cursor.execute(role_sql(migrator, serving))
        cursor.execute("RESET ROLE")
        cursor.execute(
            "SELECT pg_get_userbyid(relowner) FROM pg_class "
            "WHERE oid = 'public.t_owned'::regclass"
        )
        assert cursor.fetchone() == (migrator,)
    _as(serving, "INSERT INTO public.t_owned DEFAULT VALUES")
    _refused(serving, "ALTER TABLE public.t_owned ADD COLUMN x int")


def test_role_sql_stops_when_a_table_cannot_be_taken(roles: tuple[str, str]) -> None:
    tag = uuid.uuid4().hex[:8]
    owner, stranger = f"t_owner_{tag}", f"t_stranger_{tag}"
    with connection.cursor() as cursor:
        cursor.execute(f'CREATE ROLE "{owner}" NOSUPERUSER CREATEROLE')
        cursor.execute(f'CREATE ROLE "{stranger}"')
        cursor.execute(f'ALTER TABLE public.django_migrations OWNER TO "{stranger}"')
        cursor.execute(
            f'ALTER DATABASE "{connection.settings_dict["NAME"]}" OWNER TO "{owner}"'
        )
        cursor.execute(f'SET LOCAL ROLE "{owner}"')
        cursor.execute(f'CREATE ROLE "m_{tag}"')
        cursor.execute(f'CREATE ROLE "s_{tag}"')
        with pytest.raises(Exception, match="not owned by"), transaction.atomic():
            cursor.execute(role_sql(f"m_{tag}", f"s_{tag}"))
        cursor.execute("RESET ROLE")
