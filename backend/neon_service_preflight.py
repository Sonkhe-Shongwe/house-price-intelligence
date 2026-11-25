"""Direct restricted-service connection qualification, read-only; no data activation.
Run only in a trusted operator environment with independently pinned development
host and two already provisioned restricted login DSNs. No owner secret or HTTP.
"""
from contextlib import ExitStack
import json
import os
import sys
import psycopg
from backend.neon_preflight import DATABASE, PreflightRefused, _connection_parameters
from backend.historical_reader import ROLE as READER, READ_TABLES, _verify_reader_privileges
from backend.buyer_ownership import ROLE as BUYER, _verify_buyer_privileges
from backend.postgres_runtime import BUYER_TABLES


def service_parameters(environ):
    if environ.get("HPI_NEON_MODE")!="development-restricted-preflight" or any(k.startswith("PG") for k in os.environ):
        raise PreflightRefused("Explicit restricted mode and clean libpq environment required")
    host=environ.get("HPI_NEON_DEVELOPMENT_HOST")
    reader=_connection_parameters(environ.get("HPI_NEON_READER_DSN",""),host,READER)
    buyer=_connection_parameters(environ.get("HPI_NEON_BUYER_DSN",""),host,BUYER)
    if reader["password"]==buyer["password"]:
        raise PreflightRefused("Distinct service credentials required")
    for config in (reader,buyer):
        if len(config["password"])<24:
            raise PreflightRefused("Restricted random credential required")
        config["application_name"]="hpi_service_preflight"
    return reader,buyer


def _identity(conn,role,database):
    value=conn.execute("""SELECT current_database(),current_user,session_user,
        current_setting('server_version_num')::integer,rolcanlogin,rolsuper,
        rolcreaterole,rolcreatedb,rolinherit,rolbypassrls,rolreplication
        FROM pg_roles WHERE rolname=current_user""").fetchone()
    if not value or value[:3]!=(database,role,role) or not 170000<=value[3]<180000 or value[4:]!=(True,False,False,False,False,False,False):
        raise PreflightRefused("Restricted session identity mismatch")


def _deny(conn,statement):
    try:
        with conn.transaction():
            conn.execute(statement)
    except psycopg.errors.InsufficientPrivilege:
        return
    raise PreflightRefused("Forbidden read unexpectedly permitted")


def _inspect_services(reader,buyer,*,database):
    """Shared read-only checks. Caller independently enforces endpoint/TLS."""
    if reader is buyer or not reader.autocommit or not buyer.autocommit:
        raise PreflightRefused("Separate autocommit sessions required")
    with reader.transaction(),buyer.transaction():
        for conn,role in ((reader,READER),(buyer,BUYER)):
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            conn.execute("SET LOCAL statement_timeout='5000ms'")
            conn.execute("SET LOCAL lock_timeout='3000ms'")
            conn.execute("SET LOCAL search_path TO hpi_candidate,pg_catalog")
            _identity(conn,role,database)
        _verify_reader_privileges(reader)
        _verify_buyer_privileges(buyer,login=True)
        # LIMIT 0 proves actual SQL permission without reading any source record.
        for name in READ_TABLES:
            reader.execute("SELECT * FROM hpi_candidate."+name+" LIMIT 0")
        for name in BUYER_TABLES:
            buyer.execute("SELECT * FROM hpi_candidate."+name+" LIMIT 0")
            _deny(reader,"SELECT * FROM hpi_candidate."+name+" LIMIT 0")
        for name in READ_TABLES:
            _deny(buyer,"SELECT * FROM hpi_candidate."+name+" LIMIT 0")
        _deny(buyer,"SELECT * FROM hpi_candidate.workspace_owners LIMIT 0")
        if buyer.execute("SELECT nullif(current_setting('hpi.owner_id',true),'')").fetchone()[0] is not None:
            raise PreflightRefused("Unexpected buyer context")
        for name in BUYER_TABLES:
            if buyer.execute("SELECT EXISTS(SELECT 1 FROM hpi_candidate."+name+")").fetchone()!=(False,):
                raise PreflightRefused("Unbound buyer visibility")
    return {"status":"restricted_services_verified","postgres_major":17,"reader_tables":len(READ_TABLES),
            "buyer_tables":len(BUYER_TABLES),"read_only":True,"real_data_activated":False}


def run_preflight(environ):
    try:
        configs=service_parameters(environ)
        with ExitStack() as stack:
            reader,buyer=[stack.enter_context(psycopg.connect(**config,autocommit=True)) for config in configs]
            report=_inspect_services(reader,buyer,database=DATABASE)
            # libpq accepted mandatory verify-full and required channel binding.
            # Do not print endpoint, user configuration, certificates or passwords.
            return dict(report,direct_tls=True)
    except Exception:
        raise PreflightRefused("Restricted cloud service preflight refused or failed") from None


def main(environ=None):
    try:
        result=run_preflight(os.environ if environ is None else environ)
    except Exception:
        print("Restricted cloud service preflight refused or failed",file=sys.stderr)
        return 1
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
