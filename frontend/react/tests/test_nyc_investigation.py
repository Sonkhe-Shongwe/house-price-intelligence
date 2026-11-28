"""Compiled React to existing loopback WSGI, invented NYC records only."""
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
PATH="/v2/fictional/nyc/investigate"


class NYCInvestigationBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log=tempfile.TemporaryFile(mode="w+t",encoding="utf-8")
        with socket.socket() as sk:
            sk.bind(("127.0.0.1",0))
            cls.base=f"http://127.0.0.1:{sk.getsockname()[1]}"
        cls.server=subprocess.Popen([sys.executable,"-m","backend.run_synthetic_api","--fixture-only",
            "--frontend","react","--nyc-fixture","--port",cls.base.rsplit(":",1)[1]],
            cwd=ROOT,stdout=cls.log,stderr=subprocess.STDOUT)
        try:
            for _ in range(100):
                if cls.server.poll() is not None: raise RuntimeError("NYC fixture launcher exited")
                try:
                    with urlopen(cls.base+"/health",timeout=.4) as res:
                        if res.status==200: break
                except OSError: time.sleep(.15)
            else: raise RuntimeError("NYC fixture server unavailable")
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
        self.page.on("request",lambda r:self.external.append(r.url) if not r.url.startswith(self.base+"/") else None)
        self.assertEqual(self.page.goto(self.base+"/nyc-fictional").status,200)
        expect(self.page.get_by_test_id("nyc-study")).to_be_visible()

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors,[]);self.assertEqual(self.external,[])

    def submit(self):
        self.page.get_by_test_id("nyc-submit").click()
        expect(self.page.get_by_test_id("nyc-result")).to_be_visible()

    def test_real_response_and_existing_workspace(self):
        self.submit()
        r=self.page.get_by_test_id("nyc-result")
        expect(r).to_contain_text("$650,000.01")
        expect(r).to_contain_text("Incomplete 365-day lookback")
        expect(self.page.get_by_test_id("nyc-comparable")).to_have_count(4)
        self.assertEqual(self.page.request.get(self.base+"/v1/investigations/history").json()["investigations"],[])
        self.page.get_by_role("link",name="Existing fictional workspace").click()
        expect(self.page.get_by_test_id("buyer-workflow")).to_be_visible()

    def test_abstention_and_invalid_input_clears_stale(self):
        self.submit()
        for label,message in (("Fictional NYC Home B","Insufficient comparable evidence"),
                              ("Fictional NYC Ambiguous","Address cannot be resolved uniquely"),
                              ("Fictional NYC Unsupported","Outside supported fixture coverage")):
            self.page.get_by_label("Fictional address").select_option(label)
            expect(self.page.get_by_test_id("nyc-result")).to_have_count(0)
            self.submit()
            expect(self.page.get_by_test_id("nyc-result")).to_contain_text(message)
            expect(self.page.get_by_test_id("nyc-comparable")).to_have_count(0)
        self.page.get_by_label("Fictional asking price (USD)").fill("1.001")
        self.page.get_by_test_id("nyc-submit").click()
        expect(self.page.get_by_role("alert")).to_contain_text("two decimal places")
        expect(self.page.get_by_test_id("nyc-result")).to_have_count(0)

    def test_wrong_response_fails_closed_and_mobile(self):
        self.page.set_viewport_size({"width":375,"height":812})
        self.submit()
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
        def malformed(route):
            response=route.fetch()
            body=response.json()
            body["provenance"]["public_display_approved"]=True
            route.fulfill(response=response,json=body)
        self.page.route("**"+PATH,malformed)
        self.page.get_by_test_id("nyc-submit").click()
        expect(self.page.get_by_role("alert")).to_contain_text("Investigation unavailable")
        expect(self.page.get_by_test_id("nyc-result")).to_have_count(0)


if __name__=="__main__":
    unittest.main()
