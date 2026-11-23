"""Standalone high-fidelity UI study; file:// only, synthetic schematic geometry.

These checks do not replace the browser->HTTP->SQLite acceptance tests and do
not approve a final visual identity, geographic parcel map or framework.
"""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = (ROOT / "design-prototypes" / "map-evidence-studio.html").as_uri()


class MapEvidenceVisualStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = sync_playwright().start()
        cls.browser = cls.driver.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.driver.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.page = self.context.new_page()
        self.console_errors = []
        self.requests = []
        self.page.on("pageerror", lambda error: self.console_errors.append(str(error)))
        self.page.on("request", lambda request: self.requests.append(request.url))
        self.page.goto(PROTOTYPE)
        expect(self.page.locator("body")).to_have_attribute("data-theme", "editorial")

    def tearDown(self):
        self.assertEqual(self.console_errors, [], "Browser JavaScript errors")
        self.assertTrue(
            all(url.startswith("file://") or url.startswith("data:") for url in self.requests),
            "Standalone study must not request remote tiles, fonts, geocoders or scripts",
        )
        self.context.close()

    def test_supported_map_and_linked_comparables(self):
        expect(self.page.locator("#map-pins .map-pin")).to_have_count(4)
        expect(self.page.locator("#comp-list .comp-card")).to_have_count(3)
        self.page.locator('#map-pins [data-marker="2"]').click()
        expect(self.page.locator('#map-pins [data-marker="2"]')).to_have_attribute(
            "aria-pressed", "true"
        )
        expect(self.page.locator('#comp-list [data-comp="2"]')).to_have_attribute(
            "aria-pressed", "true"
        )
        expect(self.page.locator("#comp-details")).to_contain_text(
            "Invented earlier completed sale"
        )
        self.page.locator('#comp-list [data-comp="3"]').click()
        expect(self.page.locator('#map-pins [data-marker="3"]')).to_have_attribute(
            "aria-pressed", "true"
        )
        expect(self.page.locator("#comp-details")).to_contain_text(
            "Invented prior sale"
        )

    def test_distinct_visual_directions_are_interactive(self):
        self.page.locator('[data-theme-option="precision"]').click()
        expect(self.page.locator("body")).to_have_attribute("data-theme", "precision")
        expect(self.page.locator('[data-theme-option="precision"]')).to_have_attribute(
            "aria-pressed", "true"
        )
        self.assertEqual(
            self.page.locator(".map-shell").evaluate("(el) => getComputedStyle(el).gridColumnStart"),
            "2",
        )
        self.page.locator('[data-theme-option="editorial"]').click()
        expect(self.page.locator("body")).to_have_attribute("data-theme", "editorial")
        expect(self.page.locator('[data-theme-option="editorial"]')).to_have_attribute(
            "aria-pressed", "true"
        )

    def test_insufficient_data_clears_stale_markers_and_prices(self):
        self.page.locator('#map-pins [data-marker="2"]').click()
        self.page.locator("#swap-property").click()
        expect(self.page.locator("#subject-title")).to_have_text("105 Fictional Court")
        expect(self.page.locator("#map-pins .map-pin")).to_have_count(1)
        expect(self.page.locator("#comp-list .comp-card")).to_have_count(0)
        expect(self.page.locator("#evidence-state")).to_contain_text("Insufficient data")
        expect(self.page.locator(".evidence-empty")).to_contain_text("Not enough evidence")
        expect(self.page.locator("#evidence-warning")).to_contain_text(
            "Do not infer that the asking price"
        )
        self.page.locator("#swap-property").click()
        expect(self.page.locator("#map-pins .map-pin")).to_have_count(4)

    def test_workspace_shortlist_and_notes_are_demo_only(self):
        self.page.locator('.topnav [data-view="workspace"]').click()
        expect(self.page.locator("#view-workspace")).to_be_visible()
        self.page.locator("#workspace-shortlist").click()
        expect(self.page.locator("#view-shortlist")).to_be_visible()
        expect(self.page.locator("#compare-table")).to_be_visible()
        self.page.locator("#notes-b").fill("Example note about missing evidence.")
        expect(self.page.locator("#note-b-state")).to_contain_text("Not saved to SQLite")
        self.page.locator('[data-shortlist-mode="map"]').click()
        expect(self.page.locator("#compare-map")).to_be_visible()
        expect(self.page.locator("#compare-table")).to_be_hidden()
        self.page.locator('#view-shortlist [data-open-property="b"]').click()
        expect(self.page.locator("#subject-title")).to_have_text("105 Fictional Court")
        expect(self.page.locator("#comp-list .comp-card")).to_have_count(0)

    def test_mobile_map_list_and_reduced_motion(self):
        self.page.set_viewport_size({"width": 375, "height": 812})
        expect(self.page.locator(".mobile-tab")).to_be_visible()
        self.page.locator('[data-mobile="list"]').click()
        expect(self.page.locator(".evidence-shell")).to_be_visible()
        expect(self.page.locator(".map-shell")).to_be_hidden()
        self.page.locator('[data-mobile="map"]').click()
        expect(self.page.locator(".map-shell")).to_be_visible()
        expect(self.page.locator(".evidence-shell")).to_be_hidden()
        for name in ("investigation", "workspace", "shortlist", "methodology"):
            self.page.locator('.topnav [data-view="' + (name if name != "methodology" else "investigation") + '"]').click()
            if name == "methodology":
                self.page.locator("#method-link").click()
            self.assertFalse(
                self.page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2"),
                "Page-wide overflow on mobile view: " + name,
            )

    def test_fake_geography_and_no_current_valuation_disclosed(self):
        source = (ROOT / "design-prototypes" / "map-evidence-studio.html").read_text(encoding="utf-8")
        self.assertNotIn("https://", source)
        self.assertNotIn("http://", source)
        expect(self.page.locator(".notice")).to_contain_text("not to scale")
        expect(self.page.locator(".map-caption")).to_contain_text("No geographic measurements")
        self.page.locator('.topnav [data-view="shortlist"]').click()
        expect(self.page.locator("#compare-table")).to_contain_text("Not produced")


if __name__ == "__main__":
    unittest.main()
