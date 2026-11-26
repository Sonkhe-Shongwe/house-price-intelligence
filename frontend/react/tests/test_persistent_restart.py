"""Controlled real-browser restart of an explicitly private fictional SQLite file.

Check that two saved investigations, frozen sale hashes, shortlist members and
mutable notes remain byte-identical across stop/restart. Also prove refusal
to overwrite unfamiliar/symlink/corrupted files. Uses the canonical launcher and fixture persistence. No real properties or public network.
"""
from __future__ import annotations

import json
import os
import signal
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[3]
TESTS = Path(__file__).resolve().parent
SERVER = "backend.run_synthetic_api"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TESTS))

from backend.durable_fixture import FixturePersistenceError, open_file_demo  # noqa: E402
from backend.schema_migrations import SchemaMigrationError
from backend.synthetic_demo import example_request
from urllib.request import Request


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class LocalFixtureProcess:
    def __init__(self, port: int, *, database: Path | None, flags: bool = True, synthetic_map: bool = False, context_transport_fixture: bool = False):
        self.port=port
        self.base=f"http://127.0.0.1:{port}"
        args=[sys.executable, "-m", SERVER, "--port", str(port), "--frontend", "react"]
        if flags:
            args.append("--fixture-only")
        if synthetic_map:
            args.append("--synthetic-map")
        if context_transport_fixture:
            args.append("--context-transport-fixture")
        if database is not None:
            args.extend(["--fixture-db",str(database)])
        self.log=tempfile.TemporaryFile(mode="w+t",encoding="utf-8")
        self.proc=subprocess.Popen(args,cwd=ROOT,stdout=self.log,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+25
        while time.monotonic()<deadline:
            if self.proc.poll() is not None:
                self.log.seek(0)
                message=self.log.read()[-6500:]
                self.log.close()
                raise RuntimeError("Fixture preview refused to start: "+message)
            try:
                with urlopen(self.base+"/health",timeout=.4) as reply:
                    if reply.status==200:
                        return
            except OSError:
                time.sleep(.1)
        self.close()
        raise RuntimeError("Local preview never became healthy")

    def get(self,path):
        with urlopen(self.base+path,timeout=6) as response:
            return json.loads(response.read().decode("utf-8"))

    def close(self):
        if self.proc.poll() is None:
            # Gracefully interrupt the Python serve_forever loop on Linux, so
            # the WSGI context and SQLite connection finish their cleanup.
            if os.name == 'posix':
                self.proc.send_signal(signal.SIGINT)
            else:
                self.proc.terminate()
            try:self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)
        if not self.log.closed:
            self.log.close()


def frozen_database_rows(path:Path):
    db=sqlite3.connect(path)
    try:
        names={
            "frozen_results":"SELECT investigation_id, result_sha256, response_json FROM investigation_results ORDER BY investigation_id",
            "sale_provenance":"SELECT investigation_id, build_id, rank, transaction_id, source_snapshot_id, sale_price_usd_cents, explanation FROM comparable_evidence ORDER BY investigation_id, rank",
            "source_snapshots":"SELECT snapshot_id, dataset_id, source_query FROM source_snapshots ORDER BY snapshot_id",
            "shortlists":"SELECT shortlist_id, label, created_at_utc FROM shortlists ORDER BY shortlist_id",
            "members_notes":"SELECT shortlist_id, investigation_id, note_text FROM shortlist_investigations ORDER BY shortlist_id, investigation_id",
        }
        return {key:db.execute(sql).fetchall() for key,sql in names.items()}
    finally:
        db.close()


class RestartProof(unittest.TestCase):
    def test_browser_save_shortlist_notes_shutdown_reopen_unchanged(self):
        with tempfile.TemporaryDirectory(prefix="hpi-fictional-restart-") as folder:
            db_path=Path(folder)/"restart-fixture.sqlite3"
            port=free_port()
            server=LocalFixtureProcess(port,database=db_path)
            browser_driver=sync_playwright().start()
            options=({"executable_path":os.environ["HPI_BROWSER_EXECUTABLE"],
                      "args":["--no-sandbox"]}
                     if os.environ.get("HPI_BROWSER_EXECUTABLE") else {})
            browser=browser_driver.chromium.launch(headless=True,**options)
            page=browser.new_page(viewport={"width":1280,"height":840})
            remote=[];errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.on("request",lambda req:remote.append(req.url)
                    if not req.url.startswith(server.base+"/") else None)
            try:
                self.assertEqual(server.get("/v1/shortlists")["shortlists"],[])
                self.assertTrue(db_path.exists())
                self.assertFalse(db_path.stat().st_mode & 0o077)
                page.goto(server.base+"/buyer-workflow")
                expect(page.get_by_test_id("buyer-workflow")).to_be_visible(timeout=15000)

                def create(address, choice):
                    page.get_by_test_id("nav-investigate").click()
                    page.get_by_test_id("buyer-query").fill(address)
                    page.get_by_test_id("buyer-search").click()
                    expect(page.get_by_test_id("buyer-candidate")).to_have_count(
                        2 if "Court" in address else 1)
                    page.get_by_test_id("buyer-candidate").nth(choice).click()
                    expect(page.get_by_test_id("buyer-selected-parcel")).to_be_visible()
                    page.get_by_test_id("buyer-create").click()
                    expect(page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
                    iid=page.get_by_test_id("buyer-saved-id").inner_text()
                    page.get_by_test_id("nav-compare").click()
                    return iid

                first=create("101 Fictional Way",0)
                page.get_by_test_id("workspace-create").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("0 / 3")
                sid=page.get_by_test_id("workspace-id").inner_text()
                page.get_by_test_id("workspace-add-current").click()
                expect(page.get_by_test_id("workspace-entry")).to_have_count(1)
                second=create("105 Fictional Court",1)
                page.get_by_test_id("workspace-add-current").click()
                expect(page.get_by_test_id("workspace-entry")).to_have_count(2)
                page.get_by_test_id("workspace-entry").nth(0).get_by_test_id(
                    "workspace-note").fill("Review fictional price history first")
                page.get_by_test_id("workspace-entry").nth(0).get_by_test_id(
                    "workspace-save-note").click()
                expect(page.get_by_test_id("workspace-status")).to_contain_text(
                    "Note saved in Python SQLite")
                page.get_by_test_id("workspace-entry").nth(1).get_by_test_id(
                    "workspace-note").fill("Check the other parcel candidate")
                page.get_by_test_id("workspace-entry").nth(1).get_by_test_id(
                    "workspace-save-note").click()
                expect(page.get_by_test_id("workspace-entry").nth(1).get_by_test_id(
                    "workspace-note-state")).to_have_text("Saved note verified")
                self.assertNotEqual(first,second)
                first_doc=server.get("/v1/investigations/"+first)
                second_doc=server.get("/v1/investigations/"+second)
                first_shortlist=server.get("/v1/shortlists/"+sid)
                self.assertEqual(first_doc["comparables"][0]["sale_price_usd"],"525000.00")
                self.assertIsNone(first_doc["valuation"])
                self.assertEqual([e["investigation_id"] for e in first_shortlist["entries"]],
                                 [first,second])
                self.assertEqual([e["note_text"] for e in first_shortlist["entries"]],[
                    "Review fictional price history first",
                    "Check the other parcel candidate",
                ])
                pre_rows=frozen_database_rows(db_path)
                self.assertEqual(len(pre_rows["frozen_results"]),2)
                self.assertEqual(len(pre_rows["members_notes"]),2)
                self.assertTrue(all(len(r[1])==64 for r in pre_rows["frozen_results"]))
                # Release browser/network resources then shut down the actual
                # Python server process and close its SQLite connection.
                page.close()
                server.close()
                self.assertTrue(db_path.exists())

                restarted=LocalFixtureProcess(port,database=db_path)
                try:
                    self.assertEqual(restarted.get("/v1/investigations/"+first),first_doc)
                    self.assertEqual(restarted.get("/v1/investigations/"+second),second_doc)
                    self.assertEqual(restarted.get("/v1/shortlists/"+sid),first_shortlist)
                    self.assertEqual(frozen_database_rows(db_path),pre_rows)
                    reopened=browser.new_page(viewport={"width":1280,"height":840})
                    try:
                        reopened.goto(restarted.base+"/buyer-workflow")
                        expect(reopened.get_by_test_id("buyer-workflow")).to_be_visible()
                        reopened.get_by_test_id("buyer-reopen-id").fill(first)
                        reopened.get_by_test_id("buyer-reopen").click()
                        expect(reopened.get_by_test_id("buyer-saved-id")).to_have_text(first)
                        expect(reopened.get_by_test_id("buyer-sale").first).to_contain_text(
                            "$525,000.00")
                        expect(reopened.get_by_test_id("buyer-no-geometry")).to_be_visible()
                        reopened.get_by_test_id("nav-compare").click()
                        reopened.get_by_test_id("workspace-open-recent").click()
                        expect(reopened.get_by_test_id("workspace-entry")).to_have_count(2)
                        expect(reopened.get_by_test_id("workspace-note").nth(0)).to_have_value(
                            "Review fictional price history first")
                        expect(reopened.get_by_test_id("workspace-note").nth(1)).to_have_value(
                            "Check the other parcel candidate")
                        self.assertEqual(reopened.locator("canvas.maplibregl-canvas").count(),0)
                    finally:reopened.close()
                finally:restarted.close()
                self.assertEqual(remote,[])
                self.assertEqual(errors,[])
            finally:
                try:page.close()
                except Exception:pass
                server.close()
                browser.close()
                browser_driver.stop()

    def create_saved(self, server):
        req=Request(server.base+"/v1/investigations",data=json.dumps(example_request()).encode(),
                    headers={"Content-Type":"application/json"},method="POST")
        with urlopen(req,timeout=8) as response:
            return json.loads(response.read())

    def test_default_disposable_demo_resets(self):
        port=free_port()
        first=LocalFixtureProcess(port,database=None)
        try:
            saved=self.create_saved(first)
        finally:
            first.close()
        second=LocalFixtureProcess(port,database=None)
        try:
            with self.assertRaises(HTTPError) as caught:
                second.get("/v1/investigations/"+saved["investigation_id"])
            self.assertEqual(caught.exception.code,404)
        finally:second.close()

    def test_changed_source_sale_cents_refuse_restart_not_reseed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"tamper.sqlite3"
            port=free_port()
            original=LocalFixtureProcess(port,database=path)
            try:
                saved=self.create_saved(original)
                self.assertEqual(saved["comparables"][0]["sale_price_usd"],"525000.00")
            finally:original.close()
            before=frozen_database_rows(path)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE sale_transactions SET price_usd_cents=price_usd_cents+1 WHERE transaction_id='txn-2'")
            with self.assertRaisesRegex(RuntimeError,"trusted seed"):
                LocalFixtureProcess(port,database=path)
            self.assertEqual(frozen_database_rows(path),before)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("SELECT price_usd_cents FROM sale_transactions WHERE transaction_id='txn-2'").fetchone()[0],52500001)

    def test_unknown_and_symlink_are_refused_without_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            unknown=root/"foreign.sqlite3"
            with sqlite3.connect(unknown) as db:
                db.execute("CREATE TABLE foreign_user_records (secret TEXT)")
                db.execute("INSERT INTO foreign_user_records VALUES ('must-not-change')")
            os.chmod(unknown,0o600)
            original=unknown.read_bytes()
            with self.assertRaises((FixturePersistenceError,SchemaMigrationError)):
                open_file_demo(unknown,private_file=True)
            self.assertEqual(unknown.read_bytes(),original)
            link=root/"symlink.sqlite3"
            link.symlink_to(unknown)
            with self.assertRaises(FixturePersistenceError):
                open_file_demo(link,private_file=True)
            os.chmod(unknown,0o644)
            with self.assertRaisesRegex(FixturePersistenceError,"private"):
                open_file_demo(unknown,private_file=True)

    def test_missing_fixture_opt_in_refuses_startup(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"test.sqlite3"
            with self.assertRaisesRegex(RuntimeError,"explicit --fixture-only"):
                LocalFixtureProcess(free_port(),database=path,flags=False)
            self.assertFalse(path.exists())


if __name__=="__main__":
    unittest.main()
