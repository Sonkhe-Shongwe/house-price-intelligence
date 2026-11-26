"""Same-origin transport and generated vector archive qualification, no external tiles."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect
from test_persistent_restart import LocalFixtureProcess, free_port


class ContextArchiveTransportTests(unittest.TestCase):
    def test_opt_in_range_transport_preserves_frozen_buyer_evidence(self):
        server=LocalFixtureProcess(free_port(),database=None,context_transport_fixture=True)
        self.addCleanup(server.close)
        with sync_playwright() as pw:
            options={"args":["--no-sandbox"]}
            if os.environ.get("HPI_BROWSER_EXECUTABLE"):
                options["executable_path"]=os.environ["HPI_BROWSER_EXECUTABLE"]
            browser=pw.chromium.launch(headless=True,**options)
            try:
                page=browser.new_page(viewport={"width":320,"height":800})
                urls=[]
                page.on("request",lambda request:urls.append(request.url))
                page.goto(server.base+"/buyer-workflow")
                page.get_by_test_id("buyer-manual-pin").fill("00000000000001")
                page.get_by_test_id("buyer-create").click()
                expect(page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
                history=server.get("/v1/investigations/history")["investigations"]
                self.assertEqual(len(history),1)
                iid=history[0]["investigation_id"]
                expect(page.get_by_test_id("buyer-saved-id")).to_have_text(iid)
                before=server.get("/v1/investigations/"+iid)
                self.assertFalse(any("/context/" in u for u in urls))
                report=page.evaluate("""async () => {
                  const url='/context/qualification-v1.pmtiles';
                  const head=await fetch(url,{method:'HEAD',cache:'no-store'});
                  const tag=head.headers.get('etag');
                  const partial=await fetch(url,{headers:{Range:'bytes=250-259','If-Match':tag}});
                  const body=Array.from(new Uint8Array(await partial.arrayBuffer()));
                  const full=await fetch(url);
                  const changed=await fetch(url,{headers:{Range:'bytes=0-3','If-Range':'"wrong"'}});
                  return {head:head.status,partial:partial.status,range:partial.headers.get('content-range'),
                    body,full:full.status,changed:changed.status,fixture:partial.headers.get('x-context-transport-fixture')};
                }""")
                self.assertEqual(report,{"head":200,"partial":206,"range":"bytes 250-259/16384",
                    "body":[250,251,252,253,254,255,0,1,2,3],"full":416,"changed":412,"fixture":"true"})
                self.assertEqual(before,server.get("/v1/investigations/"+iid))
                self.assertTrue(all(u.startswith(server.base+"/") for u in urls))
                self.assertFalse(any("GeoVectorMap-" in u for u in urls))
            finally:
                browser.close()

    def test_generated_contextual_vector_archive_render(self):
        server=LocalFixtureProcess(free_port(),database=None,context_transport_fixture=True)
        self.addCleanup(server.close)
        with sync_playwright() as pw:
            options={"args":["--no-sandbox","--enable-unsafe-swiftshader","--use-angle=swiftshader"]}
            if os.environ.get("HPI_BROWSER_EXECUTABLE"):
                options["executable_path"]=os.environ["HPI_BROWSER_EXECUTABLE"]
            browser=pw.chromium.launch(headless=True,**options)
            try:
                page=browser.new_page(viewport={"width":1366,"height":850},reduced_motion="reduce")
                urls=[]
                page.on("request",lambda req:urls.append(req.url))
                page.goto(server.base+"/context-preview")
                expect(page.get_by_test_id("context-preview")).to_be_visible()
                self.assertFalse(any(u.endswith(".pmtiles") for u in urls))
                page.get_by_test_id("context-load").focus()
                page.keyboard.press("Enter")
                expect(page.get_by_role("heading",name="Contextual vector map test")).to_be_focused()
                expect(page.get_by_test_id("context-ready")).to_be_visible(timeout=20000)
                self.assertTrue(any(u.endswith("/context/atlas-fixture-v1.pmtiles") for u in urls))
                self.assertTrue(all(u.startswith(server.base+"/") for u in urls))
                expect(page.get_by_test_id("geo-pin-0")).to_have_count(0)
                page.get_by_role("button",name="Zoom in",exact=True).click()
                page.get_by_role("button",name="Reset view").click()
                from pathlib import Path
                folder=os.environ.get("HPI_GEO_SCREENSHOTS")
                if folder:
                    Path(folder).mkdir(parents=True,exist_ok=True)
                    page.get_by_test_id("context-preview").screenshot(path=str(Path(folder)/"06-invented-context-atlas-desktop.png"))
                page.set_viewport_size({"width":320,"height":800})
                self.assertTrue(page.evaluate("document.documentElement.scrollWidth<=innerWidth+2"))
                if folder:
                    Path(folder).mkdir(parents=True,exist_ok=True)
                    page.get_by_test_id("context-preview").screenshot(path=str(Path(folder)/"05-invented-context-atlas-320.png"))
                page.get_by_role("button",name="Reset view").focus()
                page.locator(".geo-canvas canvas").evaluate("e=>e.dispatchEvent(new Event('webglcontextlost',{cancelable:true}))")
                expect(page.get_by_test_id("context-unavailable")).to_be_visible(timeout=15000)
                expect(page.get_by_test_id("context-unavailable")).to_be_focused()
                expect(page.locator(".geo-canvas canvas")).to_have_count(0)
                failed=browser.new_page(viewport={"width":320,"height":800})
                failed.route("**/context/atlas-fixture-v1.pmtiles",lambda route:route.abort())
                failed.goto(server.base+"/context-preview")
                failed.get_by_test_id("context-load").click()
                expect(failed.get_by_test_id("context-unavailable")).to_be_visible(timeout=20000)
            finally:
                browser.close()
