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
                page.get_by_test_id("evidence-jump").click()
                expect(page.get_by_test_id("buyer-result")).to_be_focused()
                expect(page.get_by_test_id("evidence-position")).to_have_text("Choose a sale")
                expect(page.get_by_test_id("evidence-previous")).to_have_attribute("aria-disabled","true")
                nxt=page.get_by_test_id("evidence-next")
                nxt.focus();page.keyboard.press("Enter")
                expect(nxt).to_be_focused()
                expect(page.get_by_test_id("evidence-position")).to_have_text("Sale 1 of 3")
                nxt.click();nxt.click()
                expect(nxt).to_have_attribute("aria-disabled","true")
                expect(page.get_by_test_id("buyer-sale").nth(2)).to_have_attribute("aria-pressed","true")
                page.keyboard.press("Enter")
                expect(page.get_by_test_id("evidence-position")).to_have_text("Sale 3 of 3")
                page.get_by_test_id("evidence-previous").click()
                expect(page.get_by_test_id("evidence-position")).to_have_text("Sale 2 of 3")
                sale=page.get_by_test_id("buyer-sale").first
                sale.focus();page.keyboard.press("Enter")
                expect(sale).to_have_attribute("aria-pressed","true")
                expect(page.get_by_test_id("sale-evidence-detail")).to_contain_text("Area difference")
                expect(page.get_by_test_id("sale-evidence-detail")).to_contain_text("Age at analysis")
                expect(page.get_by_test_id("evidence-profile")).to_be_visible()
                folder=os.environ.get("HPI_WORKSPACE_SCREENSHOTS")
                for width,height in ((1440,900),(1366,850),(1024,768),(768,1024),(375,800),(320,800),(800,375)):
                    page.set_viewport_size({"width":width,"height":height})
                    self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth+2"),f"dossier overflow at {width}x{height}")
                    expect(page.get_by_test_id("buyer-sale").first).to_contain_text("$525,000.00")
                    if width==320:
                        disclosure=page.get_by_test_id("buyer-provenance-details")
                        expect(disclosure).not_to_have_attribute("open","")
                        expect(page.get_by_text("Building identity unverified. Historical source availability not established.",exact=False)).to_be_visible()
                        disclosure.locator("summary").focus();page.keyboard.press("Enter")
                        expect(disclosure).to_have_attribute("open","")
                        expect(page.get_by_test_id("buyer-saved-id")).to_be_visible()
                        page.keyboard.press("Enter")
                        expect(disclosure).not_to_have_attribute("open","")
                    self.assertGreaterEqual(page.get_by_test_id("evidence-next").bounding_box()["height"],44)
                    if folder and width in (1024,768,320):
                        Path(folder).mkdir(parents=True,exist_ok=True)
                        page.get_by_test_id("buyer-result").screenshot(path=str(Path(folder)/f"dossier-{width}.png"))
                page.set_viewport_size({"width":1440,"height":900})
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
                expect(page.get_by_test_id("evidence-navigation")).to_have_count(0)
                page.get_by_test_id("dossier-compare").click()
                page.get_by_test_id("workspace-add-current").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("2 / 3")
                table=page.get_by_role("table",name="Saved property comparison")
                expect(table).to_be_visible()
                expect(table.get_by_role("columnheader")).to_have_count(3)
                expect(table.get_by_role("rowheader",name="Valuation")).to_be_visible()
                expect(table.get_by_role("cell",name="Not produced")).to_have_count(2)
                if folder:page.get_by_test_id("workspace-comparison").screenshot(path=str(Path(folder)/"04-comparison-refinement.png"))
                region=page.get_by_role("region",name="Property evidence comparison, scroll horizontally if needed")
                for width,height in ((1440,900),(1366,850),(1024,768),(768,1024),(375,800),(320,800),(800,375)):
                    page.set_viewport_size({"width":width,"height":height})
                    region.focus();expect(region).to_be_focused()
                    self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth+2"),f"comparison overflow at {width}x{height}")
                    self.assertTrue(region.evaluate("e=>e.scrollWidth<=e.clientWidth+1"))
                    expect(region.locator("..").locator(".hpi-scroll-hint")).to_have_count(0)
                    # This summary matrix compares buyer inputs, not individual completed sale prices.
                    expect(table.get_by_role("row").filter(has=page.get_by_role("rowheader",name="Asking price (buyer-reported)",exact=True)).get_by_role("cell",name="$500,000.00",exact=True)).to_have_count(2)
                    if folder and width in (1024,768,320):page.get_by_test_id("workspace-comparison").screenshot(path=str(Path(folder)/f"comparison-{width}.png"))
                expect(table.get_by_role("columnheader")).to_have_count(3)
                expect(table.get_by_role("rowheader",name="Valuation")).to_be_visible()
            finally:browser.close();server.close()
