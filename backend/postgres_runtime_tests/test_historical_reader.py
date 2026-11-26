"""Actual PostgreSQL permission/manifest rehearsal, invented records only."""
import copy
import os
import secrets
import unittest
import psycopg
from backend.postgres_ingestion import initialise
from backend.historical_postgres import import_historical
from backend.historical_migration import migrate_historical
from backend.historical_reader import ROLE, PrivateHistoricalReader, provision_reader, seal_historical, _verified
from backend.historical_postgres import _evaluate_verified
from backend.historical_beta_projection import project_rehearsal
from backend.curated_ingestion_candidate import ImportRefused
from test_historical_import import population
from backend.buyer_ownership import ROLE as BUYER, _prepare_empty_buyer_schema
from backend.private_beta_rehearsal import PrivateBetaRehearsal
from backend.oidc_boundary import OidcBoundary, AuthDenied
from psycopg import sql

ADMIN=os.environ["HPI_PG_DSN"]

class HistoricalReaderTests(unittest.TestCase):
    def test_migrate_seal_read_privileges_and_drift(self):
        with psycopg.connect(ADMIN,autocommit=True) as admin:
            admin.execute("CREATE DATABASE hpi_ingest_fixture")
            try:
                with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",autocommit=True) as conn:
                    initialise(conn)
                    migrate_historical(conn); migrate_historical(conn)
                    args=population()
                    build=import_historical(conn,**args)
                    seal=seal_historical(conn,**args)
                    self.assertEqual(seal["build_id"],build)
                    revised=copy.deepcopy(args);revised["rows"]["sales"][0]["sale_price"]="525000.02"
                    second=import_historical(conn,**revised)
                    self.assertNotEqual(second,build)
                    password=secrets.token_urlsafe(32)
                    provision_reader(conn,password)
                    with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=ROLE,password=password,autocommit=True) as rd:
                        reader=PrivateHistoricalReader(rd,seal)
                        match=reader.search("1 fictional court","2025-04-01")
                        self.assertEqual(match["status"],"one_eligible_candidate")
                        req={"township_code":"17","class_code":"203","analysis_date":"2025-04-01",
                             "subject":{"address_id":match["address_id"],"building_area_sqft":1600}}
                        result=reader.review(req)
                        self.assertEqual(result["selected_count"],3)
                        self.assertNotIn("comparables",result)
                        self.assertFalse(result["public_display_approved"])
                        self.assertIsNone(result["valuation"])
                        # Test-only projection: exact code-generated input, same sealed
                        # transaction and canonical matching result, no HTTP route.
                        with rd.transaction():
                            rd.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                            adapter,bid,ids,stamp=_verified(rd,seal)
                            evaluated=_evaluate_verified(adapter,bid,ids,stamp,req)
                            preview=project_rehearsal(*evaluated,ids)
                            self.assertEqual(preview["source_kind"],"historical_shape_rehearsal")
                            self.assertEqual(preview["selected_count"],result["selected_count"])
                            self.assertEqual(preview["status"],result["status"])
                            self.assertEqual([s["sale_price_usd"] for s in preview["sales"]],["525000.01"]*3)
                            self.assertEqual([s["assessment_year"] for s in preview["sales"]],[2024]*3)
                            self.assertEqual([s["assessed_area_sqft"] for s in preview["sales"]],[1600]*3)
                            self.assertFalse(preview["provenance"]["publisher_attributed"])
                            for forbidden in ("pin","document","latitude","longitude","address_id","relational_sha256"):
                                self.assertNotIn("'"+forbidden+"'",str(preview))
                            self.assertNotIn("FICT-",str(preview))
                            # Wrong source membership and duplicate transaction identities
                            # must not accidentally disclose a price.
                            with self.assertRaises(ImportRefused):
                                project_rehearsal(*evaluated,dict(ids,sales="wrong"))
                            broken=copy.deepcopy(evaluated)
                            key=next(iter(broken[2]))
                            broken[2][key].append(broken[2][key][0])
                            # Corrupt a selected key, not an arbitrary subject key.
                            first=broken[1][0]
                            key=(first["pin"],first["document"],first["sale_date"])
                            broken[2][key].append(broken[2][key][0])
                            with self.assertRaises(ImportRefused):
                                project_rehearsal(*broken,ids)
                        self.assertEqual(reader.review(req),result)
                        for statement in ("SELECT * FROM hpi_candidate.investigations",
                            "UPDATE hpi_candidate.sale_transactions SET price_usd_cents=1",
                            "INSERT INTO hpi_candidate.parcels VALUES ('00000000000009','17')",
                            "CREATE TABLE hpi_candidate.forbidden(x int)",
                            "CREATE TEMP TABLE forbidden(x int)"):
                            with self.subTest(statement=statement), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                                rd.execute(statement)
                        with self.assertRaises(ImportRefused):
                            PrivateHistoricalReader(rd,dict(seal,build_id=second)).review(req)
                        with self.assertRaises(ImportRefused):
                            seal_historical(rd,**args)
                        conn.execute("GRANT SELECT ON hpi_candidate.investigations TO "+ROLE)
                        with self.assertRaisesRegex(ImportRefused,"privilege drift"):
                            reader.review(req)
                        conn.execute("REVOKE SELECT ON hpi_candidate.investigations FROM "+ROLE)
                        conn.execute("GRANT SELECT(investigation_id) ON hpi_candidate.investigations TO "+ROLE)
                        with self.assertRaisesRegex(ImportRefused,"privilege drift"):
                            reader.review(req)
                        conn.execute("REVOKE SELECT(investigation_id) ON hpi_candidate.investigations FROM "+ROLE)
                        conn.execute("UPDATE hpi_candidate.historical_migrations SET script_sha256='wrong'")
                        with self.assertRaisesRegex(ImportRefused,"migration history"):
                            reader.review(req)
                        with self.assertRaises(ImportRefused):migrate_historical(conn)
                        # Restore exact known checksum via rollback of a deliberate change in future migrations;
                        # here the disposable test has already verified fail-closed migration.
                        from backend.historical_migration import SCRIPT
                        from hashlib import sha256
                        conn.execute("UPDATE hpi_candidate.historical_migrations SET script_sha256=%s",(sha256(SCRIPT.read_bytes()).hexdigest(),))
                        self.assertEqual(reader.review(req),result)
                        conn.execute("UPDATE hpi_candidate.sale_transactions SET price_usd_cents=price_usd_cents+1 WHERE snapshot_id IN (SELECT snapshot_id FROM hpi_candidate.curated_build_sources WHERE build_id=%s AND source_role='sales')",(build,))
                        with self.assertRaisesRegex(ImportRefused,"seal mismatch"):reader.review(req)
            finally:
                admin.execute("DROP DATABASE hpi_ingest_fixture")
                admin.execute("DROP ROLE IF EXISTS "+ROLE)

    def test_split_role_authenticated_save_and_reopen(self):
        with psycopg.connect(ADMIN,autocommit=True) as admin:
            self.assertEqual((admin.info.host,admin.info.dbname,admin.info.user),("127.0.0.1","hpi_fixture","postgres"))
            admin.execute("CREATE DATABASE hpi_ingest_fixture")
            try:
                with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",autocommit=True) as conn:
                    initialise(conn)
                    migrate_historical(conn)
                    args=population()
                    rp,bp=secrets.token_urlsafe(32),secrets.token_urlsafe(32)
                    provision_reader(conn,rp)
                    conn.execute("ALTER ROLE hpi_historical_reader NOLOGIN")
                    _prepare_empty_buyer_schema(conn)
                    from backend.neon_synthetic_seed import seed_statements
                    # Exercise the identical fixed seed plan against a disposable
                    # target, with the cloud target guard independently refused.
                    with self.assertRaises(psycopg.Error), conn.transaction():
                        for statement in seed_statements():
                            conn.execute(statement)
                    with conn.transaction():
                        for statement in seed_statements(disposable=True):
                            conn.execute(statement)
                    seal=seal_historical(conn,**args)
                    with self.assertRaises(psycopg.Error), conn.transaction():
                        for statement in seed_statements(disposable=True):
                            conn.execute(statement)
                    self.assertEqual(seal_historical(conn,**args),seal)
                    # Real restricted logins exist only in this disposable DB.
                    conn.execute("ALTER ROLE hpi_historical_reader LOGIN")
                    conn.execute(sql.SQL("ALTER ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(BUYER),sql.Literal(bp)))
                    boundary=OidcBoundary(issuer="https://issuer.invalid",client_id="fixture",authorize_endpoint="https://issuer.invalid/authorize",redirect_uri="https://127.0.0.1:8766/auth/callback",public_keys={"fixture":"not-used-in-session-rehearsal"},owner_map={"a":"fixture-owner-a","b":"fixture-owner-b"})
                    a=boundary._issue_session("fixture-owner-a")
                    b=boundary._issue_session("fixture-owner-b")
                    with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=ROLE,password=rp,autocommit=True) as rd, psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=BUYER,password=bp,autocommit=True) as wr:
                        from backend.neon_service_preflight import _inspect_services
                        report=_inspect_services(rd,wr,database="hpi_ingest_fixture")
                        self.assertEqual((report["reader_tables"],report["buyer_tables"]),(13,5))
                        self.assertTrue(report["read_only"])
                        svc=PrivateBetaRehearsal(rd,wr,seal,boundary)
                        match=PrivateHistoricalReader(rd,seal).search("1 fictional court","2025-04-01")
                        req={"township_code":"17","class_code":"203","analysis_date":"2025-04-01","subject":{"address_id":match["address_id"],"building_area_sqft":1600}}
                        with self.assertRaises(AuthDenied):
                            svc.create(req,cookie=a["cookie"],origin=boundary.origin,csrf=b["csrf"])
                        with self.assertRaises(ImportRefused):
                            svc.create(dict(req,subject=dict(req["subject"],pin="00000000000001")),cookie=a["cookie"],origin=boundary.origin,csrf=a["csrf"])
                        saved=svc.create(req,cookie=a["cookie"],origin=boundary.origin,csrf=a["csrf"])
                        iid=saved["investigation_id"]
                        self.assertEqual([s["sale_price_usd"] for s in saved["sales"]],["525000.01"]*3)
                        self.assertEqual(svc.reopen(iid,cookie=a["cookie"]),saved)
                        self._check_private_http_browser(rd,wr,seal,rp,bp)
                        # Existing records are invisible without owner context.
                        self.assertEqual(_inspect_services(rd,wr,database="hpi_ingest_fixture")["status"],"restricted_services_verified")

                        self.assertIsNone(wr.execute("SELECT nullif(current_setting('hpi.owner_id',true),'')").fetchone()[0])
                        with self.assertRaises(ImportRefused):
                            svc.reopen(iid,cookie=b["cookie"])
                        with self.assertRaises(AuthDenied):
                            svc.reopen(iid,cookie="")
                        self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.investigations").fetchone()[0],3)
                        # At April 1 the first parcel's same-day sale is ineligible
                        # for the second parcel, whose own sale is also excluded.
                        # Two remaining earlier sales are below the minimum of three.
                        self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.comparable_evidence").fetchone()[0],6)
                        self.assertEqual(conn.execute("""SELECT i.evidence_status,count(e.rank)
                            FROM hpi_candidate.investigations i
                            LEFT JOIN hpi_candidate.comparable_evidence e USING(investigation_id)
                            GROUP BY i.investigation_id,i.evidence_status
                            ORDER BY i.evidence_status,count(e.rank)""").fetchall(),
                            [("insufficient_data",0),("supported_neighbourhood",3),("supported_neighbourhood",3)])
                        self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.shortlists").fetchone()[0],1)
                        self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.shortlist_investigations").fetchone()[0],2)
                        for forbidden in ("FICT-","00000000000001","relational_sha256","address_id"):
                            self.assertNotIn(forbidden,str(saved))
                        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                            wr.execute("SELECT * FROM hpi_candidate.sale_transactions")
                        self._check_provider_buyer(conn,rd,wr,seal,iid)
                        conn.execute("UPDATE hpi_candidate.comparable_evidence SET sale_price_usd_cents=sale_price_usd_cents+1 WHERE investigation_id=%s AND rank=1",(iid,))
                        with self.assertRaisesRegex(ImportRefused,"Saved evidence mismatch"):
                            svc.reopen(iid,cookie=a["cookie"])
            finally:
                admin.execute("DROP DATABASE hpi_ingest_fixture")
                for role in (BUYER,ROLE):
                    admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))

    def _check_provider_buyer(self,admin,rd,wr,seal,other_id):
        # Exercise real signed-token validation, callback, CSRF and restricted SQL.
        # Only the confidential token endpoint response is mocked; never contact Auth0.
        import json
        import tempfile
        from io import BytesIO
        from email.message import Message
        from pathlib import Path
        from time import time
        from urllib.parse import parse_qs,urlsplit,urlencode
        from unittest.mock import MagicMock
        import jwt
        from jwt.algorithms import RSAAlgorithm
        from cryptography.hazmat.primitives.asymmetric import rsa
        from backend.oidc_provider_config import prepare_auth0,CALLBACK
        from backend.oidc_identity_http import buyer_identity_application,identity_only_application,ORIGIN
        from backend.auth0_invented_buyer import Auth0InventedBuyer
        from backend.react_assets import load_react_assets
        issuer="https://example-fixture.us.auth0.com/"
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        jwks={"keys":[dict(json.loads(RSAAlgorithm.to_jwk(key.public_key())),kid="pinned",use="sig",alg="RS256")]}
        with tempfile.TemporaryDirectory() as tmp:
            boundary,exchange=prepare_auth0(issuer=issuer,client_id="fixture",client_secret="x"*48,
                redirect_uri=CALLBACK,jwks=jwks,owner_by_subject={"auth0|alice":"provider-owner"},
                session_file=Path(tmp)/"provider.sqlite")
            admin.execute("INSERT INTO hpi_candidate.workspace_owners(owner_id) VALUES('provider-owner')")
            with self.assertRaises(ImportRefused):
                PrivateBetaRehearsal(rd,wr,seal,boundary)
            with self.assertRaises(ImportRefused):
                Auth0InventedBuyer(rd,wr,dict(seal,build_id="wrong"),boundary)
            service=Auth0InventedBuyer(rd,wr,seal,boundary)
            assets=load_react_assets()
            app=buyer_identity_application(boundary,exchange,service,assets)
            exchange._opener=MagicMock()
            def call(path,method="GET",**overrides):
                env={"REQUEST_METHOD":method,"PATH_INFO":path,"QUERY_STRING":"",
                     "REMOTE_ADDR":"127.0.0.1","HTTP_HOST":"127.0.0.1:8766","wsgi.url_scheme":"https"}
                env.update(overrides)
                reply=[]
                payload=b"".join(app(env,lambda status,headers:reply.extend((status,headers))))
                return int(reply[0].split()[0]),reply[1],payload
            page="/private-beta-rehearsal"
            prefix="/v1/private-beta-rehearsal"
            self.assertEqual(call(page)[0],401)
            self.assertEqual(call(page,REMOTE_ADDR="192.0.2.1")[0],403)
            status,headers,_=call("/auth/start","POST",HTTP_ORIGIN=ORIGIN)
            self.assertEqual(status,303)
            q=parse_qs(urlsplit(dict(headers)["Location"]).query)
            binding=dict(headers)["Set-Cookie"].split(";",1)[0]
            now=int(time())
            token=jwt.encode(dict(iss=issuer,sub="auth0|alice",aud="fixture",nonce=q["nonce"][0],
                iat=now,exp=now+300),key,algorithm="RS256",headers={"kid":"pinned"})
            response=exchange._opener.open.return_value.__enter__.return_value
            response.status=200;response.geturl.return_value=issuer+"oauth/token"
            response.headers=Message();response.headers["Content-Type"]="application/json"
            response.read.return_value=json.dumps({"id_token":token}).encode()
            status,headers,_=call("/auth/callback",QUERY_STRING=urlencode(
                {"code":"fictional-code","state":q["state"][0],"iss":issuer}),HTTP_COOKIE=binding,
                HTTP_SEC_FETCH_SITE="cross-site",HTTP_SEC_FETCH_MODE="navigate",HTTP_SEC_FETCH_DEST="document")
            self.assertEqual(status,303)
            cookie=next(v for k,v in headers if k=="Set-Cookie").split(";",1)[0]
            self.assertIn(b"Open buyer workspace",call("/",HTTP_COOKIE=cookie)[2])
            # Render actual WSGI response and its CSP in Chromium, with no network/provider request.
            from playwright.sync_api import sync_playwright,expect
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
                try:
                    visual=browser.new_page(viewport={"width":1440,"height":900})
                    errors=[]
                    visual.on("pageerror",lambda exc:errors.append(str(exc)))
                    def render(response):
                        code,headers,body=response
                        visual.unroute_all()
                        visual.route("**/*",lambda route:route.fulfill(status=code,headers=dict(headers),body=body) if route.request.url==ORIGIN+"/" else route.abort())
                        visual.goto(ORIGIN+"/")
                        self.assertEqual(visual.locator("body").evaluate("el=>getComputedStyle(el).backgroundColor"),"rgb(245, 242, 233)")
                    def shot(name):
                        folder=os.environ.get("HPI_RELEASE_SCREENSHOTS")
                        if folder:
                            Path(folder).mkdir(parents=True,exist_ok=True)
                            visual.screenshot(path=str(Path(folder)/("private-auth-"+name+".png")),full_page=True,animations="disabled")
                    render(call("/"))
                    expect(visual.get_by_role("heading",name="Look beyond the asking price.")).to_be_visible()
                    expect(visual.get_by_role("button",name="Sign in",exact=True)).to_be_visible()
                    visual.keyboard.press("Tab")
                    expect(visual.get_by_role("button",name="Sign in",exact=True)).to_be_focused()
                    shot("signin")
                    for width in (375,320):
                        visual.set_viewport_size({"width":width,"height":850})
                        self.assertTrue(visual.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
                        shot("signin-"+str(width))
                    visual.set_viewport_size({"width":1440,"height":900})
                    render(call("/",HTTP_COOKIE=cookie))
                    expect(visual.get_by_role("heading",name="Identity verified")).to_be_visible()
                    expect(visual.get_by_role("link",name="Open buyer workspace")).to_have_attribute("href",page)
                    expect(visual.get_by_role("button",name="Sign out")).to_be_visible()
                    shot("verified")
                    self.assertEqual(errors,[])
                finally:browser.close()
            self.assertEqual(call(page,HTTP_COOKIE=cookie)[0],200)
            self.assertEqual(call(page,HTTP_COOKIE=cookie,HTTP_SEC_FETCH_SITE="cross-site")[0],403)
            self.assertEqual(call(prefix+"/investigations/"+other_id,HTTP_COOKIE=cookie)[0],404)
            csrf=json.loads(call("/auth/session",HTTP_COOKIE=cookie)[2])["csrf"]
            def post(path,value,csrf_value=csrf):
                raw=json.dumps(value).encode()
                return call(prefix+path,"POST",HTTP_COOKIE=cookie,HTTP_ORIGIN=ORIGIN,HTTP_X_HPI_CSRF=csrf_value,
                    CONTENT_TYPE="application/json",CONTENT_LENGTH=str(len(raw)),**{"wsgi.input":BytesIO(raw)})
            query={"query":"1 Fictional Court","analysis_date":"2025-04-01"}
            self.assertEqual(post("/search",query,"wrong")[0],401)
            status,_,body=post("/search",query)
            self.assertEqual(status,200)
            match=json.loads(body)
            status,_,body=post("/investigations",{"township_code":"17","class_code":"203",
                "analysis_date":"2025-04-01","subject":{"address_id":match["address_id"],"building_area_sqft":1600}})
            self.assertEqual(status,201)
            saved=json.loads(body);own_path=prefix+"/investigations/"+saved["investigation_id"]
            self.assertEqual(saved["selected_count"],3)
            self.assertEqual(json.loads(call(own_path,HTTP_COOKIE=cookie)[2]),saved)
            status,_,body=post("/search",dict(query,query="2 Fictional Court"))
            self.assertEqual(status,200)
            status,_,body=post("/investigations",{"township_code":"17","class_code":"203",
                "analysis_date":"2025-04-01","subject":{"address_id":json.loads(body)["address_id"],"building_area_sqft":1600}})
            self.assertEqual(status,201)
            second=json.loads(body)
            self.assertEqual(second["selected_count"],0)
            status,_,body=post("/shortlists",{"label":"Provider comparison","entries":[
                {"investigation_id":saved["investigation_id"],"note_text":"First property"},
                {"investigation_id":second["investigation_id"],"note_text":"Second property"}]})
            self.assertEqual(status,201)
            comparison=json.loads(body)
            comparison_path=prefix+"/shortlists/"+comparison["shortlist_id"]
            # Reconstruct persistent identity and service without a new token exchange.
            resumed,exchange2=prepare_auth0(issuer=issuer,client_id="fixture",client_secret="x"*48,
                redirect_uri=CALLBACK,jwks=jwks,owner_by_subject={"auth0|alice":"provider-owner"},
                session_file=Path(tmp)/"provider.sqlite")
            app=buyer_identity_application(resumed,exchange2,Auth0InventedBuyer(rd,wr,seal,resumed),assets)
            self.assertEqual(json.loads(call(own_path,HTTP_COOKIE=cookie)[2]),saved)
            self.assertEqual(json.loads(call(comparison_path,HTTP_COOKIE=cookie)[2]),comparison)
            self.assertEqual(call(prefix+"/workspace")[0],401)
            status,_,body=call(prefix+"/workspace",HTTP_COOKIE=cookie)
            self.assertEqual(status,200)
            workspace=json.loads(body)
            self.assertEqual({i["investigation_id"] for i in workspace["investigations"]},{saved["investigation_id"],second["investigation_id"]})
            self.assertEqual([i["shortlist_id"] for i in workspace["comparisons"]],[comparison["shortlist_id"]])
            self.assertNotIn(other_id,body.decode())
            self.assertFalse(workspace["truncated"])
            self.assertEqual(call("/auth/logout","POST",HTTP_COOKIE=cookie,HTTP_ORIGIN=ORIGIN,HTTP_X_HPI_CSRF=csrf)[0],200)
            self.assertEqual(call(own_path,HTTP_COOKIE=cookie)[0],401)
            self.assertEqual(call(comparison_path,HTTP_COOKIE=cookie)[0],401)
            self.assertEqual(call(prefix+"/workspace",HTTP_COOKIE=cookie)[0],401)
            self.assertEqual(admin.execute("SELECT owner_id FROM hpi_candidate.investigations WHERE investigation_id=%s",
                (saved["investigation_id"],)).fetchone()[0],"provider-owner")
            exchange._opener.open.assert_called_once()

    def _check_private_http_browser(self,rd,wr,seal,rp,bp):
        import ssl
        import json
        from contextlib import ExitStack
        import subprocess
        import tempfile
        from pathlib import Path
        from threading import Thread
        from wsgiref.simple_server import make_server
        from backend.postgres_runtime import QuietHandler
        from backend.persistent_oidc import PersistentBoundary
        from backend.offline_oidc_http import application
        from backend.react_assets import load_react_assets
        from playwright.sync_api import sync_playwright,expect
        class TLSHandler(QuietHandler):
            def get_environ(self):
                env=super().get_environ();env["HTTPS"]="on";return env
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as fresh:
            path=Path(tmp);cert=path/"cert.pem";key=path/"key.pem"
            seal_path=path/"seal.json"
            # Invented seal only; the operator-owned temporary directory is 0700.
            fd=os.open(seal_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,"w",encoding="utf-8") as stream:
                json.dump(seal,stream)
            subprocess.run(["openssl","req","-x509","-newkey","rsa:2048","-nodes","-days","1","-subj","/CN=127.0.0.1","-addext","subjectAltName=IP:127.0.0.1","-keyout",str(key),"-out",str(cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            server=make_server("127.0.0.1",0,lambda e,s:[],handler_class=TLSHandler)
            base="https://127.0.0.1:"+str(server.server_port)
            def make_boundary():
                return PersistentBoundary(session_file=path/"sessions.sqlite",issuer="https://issuer.invalid",client_id="fixture",authorize_endpoint="https://issuer.invalid/authorize",redirect_uri=base+"/auth/callback",public_keys={"fixture":"not-used-in-session-rehearsal"},owner_map={"a":"fixture-owner-a","b":"fixture-owner-b"})
            boundary=make_boundary()
            seal_path.chmod(0o644)
            with self.assertRaises(ImportRefused):
                PrivateBetaRehearsal.from_seal_file(rd,wr,seal_path,boundary)
            seal_path.chmod(0o600)
            service=PrivateBetaRehearsal.from_seal_file(rd,wr,seal_path,boundary)
            server.set_app(application(None,load_react_assets(),boundary,lambda **kw:None,private_beta=service))
            tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.load_cert_chain(cert,key)
            server.socket=tls.wrap_socket(server.socket,server_side=True)
            thread=Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                with sync_playwright() as pw:
                    browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
                    try:
                        contexts=[]
                        for owner in ("fixture-owner-a","fixture-owner-b"):
                            cookie=boundary._issue_session(owner)["cookie"].split(";",1)[0]
                            name,value=cookie.split("=",1)
                            ctx=browser.new_context(ignore_https_errors=True)
                            ctx.add_cookies([{"name":name,"value":value,"url":base,"secure":True,"httpOnly":True,"sameSite":"Lax"}])
                            contexts.append(ctx)
                        page=contexts[0].new_page()
                        # Disposable invented fixtures only. Mask recovery identifiers; never capture auth/cookies.
                        from pathlib import Path
                        shots=os.environ.get("HPI_RELEASE_SCREENSHOTS")
                        def shot(name,locator=None):
                            if not shots:return
                            folder=Path(shots);folder.mkdir(parents=True,exist_ok=True)
                            mask=[page.get_by_test_id("beta-id"),page.get_by_test_id("beta-comparison-id")]
                            target=str(folder/("private-"+name+".png"))
                            if locator is None:page.screenshot(path=target,full_page=True,mask=mask,animations="disabled")
                            else:locator.screenshot(path=target,mask=mask,animations="disabled")
                        page.set_viewport_size({"width":1440,"height":1000})
                        page.goto(base+"/private-beta-rehearsal")
                        expect(page.get_by_test_id("beta-nav-home")).to_have_attribute("aria-current","page")
                        expect(page.get_by_test_id("beta-workspace")).to_be_visible(timeout=15000)
                        expect(page.get_by_test_id("beta-search")).not_to_be_visible()
                        shot("workspace")
                        page.get_by_test_id("beta-new-investigation").click()
                        page.get_by_test_id("beta-search").click()
                        expect(page.get_by_test_id("beta-match")).to_have_text("One eligible parcel candidate")
                        expect(page.get_by_test_id("beta-operation")).to_have_text("Parcel search complete.")
                        page.get_by_test_id("beta-create").click()
                        expect(page.get_by_test_id("beta-result")).to_be_visible(timeout=15000)
                        expect(page.get_by_test_id("beta-sale")).to_have_count(3)
                        expect(page.get_by_test_id("beta-sale").first).to_contain_text("525,000.01")
                        expect(page.get_by_test_id("beta-result")).to_contain_text("1,600 sq ft")
                        expect(page.get_by_test_id("beta-geometry-unavailable")).to_be_visible()
                        expect(page.get_by_test_id("beta-operation")).to_have_text("Investigation saved and validated.")
                        expect(page.get_by_test_id("profile-age")).to_have_text("87 days earlier")
                        page.get_by_test_id("evidence-jump").click()
                        expect(page.get_by_test_id("beta-result")).to_be_focused()
                        expect(page.get_by_test_id("evidence-position")).to_have_text("Sale 1 of 3")
                        page.get_by_test_id("evidence-next").focus()
                        page.keyboard.press("Enter")
                        expect(page.get_by_test_id("evidence-next")).to_be_focused()
                        expect(page.get_by_test_id("evidence-position")).to_have_text("Sale 2 of 3")
                        page.get_by_role("button",name="Inspect comparable 2",exact=True).click()
                        expect(page.get_by_test_id("profile-age")).to_have_text("88 days earlier")
                        expect(page.get_by_test_id("profile-difference")).to_have_text("0%")
                        expect(page.get_by_test_id("beta-sale").nth(1)).to_have_attribute("data-selected","true")
                        profile=page.get_by_test_id("evidence-profile")
                        self.assertTrue(profile.evaluate("""el=>Array.from(el.querySelectorAll('svg')).every(svg=>{
                            const track=svg.querySelector('.ep-track').getBoundingClientRect();
                            const box=svg.getBoundingClientRect();
                            return Math.abs(track.width-box.width)<1 && Math.abs(track.left-box.left)<1;
                        })"""))
                        shot("supported-dossier",page.get_by_test_id("beta-result"))
                        shot("investigation-full")
                        for width,height in ((1440,1000),(1366,850),(1024,768),(768,1024),(375,850),(320,800),(800,375)):
                            page.set_viewport_size({"width":width,"height":height})
                            self.assertTrue(page.evaluate("document.documentElement.scrollWidth<=innerWidth+2"),f"private dossier overflow at {width}x{height}")
                            expect(page.get_by_test_id("beta-sale").first).to_contain_text("525,000.01")
                            self.assertGreaterEqual(page.get_by_test_id("evidence-next").bounding_box()["height"],44)
                            if width in (1024,768,320):shot("dossier-"+str(width),page.get_by_test_id("beta-result"))
                        page.set_viewport_size({"width":375,"height":850})
                        table=page.get_by_role("region",name="Eligible sales table, scroll horizontally if needed")
                        expect(table).to_have_accessible_description("More columns: scroll sideways or focus the table and use arrow keys.")
                        recovery=page.get_by_test_id("beta-investigation-recovery")
                        expect(recovery).not_to_have_attribute("open","")
                        recovery.locator("summary").focus();page.keyboard.press("Enter")
                        expect(page.get_by_test_id("beta-id")).to_be_visible()
                        page.keyboard.press("Enter")
                        expect(recovery).not_to_have_attribute("open","")
                        table.focus()
                        expect(table).to_be_focused()
                        shot("supported-dossier-375",page.get_by_test_id("beta-result"))
                        page.set_viewport_size({"width":1440,"height":1000})
                        iid=page.get_by_test_id("beta-id").input_value()
                        page.get_by_test_id("beta-add-comparison").click()
                        page.locator("#beta-note-0").fill("First property note")
                        page.get_by_test_id("beta-nav-investigate").click()
                        page.locator("#beta-address").fill("2 Fictional Court")
                        page.get_by_test_id("beta-search").click()
                        expect(page.get_by_test_id("beta-match")).to_have_text("One eligible parcel candidate")
                        page.locator("#beta-price").fill("600000.02")
                        page.get_by_test_id("beta-create").click()
                        expect(page.get_by_test_id("beta-result")).to_be_visible(timeout=15000)
                        expect(page.get_by_test_id("beta-result")).to_contain_text("0 eligible sales")
                        expect(page.get_by_test_id("beta-result")).to_contain_text("insufficient data")
                        expect(page.get_by_test_id("beta-sale")).to_have_count(0)
                        expect(page.get_by_test_id("evidence-profile")).to_have_count(0)
                        expect(page.get_by_test_id("evidence-navigation")).to_have_count(0)
                        shot("insufficient-dossier",page.get_by_test_id("beta-result"))
                        second=page.get_by_test_id("beta-id").input_value()
                        self.assertNotEqual(iid,second)
                        page.get_by_test_id("beta-add-comparison").click()
                        page.get_by_test_id("beta-save-comparison").click()
                        expect(page.get_by_test_id("beta-comparison")).to_contain_text("600,000.02")
                        expect(page.get_by_test_id("beta-comparison")).to_contain_text("First property note")
                        expect(page.get_by_test_id("beta-comparison")).to_contain_text("insufficient data")
                        sid=page.get_by_test_id("beta-comparison-id").input_value()
                        frozen=page.get_by_test_id("beta-comparison")
                        expect(page.get_by_test_id("beta-operation")).to_have_text("Comparison snapshot saved.")
                        expect(frozen.get_by_role("columnheader")).to_have_count(3)
                        expect(frozen.get_by_role("rowheader",name="Buyer-reported area")).to_be_visible()
                        expect(frozen.get_by_role("rowheader",name="Valuation")).to_be_visible()
                        shot("comparison",frozen)
                        shot("comparison-full")
                        page.locator("#beta-note-0").fill("Unsaved draft change")
                        expect(frozen).to_contain_text("First property note")
                        expect(frozen).not_to_contain_text("Unsaved draft change")
                        original_viewport=page.viewport_size
                        for width,height in ((1440,1000),(1366,850),(1024,768),(768,1024),(375,850),(320,800),(800,375)):
                            page.set_viewport_size({"width":width,"height":height})
                            self.assertTrue(page.evaluate("document.documentElement.scrollWidth<=innerWidth+2"))
                            region=frozen.get_by_role("region")
                            self.assertTrue(region.evaluate("e=>e.scrollWidth<=e.clientWidth+1"))
                            expect(frozen).to_contain_text("600,000.02")
                            if width in (1024,768,375,320):shot("comparison-"+str(width),frozen)
                        if original_viewport:page.set_viewport_size(original_viewport)
                        page.locator("#beta-note-0").fill("First property note")
                        # Reconstruct the service and identity boundary without
                        # reimporting data, reissuing cookies or reusing DB sessions.
                        new_reader=fresh.enter_context(psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=ROLE,password=rp,autocommit=True))
                        new_writer=fresh.enter_context(psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=BUYER,password=bp,autocommit=True))
                        self.assertNotEqual(rd.info.backend_pid,new_reader.info.backend_pid)
                        self.assertNotEqual(wr.info.backend_pid,new_writer.info.backend_pid)
                        resumed_boundary=make_boundary()
                        # A syntactically valid but incorrect external seal must
                        # fail startup instead of silently accepting stored evidence.
                        seal_path.write_text(json.dumps(dict(seal,relational_sha256="0"*64)))
                        with self.assertRaises(ImportRefused):
                            PrivateBetaRehearsal.from_seal_file(new_reader,new_writer,seal_path,resumed_boundary)
                        seal_path.write_text(json.dumps(seal))
                        resumed=PrivateBetaRehearsal.from_seal_file(new_reader,new_writer,seal_path,resumed_boundary)
                        server.set_app(application(None,load_react_assets(),resumed_boundary,lambda **kw:None,private_beta=resumed))
                        page.reload()
                        expect(page.get_by_test_id("beta-workspace")).to_be_visible(timeout=15000)
                        page.emulate_media(reduced_motion="reduce")
                        page.get_by_test_id("beta-nav-saved").click()
                        expect(page.get_by_test_id("beta-workspace-investigation")).not_to_have_count(0)
                        self.assertEqual(page.locator(".pw-view:not([hidden])").evaluate("el=>getComputedStyle(el).animationName"),"none")
                        self.assertEqual(page.evaluate("window.scrollY"),0)
                        page.emulate_media(reduced_motion="no-preference")
                        # Exercise ID-free reopening of a saved investigation, then the known recovery path.
                        page.get_by_test_id("beta-workspace-investigation").first.click()
                        expect(page.get_by_test_id("beta-result")).to_be_visible(timeout=15000)
                        page.get_by_test_id("beta-id").fill(iid)
                        page.get_by_test_id("beta-reopen").click()
                        expect(page.get_by_test_id("beta-sale")).to_have_count(3)
                        expect(page.get_by_test_id("beta-sale").first).to_contain_text("525,000.01")
                        self.assertIsNone(new_writer.execute("SELECT nullif(current_setting(\'hpi.owner_id\',true),\'\')").fetchone()[0])
                        page.get_by_test_id("beta-nav-saved").click()
                        expect(page.get_by_test_id("beta-workspace-comparison")).not_to_have_count(0)
                        expect(page.get_by_test_id("beta-workspace")).to_contain_text("UTC")
                        shot("saved-workspace")
                        page.get_by_test_id("beta-workspace-comparison").first.click()
                        expect(page.get_by_test_id("beta-comparison")).to_be_visible(timeout=15000)
                        page.get_by_test_id("beta-comparison-id").fill(sid)
                        page.get_by_test_id("beta-reopen-comparison").click()
                        expect(page.get_by_test_id("beta-comparison")).to_contain_text("600,000.02")
                        expect(page.get_by_test_id("beta-comparison")).to_contain_text("525,000.01")
                        expect(page.get_by_test_id("beta-comparison")).to_contain_text("First property note")
                        expect(page.get_by_test_id("beta-comparison")).to_contain_text("insufficient data")
                        # Another investigation of the first parcel already exists.
                        # Reject distinct investigation IDs that identify the same parcel.
                        auth=resumed_boundary._issue_session("fixture-owner-a")
                        from backend.synthetic_shortlists import ShortlistError
                        with new_writer.transaction():
                            new_writer.execute("SET LOCAL search_path TO hpi_candidate,pg_catalog")
                            new_writer.execute("SELECT set_config('hpi.owner_id','fixture-owner-a',true)")
                            duplicates=new_writer.execute("SELECT investigation_id FROM investigations WHERE investigation_id<>%s AND investigation_id<>%s",(iid,second)).fetchall()
                        self.assertEqual(len(duplicates),1)
                        with self.assertRaisesRegex(ShortlistError,"duplicate_property"):
                            resumed.create_comparison({"label":"Duplicate","entries":[{"investigation_id":iid},{"investigation_id":duplicates[0][0]}]},cookie=auth["cookie"],origin=resumed_boundary.origin,csrf=auth["csrf"])
                        other=contexts[1].new_page()
                        other.goto(base+"/private-beta-rehearsal")
                        expect(other.get_by_test_id("beta-workspace")).to_be_visible(timeout=15000)
                        expect(other.get_by_test_id("beta-workspace-comparison")).to_have_count(0)
                        other.get_by_test_id("beta-nav-investigate").click()
                        other.get_by_test_id("beta-id").fill(iid)
                        other.get_by_test_id("beta-reopen").click()
                        expect(other.get_by_test_id("beta-error")).to_be_visible()
                        self.assertEqual(other.get_by_test_id("beta-result").count(),0)
                        other.get_by_test_id("beta-nav-compare").click()
                        other.get_by_test_id("beta-comparison-id").fill(sid)
                        other.get_by_test_id("beta-reopen-comparison").click()
                        expect(other.get_by_test_id("beta-error")).to_be_visible()
                        self.assertEqual(other.get_by_test_id("beta-comparison").count(),0)
                        # A second tab must clear its authenticated subtree on a genuine session rejection.
                        stale=contexts[0].new_page()
                        stale.goto(base+'/private-beta-rehearsal')
                        expect(stale.get_by_test_id('beta-workspace')).to_be_visible()
                        stale.get_by_test_id('beta-workspace-comparison').first.click()
                        expect(stale.get_by_test_id('beta-comparison')).to_be_visible()
                        # Browser sign-out must clear the displayed evidence and revoke the old session.
                        old_cookie=next(c for c in contexts[0].cookies() if c['name']=='__Host-hpi_session')
                        page.get_by_test_id("beta-sign-out").click()
                        expect(page.get_by_role("heading",name="Signed out")).to_be_visible()
                        self.assertEqual(page.get_by_test_id("beta-result").count(),0)
                        self.assertEqual(page.get_by_test_id("beta-comparison").count(),0)
                        with self.assertRaises(AuthDenied):
                            resumed_boundary.authorize(cookie=old_cookie['name']+'='+old_cookie['value'],method='GET')
                        stale.get_by_test_id('beta-nav-saved').click()
                        expect(stale.get_by_test_id('beta-session-recovery')).to_be_visible()
                        expect(stale.get_by_test_id('beta-session-recovery')).to_be_focused()
                        expect(stale.get_by_test_id('beta-comparison')).to_have_count(0)
                        expect(stale.get_by_test_id('beta-workspace')).to_have_count(0)
                        expect(stale.locator('#beta-note-0')).to_have_count(0)
                        expect(stale.get_by_role('link',name='Return to sign in')).to_have_attribute('href','/')
                        stale.close()
                        # Revocation is session-specific, and does not delete durable buyer records.
                        self.assertEqual(resumed.reopen_comparison(sid,cookie=auth['cookie'])['shortlist_id'],sid)
                        for ctx in contexts:ctx.close()
                    finally:browser.close()
            finally:server.shutdown();server.server_close();thread.join(timeout=5)
