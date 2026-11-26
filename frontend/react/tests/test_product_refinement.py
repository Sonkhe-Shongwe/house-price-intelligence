import os
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from test_persistent_restart import LocalFixtureProcess,free_port
class ProductRefinementTests(unittest.TestCase):
    def test_evidence_details_and_accessible_comparison(self):
        server=LocalFixtureProcess(free_port(),database=None)
        with sync_playwright() as pw:
            opts={"headless":True,"args":["--no-sandbox"]}
            if os.environ.get("HPI_BROWSER_EXECUTABLE"):opts["executable_path"]=os.environ["HPI_BROWSER_EXECUTABLE"]
            browser=pw.chromium.launch(**opts)
            try:
                page=browser.new_page(viewport={"width":1440,"height":900})
                page.goto(server.base+"/")
                page.get_by_test_id("workspace-new-investigation").click()
                page.get_by_test_id("buyer-manual-pin").fill("00000000000001")
                page.get_by_test_id("buyer-create").click()
                expect(page.get_by_test_id("buyer-result")).to_be_visible()
                sale=page.get_by_test_id("buyer-sale").first
                sale.focus();page.keyboard.press("Enter")
                expect(sale).to_have_attribute("aria-pressed","true")
                expect(page.get_by_test_id("sale-evidence-detail")).to_contain_text("Area difference")
                expect(page.get_by_test_id("sale-evidence-detail")).to_contain_text("Age at analysis")
                expect(page.get_by_test_id("evidence-profile")).to_be_visible()
                folder=os.environ.get("HPI_WORKSPACE_SCREENSHOTS")
                if folder:
                    Path(folder).mkdir(parents=True,exist_ok=True)
                    page.get_by_test_id("buyer-result").screenshot(path=str(Path(folder)/"03-evidence-refinement.png"))
                page.get_by_test_id("dossier-compare").click()
                page.get_by_test_id("workspace-create").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("0 / 3")
                page.get_by_test_id("workspace-add-current").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("1 / 3")
                page.get_by_test_id("nav-investigate").click()
                page.get_by_test_id("buyer-manual-pin").fill("99999999999999")
                page.get_by_test_id("buyer-create").click()
                expect(page.get_by_test_id("buyer-insufficient")).to_be_visible()
                page.get_by_test_id("dossier-compare").click()
                page.get_by_test_id("workspace-add-current").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("2 / 3")
                table=page.get_by_role("table",name="Saved property comparison")
                expect(table).to_be_visible()
                expect(table.get_by_role("columnheader")).to_have_count(3)
                expect(table.get_by_role("rowheader",name="Valuation")).to_be_visible()
                expect(table.get_by_role("cell",name="Not produced")).to_have_count(2)
                if folder:page.get_by_test_id("workspace-comparison").screenshot(path=str(Path(folder)/"04-comparison-refinement.png"))
                page.set_viewport_size({"width":320,"height":800})
                region=page.get_by_role("region",name="Property evidence comparison, scroll horizontally if needed")
                region.focus();expect(region).to_be_focused()
                self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth+2"))
                self.assertTrue(region.evaluate("e=>e.scrollWidth>e.clientWidth"))
            finally:browser.close();server.close()
