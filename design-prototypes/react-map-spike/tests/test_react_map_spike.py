"""Browser acceptance for the isolated Vite-built, invented-data spatial lab.

CI-only proof. No request to live publishers, production data, geocoder or tiles.
"""
from __future__ import annotations

import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import unittest
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SPIKE = ROOT / "design-prototypes" / "react-map-spike"


class ReactMapTechnologySpikeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            cls.port = s.getsockname()[1]
        cls.url = f"http://127.0.0.1:{cls.port}/"
        cls.server = subprocess.Popen(
            ["npm", "run", "preview", "--", "--port", str(cls.port), "--strictPort"],
            cwd=SPIKE,
            stdout=cls.log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if cls.server.poll() is not None:
                    raise RuntimeError("Vite preview exited prematurely")
                try:
                    with urlopen(cls.url, timeout=0.5) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.15)
            else:
                raise RuntimeError("Local Vite preview never became healthy")
            cls.playwright = sync_playwright().start()
            cls.browser = cls.playwright.chromium.launch(headless=True, **({"executable_path": os.environ["HPI_BROWSER_EXECUTABLE"], "args": ["--no-sandbox"]} if os.environ.get("HPI_BROWSER_EXECUTABLE") else {}))
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
        self.ctx = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.page = self.ctx.new_page()
        self.errors = []
        self.remote = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.on("request", lambda r: self.remote.append(r.url)
                     if not r.url.startswith(self.url.rstrip("/")) else None)
        self.page.goto(self.url)
        expect(self.page.get_by_test_id("eligible-count")).to_have_text("3 records")

    def tearDown(self):
        self.assertEqual(self.errors, [], "No uncaught client exceptions")
        self.assertEqual(self.remote, [], "Browser must not request remote tiles, fonts, CDNs, or services")
        self.ctx.close()

    def test_svg_pin_list_selection_and_exact_text(self):
        expect(self.page.get_by_test_id("schematic-map")).to_be_visible()
        self.page.get_by_test_id("schematic-pin-c2").click()
        expect(self.page.get_by_test_id("evidence-c2")).to_have_attribute("aria-pressed", "true")
        expect(self.page.get_by_test_id("selected-reason")).to_contain_text("Second invented")
        self.page.get_by_test_id("evidence-c1").click()
        expect(self.page.get_by_test_id("schematic-pin-c1")).to_have_attribute("aria-pressed", "true")
        expect(self.page.get_by_test_id("evidence-c1")).to_contain_text("$525,000.01")

    def test_insufficient_case_never_leaks_previous_sales(self):
        self.page.get_by_test_id("evidence-c3").click()
        self.page.get_by_test_id("switch-subject").click()
        expect(self.page.get_by_test_id("eligible-count")).to_have_text("0 records")
        expect(self.page.get_by_test_id("insufficient-evidence")).to_be_visible()
        expect(self.page.get_by_test_id("schematic-pin-c3")).to_have_count(0)
        expect(self.page.get_by_test_id("evidence-list")).to_have_count(0)
        expect(self.page.get_by_test_id("selected-reason")).to_contain_text("No qualified sales")

    def test_theme_and_shortlist_are_stateful_not_persistent(self):
        self.page.get_by_role("group", name="Visual style").get_by_role("button", name="Intelligence").click()
        expect(self.page.locator("html")).to_have_attribute("data-hpi-theme", "intelligence")
        self.page.get_by_role("navigation", name="Prototype views").get_by_role("button", name="Shortlist").click()
        self.page.locator("#note-a").fill("Only a temporary study note")
        expect(self.page.locator("#note-a")).to_have_value("Only a temporary study note")
        expect(self.page.locator(".compare-table")).to_contain_text("Not produced")
        self.page.reload()
        self.page.get_by_role("navigation", name="Prototype views").get_by_role("button", name="Shortlist").click()
        expect(self.page.locator("#note-a")).to_be_empty()

    def test_mobile_reflow_and_evidence_mode(self):
        for width in (375, 320):
            self.page.set_viewport_size({"width": width, "height": 780})
            expect(self.page.get_by_role("group", name="Mobile content")).to_be_visible()
            self.page.get_by_role("group", name="Mobile content").get_by_role("button", name="Evidence").click()
            expect(self.page.get_by_test_id("evidence-list")).to_be_visible()
            self.assertFalse(self.page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2"))
            self.page.get_by_role("group", name="Mobile content").get_by_role("button", name="Map").click()
            expect(self.page.get_by_test_id("schematic-map")).to_be_visible()
            self.assertFalse(self.page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2"))
        self.page.emulate_media(reduced_motion="reduce")
        self.assertEqual(
            self.page.locator(".diagram-pin.comparable-pin").first.evaluate(
                "el => getComputedStyle(el).transitionDuration"), "0s"
        )

    def test_vector_renderer_is_local_and_has_no_data_privilege(self):
        self.page.get_by_test_id("choose-vector").click()
        self.page.get_by_test_id("vector-renderer").or_(self.page.get_by_test_id("webgl-fallback")).wait_for(timeout=12000)
        # CI should prove normal production ESM WebGL works, not merely fallback.
        if os.environ.get('HPI_REQUIRE_WEBGL') == '1':
            expect(self.page.get_by_test_id('webgl-ready')).to_be_visible(timeout=20000)
        # A software-rendered CI GPU may not support WebGL2, in which case the
        # explicitly designed fallback must remain usable and honest.
        self.page.get_by_test_id("webgl-ready").or_(
            self.page.get_by_test_id("webgl-fallback")
        ).wait_for(timeout=15000)
        expect(self.page.get_by_test_id("evidence-list")).to_be_visible()
        expect(self.page.get_by_test_id("evidence-c1")).to_contain_text("$525,000.01")
        self.page.get_by_test_id("choose-svg").click()
        expect(self.page.get_by_test_id("schematic-map")).to_be_visible()

    def test_capture_comparative_screenshots(self):
        folder = os.environ.get("HPI_SPIKE_SCREENSHOTS")
        if not folder:
            self.skipTest("Screenshots only in review CI")
        target = Path(folder)
        target.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(target / "01-react-editorial-svg-desktop.png"), full_page=True)
        self.page.get_by_role("group", name="Visual style").get_by_role("button", name="Intelligence").click()
        self.page.screenshot(path=str(target / "02-react-intelligence-svg-desktop.png"), full_page=True)
        self.page.get_by_test_id("choose-vector").click()
        self.page.get_by_test_id("webgl-ready").or_(
            self.page.get_by_test_id("webgl-fallback")
        ).wait_for(timeout=15000)
        self.page.screenshot(path=str(target / "03-react-vector-desktop.png"), full_page=True)
        self.page.set_viewport_size({"width": 375, "height": 780})
        self.page.get_by_test_id("choose-svg").click()
        self.page.screenshot(path=str(target / "04-react-editorial-mobile.png"), full_page=True)


if __name__ == "__main__":
    unittest.main()
