"""Real Chrome -> gated fictional shortlist writes -> Python WSGI -> SQLite.

The canonical fixture-only launcher exposes the existing P6 contract. Frozen
P3 sale evidence and source build hashes may never be modified by the client.
"""
from __future__ import annotations

from contextlib import closing
import copy
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SERVER = "backend.run_synthetic_api"


class ReactSavedComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:
            sk.bind(("127.0.0.1", 0))
            cls.port = sk.getsockname()[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.server = subprocess.Popen([
            sys.executable, "-m", SERVER, "--port", str(cls.port),
            "--fixture-only", "--frontend", "react",
        ], cwd=ROOT, stdout=cls.log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 27
            while time.monotonic() < deadline:
                if cls.server.poll() is not None:
                    cls.log.seek(0)
                    raise RuntimeError("Opt-in shortlist preview exited: " + cls.log.read()[-4000:])
                try:
                    with urlopen(cls.base + "/health",timeout=.4) as r:
                        if r.status==200: break
                except OSError:time.sleep(.15)
            else:raise RuntimeError("Shortlist preview did not start")
            cls.playwright = sync_playwright().start()
            opts=({"executable_path":os.environ["HPI_BROWSER_EXECUTABLE"],"args":["--no-sandbox"]}
                  if os.environ.get("HPI_BROWSER_EXECUTABLE") else {})
            cls.browser=cls.playwright.chromium.launch(headless=True,**opts)
        except Exception:
            cls.server.terminate()
            cls.server.wait(timeout=5)
            cls.log.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.terminate()
        try:cls.server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.server.kill()
            cls.server.wait(timeout=5)
        cls.log.close()

    def setUp(self):
        self.context=self.browser.new_context(viewport={"width":1440,"height":900})
        self.page=self.context.new_page()
        self.js_errors=[]
        self.remote=[]
        self.gpu=[]
        self.page.on("pageerror",lambda err:self.js_errors.append(str(err)))
        self.page.on("request",lambda req:self.remote.append(req.url)
                     if not req.url.startswith(self.base+"/") else None)
        self.page.on("request",lambda req:self.gpu.append(req.url)
                     if "VectorMap-" in req.url or "maplibre-gl-worker-" in req.url else None)
        self.page.goto(self.base+"/buyer-workflow")
        self.page.get_by_test_id("nav-compare").click()
        expect(self.page.get_by_test_id("workspace")).to_be_visible(timeout=15000)
        expect(self.page.get_by_test_id("workspace-create")).to_be_enabled()

    def tearDown(self):
        self.assertEqual(self.js_errors,[],"Browser must have no uncaught JS errors")
        self.assertEqual(self.remote,[],"No external network requests")
        self.assertEqual(self.gpu,[],"No invented geo-renderer requested by source-backed buyer UI")
        self.context.close()

    def create_investigation(self, address="101 Fictional Way", option=0):
        self.page.get_by_test_id("nav-investigate").click()
        self.page.get_by_test_id("buyer-query").fill(address)
        self.page.get_by_test_id("buyer-search").click()
        count=2 if "Court" in address else 1
        expect(self.page.get_by_test_id("buyer-candidate")).to_have_count(count)
        self.page.get_by_test_id("buyer-candidate").nth(option).click()
        expect(self.page.get_by_test_id("buyer-selected-parcel")).to_be_visible()
        self.page.get_by_test_id("buyer-create").click()
        expect(self.page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
        iid=self.page.get_by_test_id("buyer-saved-id").inner_text()
        self.page.get_by_test_id("nav-compare").click()
        return iid

    def create_workspace(self,label="My fictional homes"):
        self.page.get_by_test_id("workspace-label").fill(label)
        self.page.get_by_test_id("workspace-create").click()
        expect(self.page.get_by_test_id("workspace-count")).to_have_text("0 / 3")
        expect(self.page.get_by_test_id("workspace-empty")).to_be_visible()
        return self.page.get_by_test_id("workspace-id").inner_text()

    def add_current(self,count):
        expect(self.page.get_by_test_id("workspace-add-current")).to_be_enabled()
        self.page.get_by_test_id("workspace-add-current").click()
        expect(self.page.get_by_test_id("workspace-entry")).to_have_count(count)
        expect(self.page.get_by_test_id("workspace-count")).to_have_text(f"{count} / 3")
        expect(self.page.get_by_test_id("workspace-status")).to_contain_text("preserved")

    def get_shortlist(self,sid):
        response=self.page.request.get(self.base+"/v1/shortlists/"+sid)
        self.assertEqual(response.status,200)
        return response.json()

    def test_create_and_add_current_investigation(self):
        iid=self.create_investigation()
        sid=self.create_workspace()
        self.add_current(1)
        saved=self.get_shortlist(sid)
        self.assertEqual(saved["source_kind"],"synthetic_fixture")
        self.assertEqual(saved["max_entries"],3)
        self.assertEqual(saved["entries"][0]["investigation_id"],iid)
        self.assertEqual(saved["entries"][0]["note_text"],"")
        self.assertEqual(saved["entries"][0]["investigation"]["comparables"][0]["sale_price_usd"],
                         "525000.00")
        self.assertIsNone(saved["entries"][0]["investigation"]["valuation"])
        expect(self.page.get_by_test_id("workspace-note").first).to_have_value("")

    def test_two_independent_properties_saved_note_and_frozen_sale_evidence(self):
        first=self.create_investigation()
        sid=self.create_workspace("Weekend property comparison")
        self.add_current(1)
        before=self.get_shortlist(sid)
        second=self.create_investigation("105 Fictional Court",option=1)
        self.assertNotEqual(first,second)
        self.add_current(2)
        after_add=self.get_shortlist(sid)
        self.assertEqual(after_add["entries"][0]["investigation"],before["entries"][0]["investigation"])
        self.assertEqual(after_add["entries"][0]["match_policy_version"],before["entries"][0]["match_policy_version"])
        first_card=self.page.get_by_test_id("workspace-entry").first
        first_card.get_by_test_id("workspace-note").fill("Check historical maintenance receipts")
        expect(first_card.get_by_test_id("workspace-note-state")).to_have_text("Unsaved changes")
        first_card.get_by_test_id("workspace-save-note").click()
        expect(first_card.get_by_test_id("workspace-note-state")).to_have_text("Saved note verified")
        expect(self.page.get_by_test_id("workspace-status")).to_contain_text(
            "Note saved in Python SQLite")
        after_note=self.get_shortlist(sid)
        self.assertEqual(after_note["entries"][0]["note_text"],
                         "Check historical maintenance receipts")
        for old,new in zip(after_add["entries"],after_note["entries"]):
            self.assertEqual(old["investigation"],new["investigation"])
            self.assertEqual(old["match_policy_version"],new["match_policy_version"])
        self.page.reload()
        self.page.get_by_test_id("nav-compare").click()
        expect(self.page.get_by_test_id("workspace-create")).to_be_visible()
        self.page.get_by_test_id("workspace-reopen-id").fill(sid)
        self.page.get_by_test_id("workspace-reopen").click()
        expect(self.page.get_by_test_id("workspace-entry")).to_have_count(2)
        expect(self.page.get_by_test_id("workspace-note").first).to_have_value(
            "Check historical maintenance receipts")

    def test_duplicate_property_across_independent_investigations(self):
        self.create_investigation()
        sid=self.create_workspace()
        self.add_current(1)
        self.create_investigation("101 Fictional Way")
        expect(self.page.get_by_test_id("workspace-add-current")).to_be_disabled()
        self.assertEqual(self.get_shortlist(sid)["entries"][0]["investigation"]["subject"]["pin"],
                         "00000000000001")
        iid=self.page.get_by_test_id("buyer-saved-id").inner_text()
        response=self.page.request.post(self.base+"/v1/shortlists/"+sid+"/entries",
                                         data={"investigation_id":iid,"note_text":""})
        self.assertEqual(response.status,409)
        self.assertEqual(response.json()["error"],"duplicate_property")
        expect(self.page.get_by_test_id("workspace-entry")).to_have_count(1)

    def test_add_existing_uuid_then_reject_duplicate_investigation(self):
        first=self.create_investigation()
        sid=self.create_workspace()
        self.add_current(1)
        second=self.create_investigation("105 Fictional Court",option=0)
        self.page.get_by_test_id("workspace-other-id").fill(second)
        self.page.get_by_test_id("workspace-add-id").click()
        expect(self.page.get_by_test_id("workspace-entry")).to_have_count(2)
        self.page.get_by_test_id("workspace-other-id").fill(first)
        self.page.get_by_test_id("workspace-add-id").click()
        expect(self.page.get_by_test_id("workspace-error")).to_contain_text(
            "already on the shortlist")
        expect(self.page.get_by_test_id("workspace-entry")).to_have_count(2)

    def test_three_property_limit_is_enforced_by_ui_and_python(self):
        self.create_investigation("101 Fictional Way")
        sid=self.create_workspace()
        self.add_current(1)
        self.create_investigation("105 Fictional Court",option=0)
        self.add_current(2)
        self.create_investigation("105 Fictional Court",option=1)
        self.add_current(3)
        expect(self.page.get_by_test_id("workspace-add-current")).to_be_disabled()
        expect(self.page.get_by_test_id("workspace-add-id")).to_be_disabled()
        payload={"subject":{"pin":"00000000000099","building_area_sqft":1600,
                "asking_price_usd":"500000.00","label":"Unknown synthetic parcel"},
                 "township_code":"17","class_code":"203","analysis_date":"2024-07-01"}
        created=self.page.request.post(self.base+"/v1/investigations",data=payload)
        self.assertEqual(created.status,201)
        fourth=created.json()["investigation_id"]
        reply=self.page.request.post(self.base+"/v1/shortlists/"+sid+"/entries",
                                     data={"investigation_id":fourth})
        self.assertEqual(reply.status,409)
        self.assertEqual(reply.json()["error"],"shortlist_full")
        self.assertEqual(len(self.get_shortlist(sid)["entries"]),3)

    def test_saving_one_note_preserves_another_unsaved_draft(self):
        self.create_investigation()
        sid=self.create_workspace()
        self.add_current(1)
        self.create_investigation("105 Fictional Court",option=1)
        self.add_current(2)
        cards=self.page.get_by_test_id("workspace-entry")
        first=cards.nth(0)
        second=cards.nth(1)
        first.get_by_test_id("workspace-note").fill("First note committed")
        second.get_by_test_id("workspace-note").fill("Second note still a draft")
        first.get_by_test_id("workspace-save-note").click()
        expect(first.get_by_test_id("workspace-note-state")).to_have_text("Saved note verified")
        expect(second.get_by_test_id("workspace-note")).to_have_value("Second note still a draft")
        expect(second.get_by_test_id("workspace-note-state")).to_have_text("Unsaved changes")
        recorded=self.get_shortlist(sid)
        self.assertEqual(recorded["entries"][0]["note_text"],"First note committed")
        self.assertEqual(recorded["entries"][1]["note_text"],"")
        second.get_by_test_id("workspace-save-note").click()
        expect(second.get_by_test_id("workspace-note-state")).to_have_text("Saved note verified")
        saved=self.get_shortlist(sid)
        self.assertEqual(saved["entries"][1]["note_text"],"Second note still a draft")
        for before,after in zip(recorded["entries"],saved["entries"]):
            self.assertEqual(before["investigation"],after["investigation"])

    def test_responsive_workspace_has_no_horizontal_scroll(self):
        self.create_investigation()
        self.create_workspace("F"*80)
        self.add_current(1)
        self.create_investigation("105 Fictional Court",option=0)
        self.add_current(2)
        for width in (375,320):
            self.page.set_viewport_size({"width":width,"height":800})
            self.page.get_by_test_id("workspace").scroll_into_view_if_needed()
            self.assertFalse(self.page.evaluate(
                "document.documentElement.scrollWidth > innerWidth + 2"),
                f"Horizontal overflow at {width}px; overflowing elements: " +
                str(self.page.evaluate("""() => [...document.querySelectorAll('*')]
                  .filter(el => el.getBoundingClientRect().right > innerWidth + 2)
                  .slice(0,12).map(el => [el.tagName,el.className,el.getBoundingClientRect().right])""")))
            expect(self.page.get_by_test_id("workspace-entry")).to_have_count(2)
        self.page.emulate_media(reduced_motion="reduce")
        self.assertEqual(self.page.get_by_test_id("workspace-add-current").evaluate(
            "el => getComputedStyle(el).transitionDuration"),"0s")

    def test_note_limit_and_bad_uuid_do_not_mutate_frozen_evidence(self):
        self.create_investigation()
        sid=self.create_workspace()
        self.add_current(1)
        before=self.get_shortlist(sid)
        iid=before["entries"][0]["investigation_id"]
        invalid=self.page.request.patch(
            self.base+"/v1/shortlists/"+sid+"/entries/"+iid,
            data={"note_text":"n"*801})
        self.assertEqual(invalid.status,422)
        self.assertEqual(invalid.json()["error"],"invalid_note")
        self.page.get_by_test_id("workspace-other-id").fill("not-a-uuid")
        self.page.get_by_test_id("workspace-add-id").click()
        expect(self.page.get_by_test_id("workspace-error")).to_contain_text(
            "valid saved investigation UUID")
        self.assertEqual(self.get_shortlist(sid),before)

    def test_canonical_security_denies_unrelated_writes(self):
        with closing(http.client.HTTPConnection("127.0.0.1",self.port,timeout=8)) as conn:
            def send(method,path,body=b"",headers=None):
                conn.request(method,path,body=body,headers=headers or {})
                r=conn.getresponse();r.read();return r
            for method,path in (
                ("PATCH","/v1/shortlists"),
                ("POST","/v1/shortlists/11111111-1111-1111-1111-111111111111"),
                ("DELETE","/v1/investigations")):
                self.assertEqual(send(method,path,b"{}",{"Content-Type":"application/json"}).status,405)
            self.assertEqual(send("POST","/v1/shortlists",b'{"label":"No"}',
                                 {"Content-Type":"application/json",
                                  "Origin":"https://attacker.example"}).status,403)
            self.assertEqual(send("PATCH","/v1/shortlists/11111111-1111-1111-1111-111111111111/entries/11111111-1111-1111-1111-111111111111",
                                 b'{"note_text":"x"}',
                                 {"Content-Type":"application/json",
                                  "X-Forwarded-Host":"external.example"}).status,403)
        expect(self.page.get_by_test_id("workspace")).to_be_visible()

    def test_insufficient_investigation_is_not_assigned_a_price(self):
        sid=self.create_workspace()
        response=self.page.request.post(self.base+"/v1/investigations",data={"subject":{"pin":"00000000000099","building_area_sqft":1600,"label":"Unknown fictional parcel"},"township_code":"17","class_code":"203","analysis_date":"2024-07-01"})
        self.assertEqual(response.status,201)
        weak=response.json()
        self.page.get_by_test_id("workspace-other-id").fill(weak["investigation_id"])
        self.page.get_by_test_id("workspace-add-id").click()
        expect(self.page.get_by_test_id("workspace-entry")).to_have_count(1)
        expect(self.page.get_by_test_id("workspace-entry").first).to_contain_text(
            "insufficient_data")
        saved=self.get_shortlist(sid)["entries"][0]["investigation"]
        self.assertEqual(saved["selected_count"],0)
        self.assertEqual(saved["comparables"],[])
        self.assertIsNone(saved["valuation"])

    def test_discover_remove_and_preserve_frozen_investigation(self):
        iid=self.create_investigation()
        sid=self.create_workspace("Discoverable fictional shortlist")
        self.add_current(1)
        original=self.page.request.get(self.base+"/v1/investigations/"+iid).json()
        self.page.reload()
        recent=self.page.get_by_test_id("workspace-open-recent").filter(has_text="Discoverable fictional shortlist")
        recent.click()
        expect(self.page.get_by_test_id("workspace-id")).to_have_text(sid)
        self.page.once("dialog",lambda dialog:dialog.accept())
        self.page.get_by_test_id("workspace-remove").click()
        expect(self.page.get_by_test_id("workspace-count")).to_have_text("0 / 3")
        self.assertEqual(self.get_shortlist(sid)["entries"],[])
        self.assertEqual(self.page.request.get(self.base+"/v1/investigations/"+iid).json(),original)

    def test_note_commit_lost_response_reconciles_without_retry_or_draft_loss(self):
        first=self.create_investigation()
        sid=self.create_workspace("Recover note after interruption")
        self.add_current(1)
        self.create_investigation("105 Fictional Court",option=1)
        self.add_current(2)
        before=self.get_shortlist(sid)
        cards=self.page.get_by_test_id("workspace-entry")
        cards.nth(0).get_by_test_id("workspace-note").fill("Committed note")
        cards.nth(1).get_by_test_id("workspace-note").fill("Unsubmitted second draft")
        url=self.base+"/v1/shortlists/"+sid+"/entries/"+first
        writes=[]
        def interrupted(route):
            if route.request.method=="PATCH":
                response=route.fetch()
                writes.append(response.status)
                route.abort()
            else:route.continue_()
        self.page.route(url,interrupted)
        cards.nth(0).get_by_test_id("workspace-save-note").click()
        expect(self.page.get_by_test_id("workspace-recovery")).to_be_visible()
        expect(cards.nth(0).get_by_test_id("workspace-save-note")).to_be_disabled()
        expect(cards.nth(1).get_by_test_id("workspace-save-note")).to_be_disabled()
        expect(self.page.get_by_test_id("workspace-comparison")).to_have_count(0)
        self.assertEqual(writes,[200])
        self.assertEqual(self.get_shortlist(sid)["entries"][0]["note_text"],"Committed note")
        self.page.unroute(url,interrupted)
        self.page.get_by_test_id("workspace-recover").click()
        expect(self.page.get_by_test_id("workspace-recovery")).to_have_count(0)
        expect(cards.nth(0).get_by_test_id("workspace-note-state")).to_have_text("Saved note verified")
        expect(cards.nth(1).get_by_test_id("workspace-note")).to_have_value("Unsubmitted second draft")
        expect(cards.nth(1).get_by_test_id("workspace-note-state")).to_have_text("Unsaved changes")
        expect(self.page.get_by_test_id("workspace-comparison")).to_be_visible()
        after=self.get_shortlist(sid)
        self.assertEqual(after["entries"][1]["note_text"],"")
        for original,current in zip(before["entries"],after["entries"]):
            self.assertEqual(original["investigation"],current["investigation"])
            self.assertEqual(original["match_policy_version"],current["match_policy_version"])

    def test_remove_commit_lost_response_reconciles_membership(self):
        iid=self.create_investigation()
        sid=self.create_workspace("Recover removal after interruption")
        self.add_current(1)
        original=self.page.request.get(self.base+"/v1/investigations/"+iid).json()
        url=self.base+"/v1/shortlists/"+sid+"/entries/"+iid
        writes=[]
        def interrupted(route):
            if route.request.method=="DELETE":
                response=route.fetch()
                writes.append(response.status)
                route.abort()
            else:route.continue_()
        self.page.route(url,interrupted)
        self.page.once("dialog",lambda dialog:dialog.accept())
        self.page.get_by_test_id("workspace-remove").click()
        expect(self.page.get_by_test_id("workspace-recovery")).to_be_visible()
        self.assertEqual(writes,[200])
        self.assertEqual(self.get_shortlist(sid)["entries"],[])
        self.page.unroute(url,interrupted)
        self.page.get_by_test_id("workspace-recover").click()
        expect(self.page.get_by_test_id("workspace-recovery")).to_have_count(0)
        expect(self.page.get_by_test_id("workspace-count")).to_have_text("0 / 3")
        self.assertEqual(self.page.request.get(self.base+"/v1/investigations/"+iid).json(),original)

    def test_capture_shortlist_workflow_visuals(self):
        folder=os.environ.get("HPI_SHORTLIST_SCREENSHOTS")
        if not folder:self.skipTest("Screenshots only in hosted review CI")
        target=Path(folder);target.mkdir(parents=True,exist_ok=True)
        self.create_investigation()
        self.create_workspace()
        self.add_current(1)
        self.page.screenshot(path=str(target/"01-workspace-one-saved-property.png"),full_page=True)
        self.create_investigation("105 Fictional Court",option=1)
        self.add_current(2)
        first=self.page.get_by_test_id("workspace-entry").first
        first.get_by_test_id("workspace-note").fill("Review source and floor area.")
        first.get_by_test_id("workspace-save-note").click()
        expect(first.get_by_test_id("workspace-note-state")).to_have_text("Saved note verified")
        self.page.screenshot(path=str(target/"02-workspace-two-properties-saved-note.png"),
                             full_page=True)
        self.page.set_viewport_size({"width":375,"height":800})
        self.page.screenshot(path=str(target/"03-workspace-mobile.png"),full_page=True)

if __name__=="__main__":
    unittest.main()
