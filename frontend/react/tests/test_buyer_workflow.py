"""Actual browser -> explicit fictional parcel choice -> Python WSGI -> SQLite.

Runs through the canonical --fixture-only --frontend react launcher.
No real property data, coordinates, appraisal or public host.
"""
from __future__ import annotations

from contextlib import closing
import http.client
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


class ReactBuyerWorkflowBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:
            sk.bind(("127.0.0.1", 0))
            cls.port = sk.getsockname()[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.server = subprocess.Popen(
            [sys.executable, "-m", SERVER, "--port", str(cls.port),
             "--fixture-only", "--frontend", "react"], cwd=ROOT,
            stdout=cls.log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if cls.server.poll() is not None:
                    cls.log.seek(0)
                    raise RuntimeError("Opt-in buyer preview exited: " + cls.log.read()[-5000:])
                try:
                    with urlopen(cls.base + "/health", timeout=.4) as reply:
                        if reply.status == 200:
                            break
                except OSError:
                    time.sleep(.12)
            else:
                raise RuntimeError("Fictional buyer preview never became healthy")
            cls.driver = sync_playwright().start()
            options = ({"executable_path":os.environ["HPI_BROWSER_EXECUTABLE"],
                        "args":["--no-sandbox"]}
                       if os.environ.get("HPI_BROWSER_EXECUTABLE") else {})
            cls.browser = cls.driver.chromium.launch(headless=True,**options)
        except Exception:
            cls.server.terminate()
            cls.server.wait(timeout=5)
            cls.log.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.driver.stop()
        cls.server.terminate()
        try:
            cls.server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.server.kill()
            cls.server.wait(timeout=5)
        cls.log.close()

    def setUp(self):
        self.ctx = self.browser.new_context(viewport={"width":1366,"height":850})
        self.page = self.ctx.new_page()
        self.errors = []
        self.external = []
        self.gpu_assets = []
        self.page.on("pageerror", lambda error:self.errors.append(str(error)))
        self.page.on("request", lambda req:self.external.append(req.url)
                     if not req.url.startswith(self.base+"/") else None)
        self.page.on("request", lambda req:self.gpu_assets.append(req.url)
                     if "VectorMap-" in req.url or "maplibre-gl-worker-" in req.url else None)
        response=self.page.goto(self.base+"/buyer-workflow")
        self.assertEqual(response.status,200)
        expect(self.page.get_by_test_id("buyer-workflow")).to_be_visible()
        expect(self.page.get_by_test_id("buyer-create")).to_be_disabled()

    def tearDown(self):
        self.assertEqual(self.errors,[], "No uncaught client JavaScript errors")
        self.assertEqual(self.external,[], "Buyer UI may not contact third parties")
        self.assertEqual(self.gpu_assets,[], "Real source UI must not load invented MapLibre geometry")
        self.ctx.close()

    def search(self,query:str):
        self.page.get_by_test_id("buyer-query").fill(query)
        self.page.get_by_test_id("buyer-search").click()

    def select_and_save(self,query="101 Fictional Way",price="500000.00"):
        self.search(query)
        expect(self.page.get_by_test_id("buyer-candidate")).to_have_count(1)
        self.page.get_by_test_id("buyer-candidate").first.click()
        expect(self.page.get_by_test_id("buyer-selected-parcel")).to_be_visible()
        self.page.get_by_test_id("buyer-price").fill(price)
        self.page.get_by_test_id("buyer-create").click()
        expect(self.page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
        return self.page.get_by_test_id("buyer-saved-id").inner_text()

    def test_shared_address_demands_explicit_parcel_selection(self):
        self.search("105 Fictional Court")
        expect(self.page.get_by_test_id("buyer-candidate")).to_have_count(2)
        expect(self.page.get_by_test_id("buyer-candidate").first).to_contain_text(
            "Synthetic parcel option A")
        expect(self.page.get_by_test_id("buyer-candidate").nth(1)).to_contain_text(
            "Synthetic parcel option B")
        expect(self.page.get_by_test_id("buyer-create")).to_be_disabled()
        self.page.get_by_test_id("buyer-candidate").nth(1).click()
        expect(self.page.get_by_test_id("buyer-selected-parcel")).to_contain_text(
            "00000000000006")
        self.page.get_by_test_id("buyer-create").click()
        expect(self.page.get_by_test_id("buyer-count")).to_have_text("3 eligible sales")
        expect(self.page.get_by_test_id("buyer-sale")).to_have_count(3)
        saved=self.page.get_by_test_id("buyer-saved-id").inner_text()
        reopened=self.page.request.get(self.base+"/v1/investigations/"+saved).json()
        self.assertEqual(reopened["subject"]["pin"],"00000000000006")
        self.assertEqual(reopened["subject"]["address_id"],"fictional-6")
        self.assertIsNone(reopened["valuation"])
        expect(self.page.get_by_test_id("buyer-no-geometry")).to_be_visible()

    def test_exact_asking_cents_and_frozen_sale_amounts(self):
        saved=self.select_and_save(price="530000.07")
        expect(self.page.get_by_test_id("buyer-sale").first).to_contain_text("$525,000.00")
        expect(self.page.get_by_test_id("buyer-result")).to_contain_text("$530,000.07")
        expect(self.page.get_by_test_id("buyer-build")).to_have_text("synthetic-build")
        expect(self.page.get_by_test_id("buyer-snapshots")).to_contain_text("sale-snap")
        original=self.page.request.get(self.base+"/v1/investigations/"+saved).json()
        self.assertEqual(original["subject"]["asking_price_usd"],"530000.07")
        self.assertEqual(original["comparables"][0]["sale_price_usd"],"525000.00")
        self.page.get_by_test_id("buyer-sale").first.click()
        expect(self.page.get_by_test_id("buyer-explanation")).to_have_text(
            original["comparables"][0]["explanation"])
        self.assertEqual(self.page.locator(".maplibregl-canvas").count(),0)

    def test_search_edit_clears_candidate_and_prevents_stale_create(self):
        self.search("105 Fictional Court")
        expect(self.page.get_by_test_id("buyer-candidate")).to_have_count(2)
        self.page.get_by_test_id("buyer-candidate").first.click()
        expect(self.page.get_by_test_id("buyer-selected-parcel")).to_be_visible()
        self.page.get_by_test_id("buyer-query").fill("Fictional Way")
        expect(self.page.get_by_test_id("buyer-selected-parcel")).to_have_count(0)
        expect(self.page.get_by_test_id("buyer-create")).to_be_disabled()
        self.search("Neverland Fake Street")
        expect(self.page.get_by_test_id("buyer-feedback")).to_contain_text(
            "No invented addresses matched")
        expect(self.page.get_by_test_id("buyer-candidate")).to_have_count(0)
        expect(self.page.get_by_test_id("buyer-create")).to_be_disabled()

    def test_saved_result_can_reopen_after_new_search(self):
        saved=self.select_and_save()
        self.page.get_by_test_id("buyer-query").fill("105 Fictional Court")
        expect(self.page.get_by_test_id("buyer-result")).to_have_count(0)
        self.page.get_by_test_id("buyer-reopen-id").fill(saved)
        self.page.get_by_test_id("buyer-reopen").click()
        expect(self.page.get_by_test_id("buyer-saved-id")).to_have_text(saved)
        expect(self.page.get_by_test_id("buyer-count")).to_have_text("3 eligible sales")
        expect(self.page.get_by_test_id("buyer-feedback")).to_contain_text(
            "without re-running matching")

    def test_failed_or_corrupted_reopen_does_not_leak_previous_evidence(self):
        self.select_and_save()
        self.page.get_by_test_id("buyer-reopen-id").fill(
            "11111111-1111-1111-1111-111111111111")
        self.page.get_by_test_id("buyer-reopen").click()
        expect(self.page.get_by_test_id("buyer-error")).to_contain_text(
            "investigation_not_found")
        expect(self.page.get_by_test_id("buyer-sale")).to_have_count(0)
        self.page.get_by_test_id("buyer-reopen-id").fill("not-a-uuid")
        self.page.get_by_test_id("buyer-reopen").click()
        expect(self.page.get_by_test_id("buyer-error")).to_contain_text(
            "valid lowercase saved investigation UUID")

    def test_pending_save_lost_response_recovers_without_duplicate_write(self):
        self.page.get_by_test_id("buyer-manual-pin").fill("00000000000001")
        url=self.base+"/v1/investigations"
        held=[]
        self.page.route(url,lambda route:held.append(route))
        self.page.get_by_test_id("buyer-create").click()
        expect(self.page.get_by_test_id("buyer-pending")).to_be_visible()
        expect(self.page.get_by_test_id("buyer-create")).to_be_disabled()
        expect(self.page.get_by_test_id("buyer-result")).to_have_count(0)
        # Programmatic form submit exercises the synchronous pending-write lock too.
        self.page.get_by_test_id("buyer-create").evaluate("el=>el.form.requestSubmit()")
        self.assertEqual(len(held),1)
        response=held[0].fetch()
        self.assertEqual(response.status,201)
        saved=response.json()["investigation_id"]
        held[0].abort()
        self.page.unroute(url)
        expect(self.page.get_by_test_id("buyer-error")).to_contain_text("check Saved properties")
        expect(self.page.get_by_test_id("buyer-feedback")).to_have_count(0)
        expect(self.page.get_by_test_id("buyer-result")).to_have_count(0)
        self.page.get_by_test_id("nav-saved").click()
        self.page.get_by_test_id("history-search").fill("00000000000001")
        # Shared test fixture may contain other records; identify this save by its frozen ID.
        self.page.get_by_test_id("nav-investigate").click()
        self.page.get_by_test_id("buyer-reopen-id").fill(saved)
        self.page.get_by_test_id("buyer-reopen").click()
        expect(self.page.get_by_test_id("buyer-saved-id")).to_have_text(saved)
        expect(self.page.get_by_test_id("buyer-result")).to_be_visible()

    def test_canonical_security_boundary(self):
        with closing(http.client.HTTPConnection("127.0.0.1",self.port,timeout=8)) as conn:
            def send_request(method,path,body=None,headers=None):
                conn.request(method,path,body=body,headers=headers or {})
                response=conn.getresponse()
                content=response.read()
                return response,content
            page,body=send_request("GET","/buyer-workflow")
            self.assertEqual(page.status,200)
            headers=dict(page.getheaders())
            self.assertEqual(headers["X-Synthetic-Only"],"true")
            self.assertIn("default-src 'none'",headers["Content-Security-Policy"])
            self.assertNotIn("'unsafe-inline'",headers["Content-Security-Policy"])
            for method,path,status in (("DELETE","/v1/investigations",405),
                                       ("POST","/some-random-path",404),
                                       ("POST","/buyer-workflow",405)):
                result,_=send_request(method,path,b"{}",{"Content-Type":"application/json"})
                self.assertEqual(result.status,status,(method,path))
            fail,_=send_request("POST","/v1/addresses/search",b'{"query":"Fictional Way"}',
                        {"Content-Type":"application/json","Origin":"http://attacker.invalid"})
            self.assertEqual(fail.status,403)
            fail,_=send_request("POST","/v1/addresses/search",b'{"query":"Fictional Way"}',
                        {"Content-Type":"application/json","X-Forwarded-Host":"external.invalid"})
            self.assertEqual(fail.status,403)
            fail,_=send_request("POST","/v1/investigations",b"{broken",
                        {"Content-Type":"application/json"})
            self.assertEqual(fail.status,400)
            fail,_=send_request("GET","/assets/../../.env")
            self.assertEqual(fail.status,404)

    def test_unknown_manual_pin_safely_abstains(self):
        self.page.get_by_test_id("buyer-manual-pin").fill("00000000000099")
        self.page.get_by_test_id("buyer-price").fill("")
        self.page.get_by_test_id("buyer-create").click()
        expect(self.page.get_by_test_id("buyer-insufficient")).to_be_visible()
        expect(self.page.get_by_test_id("buyer-count")).to_have_text("0 eligible sales")
        iid=self.page.get_by_test_id("buyer-saved-id").inner_text()
        doc=self.page.request.get(self.base+"/v1/investigations/"+iid).json()
        self.assertEqual(doc["status"],"insufficient_data")
        self.assertIsNone(doc["valuation"])

    def test_narrow_mobile_and_accessible_controls(self):
        for width in (375,320):
            self.page.set_viewport_size({"width":width,"height":800})
            self.assertFalse(self.page.evaluate(
                "document.documentElement.scrollWidth > innerWidth + 2"),
                "Page horizontal overflow at "+str(width))
            self.search("105 Fictional Court")
            expect(self.page.get_by_test_id("buyer-candidate")).to_have_count(2)
            self.assertFalse(self.page.evaluate(
                "document.documentElement.scrollWidth > innerWidth + 2"),
                "Result horizontal overflow at "+str(width))
        self.page.emulate_media(reduced_motion="reduce")
        self.assertEqual(self.page.locator(".buyer-candidates button").first.evaluate(
            "(el) => getComputedStyle(el).transitionDuration"),"0s")

    def test_capture_buyer_workflow_visuals(self):
        directory=os.environ.get("HPI_BUYER_SCREENSHOTS")
        if not directory:
            self.skipTest("Hosted review screenshots only")
        target=Path(directory);target.mkdir(parents=True,exist_ok=True)
        self.page.screenshot(path=str(target/"01-buyer-empty-desktop.png"),full_page=True)
        self.search("105 Fictional Court")
        expect(self.page.get_by_test_id("buyer-candidate")).to_have_count(2)
        self.page.screenshot(path=str(target/"02-buyer-ambiguous-choice.png"),full_page=True)
        self.page.get_by_test_id("buyer-candidate").first.click()
        expect(self.page.get_by_test_id("buyer-selected-parcel")).to_be_visible()
        self.page.get_by_test_id("buyer-create").click()
        expect(self.page.get_by_test_id("buyer-result")).to_be_visible()
        self.page.screenshot(path=str(target/"03-buyer-saved-evidence.png"),full_page=True)
        self.page.set_viewport_size({"width":375,"height":800})
        self.page.screenshot(path=str(target/"04-buyer-mobile.png"),full_page=True)


if __name__=="__main__":
    unittest.main()
