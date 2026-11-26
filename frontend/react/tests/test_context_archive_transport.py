"""Same-origin Chromium transport qualification, no tiles or archive parser."""
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
                iid=page.get_by_test_id("buyer-saved-id").inner_text()
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
