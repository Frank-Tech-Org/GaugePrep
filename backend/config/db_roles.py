"""SQL that splits a database into a migration role (owner) and a serving role.

python -m config.db_roles <migrator> <serving> | psql "$OWNER_URL" -v ON_ERROR_STOP=1
"""

import re
import sys

ROLE_NAME = re.compile(r"[a-z][a-z0-9_]{0,62}")


def _ident(name: str) -> str:
    if not ROLE_NAME.fullmatch(name):
        raise ValueError(f"role name must match {ROLE_NAME.pattern}: {name!r}")
    return f'"{name}"'


# Run as the current owner or a superuser, on every database that should be split.
def role_sql(migrator: str, serving: str) -> str:
    m, s = _ident(migrator), _ident(serving)
    return f"""
-- Needed so the owner can hand objects to the migration role.
GRANT {m} TO CURRENT_USER;

DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT nspname FROM pg_namespace
           WHERE nspname !~ '^pg_' AND nspname <> 'information_schema' LOOP
    EXECUTE format('ALTER SCHEMA %I OWNER TO {m}', r.nspname);
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO {s}', r.nspname);
  END LOOP;
  FOR r IN SELECT schemaname, tablename FROM pg_tables
           WHERE schemaname !~ '^pg_' AND schemaname <> 'information_schema' LOOP
    EXECUTE format('ALTER TABLE %I.%I OWNER TO {m}', r.schemaname, r.tablename);
    EXECUTE format('REVOKE ALL ON %I.%I FROM {s}', r.schemaname, r.tablename);
    EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON %I.%I TO {s}',
                   r.schemaname, r.tablename);
  END LOOP;
  FOR r IN SELECT schemaname, sequencename FROM pg_sequences
           WHERE schemaname !~ '^pg_' AND schemaname <> 'information_schema' LOOP
    EXECUTE format('ALTER SEQUENCE %I.%I OWNER TO {m}', r.schemaname, r.sequencename);
    EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %I.%I TO {s}',
                   r.schemaname, r.sequencename);
  END LOOP;
END $$;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM {s};

-- Without IN SCHEMA these cover schemas created later, one per module.
ALTER DEFAULT PRIVILEGES FOR ROLE {m} GRANT USAGE ON SCHEMAS TO {s};
ALTER DEFAULT PRIVILEGES FOR ROLE {m}
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {s};
ALTER DEFAULT PRIVILEGES FOR ROLE {m} GRANT USAGE, SELECT ON SEQUENCES TO {s};
"""


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        sys.exit("usage: python -m config.db_roles <migrator> <serving>")
    print(role_sql(argv[0], argv[1]))


if __name__ == "__main__":
    main(sys.argv[1:])
