from django.db import migrations

# Takes UPDATE, DELETE and TRUNCATE away from every non-owner role, whatever its name,
# so the same migration runs on dev, staging and production.
_REVOKE = """
DO $$
DECLARE g oid;
BEGIN
  FOR g IN SELECT DISTINCT a.grantee
           FROM pg_class c, aclexplode(c.relacl) a
           WHERE c.oid = '{table}'::regclass
             AND a.grantee <> c.relowner AND a.grantee <> 0
  LOOP
    EXECUTE format('REVOKE UPDATE, DELETE, TRUNCATE ON {table} FROM %I',
                   g::regrole::text);
  END LOOP;
END $$;
"""

_RESTORE = """
DO $$
DECLARE g oid;
BEGIN
  FOR g IN SELECT DISTINCT a.grantee
           FROM pg_class c, aclexplode(c.relacl) a
           WHERE c.oid = '{table}'::regclass
             AND a.grantee <> c.relowner AND a.grantee <> 0
  LOOP
    EXECUTE format('GRANT UPDATE, DELETE ON {table} TO %I', g::regrole::text);
  END LOOP;
END $$;
"""


def append_only(table: str) -> migrations.RunSQL:
    """Serving role keeps insert and select on `table`, loses update and delete."""
    return migrations.RunSQL(
        _REVOKE.format(table=table), reverse_sql=_RESTORE.format(table=table)
    )
