"""Actual canonical launcher, real browser, optional virtual map and frozen evidence."""
import os
import unittest
from pathlib import Path
from playwright.sync_api import expect, sync_playwright
from test_persistent_restart import LocalFixtureProcess, free_port

class GeographicIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=LocalFixtureProcess(free_port(),database=None,synthetic_map=True)
        cls.driver=sync_playwright().start()
        options={"args":["--no-sandbox","--enable-unsafe-swiftshader","--use-angle=swiftshader"]}
        if os.environ.get("HPI_BROWSER_EXECUTABLE"):
            options["executable_path"]=os.environ["HPI_BROWSER_EXECUTABLE"]
        cls.browser=cls.driver.chromium.launch(headless=True,**options)
    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.driver.stop()
        cls.server.close()
    def setUp(self):
        self.context=self.browser.new_context(viewport={"width":1366,"height":850})
        self.page=self.context.new_page()
        self.external=[]
        self.page.on("request",lambda r:self.external.append(r.url) if not r.url.startswith(self.server.base+"/") else None)
        self.page.goto(self.server.base+"/buyer-workflow")
    def tearDown(self):
        self.context.close()
        self.assertEqual(self.external,[])
    def save(self,pin="00000000000001"):
        self.page.get_by_test_id("buyer-manual-pin").fill(pin)
        self.page.get_by_test_id("buyer-create").click()
        expect(self.page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
        return self.page.get_by_test_id("buyer-saved-id").inner_text()
    def test_map_and_sale_selection_and_frozen_identity(self):
        iid=self.save()
        before=self.server.get("/v1/investigations/"+iid)
        self.page.get_by_test_id("geo-load").click()
        expect(self.page.get_by_test_id("geo-ready")).to_be_visible(timeout=20000)
        expect(self.page.get_by_test_id("geo-pin-0")).to_be_visible()
        self.page.get_by_test_id("geo-pin-2").click()
        expect(self.page.get_by_test_id("buyer-sale").nth(1)).to_have_attribute("aria-pressed","true")
        self.page.get_by_test_id("buyer-sale").nth(0).click()
        expect(self.page.get_by_test_id("geo-pin-1")).to_have_attribute("aria-pressed","true")
        self.page.get_by_test_id("evidence-next").click()
        expect(self.page.get_by_test_id("geo-pin-2")).to_have_attribute("aria-pressed","true")
        self.page.get_by_test_id("evidence-previous").click()
        expect(self.page.get_by_test_id("geo-pin-1")).to_have_attribute("aria-pressed","true")
        self.page.get_by_role("button",name="Zoom in fictional map").click()
        self.page.get_by_role("button",name="Reset fictional map view").click()
        expect(self.page.get_by_test_id("geo-pin-1")).to_have_attribute("aria-pressed","true")
        expect(self.page.locator(".geo-themed")).to_have_attribute("data-map-theme","atlas")
        self.page.get_by_role("button",name="Terminal",exact=True).click()
        expect(self.page.get_by_test_id("geo-ready")).to_be_visible(timeout=20000)
        expect(self.page.get_by_test_id("geo-pin-1")).to_have_attribute("aria-pressed","true")
        expect(self.page.locator(".geo-themed")).to_have_attribute("data-map-theme","terminal")
        self.page.get_by_test_id("geo-pin-3").click()
        expect(self.page.get_by_test_id("buyer-sale").nth(2)).to_have_attribute("aria-pressed","true")
        path=os.environ.get("HPI_GEO_SCREENSHOTS")
        if path:
            Path(path).mkdir(parents=True,exist_ok=True)
            self.page.get_by_test_id("geo-panel").screenshot(path=str(Path(path)/"02-terminal-virtual-map.png"))
        self.page.get_by_role("button",name="Atlas",exact=True).click()
        expect(self.page.get_by_test_id("geo-ready")).to_be_visible(timeout=20000)
        expect(self.page.get_by_test_id("geo-pin-3")).to_have_attribute("aria-pressed","true")
        self.assertEqual(before,self.server.get("/v1/investigations/"+iid))
        path=os.environ.get("HPI_GEO_SCREENSHOTS")
        if path:
            Path(path).mkdir(parents=True,exist_ok=True)
            self.page.get_by_test_id("buyer-result").screenshot(path=str(Path(path)/"01-linked-fictional-map.png"))
        self.save("99999999999999")
        expect(self.page.get_by_test_id("geo-pin-1")).to_have_count(0)
        self.page.get_by_test_id("geo-load").click()
        expect(self.page.get_by_test_id("geo-unavailable")).to_be_visible()
        expect(self.page.get_by_test_id("geo-static-fallback")).to_have_count(0)
    def test_lightweight_choice_reuses_verified_response_without_gpu(self):
        iid=self.save()
        before=self.server.get("/v1/investigations/"+iid)
        requests=[]
        self.page.on("request",lambda r:requests.append(r.url))
        self.page.get_by_test_id("geo-load-schematic").click()
        expect(self.page.get_by_test_id("geo-static-fallback")).to_be_visible()
        expect(self.page.get_by_test_id("geo-mode-schematic")).to_have_attribute("aria-pressed","true")
        expect(self.page.get_by_test_id("geo-vector")).to_have_count(0)
        self.assertFalse(any("GeoVectorMap-" in r or "maplibre-gl-worker-" in r for r in requests))
        self.page.get_by_test_id("geo-static-rank-1").focus()
        self.page.keyboard.press("Enter")
        expect(self.page.get_by_test_id("geo-selected-sale")).to_contain_text("$525,000.00")
        expect(self.page.get_by_test_id("buyer-sale").first).to_have_attribute("aria-pressed","true")
        self.page.get_by_test_id("geo-mode-interactive").click()
        expect(self.page.get_by_test_id("geo-ready")).to_be_visible(timeout=20000)
        expect(self.page.get_by_test_id("geo-pin-1")).to_have_attribute("aria-pressed","true")
        self.page.get_by_test_id("geo-pin-2").click()
        self.page.get_by_test_id("geo-mode-schematic").click()
        expect(self.page.get_by_test_id("geo-static-rank-2")).to_have_attribute("aria-pressed","true")
        expect(self.page.get_by_test_id("geo-mode-schematic")).to_be_focused()
        expect(self.page.get_by_test_id("geo-vector")).to_have_count(0)
        self.assertEqual(sum(r.endswith("/"+iid+"/map") for r in requests),1)
        self.assertEqual(before,self.server.get("/v1/investigations/"+iid))
        self.page.set_viewport_size({"width":320,"height":800})
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth<=innerWidth+2"))
        path=os.environ.get("HPI_GEO_SCREENSHOTS")
        if path:
            Path(path).mkdir(parents=True,exist_ok=True)
            self.page.get_by_test_id("geo-panel").screenshot(path=str(Path(path)/"04-selected-lightweight-320.png"))

    def test_context_loss_releases_renderer_and_preserves_keyboard_selection(self):
        iid=self.save()
        before=self.server.get("/v1/investigations/"+iid)
        self.page.get_by_test_id("geo-load").click()
        expect(self.page.get_by_test_id("geo-ready")).to_be_visible(timeout=20000)
        marker=self.page.get_by_test_id("geo-pin-2")
        marker.focus();self.page.keyboard.press("Enter")
        expect(marker).to_have_attribute("aria-pressed","true")
        # Dispatch a synthetic context-lost event through the real renderer listener.
        self.page.locator(".geo-canvas canvas").evaluate("e=>e.dispatchEvent(new Event('webglcontextlost',{cancelable:true}))")
        expect(self.page.get_by_test_id("geo-fallback")).to_be_visible(timeout=20000)
        expect(self.page.locator(".geo-canvas canvas")).to_have_count(0)
        expect(self.page.get_by_test_id("geo-fallback")).to_be_focused()
        expect(self.page.get_by_test_id("geo-static-rank-2")).to_have_attribute("aria-pressed","true")
        self.assertEqual(before,self.server.get("/v1/investigations/"+iid))

    def test_touch_context_supports_lightweight_selection(self):
        with self.browser.new_context(viewport={"width":375,"height":850},has_touch=True,is_mobile=True,reduced_motion="reduce") as ctx:
            page=ctx.new_page()
            page.on("request",lambda r:self.external.append(r.url) if not r.url.startswith(self.server.base+"/") else None)
            page.goto(self.server.base+"/buyer-workflow")
            page.get_by_test_id("buyer-manual-pin").fill("00000000000001")
            page.get_by_test_id("buyer-create").tap()
            expect(page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
            page.get_by_test_id("geo-load-schematic").tap()
            expect(page.get_by_test_id("geo-static-fallback")).to_be_visible()
            rank=page.get_by_test_id("geo-static-rank-3")
            rank.tap()
            expect(rank).to_have_attribute("aria-pressed","true")
            expect(page.get_by_test_id("buyer-sale").nth(2)).to_have_attribute("aria-pressed","true")
            self.assertGreaterEqual(rank.evaluate("e=>e.getBoundingClientRect().height"),44)
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth<=innerWidth+2"))

    def test_tampered_map_identity_is_rejected(self):
        iid=self.save()
        route=self.server.base+"/v1/investigations/"+iid+"/map"
        def tamper(r):
            data=r.fetch().json()
            data["feature_collection"]["features"][1]["properties"]["pin"]="99999999999999"
            r.fulfill(json=data)
        self.page.route(route,tamper)
        self.page.get_by_test_id("geo-load").click()
        expect(self.page.get_by_test_id("geo-error")).to_be_visible()
        expect(self.page.get_by_test_id("geo-vector")).to_have_count(0)
        expect(self.page.get_by_test_id("geo-static-fallback")).to_have_count(0)
        expect(self.page.get_by_test_id("buyer-sale")).to_have_count(3)
    def test_missing_optional_bundle_does_not_crash_buyer(self):
        self.save()
        self.page.route("**/assets/GeoVectorMap-*.js",lambda r:r.abort())
        self.page.get_by_test_id("geo-load").click()
        expect(self.page.get_by_test_id("geo-bundle-fallback")).to_be_visible(timeout=15000)
        expect(self.page.get_by_test_id("geo-static-fallback")).to_be_visible()
        sale=self.page.get_by_test_id("geo-static-rank-2")
        sale.focus();self.page.keyboard.press("Enter")
        expect(sale).to_be_focused()
        expect(self.page.get_by_test_id("buyer-sale").nth(1)).to_have_attribute("aria-pressed","true")
        expect(self.page.get_by_test_id("geo-static-point-2")).to_have_attribute("data-selected","true")
        expect(self.page.get_by_test_id("buyer-sale")).to_have_count(3)
        self.page.get_by_test_id("buyer-sale").nth(1).click()
        expect(self.page.get_by_test_id("buyer-sale").nth(1)).to_have_attribute("aria-pressed","true")

    def test_renderer_failure_keeps_evidence_and_mobile_reflow(self):
        self.page.set_viewport_size({"width":320,"height":800})
        self.page.add_init_script("""const orig=HTMLCanvasElement.prototype.getContext;
          HTMLCanvasElement.prototype.getContext=function(t,...a){
            if(t==='webgl'||t==='webgl2'||t==='experimental-webgl')return null;
            return orig.call(this,t,...a);
          };""")
        self.page.reload()
        self.save()
        self.page.get_by_test_id("geo-load").click()
        expect(self.page.get_by_test_id("geo-fallback")).to_be_visible(timeout=20000)
        expect(self.page.get_by_test_id("geo-static-fallback")).to_be_visible()
        self.page.get_by_test_id("geo-static-rank-3").click()
        expect(self.page.get_by_test_id("buyer-sale").nth(2)).to_have_attribute("aria-pressed","true")
        self.page.get_by_test_id("evidence-previous").click()
        expect(self.page.get_by_test_id("geo-static-rank-2")).to_have_attribute("aria-pressed","true")
        path=os.environ.get("HPI_GEO_SCREENSHOTS")
        if path:
            Path(path).mkdir(parents=True,exist_ok=True)
            self.page.get_by_test_id("geo-static-fallback").screenshot(path=str(Path(path)/"03-virtual-fallback-320.png"))
        expect(self.page.get_by_test_id("buyer-sale")).to_have_count(3)
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"))
