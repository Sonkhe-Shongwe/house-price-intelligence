"""Real browser -> same-origin loopback preview -> actual Python WSGI -> SQLite.

No real property data, live geocoder, external map assets, account notes, or
new backend endpoints. Tests exercise the compiled ESM React source-review path.
"""
from __future__ import annotations

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
SPIKE = ROOT / "design-prototypes" / "react-map-spike"
SERVER = SPIKE / "tests" / "source_preview_server.py"


class ReadOnlySourceReviewBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        cls.url = f"http://127.0.0.1:{cls.port}"
        cls.server = subprocess.Popen(
            [sys.executable, str(SERVER), "--port", str(cls.port)],
            cwd=ROOT, stdout=cls.log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if cls.server.poll() is not None:
                    cls.log.seek(0)
                    raise RuntimeError("Isolated preview exited: " + cls.log.read()[-4000:])
                try:
                    with urlopen(cls.url + "/health", timeout=0.5) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.12)
            else:
                raise RuntimeError("Isolated Python WSGI preview never became healthy")
            cls.playwright = sync_playwright().start()
            launch = ({"executable_path": os.environ["HPI_BROWSER_EXECUTABLE"],
                       "args": ["--no-sandbox"]}
                      if os.environ.get("HPI_BROWSER_EXECUTABLE") else {})
            cls.browser = cls.playwright.chromium.launch(headless=True, **launch)
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
        try:
            cls.server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.server.kill()
            cls.server.wait(timeout=5)
        cls.log.close()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.page = self.context.new_page()
        self.js_errors = []
        self.external = []
        self.map_code_requests = []
        self.page.on("pageerror", lambda error: self.js_errors.append(str(error)))
        self.page.on("request", lambda request:
                     self.external.append(request.url)
                     if not request.url.startswith(self.url + "/") else None)
        self.page.on("request", lambda request:
                     self.map_code_requests.append(request.url)
                     if "VectorMap-" in request.url or "maplibre-gl-worker-" in request.url else None)
        result = self.page.goto(self.url + "/source-review")
        self.assertEqual(result.status, 200)
        expect(self.page.get_by_test_id("source-review")).to_be_visible()
        expect(self.page.get_by_test_id("source-count")).to_have_text("3", timeout=15000)

    def tearDown(self):
        self.assertEqual(self.js_errors, [], "No uncaught client-side errors")
        self.assertEqual(self.external, [], "No third-party map, font, geocoder or service requests")
        self.assertEqual(self.map_code_requests, [],
                         "Source-only investigations must not download the GPU map worker or fake pins")
        self.context.close()

    def test_actual_wsgi_frozen_prices_snapshots_and_withheld_map(self):
        expect(self.page.get_by_test_id("source-status")).to_have_text(
            "Supported neighbourhood evidence")
        expect(self.page.get_by_test_id("source-sale")).to_have_count(3)
        expect(self.page.get_by_test_id("source-sale").first).to_contain_text("$525,000.00")
        expect(self.page.get_by_test_id("source-asking-price")).to_have_count(0)  # value is in a labelled card
        expect(self.page.get_by_test_id("source-build")).to_have_text("synthetic-build")
        expect(self.page.get_by_test_id("source-snapshots")).to_contain_text("sale-snap")
        expect(self.page.get_by_test_id("source-map-unavailable")).to_contain_text(
            "No approved geographic features")
        self.assertEqual(self.page.locator("canvas.maplibregl-canvas").count(), 0)
        self.page.get_by_test_id("source-sale").first.click()
        expect(self.page.get_by_test_id("source-sale-reason")).to_contain_text("Same")
        expect(self.page.get_by_test_id("source-warning")).to_contain_text("no current valuation")

    def test_insufficient_evidence_clears_comparables_and_fakes_no_value(self):
        self.page.get_by_test_id("source-sale").nth(2).click()
        self.page.get_by_test_id("source-case-insufficient").click()
        expect(self.page.get_by_test_id("source-status")).to_have_text("Insufficient data")
        expect(self.page.get_by_test_id("source-count")).to_have_text("0")
        expect(self.page.get_by_test_id("source-sale")).to_have_count(0)
        expect(self.page.get_by_test_id("source-insufficient")).to_contain_text(
            "not a zero-dollar valuation")
        expect(self.page.get_by_test_id("source-map-unavailable")).to_be_visible()
        self.page.get_by_test_id("source-case-supported").click()
        expect(self.page.get_by_test_id("source-sale")).to_have_count(3)

    def test_readonly_shortlist_is_real_wsgi_state(self):
        self.page.get_by_role("group", name="Connected research views").get_by_role(
            "button", name="Saved comparison").click()
        expect(self.page.get_by_test_id("source-shortlist-entry")).to_have_count(2)
        expect(self.page.get_by_test_id("source-shortlist-entry").first).to_contain_text(
            "Check the original recorded evidence")
        expect(self.page.get_by_test_id("source-shortlist-entry").nth(1)).to_contain_text(
            "No eligible sales, do not infer a price")
        self.assertEqual(self.page.locator("#root textarea").count(), 0)
        self.page.get_by_test_id("source-shortlist-entry").nth(1).get_by_role(
            "button", name="Inspect frozen evidence").click()
        expect(self.page.get_by_test_id("source-status")).to_have_text("Insufficient data")
        expect(self.page.get_by_test_id("source-sale")).to_have_count(0)

    def test_mobile_and_reduced_motion_have_no_horizontal_overflow(self):
        for width in (375, 320):
            self.page.set_viewport_size({"width": width, "height": 800})
            expect(self.page.get_by_test_id("source-map-unavailable")).to_be_visible()
            self.assertFalse(self.page.evaluate(
                "document.documentElement.scrollWidth > window.innerWidth + 2"))
            self.page.get_by_role("group", name="Connected research views").get_by_role(
                "button", name="Saved comparison").click()
            expect(self.page.get_by_test_id("source-shortlist-entry")).to_have_count(2)
            self.assertFalse(self.page.evaluate(
                "document.documentElement.scrollWidth > window.innerWidth + 2"))
            self.page.get_by_role("group", name="Connected research views").get_by_role(
                "button", name="Investigation").click()
        self.page.emulate_media(reduced_motion="reduce")
        self.assertEqual(self.page.locator(".source-casebar button").first.evaluate(
            "el => getComputedStyle(el).transitionDuration"), "0s")

    def test_security_no_write_no_cross_site_no_arbitrary_static(self):
        with http.client.HTTPConnection("127.0.0.1", self.port, timeout=8) as conn:
            conn.request("GET", "/source-review")
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            headers = dict(response.getheaders())
            self.assertEqual(headers.get("X-Synthetic-Only"), "true")
            self.assertEqual(headers.get("X-Proof-Mode"), "read-only")
            self.assertEqual(headers.get("Cache-Control"), "no-store")
            self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(headers.get("X-Frame-Options"), "DENY")
            csp = headers.get("Content-Security-Policy", "")
            for phrase in ("default-src 'none'", "script-src 'self'", "connect-src 'self'",
                           "style-src 'self'", "worker-src 'self'", "frame-ancestors 'none'"):
                self.assertIn(phrase, csp)
            self.assertNotIn("'unsafe-inline'", csp)
            response.read()
            conn.request("POST", "/v1/investigations", body=b"{}",
                         headers={"Content-Type": "application/json"})
            self.assertEqual(conn.getresponse().status, 405)
            conn.request("GET", "/.env")
            self.assertEqual(conn.getresponse().status, 404)
            conn.request("GET", "/_study/cases?debug=true")
            self.assertEqual(conn.getresponse().status, 400)
            conn.request("GET", "/source-review", headers={"Host": "attacker.example"})
            self.assertEqual(conn.getresponse().status, 403)
            conn.request("GET", "/_study/cases", headers={"X-Forwarded-Host": "public.example"})
            self.assertEqual(conn.getresponse().status, 403)
            conn.request("GET", "/source-review", headers={"Origin": "http://attacker.example"})
            self.assertEqual(conn.getresponse().status, 403)

    def test_rejects_tampered_source_response_without_stale_evidence(self):
        first = self.page.get_by_test_id("source-case-insufficient")
        def intercept(route):
            source = route.fetch()
            data = source.json()
            data["valuation"] = 999999.99
            route.fulfill(response=source, json=data)
        self.page.route("**/v1/investigations/*", intercept)
        first.click()
        expect(self.page.get_by_test_id("source-investigation-error")).to_contain_text(
            "unexpected_valuation")
        expect(self.page.get_by_test_id("source-sale")).to_have_count(0)
        expect(self.page.get_by_test_id("source-map-unavailable")).to_have_count(0)

    def test_capture_source_review_screenshots(self):
        directory = os.environ.get("HPI_SOURCE_SCREENSHOTS")
        if not directory:
            self.skipTest("Screenshots requested only in hosted visual-review CI")
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(target / "01-source-connected-supported-desktop.png"),
                             full_page=True)
        self.page.get_by_test_id("source-case-insufficient").click()
        expect(self.page.get_by_test_id("source-status")).to_have_text("Insufficient data")
        self.page.screenshot(path=str(target / "02-source-connected-insufficient-desktop.png"),
                             full_page=True)
        self.page.get_by_role("group", name="Connected research views").get_by_role(
            "button", name="Saved comparison").click()
        expect(self.page.get_by_test_id("source-shortlist-entry")).to_have_count(2)
        self.page.screenshot(path=str(target / "03-source-connected-shortlist.png"),
                             full_page=True)
        self.page.get_by_role("group", name="Connected research views").get_by_role(
            "button", name="Investigation").click()
        self.page.set_viewport_size({"width": 375, "height": 812})
        self.page.screenshot(path=str(target / "04-source-connected-mobile.png"),
                             full_page=True)


if __name__ == "__main__":
    unittest.main()
