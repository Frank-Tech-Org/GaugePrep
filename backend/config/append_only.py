import re

from django.db import migrations

from config.db_roles import GUARD

TABLE_NAME = re.compile(r"[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)?")

_CREATE_GUARD = f"""
CREATE OR REPLACE FUNCTION {GUARD}() RETURNS trigger LANGUAGE plpgsql AS $f$
BEGIN
  RAISE EXCEPTION 'table % is append-only', TG_TABLE_NAME
    USING ERRCODE = 'insufficient_privilege';
END $f$;
"""

# WHY: revokes by grantee, not role name, so one migration runs on every environment.
_REVOKE = """
DO $$
DECLARE g oid;
BEGIN
  FOR g IN SELECT DISTINCT a.grantee
           FROM pg_class c, aclexplode(c.relacl) a
           WHERE c.oid = '{table}'::regclass
             AND a.grantee <> c.relowner AND a.grantee <> 0
  LOOP
    EXECUTE format('REVOKE UPDATE, DELETE, TRUNCATE ON {table} FROM %s',
                   g::regrole::text);
  END LOOP;
END $$;
"""

# WHY: only a role that can insert (the serving role) gets update and delete back.
_RESTORE = """
DO $$
DECLARE g oid;
BEGIN
  FOR g IN SELECT DISTINCT a.grantee
           FROM pg_class c, aclexplode(c.relacl) a
           WHERE c.oid = '{table}'::regclass
             AND a.grantee <> c.relowner AND a.grantee <> 0
             AND a.privilege_type = 'INSERT'
  LOOP
    EXECUTE format('GRANT UPDATE, DELETE ON {table} TO %s', g::regrole::text);
  END LOOP;
END $$;
"""


def append_only(table: str) -> migrations.RunSQL:
    """Leave the serving role insert and select on `table`; triggers refuse the rest.

    The triggers also stop the migration role, so Django's flush (tests with
    transaction=True) fails on this table, and a backfill that updates rows must drop
    the triggers first and recreate them (reverse this operation, then apply it).
    """
    if not TABLE_NAME.fullmatch(table):
        raise ValueError(f"table must look like schema.table: {table!r}")
    base = f"gp_append_only_{table.replace('.', '_')}"[:55]
    return migrations.RunSQL(
        [
            _CREATE_GUARD,
            f"CREATE OR REPLACE TRIGGER {base}_row BEFORE UPDATE OR DELETE "
            f"ON {table} FOR EACH ROW EXECUTE FUNCTION {GUARD}()",
            f"CREATE OR REPLACE TRIGGER {base}_stmt BEFORE TRUNCATE "
            f"ON {table} FOR EACH STATEMENT EXECUTE FUNCTION {GUARD}()",
            _REVOKE.format(table=table),
        ],
        reverse_sql=[
            f"DROP TRIGGER IF EXISTS {base}_row ON {table}",
            f"DROP TRIGGER IF EXISTS {base}_stmt ON {table}",
            _RESTORE.format(table=table),
        ],
    )
