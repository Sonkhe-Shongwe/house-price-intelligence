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
from backend.postgres_runtime import bootstrap,ROLE
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
