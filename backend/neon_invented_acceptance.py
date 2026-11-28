"""One-shot invented Neon browser acceptance. No production hosting or owner DSN.
Seal is derived independently on a local disposable PostgreSQL database.
Only aggregate, fixed-stage messages leave the protected command.
"""
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
import tempfile
from contextlib import ExitStack, contextmanager
from threading import Thread
from wsgiref.simple_server import make_server, WSGIServer
from time import monotonic
import psycopg
from backend.postgres_ingestion import initialise
from backend.historical_migration import migrate_historical
from backend.historical_postgres import import_historical
from backend.historical_reader import seal_historical, ROLE as READER, provision_reader
from backend.buyer_ownership import ROLE as BUYER, _prepare_empty_buyer_schema
from backend.neon_synthetic_seed import fixture_intake, seed_statements
from backend.neon_synthetic_journey import open_neon_synthetic_journey, MODE
from backend.private_beta_rehearsal import PrivateBetaRehearsal
from backend.persistent_oidc import PersistentBoundary
from backend.offline_oidc_http import application
from backend.react_assets import load_react_assets
from backend.postgres_runtime import QuietHandler
from backend.curated_ingestion_candidate import ImportRefused
from psycopg import sql

DB="hpi_ingest_fixture"


def _private_directory(path):
    root=Path(path).absolute()
    if root.resolve(strict=True)!=root or not root.is_dir() or root.stat().st_uid!=os.getuid() or root.stat().st_mode&0o077:
        raise ImportRefused("Private acceptance directory required")
    return root


@contextmanager
def _fixture_admin(dsn):
    # Check BEFORE executing any SQL or overriding the database name.
    p=psycopg.conninfo.conninfo_to_dict(dsn)
    if (p.get("host"),p.get("dbname"),p.get("user"))!=("127.0.0.1","hpi_fixture","postgres") or set(p)-{"host","port","dbname","user","password"}:
        raise ImportRefused("Disposable local admin required")
    with psycopg.connect(dsn,autocommit=True) as admin:
        if (admin.info.host,admin.info.dbname,admin.info.user)!=("127.0.0.1","hpi_fixture","postgres"):
            raise ImportRefused("Disposable local admin required")
        if admin.execute("SELECT 1 FROM pg_database WHERE datname=%s",(DB,)).fetchone() is not None:
            raise ImportRefused("Disposable database already exists")
        admin.execute("CREATE DATABASE hpi_ingest_fixture")
        try:
            with psycopg.connect(dsn,dbname=DB,autocommit=True) as conn:
                initialise(conn)
                migrate_historical(conn)
                yield conn
        finally:
            admin.execute("DROP DATABASE hpi_ingest_fixture")


def _write_seal(root,seal):
    path=root/"seal.json"
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as out:
        json.dump(seal,out)
    return path


def prepare_seal(dsn,root):
    root=_private_directory(root)
    with _fixture_admin(dsn) as conn:
        args=fixture_intake()
        import_historical(conn,**args)
        seal=seal_historical(conn,**args)
    return _write_seal(root,seal)


class AcceptanceServer(WSGIServer):
    def handle_error(self,request,client_address):
        print('Invented acceptance: HTTP transport failure',file=sys.stderr,flush=True)


class TLSHandler(QuietHandler):
    def get_environ(self):
        env=super().get_environ()
        env["HTTPS"]="on"
        return env


def browser_journey(root,open_service,*,progress=lambda stage:None):
    """Real Chromium, exact cents, insufficient evidence, persistence and denial.
    The service factory is invoked twice; no reimport or new buyer cookie.
    """
    from playwright.sync_api import sync_playwright,expect
    expect.set_options(timeout=60000)
    root=_private_directory(root)
    cert=root/"cert.pem";key=root/"key.pem"
    subprocess.run(["openssl","req","-x509","-newkey","rsa:2048","-nodes","-days","1","-subj","/CN=127.0.0.1","-addext","subjectAltName=IP:127.0.0.1","-keyout",str(key),"-out",str(cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    assets=load_react_assets()
    server=make_server("127.0.0.1",0,lambda e,s:[],server_class=AcceptanceServer,handler_class=TLSHandler)
    base="https://127.0.0.1:"+str(server.server_port)
    def boundary():
        return PersistentBoundary(session_file=root/"sessions.sqlite",issuer="https://issuer.invalid",client_id="fixture",
            authorize_endpoint="https://issuer.invalid/authorize",redirect_uri=base+"/auth/callback",
            public_keys={"fixture":"not-used-in-session-rehearsal"},owner_map={"a":"fixture-owner-a","b":"fixture-owner-b"})
    tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(cert,key)
    server.socket=tls.wrap_socket(server.socket,server_side=True)
    thread=None
    with ExitStack() as sessions:
        try:
            progress('startup')
            first=boundary()
            service=sessions.enter_context(open_service(first))
            progress('startup_verified')
            server.set_app(application(None,assets,first,lambda **kw:None,private_beta=service))
            thread=Thread(target=server.serve_forever,daemon=True)
            thread.start()
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
                try:
                    contexts=[]
                    for owner in ("fixture-owner-a","fixture-owner-b"):
                        cookie=first._issue_session(owner)["cookie"].split(";",1)[0]
                        name,value=cookie.split("=",1)
                        ctx=browser.new_context(ignore_https_errors=True)
                        ctx.add_cookies([{"name":name,"value":value,"url":base,"secure":True,"httpOnly":True,"sameSite":"Lax"}])
                        ctx.set_default_timeout(60000)
                        contexts.append(ctx)
                    page=contexts[0].new_page()
                    progress("first_search")
                    page.goto(base+"/private-beta-rehearsal")
                    expect(page.get_by_test_id("beta-nav-home")).to_have_attribute("aria-current","page")
                    expect(page.get_by_test_id("beta-workspace")).to_be_visible()
                    page.get_by_test_id("beta-new-investigation").click()
                    page.get_by_test_id("beta-search").click()
                    expect(page.get_by_test_id("beta-match")).to_have_text("One eligible parcel candidate")
                    progress("first_save")
                    page.get_by_test_id("beta-create").click()
                    expect(page.get_by_test_id("beta-result")).to_be_visible(timeout=60000)
                    expect(page.get_by_test_id("beta-sale")).to_have_count(3)
                    expect(page.get_by_test_id("beta-sale").first).to_contain_text("525,000.01")
                    iid=page.get_by_test_id("beta-id").input_value()
                    page.get_by_test_id("beta-add-comparison").click()
                    page.locator("#beta-note-0").fill("First property note")
                    progress("second_search")
                    page.get_by_test_id("beta-nav-investigate").click()
                    page.locator("#beta-address").fill("2 Fictional Court")
                    page.get_by_test_id("beta-search").click()
                    expect(page.get_by_test_id("beta-match")).to_have_text("One eligible parcel candidate")
                    progress("second_save")
                    page.locator("#beta-price").fill("600000.02")
                    page.get_by_test_id("beta-create").click()
                    expect(page.get_by_test_id("beta-result")).to_contain_text("0 eligible sales",timeout=60000)
                    expect(page.get_by_test_id("beta-sale")).to_have_count(0)
                    page.get_by_test_id("beta-add-comparison").click()
                    progress("comparison_save")
                    page.get_by_test_id("beta-save-comparison").click()
                    comparison=page.get_by_test_id("beta-comparison")
                    for value in ("600,000.02","525,000.01","First property note","insufficient data"):
                        expect(comparison).to_contain_text(value,timeout=60000)
                    sid=page.get_by_test_id("beta-comparison-id").input_value()
                    progress("reconstruct")
                    second=boundary()
                    resumed=sessions.enter_context(open_service(second))
                    if (service.reader.info.backend_pid==resumed.reader.info.backend_pid or
                        service.writer.info.backend_pid==resumed.writer.info.backend_pid):
                        raise ImportRefused("Fresh service connections required")
                    server.set_app(application(None,assets,second,lambda **kw:None,private_beta=resumed))
                    progress("reopen_investigation")
                    page.reload()
                    expect(page.get_by_test_id("beta-workspace")).to_be_visible()
                    page.get_by_test_id("beta-nav-investigate").click()
                    page.get_by_test_id("beta-id").fill(iid)
                    page.get_by_test_id("beta-reopen").click()
                    expect(page.get_by_test_id("beta-sale")).to_have_count(3,timeout=60000)
                    expect(page.get_by_test_id("beta-sale").first).to_contain_text("525,000.01")
                    progress("reopen_comparison")
                    page.get_by_test_id("beta-nav-compare").click()
                    page.get_by_test_id("beta-comparison-id").fill(sid)
                    page.get_by_test_id("beta-reopen-comparison").click()
                    for value in ("600,000.02","525,000.01","First property note","insufficient data"):
                        expect(comparison).to_contain_text(value,timeout=60000)
                    progress("cross_owner_denial")
                    other=contexts[1].new_page()
                    other.goto(base+"/private-beta-rehearsal")
                    expect(other.get_by_test_id("beta-workspace")).to_be_visible()
                    expect(other.get_by_test_id("beta-workspace-comparison")).to_have_count(0)
                    other.get_by_test_id("beta-nav-investigate").click()
                    other.get_by_test_id("beta-id").fill(iid)
                    other.get_by_test_id("beta-reopen").click()
                    expect(other.get_by_test_id("beta-error")).to_be_visible()
                    expect(other.get_by_test_id("beta-result")).to_have_count(0)
                    other.get_by_test_id("beta-nav-compare").click()
                    other.get_by_test_id("beta-comparison-id").fill(sid)
                    other.get_by_test_id("beta-reopen-comparison").click()
                    expect(other.get_by_test_id("beta-error")).to_be_visible()
                    expect(other.get_by_test_id("beta-comparison")).to_have_count(0)
                    if resumed.writer.execute("SELECT nullif(current_setting('hpi.owner_id',true),'')").fetchone()!=(None,):
                        raise ImportRefused("Buyer context leaked")
                finally:
                    browser.close()
        finally:
            # Wait for the single request-serving thread to finish before
            # unwinding ExitStack and closing its database connections.
            if thread is not None:
                server.shutdown()
                thread.join()
            server.server_close()
    return {"status":"invented_browser_journey_verified","investigations_created":2,"comparison_created":1,
            "supported_sales":3,"insufficient_sales":0,"reconstructed":True,"cross_owner_denied":True,
            "real_data_activated":False}


def main():
    # No raw exceptions, DSNs, seal values, screenshots or browser traces.
    if len(sys.argv)!=3 or sys.argv[1] not in ("prepare","run"):
        print("Invented acceptance invocation refused",file=sys.stderr)
        return 1
    stage=sys.argv[1]
    current=stage
    started=monotonic()
    def progress(value):
        nonlocal current
        current=value
        print('Invented acceptance stage: '+value+' elapsed_seconds='+str(round(monotonic()-started)),flush=True)
    try:
        root=_private_directory(sys.argv[2])
        if stage=="prepare":
            prepare_seal(os.environ["HPI_PG_DSN"],root)
            print("Independent invented seal prepared")
        else:
            if os.environ.get("HPI_NEON_MODE")!=MODE:
                raise ImportRefused("Explicit mode required")
            report=browser_journey(root,lambda b:open_neon_synthetic_journey(os.environ,root/"seal.json",b,progress=progress),progress=progress)
            print(json.dumps(report,sort_keys=True))
        return 0
    except Exception as exc:
        # Classify only; no exception message, SQL, browser trace or secret.
        category=("assertion" if isinstance(exc,AssertionError) else "database" if isinstance(exc,psycopg.Error) else "refused" if isinstance(exc,ImportRefused) else "other")
        print("Invented acceptance failed at "+current+" category="+category,file=sys.stderr,flush=True)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
