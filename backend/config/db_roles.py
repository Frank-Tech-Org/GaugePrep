# Emits the SQL that splits a database into a migration role and a serving role.

import re
import sys

ROLE_NAME = re.compile(r"[a-z][a-z0-9_]{0,62}")
GUARD = "public.gp_append_only_refuse"


def _ident(name: str) -> str:
    if not ROLE_NAME.fullmatch(name):
        raise ValueError(f"role name must match {ROLE_NAME.pattern}: {name!r}")
    return f'"{name}"'


# WHY: safe to repeat; tables with the append-only trigger keep select and insert only.
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
  FOR g IN SELECT DISTINCT a.grantee FROM pg_database d, aclexplode(d.datacl) a
           WHERE d.datname = current_database() AND a.privilege_type = 'CONNECT'
             AND a.grantee NOT IN (0, d.datdba)
             AND pg_get_userbyid(a.grantee)
                 NOT IN (current_user, '{migrator}', '{serving}')
  LOOP
    EXECUTE format('REVOKE CONNECT ON DATABASE %s FROM %s', db,
                   g.grantee::regrole::text);
  END LOOP;

  -- WHY: a copied branch may hold another migration role's objects.
  FOR r IN SELECT n.nspname, n.nspowner AS owner FROM pg_namespace n
           WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
             AND pg_get_userbyid(n.nspowner) <> '{migrator}' LOOP
    IF pg_has_role(current_user, r.owner, 'USAGE') THEN
      EXECUTE format('ALTER SCHEMA %I OWNER TO {m}', r.nspname);
    ELSE
      RAISE NOTICE 'skipped schema %: its owner is out of reach', r.nspname;
    END IF;
  END LOOP;
  FOR r IN SELECT nspname FROM pg_namespace
           WHERE nspname !~ '^pg_' AND nspname <> 'information_schema' LOOP
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO {s}', r.nspname);
  END LOOP;
  GRANT USAGE, CREATE ON SCHEMA public TO {m};

  FOR r IN SELECT n.nspname, c.relname, c.relkind, c.relowner AS owner FROM pg_class c
           JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE c.relkind IN ('r', 'p', 'v', 'm')
             AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
             AND pg_get_userbyid(c.relowner) <> '{migrator}'
             AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.deptype = 'e'
                             AND d.classid = 'pg_class'::regclass AND d.objid = c.oid)
  LOOP
    IF pg_has_role(current_user, r.owner, 'USAGE') THEN
      EXECUTE format('ALTER %s %I.%I OWNER TO {m}',
        CASE r.relkind WHEN 'v' THEN 'VIEW' WHEN 'm' THEN 'MATERIALIZED VIEW'
                       ELSE 'TABLE' END, r.nspname, r.relname);
    ELSE
      RAISE NOTICE 'skipped %.%: its owner is out of reach', r.nspname, r.relname;
    END IF;
  END LOOP;

  FOR r IN SELECT p.oid, p.proowner AS owner FROM pg_proc p
           JOIN pg_namespace n ON n.oid = p.pronamespace
           WHERE p.prokind IN ('f', 'p')
             AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
             AND pg_get_userbyid(p.proowner) <> '{migrator}'
             AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.deptype = 'e'
                             AND d.classid = 'pg_proc'::regclass AND d.objid = p.oid)
  LOOP
    IF pg_has_role(current_user, r.owner, 'USAGE') THEN
      EXECUTE format('ALTER ROUTINE %s OWNER TO {m}', r.oid::regprocedure);
    ELSE
      RAISE NOTICE 'skipped routine %: owner not reachable', r.oid::regprocedure;
    END IF;
  END LOOP;

  FOR r IN SELECT t.oid, t.typtype, t.typowner AS owner FROM pg_type t
           JOIN pg_namespace n ON n.oid = t.typnamespace
           WHERE t.typtype IN ('e', 'd', 'r')
             AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
             AND pg_get_userbyid(t.typowner) <> '{migrator}'
             AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.deptype = 'e'
                             AND d.classid = 'pg_type'::regclass AND d.objid = t.oid)
  LOOP
    IF pg_has_role(current_user, r.owner, 'USAGE') THEN
      EXECUTE format('ALTER %s %s OWNER TO {m}',
        CASE r.typtype WHEN 'd' THEN 'DOMAIN' ELSE 'TYPE' END, r.oid::regtype);
    ELSE
      RAISE NOTICE 'skipped type %: owner not reachable', r.oid::regtype;
    END IF;
  END LOOP;

  IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
             WHERE c.relkind IN ('r', 'p', 'S')
               AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
               AND pg_get_userbyid(c.relowner) <> '{migrator}'
               AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.deptype = 'e'
                               AND d.classid = 'pg_class'::regclass
                               AND d.objid = c.oid))
  THEN
    RAISE EXCEPTION 'tables or sequences not owned by {migrator}; see the notices';
  END IF;

  FOR r IN SELECT c.relkind, c.relowner, c.relacl, n.nspname, c.relname,
                  EXISTS (SELECT 1 FROM pg_trigger t WHERE t.tgrelid = c.oid
                          AND t.tgfoid = to_regproc('{GUARD}')::oid) AS locked
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
    IF r.relkind IN ('v', 'm') OR r.relname = 'django_migrations' THEN
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

-- WHY: without IN SCHEMA these also cover schemas created later, one per module.
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
