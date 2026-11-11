"""SQL that splits a database into a migration role (owner) and a serving role.

python -m config.db_roles <migrator> <serving> | psql -v ON_ERROR_STOP=1
"""

import re
import sys

ROLE_NAME = re.compile(r"[a-z][a-z0-9_]{0,62}")
APPEND_ONLY_COMMENT = "append-only"


def _ident(name: str) -> str:
    if not ROLE_NAME.fullmatch(name):
        raise ValueError(f"role name must match {ROLE_NAME.pattern}: {name!r}")
    return f'"{name}"'


# Run as the current owner or a superuser, on every database to split. Safe to
# repeat: tables marked append-only (see config.append_only) keep select and insert.
def role_sql(migrator: str, serving: str) -> str:
    m, s = _ident(migrator), _ident(serving)
    return f"""
GRANT {m} TO CURRENT_USER;

DO $$
DECLARE r record; g record; db text := quote_ident(current_database());
BEGIN
  EXECUTE format('REVOKE CONNECT, TEMPORARY ON DATABASE %s FROM PUBLIC', db);
  EXECUTE format('GRANT CONNECT ON DATABASE %s TO {m}, {s}, CURRENT_USER', db);
  EXECUTE format('GRANT CREATE ON DATABASE %s TO {m}', db);

  -- Ownership moves only for objects the current user owns and no extension owns.
  FOR r IN SELECT n.nspname, pg_get_userbyid(n.nspowner) AS owner
           FROM pg_namespace n
           WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema' LOOP
    IF r.owner = current_user THEN
      EXECUTE format('ALTER SCHEMA %I OWNER TO {m}', r.nspname);
    END IF;
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO {s}', r.nspname);
  END LOOP;
  GRANT USAGE, CREATE ON SCHEMA public TO {m};

  FOR r IN SELECT n.nspname, c.relname, c.relkind FROM pg_class c
           JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE c.relkind IN ('r', 'p', 'v', 'm')
             AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
             AND pg_get_userbyid(c.relowner) = current_user
             AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.deptype = 'e'
                             AND d.classid = 'pg_class'::regclass AND d.objid = c.oid)
  LOOP
    EXECUTE format('ALTER %s %I.%I OWNER TO {m}',
      CASE r.relkind WHEN 'v' THEN 'VIEW' WHEN 'm' THEN 'MATERIALIZED VIEW'
                     ELSE 'TABLE' END, r.nspname, r.relname);
  END LOOP;

  FOR r IN SELECT p.oid FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
           WHERE p.prokind IN ('f', 'p')
             AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
             AND pg_get_userbyid(p.proowner) = current_user
             AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.deptype = 'e'
                             AND d.classid = 'pg_proc'::regclass AND d.objid = p.oid)
  LOOP
    EXECUTE format('ALTER ROUTINE %s OWNER TO {m}', r.oid::regprocedure);
  END LOOP;

  FOR r IN SELECT t.oid, t.typtype FROM pg_type t
           JOIN pg_namespace n ON n.oid = t.typnamespace
           WHERE t.typtype IN ('e', 'd', 'r')
             AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
             AND pg_get_userbyid(t.typowner) = current_user
             AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.deptype = 'e'
                             AND d.classid = 'pg_type'::regclass AND d.objid = t.oid)
  LOOP
    EXECUTE format('ALTER %s %s OWNER TO {m}',
      CASE r.typtype WHEN 'd' THEN 'DOMAIN' ELSE 'TYPE' END, r.oid::regtype);
  END LOOP;

  FOR r IN SELECT c.oid, c.relkind, c.relowner, c.relacl, n.nspname, c.relname,
                  coalesce(obj_description(c.oid, 'pg_class'), '')
                    = '{APPEND_ONLY_COMMENT}' AS locked
           FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE c.relkind IN ('r', 'p', 'v', 'm')
             AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
             AND pg_get_userbyid(c.relowner) = '{migrator}'
  LOOP
    FOR g IN SELECT DISTINCT a.grantee FROM aclexplode(r.relacl) a
             WHERE a.grantee NOT IN (0, r.relowner) LOOP
      EXECUTE format('REVOKE ALL ON %I.%I FROM %s', r.nspname, r.relname,
                     g.grantee::regrole::text);
    END LOOP;
    EXECUTE format('REVOKE ALL ON %I.%I FROM PUBLIC', r.nspname, r.relname);
    IF r.relkind IN ('v', 'm') THEN
      EXECUTE format('GRANT SELECT ON %I.%I TO {s}', r.nspname, r.relname);
    ELSIF r.locked THEN
      EXECUTE format('GRANT SELECT, INSERT ON %I.%I TO {s}', r.nspname, r.relname);
    ELSE
      EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON %I.%I TO {s}',
                     r.nspname, r.relname);
    END IF;
  END LOOP;

  FOR r IN SELECT n.nspname, c.relname FROM pg_class c
           JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE c.relkind = 'S' AND n.nspname !~ '^pg_'
             AND n.nspname <> 'information_schema'
             AND pg_get_userbyid(c.relowner) = '{migrator}' LOOP
    EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %I.%I TO {s}',
                   r.nspname, r.relname);
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
