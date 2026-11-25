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
                    import_historical(conn,**args)
                    seal=seal_historical(conn,**args)
                    rp,bp=secrets.token_urlsafe(32),secrets.token_urlsafe(32)
                    provision_reader(conn,rp)
                    _prepare_empty_buyer_schema(conn)
                    conn.execute("INSERT INTO hpi_candidate.workspace_owners VALUES ('fixture-owner-a'),('fixture-owner-b')")
                    # A real restricted login is used only in the disposable DB.
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
                        self._check_private_http_browser(rd,wr,seal)
                        # Existing records are invisible without owner context.
                        self.assertEqual(_inspect_services(rd,wr,database="hpi_ingest_fixture")["status"],"restricted_services_verified")

                        self.assertIsNone(wr.execute("SELECT nullif(current_setting('hpi.owner_id',true),'')").fetchone()[0])
                        with self.assertRaises(ImportRefused):
                            svc.reopen(iid,cookie=b["cookie"])
                        with self.assertRaises(AuthDenied):
                            svc.reopen(iid,cookie="")
                        self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.investigations").fetchone()[0],2)
                        self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.comparable_evidence").fetchone()[0],6)
                        for forbidden in ("FICT-","00000000000001","relational_sha256","address_id"):
                            self.assertNotIn(forbidden,str(saved))
                        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                            wr.execute("SELECT * FROM hpi_candidate.sale_transactions")
                        conn.execute("UPDATE hpi_candidate.comparable_evidence SET sale_price_usd_cents=sale_price_usd_cents+1 WHERE investigation_id=%s AND rank=1",(iid,))
                        with self.assertRaisesRegex(ImportRefused,"Saved evidence mismatch"):
                            svc.reopen(iid,cookie=a["cookie"])
            finally:
                admin.execute("DROP DATABASE hpi_ingest_fixture")
                for role in (BUYER,ROLE):
                    admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))

    def _check_private_http_browser(self,rd,wr,seal):
        import ssl
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
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);cert=path/"cert.pem";key=path/"key.pem"
            subprocess.run(["openssl","req","-x509","-newkey","rsa:2048","-nodes","-days","1","-subj","/CN=127.0.0.1","-addext","subjectAltName=IP:127.0.0.1","-keyout",str(key),"-out",str(cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            server=make_server("127.0.0.1",0,lambda e,s:[],handler_class=TLSHandler)
            base="https://127.0.0.1:"+str(server.server_port)
            boundary=PersistentBoundary(session_file=path/"sessions.sqlite",issuer="https://issuer.invalid",client_id="fixture",authorize_endpoint="https://issuer.invalid/authorize",redirect_uri=base+"/auth/callback",public_keys={"fixture":"not-used-in-session-rehearsal"},owner_map={"a":"fixture-owner-a","b":"fixture-owner-b"})
            service=PrivateBetaRehearsal(rd,wr,seal,boundary)
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
                        page.goto(base+"/private-beta-rehearsal")
                        page.get_by_test_id("beta-search").click()
                        expect(page.get_by_test_id("beta-match")).to_have_text("One eligible parcel candidate")
                        page.get_by_test_id("beta-create").click()
                        expect(page.get_by_test_id("beta-result")).to_be_visible(timeout=15000)
                        expect(page.get_by_test_id("beta-sale")).to_have_count(3)
                        expect(page.get_by_test_id("beta-sale").first).to_contain_text("525,000.01")
                        iid=page.get_by_test_id("beta-id").input_value()
                        page.reload()
                        page.get_by_test_id("beta-id").fill(iid)
                        page.get_by_test_id("beta-reopen").click()
                        expect(page.get_by_test_id("beta-sale")).to_have_count(3)
                        other=contexts[1].new_page()
                        other.goto(base+"/private-beta-rehearsal")
                        other.get_by_test_id("beta-id").fill(iid)
                        other.get_by_test_id("beta-reopen").click()
                        expect(other.get_by_test_id("beta-error")).to_be_visible()
                        self.assertEqual(other.get_by_test_id("beta-result").count(),0)
                        for ctx in contexts:ctx.close()
                    finally:browser.close()
            finally:server.shutdown();server.server_close();thread.join(timeout=5)
