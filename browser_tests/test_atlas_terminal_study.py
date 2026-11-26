"""Offline art-direction candidate; not production app acceptance."""
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from playwright.sync_api import sync_playwright, expect

HTML = Path(__file__).resolve().parents[1] / "design-prototypes/hpi-atlas-terminal-study.html"

class AtlasTerminalStudy(unittest.TestCase):
    def test_two_concepts_full_journey(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(viewport={"width":1440,"height":1000})
                errors, external = [], []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("request", lambda r: external.append(r.url) if r.url.startswith(("http:","https:")) else None)
                page.goto(HTML.as_uri())
                shots = os.environ.get("HPI_DESIGN_SCREENSHOTS")
                def shot(name):
                    if shots:
                        Path(shots).mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(Path(shots) / (name+".png")), full_page=True)
                def click(action):
                    page.locator('[data-action="'+action+'"]').first.click()
                def find(address):
                    click("nav-investigate")
                    page.locator("#query").fill(address)
                    click("search")
                    click("candidate")
                def no_overflow():
                    self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
                expect(page.get_by_role("heading",name="Look beyond the asking price.")).to_be_visible()
                shot("atlas-sign-in")
                click("enter")
                expect(page.get_by_text("No investigations yet")).to_be_visible()
                shot("atlas-empty-workspace")
                find("1 Fictional Court")
                expect(page.get_by_text("No geographic evidence to display.")).to_be_visible()
                expect(page.locator(".sale")).to_have_count(3)
                expect(page.locator(".sale strong").first).to_have_text("$525,000.01")
                shot("atlas-no-geometry")
                click("geometry")
                page.locator(".pins [data-action=rank-2]").click()
                expect(page.locator(".sale[data-action=rank-2]")).to_have_attribute("aria-pressed","true")
                expect(page.get_by_text("WHY SALE 02 QUALIFIES")).to_be_visible()
                shot("atlas-dossier")
                page.locator("#theme").click()
                expect(page.locator("body")).to_have_class("terminal")
                expect(page.locator(".pins [data-action=rank-2]")).to_have_attribute("aria-pressed","true")
                shot("terminal-dossier")
                click("save")
                click("add")
                find("2 Fictional Court")
                expect(page.locator(".sale")).to_have_count(0)
                expect(page.locator(".pins button")).to_have_count(0)
                expect(page.get_by_text("Insufficient historical evidence",exact=True)).to_be_visible()
                shot("terminal-insufficient")
                click("add")
                click("nav-compare")
                page.locator("[data-note='1']").fill("Illustrative note")
                click("save-comparison")
                expect(page.get_by_text("Saved for this review session.")).to_be_visible()
                shot("terminal-compare")
                page.locator("#theme").click()
                expect(page.locator("[data-note='1']")).to_have_value("Illustrative note")
                shot("atlas-compare")
                click("nav-saved")
                expect(page.locator(".list .line")).to_have_count(2)
                shot("atlas-saved")
                click("open-1")
                for width in (375,320):
                    page.set_viewport_size({"width":width,"height":850})
                    no_overflow()
                    click("mobile-map")
                    expect(page.locator(".mapstage")).to_be_visible()
                    no_overflow()
                    shot("atlas-mobile-map-"+str(width))
                    click("mobile-evidence")
                    expect(page.locator(".sale").first).to_be_visible()
                    no_overflow()
                    shot("atlas-mobile-evidence-"+str(width))
                click("nav-workspace")
                expect(page.get_by_text("My property comparison")).to_be_visible()
                page.locator("#exit").click()
                click("enter")
                expect(page.get_by_text("No investigations yet")).to_be_visible()
                self.assertEqual(errors, [])
                self.assertEqual(external, [])
            finally:
                browser.close()
