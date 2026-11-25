"""Loopback-only PostgreSQL runtime candidate; never deploy.
HTTP Basic is a disposable fictional authentication harness, not production auth.
No real account registration, real data, public bind or migration of user DBs.
"""
from base64 import b64decode
from binascii import Error as Base64Error
from hmac import compare_digest
import os
import argparse
from dataclasses import dataclass
import re
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg_pool import ConnectionPool, PoolTimeout
from backend.postgres_fixture import migrate, seed, PostgresFixtureStore, ROOT
from backend.synthetic_http import create_app, ALLOWED_HOST, _response
from backend.synthetic_investigation_store import EvidenceStoreError
from backend.react_assets import load_react_assets
from backend.postgres_consolidation import prepare, ConsolidatedStore, SOURCE_LOCK, TABLES as SOURCE_TABLES

ROLE="hpi_runtime_fixture"
OWNERS={"alice":"fictional-alice","bob":"fictional-bob"}
BUYER_TABLES=("investigations","shortlists","shortlist_investigations","investigation_results","comparable_evidence")
READ_TABLES=(*SOURCE_TABLES,*BUYER_TABLES,"schema_migrations","active_fixture_build","fixture_build_events")
KNOWN_TABLES=set(READ_TABLES)|{"workspace_owners"}
SEQUENCE="shortlist_investigations_member_order_seq"
POLICIES={
    "investigations":"own_investigations","shortlists":"own_shortlists",
    "shortlist_investigations":"own_members","investigation_results":"own_results",
    "comparable_evidence":"own_evidence",
}
OWNER_QUAL="(owner_id = NULLIF(current_setting('hpi.owner_id'::text, true), ''::text))"
def expected_qual(table):
    if table in ("investigations","shortlists","shortlist_investigations"):
        return OWNER_QUAL
    return "(EXISTS ( SELECT 1 FROM investigations i WHERE (i.investigation_id = "+table+".investigation_id)))"

def compact_sql(value):
    # PostgreSQL 17 deparse of the reviewed exact expressions. Formatting
    # whitespace only, not operators, parentheses or literal values.
    return re.sub(r"\s+","",value or "")

@dataclass(frozen=True,repr=False)
class RuntimeSettings:
    dsn: str
    passwords: dict
    pool_size: int
    port: int

def load_runtime_settings(environ,port):
    """Explicit safe fixture settings; no production-mode fallback or secret repr."""
    if environ.get("HPI_RUNTIME_MODE","fixture-only")!="fixture-only":
        raise ValueError("Unapproved runtime mode")
    if environ.get("HPI_RUNTIME_BIND","127.0.0.1")!="127.0.0.1":
        raise ValueError("Unapproved runtime bind")
    if type(port) is not int or not 1024<=port<=65535:
        raise ValueError("Invalid runtime port")
    dsn=environ["HPI_RUNTIME_DSN"]
    _dsn_check(dsn,ROLE)
    p=conninfo_to_dict(dsn)
    if not p.get("password") or not p.get("port") or not 1<=int(p["port"])<=65535:
        raise ValueError("Explicit fixture database credentials and port required")
    passwords={name:environ["HPI_FIXTURE_"+name.upper()+"_PASSWORD"] for name in OWNERS}
    if any(not isinstance(p,str) or len(p)<24 or not p.isascii() for p in passwords.values()) or len(set(passwords.values()))!=2:
        raise ValueError("Distinct fictional passwords required")
    size=environ.get("HPI_RUNTIME_POOL_SIZE","4")
    if not isinstance(size,str) or not re.fullmatch(r"[1-8]",size):
        raise ValueError("Invalid pool capacity")
    return RuntimeSettings(dsn,passwords,int(size),port)


def _dsn_check(dsn,user):
    p=conninfo_to_dict(dsn)
    if p.get("host")!="127.0.0.1" or p.get("dbname")!="hpi_fixture" or p.get("user")!=user or p.get("hostaddr", "127.0.0.1")!="127.0.0.1":
        raise ValueError("Only disposable loopback hpi_fixture allowed")
    if set(p)-{"host","port","dbname","user","password","hostaddr","connect_timeout"}:
        raise ValueError("Unsupported fixture connection options")

def bootstrap(admin_dsn, password):
    """Explicit fresh disposable database only. Never invoked on app start."""
    _dsn_check(admin_dsn,"postgres")
    if not isinstance(password,str) or len(password)<24:raise ValueError("Require random CI-only database password")
    with psycopg.connect(admin_dsn,autocommit=True) as conn:
        with conn.transaction():
            conn.execute("SELECT pg_advisory_xact_lock(194322)")
            if conn.execute("SELECT to_regnamespace('hpi_candidate')").fetchone()[0] is not None:
                raise ValueError("Refusing existing candidate schema")
            if conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s",(ROLE,)).fetchone():
                raise ValueError("Refusing existing candidate role")
            migrate(conn)
            seed(conn)
            conn.execute("SET LOCAL search_path TO hpi_candidate, pg_catalog")
            prepare(conn)
            conn.execute((ROOT.parent/"postgres_ownership_candidate.sql").read_text(),prepare=False)
            conn.execute("INSERT INTO workspace_owners VALUES (%s),(%s)",tuple(OWNERS.values()))
            conn.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS PASSWORD {}").format(sql.Identifier(ROLE),sql.Literal(password)))
            conn.execute(sql.SQL("GRANT USAGE ON SCHEMA hpi_candidate TO {}").format(sql.Identifier(ROLE)))
            conn.execute("REVOKE CREATE ON SCHEMA hpi_candidate FROM PUBLIC")
            conn.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
            conn.execute("REVOKE TEMPORARY ON DATABASE hpi_fixture FROM PUBLIC")
            conn.execute(sql.SQL("GRANT SELECT ON {} TO {}").format(
                sql.SQL(",").join(sql.Identifier("hpi_candidate",t) for t in READ_TABLES),sql.Identifier(ROLE)))
            conn.execute(sql.SQL("GRANT INSERT ON investigations, investigation_results, comparable_evidence, shortlists, shortlist_investigations TO {}").format(sql.Identifier(ROLE)))
            conn.execute(sql.SQL("GRANT UPDATE(note_text), DELETE ON shortlist_investigations TO {}").format(sql.Identifier(ROLE)))
            conn.execute(sql.SQL("GRANT USAGE ON SEQUENCE {} TO {}").format(sql.Identifier("hpi_candidate",SEQUENCE),sql.Identifier(ROLE)))

def verify_role(conn):
    row=conn.execute("""SELECT current_user,session_user,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolinherit
        FROM pg_roles WHERE rolname=current_user""").fetchone()
    if row!=(ROLE,ROLE,False,False,False,False,False):
        raise EvidenceStoreError("Invalid fixture runtime role")
    if conn.execute("SELECT EXISTS(SELECT 1 FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user))").fetchone()[0]:
        raise EvidenceStoreError("Runtime role membership drift")
    if conn.execute("""SELECT has_schema_privilege(current_user,'hpi_candidate','CREATE'),
        has_schema_privilege(current_user,'public','CREATE'),
        has_database_privilege(current_user,current_database(),'CREATE,TEMP'),
        current_setting('search_path')""").fetchone()!=(False,False,False,"hpi_candidate, pg_catalog"):
        raise EvidenceStoreError("Runtime namespace privilege drift")
    rows=conn.execute("""SELECT c.relname,c.relrowsecurity,pg_get_userbyid(c.relowner),
        has_table_privilege(current_user,c.oid,'SELECT'),
        has_table_privilege(current_user,c.oid,'INSERT'),
        has_table_privilege(current_user,c.oid,'DELETE'),
        has_table_privilege(current_user,c.oid,'UPDATE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN'),
        has_any_column_privilege(current_user,c.oid,'SELECT'),
        has_any_column_privilege(current_user,c.oid,'INSERT'),
        has_any_column_privilege(current_user,c.oid,'REFERENCES'),
        ARRAY(SELECT a.attname::text FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attnum>0
              AND NOT a.attisdropped AND has_column_privilege(current_user,c.oid,a.attnum,'UPDATE') ORDER BY a.attname)
         FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
         WHERE n.nspname='hpi_candidate' AND c.relkind IN ('r','p','v','m','f')""").fetchall()
    if {r[0] for r in rows}!=KNOWN_TABLES:
        raise EvidenceStoreError("Runtime relation inventory drift")
    for name,rls,owner,read,insert,delete,other,colread,colinsert,colref,updates in rows:
        if (owner==ROLE or rls!=(name in BUYER_TABLES) or read!=(name in READ_TABLES)
            or colread!=read or insert!=(name in BUYER_TABLES) or colinsert!=insert
            or delete!=(name=="shortlist_investigations") or other or colref
            or updates!=(["note_text"] if name=="shortlist_investigations" else [])):
            raise EvidenceStoreError("Runtime table privilege drift")
    sequences=conn.execute("""SELECT c.relname,pg_get_userbyid(c.relowner),
        has_sequence_privilege(current_user,c.oid,'USAGE'),has_sequence_privilege(current_user,c.oid,'SELECT,UPDATE')
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='hpi_candidate' AND c.relkind='S'""").fetchall()
    if len(sequences)!=1 or sequences[0][0]!=SEQUENCE or sequences[0][1]==ROLE or sequences[0][2:]!=(True,False):
        raise EvidenceStoreError("Runtime sequence privilege drift")
    policies=conn.execute("""SELECT tablename,policyname,permissive,roles::text,cmd,qual,with_check
        FROM pg_policies WHERE schemaname='hpi_candidate'""").fetchall()
    if len(policies)!=len(POLICIES) or {p[0] for p in policies}!=set(POLICIES):
        raise EvidenceStoreError("Runtime ownership policy drift")
    for table,name,permissive,roles,cmd,qual,check in policies:
        if (name!=POLICIES[table] or permissive!="PERMISSIVE" or roles!="{public}" or cmd!="ALL"
            or check is not None or compact_sql(qual)!=compact_sql(expected_qual(table))):
            raise EvidenceStoreError("Runtime ownership policy drift")
    if conn.execute("SELECT nullif(current_setting('hpi.owner_id',true),'')").fetchone()[0] is not None:
        raise EvidenceStoreError("Unexpected pooled owner context")

def make_pool(dsn, *, max_size=4):
    _dsn_check(dsn,ROLE)
    if not 1<=max_size<=8:raise ValueError("Invalid pool capacity")
    def configure(conn):
        conn.execute("SET search_path TO hpi_candidate, pg_catalog")
        verify_role(conn)
        ConsolidatedStore(conn)
    def reset(conn):
        # Identity always transaction-local; additionally refuse any session residue.
        verify_role(conn)
    pool=ConnectionPool(dsn,kwargs={"autocommit":True,"connect_timeout":3},
                        min_size=1,max_size=max_size,timeout=4,open=False,configure=configure,reset=reset)
    try:pool.open(wait=True,timeout=10)
    except Exception:
        pool.close()
        raise
    return pool

def credentials(header, passwords):
    if not isinstance(header,str) or len(header)>512 or not header.startswith("Basic "):return None
    try:
        value=b64decode(header[6:],validate=True).decode("ascii")
        name,secret=value.split(":",1)
    except (ValueError,UnicodeError,Base64Error):return None
    if name not in OWNERS or not compare_digest(secret,passwords[name]):return None
    return OWNERS[name]

class _Abort(Exception):pass

def application(pool,passwords,assets):
    if set(passwords)!=set(OWNERS) or any(not isinstance(p,str) or len(p)<24 or not p.isascii() for p in passwords.values()) or len(set(passwords.values()))!=2:
        raise ValueError("Two distinct random fictional passwords required")
    passwords=dict(passwords)
    def app(environ,start_response):
        host=environ.get("HTTP_HOST","")
        origin=environ.get("HTTP_ORIGIN")
        if (environ.get("REMOTE_ADDR") not in ("127.0.0.1","::1") or not ALLOWED_HOST.fullmatch(host)
            or (origin is not None and origin.lower()!="http://"+host.lower())
            or environ.get("HTTP_SEC_FETCH_SITE") in ("cross-site","same-site")
            or any(environ.get(k) for k in ("HTTP_X_FORWARDED_FOR","HTTP_X_FORWARDED_HOST","HTTP_X_FORWARDED_PROTO","HTTP_X_REAL_IP","HTTP_FORWARDED"))):
            return _response(start_response,403,{"error":"local_fixture_only"})
        # Basic credentials are sent automatically by browsers. Require exact
        # Origin for mutations, including DELETE, to prevent CSRF.
        if environ.get("REQUEST_METHOD") in ("POST","PATCH","DELETE") and origin is None:
            return _response(start_response,403,{"error":"same_origin_required"})
        owner=credentials(environ.get("HTTP_AUTHORIZATION"),passwords)
        if owner is None:
            body=b'{"error":"fictional_authentication_required"}'
            start_response("401 Unauthorized",[("Content-Type","application/json"),("Cache-Control","no-store"),
                ("X-Content-Type-Options","nosniff"),("Content-Length",str(len(body))),
                ("WWW-Authenticate",'Basic realm="Fictional HPI", charset="UTF-8"')])
            return [body]
        return serve_owner(pool,assets,environ,start_response,owner)
    return app

def serve_owner(pool,assets,environ,start_response,owner):
    """Internal trusted identity boundary; never read owner from request."""
    if owner not in OWNERS.values():return _response(start_response,403,{"error":"identity_denied"})
    # Authenticated process liveness is deliberately independent of the
    # database pool. /health retains full DB/source/role readiness semantics.
    if environ.get("PATH_INFO")=="/health/live":
        if environ.get("QUERY_STRING"):
            return _response(start_response,400,{"error":"query_parameters_not_supported"})
        if environ.get("REQUEST_METHOD")!="GET":
            return _response(start_response,405,{"error":"method_not_allowed"},allow="GET")
        return _response(start_response,200,{"status":"alive","mode":"synthetic_fixture_only"})
    captured=[]
    def capture(status,headers,exc_info=None):
        captured[:]=[status,headers]
    try:
        with pool.connection() as conn:
            try:
                with conn.transaction():
                    verify_role(conn)
                    conn.execute("SET LOCAL statement_timeout='4000ms'")
                    conn.execute("SET LOCAL lock_timeout='3000ms'")
                    conn.execute("SELECT set_config('hpi.owner_id',%s,true)",(owner,))
                    # Coarse owner-level serialisation keeps all read/check/write
                    # operations atomic. Different owners can proceed concurrently.
                    conn.execute("SELECT pg_advisory_xact_lock(%s)",(194330 if owner==OWNERS["alice"] else 194331,))
                    conn.execute("SELECT pg_advisory_xact_lock_shared(%s)",(SOURCE_LOCK,))
                    store=ConsolidatedStore(conn)
                    payload=list(create_app(store,react_assets=assets,synthetic_map=True)(environ,capture))
                    if int(captured[0][:3])>=400:raise _Abort()
            except _Abort:pass
        if int(captured[0][:3])==500:
            return _response(start_response,503,{"error":"evidence_unavailable"})
        start_response(*captured)
        return payload
    except (psycopg.Error,PoolTimeout,EvidenceStoreError,ValueError,RuntimeError):
        return _response(start_response,503,{"error":"evidence_unavailable"})


class ThreadedServer(ThreadingMixIn,WSGIServer):
    daemon_threads=True
class QuietHandler(WSGIRequestHandler):
    def log_message(self,*args):pass

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only",action="store_true")
    p.add_argument("--port",type=int,default=8766)
    args=p.parse_args()
    if not args.fixture_only or not 1024<=args.port<=65535:p.error("Explicit fixture-only and valid port required")
    pool=None
    try:
        settings=load_runtime_settings(os.environ,args.port)
        assets=load_react_assets()
        pool=make_pool(settings.dsn,max_size=settings.pool_size)
        app=application(pool,settings.passwords,assets)
        with make_server("127.0.0.1",settings.port,app,server_class=ThreadedServer,handler_class=QuietHandler) as server:
            print("Fictional PostgreSQL runtime ready",flush=True)
            server.serve_forever()
    except (ValueError,KeyError,psycopg.Error,PoolTimeout,EvidenceStoreError,OSError,RuntimeError):
        p.error("Fictional runtime startup refused")
    finally:
        if pool is not None:pool.close()
if __name__=="__main__":main()
