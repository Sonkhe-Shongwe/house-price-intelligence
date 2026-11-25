"""Explicit Neon development preflight, not an importer or runtime.
No connection at import time. Never accept credentials from browser requests.
Run only with reviewed secrets from a trusted operator environment.
"""
import os
import re
import psycopg
from psycopg.conninfo import conninfo_to_dict

DATABASE = "hpi_private"
OWNER = "hpi_private_owner"
# Only direct Frankfurt AWS Neon endpoint names. The precise development
# endpoint must also be independently pinned by the operator.
HOST = re.compile(r"ep-[a-z0-9]+(?:-[a-z0-9]+)*\.c-[0-9]+\.eu-central-1\.aws\.neon\.tech")
ALLOWED = {"host", "port", "dbname", "user", "password", "sslmode", "channel_binding", "sslrootcert"}

class PreflightRefused(ValueError):
    pass

def connection_parameters(dsn, expected_host):
    """Normalise console DSN into an explicit, stricter libpq configuration."""
    try:
        p = conninfo_to_dict(dsn)
    except Exception:
        raise PreflightRefused("Invalid cloud connection configuration") from None
    host = p.get("host", "")
    if (set(p) - ALLOWED or not isinstance(expected_host, str)
            or not HOST.fullmatch(host) or "-pooler" in host
            or host != expected_host or p.get("dbname") != DATABASE
            or p.get("user") != OWNER or not p.get("password")
            or p.get("port", "5432") != "5432"
            or p.get("sslmode") not in ("require", "verify-full")
            or p.get("channel_binding") != "require"
            or p.get("sslrootcert", "system") != "system"):
        raise PreflightRefused("Unapproved development connection configuration")
    return dict(host=host, port=5432, dbname=DATABASE, user=OWNER,
                password=p["password"], sslmode="verify-full", sslrootcert="system",
                channel_binding="require", gssencmode="disable", connect_timeout=15,
                application_name="hpi_cloud_preflight")

def inspect_connection(conn):
    """Check database identity, privileges and emptiness in a read-only transaction."""
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        conn.execute("SET LOCAL statement_timeout='5000ms'")
        identity = conn.execute("""SELECT current_database(), current_user, session_user,
            current_setting('server_version_num')::integer, rolsuper, rolcreaterole,
            rolcreatedb, rolbypassrls FROM pg_roles WHERE rolname=current_user""").fetchone()
        if (not identity or identity[:3] != (DATABASE, OWNER, OWNER)
                or not 170000 <= identity[3] < 180000
                or identity[4:] != (False, True, True, True)):
            raise PreflightRefused("Unexpected cloud database identity or owner privileges")
        count = conn.execute("""SELECT count(*) FROM pg_class c
            JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE c.relkind IN ('r','p','v','m','f','S')
            AND n.nspname NOT IN ('pg_catalog','information_schema')
            AND n.nspname NOT LIKE 'pg_%'""").fetchone()[0]
        if count != 0:
            raise PreflightRefused("Cloud database is not an empty application target")
        roles = conn.execute("""SELECT rolname FROM pg_roles
            WHERE left(rolname,4)='hpi_' ORDER BY rolname""").fetchall()
        if roles != [(OWNER,)]:
            raise PreflightRefused("Unexpected application roles")
        return {"status": "empty_development_preflight", "postgres_major": 17,
                "application_relations": 0, "application_roles": 1,
                "read_only": True, "real_data_activated": False}

def run_preflight(environ):
    if (environ.get("HPI_NEON_MODE") != "development-empty-preflight"
            or any(key.startswith("PG") for key in os.environ)):
        raise PreflightRefused("Explicit cloud mode and clean libpq environment required")
    p = connection_parameters(environ.get("HPI_NEON_OWNER_DSN", ""),
                              environ.get("HPI_NEON_DEVELOPMENT_HOST"))
    try:
        with psycopg.connect(**p, autocommit=True) as conn:
            return inspect_connection(conn)
    except PreflightRefused:
        raise
    except Exception:
        # Connection diagnostics can contain secret-bearing connection details.
        raise PreflightRefused("Cloud connection or read-only inspection failed") from None
