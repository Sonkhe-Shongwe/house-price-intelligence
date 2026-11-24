"""Actual HTTP, concurrent requests, PostgreSQL and Chromium. Invented data only."""
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import psycopg
from psycopg.conninfo import make_conninfo
from playwright.sync_api import sync_playwright,expect
from backend.postgres_runtime import bootstrap,ROLE,make_pool,application,ThreadedServer,QuietHandler
from backend.postgres_consolidation import BUILDS,activate
from backend.react_assets import load_react_assets
from wsgiref.simple_server import make_server
from threading import Thread
from statistics import median
from backend.postgres_ingestion import initialise,import_revision,ImportedFixtureStore
from backend.curated_ingestion_candidate import ImportRefused,address_candidates
from backend.synthetic_demo import example_request
from backend.synthetic_shortlists import SyntheticShortlistService
from backend.synthetic_investigation_store import EvidenceStoreError

ADMIN=os.environ["HPI_PG_DSN"]

class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.passwords={n:secrets.token_urlsafe(32) for n in ("alice","bob")}
        dbpass=secrets.token_urlsafe(32)
        bootstrap(ADMIN,dbpass)
        cls.dsn=make_conninfo(ADMIN,user=ROLE,password=dbpass)
        cls.env={**os.environ,"HPI_RUNTIME_DSN":cls.dsn,**{"HPI_FIXTURE_"+n.upper()+"_PASSWORD":p for n,p in cls.passwords.items()}}
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0))
            cls.port=sock.getsockname()[1]
        cls.base=f"http://127.0.0.1:{cls.port}"
        cls.start()
    @classmethod
    def start(cls):
        cls.log=tempfile.TemporaryFile()
        cls.proc=subprocess.Popen([sys.executable,"-m","backend.postgres_runtime","--fixture-only","--port",str(cls.port)],env=cls.env,stdout=cls.log,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            if cls.proc.poll() is not None:
                raise RuntimeError("Runtime startup refused")
            try:
                if cls.call("alice","GET","/health")[0]==200:return
            except OSError:pass
            time.sleep(.15)
        cls.stop()
        raise RuntimeError("Runtime did not become ready")
    @classmethod
    def stop(cls):
        if cls.proc.poll() is None:
            cls.proc.terminate()
            try:cls.proc.wait(timeout=6)
            except subprocess.TimeoutExpired:cls.proc.kill();cls.proc.wait()
        cls.log.close()
    @classmethod
    def tearDownClass(cls):
        cls.stop()
    @classmethod
    def call(cls,owner,method,path,payload=None,origin=True):
        headers={}
        if owner:
            headers["Authorization"]="Basic "+base64.b64encode((owner+":"+cls.passwords[owner]).encode()).decode()
        if origin:headers["Origin"]=cls.base
        if payload is not None:headers["Content-Type"]="application/json"
        req=Request(cls.base+path,method=method,headers=headers,data=None if payload is None else json.dumps(payload).encode())
        try:
            with urlopen(req,timeout=12) as res:return res.status,json.load(res)
        except HTTPError as exc:return exc.code,json.load(exc)
    def create(self,owner,pin):
        p=example_request();p["subject"]["pin"]=pin
        code,r=self.call(owner,"POST","/v1/investigations",p)
        self.assertEqual(code,201,r)
        return r
    def test_build_activation_rollback_and_revision_browser_map(self):
        original=self.create("alice","00000000000001")
        old=original["investigation_id"]
        _,short=self.call("alice","POST","/v1/shortlists",{"label":"Revision comparison"})
        path="/v1/shortlists/"+short["shortlist_id"]
        self.assertEqual(self.call("alice","POST",path+"/entries",{"investigation_id":old,"note_text":"Original evidence"})[0],201)
        gen=activate(ADMIN,BUILDS[1],0)
        self.assertEqual(gen,1)
        try:
            with self.assertRaises(ValueError):activate(ADMIN,BUILDS[2],0)
            with self.assertRaises(ValueError):activate(ADMIN,"unknown",gen)
            _,matches=self.call("alice","POST","/v1/addresses/search",{"query":"105 Fictional Way"})
            self.assertEqual(len(matches["candidates"]),2)
            chosen=matches["candidates"][0]["address_id"]
            self.assertTrue(matches["candidates"][0]["ambiguous_address"])
            p=example_request()
            p["subject"]={"address_id":chosen,"building_area_sqft":1600}
            code,new=self.call("alice","POST","/v1/investigations",p)
            self.assertEqual(code,201,new)
            self.assertEqual(new["data_build"]["build_id"],BUILDS[1])
            self.assertEqual(self.call("alice","POST",path+"/entries",{"investigation_id":new["investigation_id"]})[0],201)
            gen=activate(ADMIN,BUILDS[2],gen)
            self.assertEqual(self.call("alice","GET","/v1/addresses/"+chosen)[0],404)
            revised=self.create("alice","00000000000001")
            self.assertEqual(revised["data_build"]["build_id"],BUILDS[2])
            self.assertNotEqual([c["sale_price_usd"] for c in original["comparables"]],[c["sale_price_usd"] for c in revised["comparables"]])
            self.assertEqual(self.call("alice","GET","/v1/investigations/"+old)[1],original)
            self.assertEqual(self.call("bob","GET","/v1/investigations/"+old)[0],404)
            self.assertEqual(self.call("bob","GET",path)[0],404)
            history=self.call("alice","GET","/v1/investigations/history")[1]["investigations"]
            self.assertTrue({old,new["investigation_id"],revised["investigation_id"]}<={i["investigation_id"] for i in history})
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,args=["--no-sandbox","--enable-unsafe-swiftshader","--use-angle=swiftshader"])
                try:
                    context=browser.new_context(http_credentials={"username":"alice","password":self.passwords["alice"]})
                    page=context.new_page();external=[]
                    page.on("request",lambda r:external.append(r.url) if not r.url.startswith(self.base+"/") else None)
                    page.goto(self.base+"/buyer-workflow")
                    page.get_by_test_id("buyer-manual-pin").fill("00000000000001")
                    page.get_by_test_id("buyer-create").click()
                    expect(page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
                    expect(page.get_by_test_id("buyer-build")).to_have_text(BUILDS[2])
                    page.get_by_test_id("geo-load").click()
                    expect(page.get_by_test_id("geo-ready")).to_be_visible(timeout=20000)
                    page.get_by_test_id("geo-pin-2").click()
                    expect(page.get_by_test_id("buyer-sale").nth(1)).to_have_attribute("aria-pressed","true")
                    self.assertEqual(external,[])
                    context.close()
                finally:browser.close()
            before=self.call("alice","GET",path)[1]
            gen=activate(ADMIN,BUILDS[0],gen)
            self.stop();self.start()
            self.assertEqual(self.call("alice","GET",path)[1],before)
            self.assertEqual(self.call("alice","GET","/v1/investigations/"+revised["investigation_id"])[1],revised)
            self.assertEqual(self.create("alice","00000000000001")["data_build"]["build_id"],BUILDS[0])
            self.assertTrue(self.call("alice","GET","/v1/investigations/"+revised["investigation_id"]+"/map")[1]["map_available"])
        finally:
            # Restore baseline for the existing runtime tests even on failure.
            with psycopg.connect(ADMIN,autocommit=True) as conn:
                row=conn.execute("SELECT build_id,generation FROM hpi_candidate.active_fixture_build").fetchone()
            if row[0]!=BUILDS[0]:activate(ADMIN,BUILDS[0],row[1])
    def test_pool_exhaustion_connection_loss_and_recovery(self):
        pool=make_pool(self.dsn,max_size=1)
        server=make_server("127.0.0.1",0,application(pool,self.passwords,load_react_assets()),server_class=ThreadedServer,handler_class=QuietHandler)
        thread=Thread(target=server.serve_forever,daemon=True);thread.start()
        base="http://127.0.0.1:"+str(server.server_port)
        def request():
            auth=base64.b64encode(("alice:"+self.passwords["alice"]).encode()).decode()
            req=Request(base+"/health",headers={"Authorization":"Basic "+auth})
            try:
                with urlopen(req,timeout=10) as res:return res.status,json.load(res)
            except HTTPError as exc:return exc.code,json.load(exc)
        try:
            with pool.connection() as held:
                start=time.monotonic()
                self.assertEqual(request(),(503,{"error":"evidence_unavailable"}))
                self.assertLess(time.monotonic()-start,9)
                pid=held.info.backend_pid
            self.assertEqual(request()[0],200)
            # Terminate the single idle backend, not the database or any external session.
            with psycopg.connect(ADMIN,autocommit=True) as admin:
                self.assertTrue(admin.execute("SELECT pg_terminate_backend(%s)",(pid,)).fetchone()[0])
            status,body=request()
            self.assertIn(status,(200,503))
            if status==503:self.assertEqual(body,{"error":"evidence_unavailable"})
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                if request()[0]==200:break
                time.sleep(.2)
            else:self.fail("Pool did not recover")
        finally:
            server.shutdown();server.server_close();thread.join(timeout=5);pool.close()
    def test_bounded_parallel_smoke_and_source_control_permissions(self):
        def sample(i):
            start=time.monotonic()
            code,_=self.call("alice" if i%2 else "bob","GET","/health")
            return code,(time.monotonic()-start)*1000
        with ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(sample,range(24)))
        self.assertTrue(all(code==200 for code,_ in results))
        timings=sorted(t for _,t in results)
        p95=timings[22]
        print(f"Aggregate loopback smoke: n=24 workers=4 median_ms={median(timings):.1f} p95_ms={p95:.1f} max_ms={timings[-1]:.1f}",flush=True)
        self.assertLess(timings[-1],10000)
        with psycopg.connect(self.dsn,autocommit=True) as conn:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                conn.execute("UPDATE hpi_candidate.active_fixture_build SET generation=0")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                conn.execute("DELETE FROM hpi_candidate.fixture_build_events")
    def test_rich_revision_preserves_frozen_evidence(self):
        with psycopg.connect(ADMIN,autocommit=True) as conn:
            old_build,generation=conn.execute("SELECT build_id,generation FROM hpi_candidate.active_fixture_build").fetchone()
        original=self.create("alice","00000000000001")
        generation=activate(ADMIN,BUILDS[3],generation)
        try:
            result=self.create("alice","00000000000001")
            self.assertEqual(result["data_build"]["build_id"],BUILDS[3])
            self.assertEqual(len({r["sale_price_usd"] for r in result["comparables"]}),3)
            self.assertEqual(len({r["age_days"] for r in result["comparables"]}),3)
            self.assertEqual(len({r["size_difference_pct"] for r in result["comparables"]}),3)
            self.assertEqual(self.call("alice","GET","/v1/investigations/"+original["investigation_id"])[1],original)
            self.assertTrue(self.call("alice","GET","/v1/investigations/"+result["investigation_id"]+"/map")[1]["map_available"])
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,args=["--no-sandbox","--enable-unsafe-swiftshader","--use-angle=swiftshader"])
                try:
                    page=browser.new_page(http_credentials={"username":"alice","password":self.passwords["alice"]})
                    page.goto(self.base+"/buyer-workflow")
                    page.get_by_test_id("buyer-query").fill("12 Imaginary Cedar")
                    page.get_by_test_id("buyer-search").click()
                    page.get_by_test_id("buyer-candidate").first.click()
                    page.get_by_test_id("buyer-create").click()
                    expect(page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
                    expect(page.get_by_test_id("buyer-result")).to_contain_text("12 Imaginary Cedar Lane")
                    page.get_by_test_id("geo-load").click()
                    expect(page.get_by_test_id("geo-ready")).to_be_visible(timeout=20000)
                    page.get_by_test_id("buyer-sale").first.click()
                    expect(page.get_by_test_id("sale-evidence-detail")).to_be_visible()
                    if os.environ.get("HPI_RELEASE_SCREENSHOTS"):
                        from pathlib import Path
                        folder=Path(os.environ["HPI_RELEASE_SCREENSHOTS"]);folder.mkdir(parents=True,exist_ok=True)
                        page.get_by_test_id("buyer-result").screenshot(path=str(folder/"rich-fictional-evidence.png"))
                finally:browser.close()
        finally:activate(ADMIN,old_build,generation)

    def test_source_shaped_replay_from_intake_through_react(self):
        with psycopg.connect(ADMIN,autocommit=True) as conn:
            old_build,generation=conn.execute("SELECT build_id,generation FROM hpi_candidate.active_fixture_build").fetchone()
        original=self.create("alice","00000000000001")
        generation=activate(ADMIN,BUILDS[4],generation)
        try:
            code,matches=self.call("alice","POST","/v1/addresses/search",{"query":"10 Fictional Replay Lane"})
            self.assertEqual(code,200)
            self.assertEqual(len(matches["candidates"]),1)
            request=example_request()
            request["subject"]={"address_id":matches["candidates"][0]["address_id"],"building_area_sqft":1600}
            code,result=self.call("alice","POST","/v1/investigations",request)
            self.assertEqual(code,201)
            self.assertEqual(result["data_build"]["build_id"],BUILDS[4])
            self.assertEqual(result["data_build"]["source_kind"],"synthetic_fixture")
            self.assertEqual({c["sale_price_usd"] for c in result["comparables"]},{"487500.01","542750.02","519900.03"})
            self.assertIsNone(result["valuation"])
            self.assertEqual(self.call("alice","GET","/v1/investigations/"+original["investigation_id"])[1],original)
            self.assertFalse(self.call("alice","GET","/v1/investigations/"+result["investigation_id"]+"/map")[1]["map_available"])
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
                try:
                    page=browser.new_page(http_credentials={"username":"alice","password":self.passwords["alice"]})
                    page.goto(self.base+"/buyer-workflow")
                    page.get_by_test_id("buyer-query").fill("10 Fictional Replay Lane")
                    page.get_by_test_id("buyer-search").click()
                    page.get_by_test_id("buyer-candidate").first.click()
                    page.get_by_test_id("buyer-create").click()
                    expect(page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
                    expect(page.get_by_test_id("buyer-build")).to_have_text(BUILDS[4])
                    expect(page.get_by_test_id("buyer-result")).to_contain_text("$487,500.01")
                    expect(page.get_by_test_id("buyer-result")).to_contain_text("$542,750.02")
                    expect(page.get_by_test_id("buyer-result")).to_contain_text("$519,900.03")
                finally:browser.close()
        finally:activate(ADMIN,old_build,generation)

    def test_offline_oidc_https_persistence_and_owner_isolation(self):
        import ssl
        from pathlib import Path
        from urllib.parse import urlencode,parse_qs,urlsplit
        from urllib.request import build_opener,HTTPSHandler,HTTPRedirectHandler
        import jwt
        from cryptography.hazmat.primitives.asymmetric import rsa
        from backend.persistent_oidc import PersistentBoundary
        from backend.offline_oidc_http import application as session_application
        from backend.oidc_boundary import COOKIE
        from wsgiref.simple_server import WSGIRequestHandler
        class TLSHandler(QuietHandler):
            def get_environ(self):
                env=super().get_environ();env["HTTPS"]="on";return env
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);cert=path/"cert.pem";keyfile=path/"key.pem"
            subprocess.run(["openssl","req","-x509","-newkey","rsa:2048","-nodes","-days","1","-subj","/CN=127.0.0.1","-addext","subjectAltName=IP:127.0.0.1","-keyout",str(keyfile),"-out",str(cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            sslserver=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);sslserver.load_cert_chain(cert,keyfile)
            client=ssl.create_default_context(cafile=str(cert))
            opener=build_opener(HTTPSHandler(context=client),NoRedirect())
            pool=make_pool(self.dsn,max_size=2)
            private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
            issued={}
            server=make_server("127.0.0.1",0,lambda e,s:[],server_class=ThreadedServer,handler_class=TLSHandler)
            base="https://127.0.0.1:"+str(server.server_port)
            config=dict(session_file=path/"sessions.sqlite",issuer="https://fictional-idp.invalid/",client_id="hpi-fixture",
                authorize_endpoint="https://fictional-idp.invalid/authorize",redirect_uri=base+"/auth/callback",
                public_keys={"local":private.public_key()},owner_map={("https://fictional-idp.invalid/",n):"fictional-"+n for n in ("alice","bob")})
            def exchange(**args):
                subject,nonce=issued.pop(args["code"])
                now=int(time.time())
                return jwt.encode({"iss":config["issuer"],"aud":config["client_id"],"sub":subject,"nonce":nonce,"iat":now,"exp":now+300},private,algorithm="RS256",headers={"kid":"local"})
            def setup():
                return session_application(pool,load_react_assets(),PersistentBoundary(**config),exchange)
            server.set_app(setup());server.socket=sslserver.wrap_socket(server.socket,server_side=True)
            thread=Thread(target=server.serve_forever,daemon=True);thread.start()
            def request(method,route,cookie="",csrf=None,payload=None,origin=True):
                headers={"Cookie":cookie}
                if origin:headers["Origin"]=base
                if csrf:headers["X-HPI-CSRF"]=csrf
                if payload is not None:headers["Content-Type"]="application/json"
                req=Request(base+route,method=method,headers=headers,data=json.dumps(payload).encode() if payload is not None else None)
                try:
                    with opener.open(req,timeout=10) as res:return res.status,res.headers,json.load(res)
                except HTTPError as exc:return exc.code,exc.headers,json.load(exc)
            def login(owner):
                status,headers,body=request("POST","/auth/start")
                self.assertEqual(status,200)
                bind=headers.get("Set-Cookie").split(";")[0]
                params=parse_qs(urlsplit(body["authorize_url"]).query)
                code=secrets.token_urlsafe(32);issued[code]=(owner,params["nonce"][0])
                route="/auth/callback?"+urlencode({"state":params["state"][0],"code":code})
                status,headers,_=request("GET",route,bind)
                self.assertEqual(status,303)
                session=headers.get_all("Set-Cookie")[0]
                self.assertIn("Secure; HttpOnly; SameSite=Lax",session)
                self.assertEqual(request("GET",route,bind)[0],401)
                cookie=session.split(";")[0]
                csrf=request("GET","/auth/session",cookie)[2]["csrf"]
                return cookie,csrf
            try:
                self.assertEqual(request("GET","/health")[0],401)
                alice,csrf=login("alice");bob,bcsrf=login("bob")
                self.assertEqual(request("POST","/v1/investigations",alice,payload=example_request())[0],401)
                status,_,saved=request("POST","/v1/investigations",alice,csrf,example_request())
                self.assertEqual(status,201)
                route="/v1/investigations/"+saved["investigation_id"]
                self.assertEqual(request("GET",route,bob)[0],404)
                server.set_app(setup()) # reconstruct identity boundary from persistent storage
                self.assertEqual(request("GET",route,alice)[2],saved)
                # Test authenticated React writes over real local TLS. The only
                # certificate exception is in this disposable browser context.
                with sync_playwright() as pw:
                    browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
                    try:
                        ctx=browser.new_context(ignore_https_errors=True)
                        name,value=alice.split("=",1)
                        ctx.add_cookies([{"name":name,"value":value,"url":base,"secure":True,"httpOnly":True,"sameSite":"Lax"}])
                        page=ctx.new_page()
                        page.goto(base+"/")
                        page.get_by_test_id("workspace-new-investigation").click()
                        page.get_by_test_id("buyer-manual-pin").fill("00000000000001")
                        page.get_by_test_id("buyer-create").click()
                        expect(page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
                        page.get_by_test_id("dossier-compare").click()
                        page.get_by_test_id("workspace-create").click()
                        expect(page.get_by_test_id("workspace-count")).to_have_text("0 / 3")
                        page.get_by_test_id("workspace-add-current").click()
                        expect(page.get_by_test_id("workspace-count")).to_have_text("1 / 3")
                        page.get_by_test_id("workspace-note").first.fill("Offline session note")
                        page.get_by_test_id("workspace-save-note").first.click()
                        expect(page.get_by_test_id("workspace-note-state").first).to_have_text("Saved note verified")
                        sid=page.get_by_test_id("workspace-id").inner_text()
                        self.assertEqual(request("GET","/v1/shortlists/"+sid,bob)[0],404)
                        ctx.close()
                    finally:browser.close()
                self.assertEqual(request("POST","/auth/logout",alice,csrf)[0],200)
                self.assertEqual(request("GET",route,alice)[0],401)
                self.assertEqual(request("GET","/health",bob)[0],200)
            finally:server.shutdown();server.server_close();thread.join(timeout=5);pool.close()

    def test_tampered_source_refused_then_restored(self):
        with psycopg.connect(ADMIN,autocommit=True) as conn:
            conn.execute("UPDATE hpi_candidate.sale_transactions SET price_usd_cents=price_usd_cents+1 WHERE transaction_id='txn-2'")
            try:self.assertEqual(self.call("alice","GET","/health"),(503,{"error":"evidence_unavailable"}))
            finally:conn.execute("UPDATE hpi_candidate.sale_transactions SET price_usd_cents=price_usd_cents-1 WHERE transaction_id='txn-2'")
        self.assertEqual(self.call("bob","GET","/health")[0],200)
    def test_http_isolation_and_concurrency(self):
        self.assertEqual(self.call(None,"GET","/v1/investigations/history")[0],401)
        self.assertEqual(self.call("alice","POST","/v1/investigations",example_request(),origin=False)[0],403)
        alice=[self.create("alice",f"{i:014d}") for i in range(1,5)]
        bob=self.create("bob","00000000000001")
        iid=alice[0]["investigation_id"]
        self.assertEqual(self.call("bob","GET","/v1/investigations/"+iid)[0],404)
        self.assertEqual(self.call("bob","GET","/v1/investigations/"+iid+"/map")[0],404)
        code,short=self.call("alice","POST","/v1/shortlists",{"label":"Concurrent fictional"})
        self.assertEqual(code,201,short)
        path="/v1/shortlists/"+short["shortlist_id"]
        with ThreadPoolExecutor(max_workers=4) as ex:
            results=list(ex.map(lambda r:self.call("alice","POST",path+"/entries",{"investigation_id":r["investigation_id"]}),alice))
        self.assertEqual(sorted(x[0] for x in results),[201,201,201,409])
        code,after=self.call("alice","GET",path);self.assertEqual(code,200);self.assertEqual(len(after["entries"]),3)
        self.assertEqual(self.call("bob","GET",path)[0],404)
        self.assertEqual(self.call("bob","PATCH",path+"/entries/"+iid,{"note_text":"blocked"})[0],404)
        self.assertEqual(self.call("bob","DELETE",path+"/entries/"+iid)[0],404)
        code,bs=self.call("bob","POST","/v1/shortlists",{"label":"Bob fictional"});self.assertEqual(code,201)
        self.assertEqual(self.call("bob","POST","/v1/shortlists/"+bs["shortlist_id"]+"/entries",{"investigation_id":iid})[0],404)
        self.assertEqual(self.call("alice","GET","/v1/investigations/"+bob["investigation_id"])[0],404)
        self.assertTrue(self.call("alice","GET","/v1/investigations/"+iid+"/map")[1]["map_available"])
        with psycopg.connect(self.dsn,autocommit=True) as conn:
            conn.execute("SET search_path TO hpi_candidate,pg_catalog")
            self.assertEqual(conn.execute("SELECT count(*) FROM investigations").fetchone()[0],0)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                conn.execute("UPDATE sale_transactions SET price_usd_cents=1")
        # Stop/restart the application process, not the database.
        self.stop();self.start()
        self.assertEqual(self.call("alice","GET",path)[1],after)
        self.assertEqual(self.call("alice","GET","/v1/investigations/"+iid)[1],alice[0])
    def test_real_browser_two_workspaces_and_saved_note(self):
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
            try:
                contexts={name:browser.new_context(http_credentials={"username":name,"password":self.passwords[name]}) for name in self.passwords}
                a=contexts["alice"].new_page()
                a.goto(self.base+"/")
                a.get_by_test_id("workspace-new-investigation").click()
                a.get_by_test_id("buyer-manual-pin").fill("00000000000001")
                a.get_by_test_id("buyer-create").click()
                expect(a.get_by_test_id("buyer-result")).to_be_visible(timeout=12000)
                iid=a.get_by_test_id("buyer-saved-id").inner_text()
                a.get_by_test_id("dossier-compare").click()
                a.get_by_test_id("workspace-create").click()
                expect(a.get_by_test_id("workspace-count")).to_have_text("0 / 3")
                sid=a.get_by_test_id("workspace-id").inner_text()
                a.get_by_test_id("workspace-add-current").click()
                expect(a.get_by_test_id("workspace-count")).to_have_text("1 / 3")
                a.get_by_test_id("workspace-note").first.fill("PostgreSQL fictional note")
                a.get_by_test_id("workspace-save-note").first.click()
                expect(a.get_by_test_id("workspace-note-state").first).to_have_text("Saved note verified")
                b=contexts["bob"].new_page();b.goto(self.base+"/")
                expect(b.get_by_test_id("nav-home")).to_have_attribute("aria-current","page")
                self.assertEqual(b.request.get(self.base+"/v1/investigations/"+iid).status,404)
                self.assertEqual(b.request.get(self.base+"/v1/shortlists/"+sid).status,404)
                a.reload();a.get_by_test_id("nav-compare").click()
                # Explicit UUID remains available even when other lists exist.
                self.assertEqual(a.request.get(self.base+"/v1/shortlists/"+sid).json()["entries"][0]["note_text"],"PostgreSQL fictional note")
                for context in contexts.values():context.close()
            finally:browser.close()

class RevisionTests(unittest.TestCase):
    def test_postgres_revision_import_and_frozen_evidence(self):
        with psycopg.connect(ADMIN,autocommit=True) as admin:
            admin.execute("CREATE DATABASE hpi_ingest_fixture")
            try:
                with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",autocommit=True) as conn:
                    initialise(conn)
                    one=import_revision(conn,"v1")
                    first=ImportedFixtureStore(conn,"v1")
                    saved=first.create(example_request())
                    self.assertEqual(import_revision(conn,"v1"),one)
                    self.assertEqual(conn.execute("SELECT count(*) FROM sale_transactions").fetchone()[0],3)
                    two=import_revision(conn,"v2")
                    self.assertNotEqual(one,two)
                    revised=ImportedFixtureStore(conn,"v2").create(example_request())
                    self.assertNotEqual([c["sale_price_usd"] for c in saved["comparables"]],[c["sale_price_usd"] for c in revised["comparables"]])
                    self.assertEqual(first.reopen(saved["investigation_id"]),saved)
                    self.assertEqual(address_candidates(first.connection,"v1","105 fictional way, demonstration district")["status"],"ambiguous")
                    with self.assertRaises(EvidenceStoreError):ImportedFixtureStore(conn,"v2").reopen(saved["investigation_id"])
                    conn.execute("DELETE FROM candidate_addresses WHERE snapshot_id=(SELECT snapshot_id FROM candidate_manifests WHERE role='address' AND revision='v1') AND pin='00000000000001'")
                    with self.assertRaises(ImportRefused):import_revision(conn,"v1")
            finally:admin.execute("DROP DATABASE hpi_ingest_fixture")
