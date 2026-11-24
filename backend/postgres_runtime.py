"""Loopback-only PostgreSQL runtime candidate; never deploy.
HTTP Basic is a disposable fictional authentication harness, not production auth.
No real account registration, real data, public bind or migration of user DBs.
"""
from base64 import b64decode
from binascii import Error as Base64Error
from hmac import compare_digest
import os
import argparse
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

ROLE="hpi_runtime_fixture"
OWNERS={"alice":"fictional-alice","bob":"fictional-bob"}
BUYER_TABLES=("investigations","shortlists","shortlist_investigations","investigation_results","comparable_evidence")

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
            conn.execute((ROOT.parent/"postgres_ownership_candidate.sql").read_text(),prepare=False)
            conn.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS PASSWORD {}").format(sql.Identifier(ROLE),sql.Literal(password)))
            conn.execute(sql.SQL("GRANT USAGE ON SCHEMA hpi_candidate TO {}").format(sql.Identifier(ROLE)))
            conn.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA hpi_candidate TO {}").format(sql.Identifier(ROLE)))
            conn.execute(sql.SQL("GRANT INSERT ON investigations, investigation_results, comparable_evidence, shortlists, shortlist_investigations TO {}").format(sql.Identifier(ROLE)))
            conn.execute(sql.SQL("GRANT UPDATE(note_text), DELETE ON shortlist_investigations TO {}").format(sql.Identifier(ROLE)))
            conn.execute(sql.SQL("GRANT USAGE ON ALL SEQUENCES IN SCHEMA hpi_candidate TO {}").format(sql.Identifier(ROLE)))

def verify_role(conn):
    row=conn.execute("""SELECT current_user,session_user,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb
        FROM pg_roles WHERE rolname=current_user""").fetchone()
    if row!=(ROLE,ROLE,False,False,False,False):
        raise EvidenceStoreError("Invalid fixture runtime role")
    rows=conn.execute("""SELECT c.relname,c.relrowsecurity,pg_get_userbyid(c.relowner)
         FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
         WHERE n.nspname='hpi_candidate' AND c.relname=ANY(%s)""",(list(BUYER_TABLES),)).fetchall()
    if {r[0] for r in rows}!=set(BUYER_TABLES) or any(not r[1] or r[2]==ROLE for r in rows):
        raise EvidenceStoreError("Ownership boundary unavailable")
    if conn.execute("SELECT nullif(current_setting('hpi.owner_id',true),'')").fetchone()[0] is not None:
        raise EvidenceStoreError("Unexpected pooled owner context")

def make_pool(dsn, *, max_size=4):
    _dsn_check(dsn,ROLE)
    if not 1<=max_size<=8:raise ValueError("Invalid pool capacity")
    def configure(conn):
        conn.execute("SET search_path TO hpi_candidate, pg_catalog")
        verify_role(conn)
        PostgresFixtureStore(conn)
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
                        store=PostgresFixtureStore(conn)
                        payload=list(create_app(store,react_assets=assets,synthetic_map=True)(environ,capture))
                        if int(captured[0][:3])>=400:raise _Abort()
                except _Abort:pass
            if int(captured[0][:3])==500:
                return _response(start_response,503,{"error":"evidence_unavailable"})
            start_response(*captured)
            return payload
        except (psycopg.Error,PoolTimeout,EvidenceStoreError,ValueError,RuntimeError):
            return _response(start_response,503,{"error":"evidence_unavailable"})
    return app

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
        pool=make_pool(os.environ["HPI_RUNTIME_DSN"])
        app=application(pool,{name:os.environ["HPI_FIXTURE_"+name.upper()+"_PASSWORD"] for name in OWNERS},load_react_assets())
        with make_server("127.0.0.1",args.port,app,server_class=ThreadedServer,handler_class=QuietHandler) as server:
            print("Fictional PostgreSQL runtime ready",flush=True)
            server.serve_forever()
    except (ValueError,KeyError,psycopg.Error,PoolTimeout,EvidenceStoreError,OSError,RuntimeError):
        p.error("Fictional runtime startup refused")
    finally:
        if pool is not None:pool.close()
if __name__=="__main__":main()
