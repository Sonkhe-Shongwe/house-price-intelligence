"""Direct restricted-service connection qualification, read-only; no data activation.
Run only in a trusted operator environment with independently pinned development
host and two already provisioned restricted login DSNs. No owner secret or HTTP.
"""
import json
import os
import sys
import psycopg
from backend.neon_preflight import (DATABASE, CONFIG_REASONS, ConfigurationRefused,
                                    PreflightRefused, _connection_parameters)
from backend.historical_reader import ROLE as READER, READ_TABLES, _verify_reader_privileges
from backend.buyer_ownership import ROLE as BUYER, _verify_buyer_privileges
from backend.postgres_runtime import BUYER_TABLES


class ServicePreflightRefused(PreflightRefused):
    """Only allowlisted diagnostic codes may leave the CLI."""
    def __init__(self, code, outcomes=None):
        super().__init__("Restricted cloud service preflight refused or failed")
        self.code=code
        self.outcomes=outcomes


DIAGNOSTICS=frozenset(("mode_or_environment","reader_configuration","buyer_configuration",
    "duplicate_credentials","reader_credential_shape","buyer_credential_shape",
    "reader_connection","buyer_connection","service_permission_checks","service_checks_failed","unexpected_failure")) | frozenset(
        f"{kind}_configuration_{reason}" for kind in ("reader", "buyer") for reason in CONFIG_REASONS)


def service_parameters(environ):
    if environ.get("HPI_NEON_MODE")!="development-restricted-preflight" or any(k.startswith("PG") for k in os.environ):
        raise ServicePreflightRefused("mode_or_environment")
    host=environ.get("HPI_NEON_DEVELOPMENT_HOST")
    configs=[]
    for key,role,kind in (("HPI_NEON_READER_DSN",READER,"reader"),("HPI_NEON_BUYER_DSN",BUYER,"buyer")):
        try:
            configs.append(_connection_parameters(environ.get(key,""),host,role))
        except ConfigurationRefused as exc:
            raise ServicePreflightRefused(f"{kind}_configuration_{exc.reason}") from None
        except PreflightRefused:
            raise ServicePreflightRefused(kind+"_configuration") from None
    reader,buyer=configs
    if reader["password"]==buyer["password"]:
        raise ServicePreflightRefused("duplicate_credentials")
    for config,kind in ((reader,"reader"),(buyer,"buyer")):
        password=config["password"]
        # Provider-generated random credentials are accepted for this short-lived
        # qualification. Length alone is not proof of randomness. Reject masked
        # console placeholders and obviously undersized values.
        if len(password)<12 or set(password)=={"*"}:
            raise ServicePreflightRefused(kind+"_credential_shape")
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


def _inspect_service(conn, role, *, database):
    """Verify each connected role independently using read-only transactions."""
    if not conn.autocommit or role not in (READER, BUYER):
        raise PreflightRefused("Restricted autocommit session required")
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        conn.execute("SET LOCAL statement_timeout='5000ms'")
        conn.execute("SET LOCAL lock_timeout='3000ms'")
        conn.execute("SET LOCAL search_path TO hpi_candidate,pg_catalog")
        _identity(conn,role,database)
        if role==READER:
            _verify_reader_privileges(conn)
            for name in READ_TABLES:
                conn.execute("SELECT * FROM hpi_candidate."+name+" LIMIT 0")
            for name in BUYER_TABLES:
                _deny(conn,"SELECT * FROM hpi_candidate."+name+" LIMIT 0")
        else:
            _verify_buyer_privileges(conn,login=True)
            for name in BUYER_TABLES:
                conn.execute("SELECT * FROM hpi_candidate."+name+" LIMIT 0")
            for name in READ_TABLES:
                _deny(conn,"SELECT * FROM hpi_candidate."+name+" LIMIT 0")
            _deny(conn,"SELECT * FROM hpi_candidate.workspace_owners LIMIT 0")
            if conn.execute("SELECT nullif(current_setting('hpi.owner_id',true),'')").fetchone()[0] is not None:
                raise PreflightRefused("Unexpected buyer context")
            for name in BUYER_TABLES:
                if conn.execute("SELECT EXISTS(SELECT 1 FROM hpi_candidate."+name+")").fetchone()!=(False,):
                    raise PreflightRefused("Unbound buyer visibility")


def _verified_report():
    return {"status":"restricted_services_verified","postgres_major":17,"reader_tables":len(READ_TABLES),
            "buyer_tables":len(BUYER_TABLES),"read_only":True,"real_data_activated":False}


def _inspect_services(reader,buyer,*,database):
    """Shared fixture qualification; retain the distinct-session invariant."""
    if reader is buyer:
        raise PreflightRefused("Separate autocommit sessions required")
    _inspect_service(reader,READER,database=database)
    _inspect_service(buyer,BUYER,database=database)
    return _verified_report()


OUTCOMES=frozenset(("verified","authentication","channel_binding","certificate",
                    "tls","dns","timeout","network","database","server_rejected",
                    "client_configuration","permission_checks","unknown_connection"))


def _connection_outcome(exc):
    """Map known driver errors to fixed categories; never return exception text.

    libpq can omit SQLSTATE on connection failures. Only recognise known
    phrases then; unfamiliar or ambiguous failures stay unknown.
    """
    if not isinstance(exc, psycopg.Error):
        return "unknown_connection"
    state=getattr(exc,"sqlstate",None)
    message=str(exc).lower()
    if state=="28P01" or "password authentication failed" in message or "no password supplied" in message:
        return "authentication"
    if "channel binding" in message or "scram-sha-256-plus" in message:
        return "channel_binding"
    if any(x in message for x in ("certificate verify failed","certificate verification failed",
            "server certificate","root certificate","certificate has expired","sslrootcert")):
        return "certificate"
    if any(x in message for x in ("could not translate host name","name or service not known",
            "temporary failure in name resolution","nodename nor servname")):
        return "dns"
    if isinstance(exc,psycopg.errors.ConnectionTimeout) or any(x in message for x in
            ("timeout expired","connection timed out","connect timeout")):
        return "timeout"
    if state=="3D000" or ("database " in message and "does not exist" in message):
        return "database"
    if state in ("28000","53300","57P03") or any(x in message for x in
            ("no pg_hba.conf entry","is not permitted to log in","endpoint is disabled",
             "too many connections","connection is insecure")):
        return "server_rejected"
    if any(x in message for x in ("invalid connection option","invalid connection string",
            "invalid sslmode","invalid channel_binding")):
        return "client_configuration"
    if any(x in message for x in ("ssl error","ssl handshake","tls handshake",
            "server does not support ssl","ssl connection has been closed")):
        return "tls"
    if any(x in message for x in ("connection refused","network is unreachable",
            "no route to host","connection reset","server closed the connection unexpectedly")):
        return "network"
    return "unknown_connection"


def _qualify_role(config,role):
    try:
        with psycopg.connect(**config,autocommit=True) as conn:
            try:
                _inspect_service(conn,role,database=DATABASE)
            except Exception:
                return "permission_checks"
    except Exception as exc:
        return _connection_outcome(exc)
    return "verified"


def run_preflight(environ):
    try:
        reader,buyer=service_parameters(environ)
        # Both configurations must be safe first. Attempt each role once,
        # even if the other fails; successful connections are always closed.
        outcomes={"reader":_qualify_role(reader,READER),
                  "buyer":_qualify_role(buyer,BUYER)}
        if any(value!="verified" for value in outcomes.values()):
            raise ServicePreflightRefused("service_checks_failed",outcomes)
        return dict(_verified_report(),direct_tls=True)
    except ServicePreflightRefused:
        raise
    except Exception:
        raise ServicePreflightRefused("unexpected_failure") from None


def main(environ=None):
    try:
        result=run_preflight(os.environ if environ is None else environ)
    except ServicePreflightRefused as exc:
        code=exc.code if exc.code in DIAGNOSTICS else "unexpected_failure"
        print("Restricted cloud service preflight refused or failed: "+code,file=sys.stderr)
        if code=="service_checks_failed" and isinstance(exc.outcomes,dict):
            safe={kind: exc.outcomes.get(kind) if exc.outcomes.get(kind) in OUTCOMES
                  else "unknown_connection" for kind in ("reader","buyer")}
            print(json.dumps(safe,sort_keys=True),file=sys.stderr)
        return 1
    except Exception:
        print("Restricted cloud service preflight refused or failed: unexpected_failure",file=sys.stderr)
        return 1
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
