"""Real browser: workspace navigation, durable discovery, draft preservation."""
import os
import tempfile
import unittest
from pathlib import Path
from playwright.sync_api import expect,sync_playwright
from test_persistent_restart import LocalFixtureProcess,free_port

class WorkspaceNavigationTests(unittest.TestCase):
    def test_returning_buyer_history_compare_drafts_and_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"workspace.sqlite"
            port=free_port()
            server=LocalFixtureProcess(port,database=path)
            driver=sync_playwright().start()
            opts={"args":["--no-sandbox"]}
            if os.environ.get("HPI_BROWSER_EXECUTABLE"):opts["executable_path"]=os.environ["HPI_BROWSER_EXECUTABLE"]
            browser=driver.chromium.launch(headless=True,**opts)
            page=browser.new_page(viewport={"width":1440,"height":900})
            try:
                page.goto(server.base+"/")
                expect(page.get_by_test_id("history-empty")).to_be_visible()
                expect(page.get_by_test_id("nav-home")).to_have_attribute("aria-current","page")
                page.get_by_test_id("workspace-new-investigation").click()
                expect(page.locator("#hpi-content")).to_be_focused()
                def save(pin):
                    page.get_by_test_id("buyer-manual-pin").fill(pin)
                    page.get_by_test_id("buyer-create").click()
                    expect(page.get_by_test_id("buyer-result")).to_be_visible()
                    return page.get_by_test_id("buyer-saved-id").inner_text()
                first=save("00000000000001")
                page.get_by_test_id("dossier-compare").click()
                page.get_by_test_id("workspace-create").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("0 / 3")
                sid=page.get_by_test_id("workspace-id").inner_text()
                page.get_by_test_id("workspace-add-current").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("1 / 3")
                note=page.get_by_test_id("workspace-note").first
                note.fill("Draft survives navigation")
                page.get_by_test_id("nav-investigate").click()
                weak=save("99999999999999")
                page.get_by_test_id("nav-saved").click()
                expect(page.get_by_test_id("history-open")).to_have_count(2)
                page.get_by_test_id("history-status-filter").select_option("insufficient_data")
                expect(page.get_by_test_id("history-open")).to_have_count(1)
                page.get_by_test_id("history-search").fill("99999999999999")
                expect(page.get_by_test_id("history-open")).to_have_count(1)
                page.get_by_test_id("history-open").click()
                expect(page.get_by_test_id("buyer-saved-id")).to_have_text(weak)
                expect(page.get_by_test_id("buyer-insufficient")).to_be_visible()
                page.get_by_test_id("dossier-compare").click()
                expect(note).to_have_value("Draft survives navigation")
                expect(page.get_by_test_id("workspace-note-state").first).to_have_text("Unsaved changes")
                page.get_by_test_id("workspace-add-current").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("2 / 3")
                expect(note).to_have_value("Draft survives navigation")
                page.get_by_test_id("workspace-save-note").first.click()
                expect(page.get_by_test_id("workspace-note-state").first).to_have_text("Saved note verified")
                page.get_by_test_id("nav-home").click()
                expect(page.get_by_test_id("history-open")).to_have_count(2)
                path_env=os.environ.get("HPI_WORKSPACE_SCREENSHOTS")
                if path_env:
                    dest=Path(path_env);dest.mkdir(parents=True,exist_ok=True)
                    page.screenshot(path=str(dest/"01-workspace-desktop.png"),full_page=True)
                for width in (375,320):
                    page.set_viewport_size({"width":width,"height":800})
                    self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth+2"))
                    page.get_by_test_id("nav-methodology").focus()
                    page.keyboard.press("Enter")
                    expect(page.get_by_test_id("methodology")).to_be_visible()
                    expect(page.locator("#hpi-content")).to_be_focused()
                    self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth+2"))
                    page.get_by_test_id("nav-home").click()
                if path_env:page.screenshot(path=str(dest/"02-workspace-mobile.png"),full_page=True)
                original=server.get("/v1/investigations/"+first)
                page.close();server.close()
                server=LocalFixtureProcess(port,database=path)
                page=browser.new_page()
                page.goto(server.base+"/")
                expect(page.get_by_test_id("history-open")).to_have_count(2)
                page.get_by_test_id("nav-saved").click()
                page.get_by_test_id("history-search").fill("00000000000001")
                expect(page.get_by_test_id("history-open")).to_have_count(1)
                page.get_by_test_id("history-open").click()
                expect(page.get_by_test_id("buyer-saved-id")).to_have_text(first)
                self.assertEqual(server.get("/v1/investigations/"+first),original)
                page.get_by_test_id("dossier-compare").click()
                page.get_by_test_id("workspace-open-recent").click()
                expect(page.get_by_test_id("workspace-id")).to_have_text(sid)
                expect(page.get_by_test_id("workspace-note").first).to_have_value("Draft survives navigation")
            finally:
                browser.close();driver.stop();server.close()
