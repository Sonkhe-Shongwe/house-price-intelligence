"""Actual opt-in React ZA page through the localhost fixture server."""
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[3]


class SouthAfricanBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log=tempfile.TemporaryFile(mode="w+t",encoding="utf-8")
        with socket.socket() as sk:
            sk.bind(("127.0.0.1",0))
            cls.base=f"http://127.0.0.1:{sk.getsockname()[1]}"
        cls.server=subprocess.Popen([sys.executable,"-m","backend.run_synthetic_api","--fixture-only",
                                     "--frontend","react","--sa-fixture","--sa-saved-fixture","--port",cls.base.rsplit(":",1)[1]],
                                    cwd=ROOT,stdout=cls.log,stderr=subprocess.STDOUT)
        try:
            for _ in range(100):
                if cls.server.poll() is not None:
                    raise RuntimeError("ZA fixture launcher exited")
                try:
                    with urlopen(cls.base+"/health",timeout=.4) as res:
                        if res.status==200: break
                except OSError: time.sleep(.15)
            else: raise RuntimeError("ZA fixture server unavailable")
            cls.driver=sync_playwright().start()
            options={"executable_path":os.environ["HPI_BROWSER_EXECUTABLE"],"args":["--no-sandbox"]} if os.environ.get("HPI_BROWSER_EXECUTABLE") else {}
            cls.browser=cls.driver.chromium.launch(headless=True,**options)
        except Exception:
            cls.server.terminate();cls.server.wait(timeout=5);cls.log.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.driver.stop();cls.server.terminate()
        try: cls.server.wait(timeout=5)
        except subprocess.TimeoutExpired: cls.server.kill();cls.server.wait(timeout=5)
        cls.log.close()

    def setUp(self):
        self.context=self.browser.new_context(viewport={"width":1366,"height":850})
        self.page=self.context.new_page();self.errors=[];self.external=[]
        self.page.on("pageerror",lambda e:self.errors.append(str(e)))
        self.page.on("request",lambda req:self.external.append(req.url) if not req.url.startswith(self.base+"/") else None)
        self.assertEqual(self.page.goto(self.base+"/za-fictional").status,200)
        expect(self.page.get_by_test_id("za-study")).to_be_visible()

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors,[]);self.assertEqual(self.external,[])

    def submit(self):
        self.page.get_by_test_id("za-submit").click()
        expect(self.page.get_by_test_id("za-result")).to_be_visible()

    def test_real_response_and_us_preserved(self):
        self.submit()
        expect(self.page.get_by_test_id("za-comparable")).to_have_count(5)
        expect(self.page.get_by_test_id("za-result")).to_contain_text("R 2 500 000.01")
        expect(self.page.get_by_test_id("za-result")).to_contain_text("365 days")
        self.assertEqual(self.page.request.get(self.base+"/v1/investigations/history").json()["investigations"],[])
        self.page.get_by_label("Evidence mode").select_option("retrospective")
        expect(self.page.get_by_test_id("za-result")).to_have_count(0)
        self.submit()
        expect(self.page.get_by_test_id("za-result")).to_contain_text("Retrospective only")
        self.page.get_by_role("link",name="US fictional buyer workspace").click()
        expect(self.page.get_by_test_id("buyer-workflow")).to_be_visible()

    def test_ambiguous_and_invalid_no_stale_result(self):
        self.submit()
        self.page.get_by_label("Fictional erf").select_option("fictional-erf-000010")
        self.submit()
        expect(self.page.get_by_test_id("za-result")).to_contain_text("cannot be resolved exactly")
        expect(self.page.get_by_test_id("za-comparable")).to_have_count(0)
        self.page.get_by_label("Fictional asking price (ZAR)").fill("1.001")
        self.page.get_by_test_id("za-submit").click()
        expect(self.page.get_by_role("alert")).to_contain_text("two decimal places")
        expect(self.page.get_by_test_id("za-result")).to_have_count(0)

    def test_cross_market_response_refused_and_retry(self):
        path="**/v2/fictional/za/investigate"
        def corrupt(route):
            response=route.fetch()
            value=response.json();value["currency"]="USD"
            route.fulfill(response=response,json=value)
        self.page.route(path,corrupt)
        self.page.get_by_test_id("za-submit").click()
        expect(self.page.get_by_role("alert")).to_contain_text("Investigation unavailable")
        expect(self.page.get_by_test_id("za-result")).to_have_count(0)
        self.page.unroute(path,corrupt)
        self.submit()
        expect(self.page.get_by_test_id("za-comparable")).to_have_count(5)

    def test_save_reload_reopen_and_retry(self):
        self.submit()
        before=len(self.page.request.get(self.base+"/v2/fictional/za/saved").json()["investigations"])
        path="**/v2/fictional/za/saved"
        def lost_reply(route):
            if route.request.method=="POST":
                route.fetch()
                route.abort()
            else: route.continue_()
        self.page.route(path,lost_reply)
        self.page.get_by_test_id("za-save").click()
        expect(self.page.get_by_text("Save not confirmed.",exact=False)).to_be_visible()
        self.page.unroute(path,lost_reply)
        self.page.get_by_test_id("za-save").click()
        expect(self.page.get_by_test_id("za-saved-id")).to_be_visible()
        saved_id=self.page.get_by_test_id("za-saved-id").inner_text().split(": ",1)[1]
        self.assertEqual(len(self.page.request.get(self.base+"/v2/fictional/za/saved").json()["investigations"]),before+1)
        expect(self.page.get_by_test_id("za-save")).to_be_disabled()
        self.page.reload()
        self.page.get_by_role("button",name="Reopen "+saved_id).click()
        expect(self.page.get_by_test_id("za-comparable")).to_have_count(5)
        expect(self.page.get_by_text("Reopened frozen evidence; not recalculated.")).to_be_visible()
        expect(self.page.get_by_test_id("za-result")).to_contain_text("R 2 500 000.01")
        self.assertEqual(self.page.request.get(self.base+"/v1/investigations/history").json()["investigations"],[])

    def test_mobile_reflow(self):
        for width in (768,375,320):
            self.page.set_viewport_size({"width":width,"height":850})
            self.submit()
            self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"))
            expect(self.page.get_by_role("region",name="Fictional comparable sales")).to_be_visible()
        target=os.environ.get("HPI_BUYER_SCREENSHOTS")
        if target:
            Path(target).mkdir(parents=True,exist_ok=True)
            self.page.screenshot(path=str(Path(target)/"za-mobile.png"),full_page=True)
            self.page.set_viewport_size({"width":1366,"height":850})
            self.page.screenshot(path=str(Path(target)/"za-desktop.png"),full_page=True)
