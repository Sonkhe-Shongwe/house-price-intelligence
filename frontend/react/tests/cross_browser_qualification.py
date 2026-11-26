"""Bounded FE6 lab qualification on the canonical invented-only application.
No external browser traffic, no real records, no runtime dependency or field Web Vitals.
Report aggregate timings and asset sizes only. Browser install failures are not passes.
"""
import gzip
import json
import os
from pathlib import Path
import time
from playwright.sync_api import sync_playwright, expect
from test_persistent_restart import LocalFixtureProcess, free_port

DIST=Path(__file__).resolve().parents[1]/"dist"

def bundle():
    assets=DIST/"assets"
    report={}
    # Generous, explicit regression ceilings, not performance SLAs. Map remains lazy.
    for kind,glob,ceiling in (("entry_js","index-*.js",110000),("entry_css","index-*.css",22000)):
        files=sorted(assets.glob(glob))
        if len(files)!=1:raise AssertionError(f"Unexpected {kind} asset inventory")
        raw=files[0].read_bytes()
        size=len(gzip.compress(raw,mtime=0))
        report[kind]={"bytes":len(raw),"gzip_bytes":size,"ceiling_gzip_bytes":ceiling}
        if size>ceiling:raise AssertionError(f"{kind} exceeds initial bundle ceiling: {size}")
    return report

def main():
    output=Path(os.environ["HPI_CROSS_BROWSER_REPORT"])
    report={"scope":"loopback fictional core buyer journey; no private cross-engine or GPU certification",
            "measurement":"single hosted lab run per engine, not field Web Vitals","status":"blocked","engines":[]}
    server=LocalFixtureProcess(free_port(),database=None)
    try:
        report["bundle"]=bundle()
        with sync_playwright() as pw:
            for name in ("firefox","webkit"):
                engine={"browser":name,"status":"failed"}
                report["engines"].append(engine)
                browser=getattr(pw,name).launch(headless=True)
                try:
                    engine["version"]=browser.version
                    page=browser.new_page(viewport={"width":1366,"height":850},reduced_motion="reduce")
                    requests=[];errors=[]
                    page.on("request",lambda req:requests.append(req.url))
                    page.on("pageerror",lambda error:errors.append(type(error).__name__))
                    start=time.perf_counter()
                    page.goto(server.base+"/")
                    expect(page.get_by_test_id("history-panel")).to_be_visible()
                    expect(page.get_by_test_id("history-empty")).to_be_visible()
                    engine["workspace_ready_ms"]=round((time.perf_counter()-start)*1000)
                    engine["navigation_timing"]=page.evaluate("""() => {
                        const n=performance.getEntriesByType('navigation')[0];
                        return n?{dom_content_loaded_ms:Math.round(n.domContentLoadedEventEnd),
                            load_event_ms:Math.round(n.loadEventEnd)}:null;
                    }""")
                    page.get_by_test_id("workspace-new-investigation").focus()
                    page.keyboard.press("Enter")
                    expect(page.locator("#hpi-content")).to_be_focused()
                    page.get_by_test_id("buyer-manual-pin").fill("00000000000001")
                    page.get_by_test_id("buyer-price").fill("530000.07")
                    start=time.perf_counter()
                    page.get_by_test_id("buyer-create").click()
                    expect(page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
                    engine["saved_evidence_ready_ms"]=round((time.perf_counter()-start)*1000)
                    expect(page.get_by_test_id("buyer-result")).to_contain_text("$530,000.07")
                    expect(page.get_by_test_id("buyer-sale").first).to_contain_text("$525,000.00")
                    iid=page.get_by_test_id("buyer-saved-id").inner_text()
                    before=server.get("/v1/investigations/"+iid)
                    page.get_by_test_id("evidence-jump").click()
                    expect(page.get_by_test_id("buyer-result")).to_be_focused()
                    page.get_by_test_id("evidence-next").focus();page.keyboard.press("Enter")
                    expect(page.get_by_test_id("evidence-position")).to_have_text("Sale 1 of 3")
                    expect(page.get_by_test_id("evidence-next")).to_be_focused()
                    page.get_by_test_id("dossier-compare").click()
                    page.get_by_test_id("workspace-create").click()
                    expect(page.get_by_test_id("workspace-count")).to_have_text("0 / 3")
                    page.get_by_test_id("workspace-add-current").click()
                    expect(page.get_by_test_id("workspace-count")).to_have_text("1 / 3")
                    note=page.get_by_test_id("workspace-note").first
                    note.fill("Engine qualification draft")
                    page.get_by_test_id("nav-investigate").click()
                    page.get_by_test_id("buyer-manual-pin").fill("99999999999999")
                    page.get_by_test_id("buyer-create").click()
                    expect(page.get_by_test_id("buyer-insufficient")).to_be_visible()
                    expect(page.get_by_test_id("evidence-navigation")).to_have_count(0)
                    page.get_by_test_id("dossier-compare").click()
                    expect(note).to_have_value("Engine qualification draft")
                    page.get_by_test_id("workspace-add-current").click()
                    expect(page.get_by_test_id("workspace-count")).to_have_text("2 / 3")
                    table=page.get_by_role("table",name="Saved property comparison")
                    expect(table).to_contain_text("$530,000.07")
                    expect(table.get_by_role("cell",name="Not produced")).to_have_count(2)
                    for width in (768,320):
                        page.set_viewport_size({"width":width,"height":800})
                        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+2"),f"{name}: overflow {width}"
                        expect(table.get_by_role("columnheader")).to_have_count(3)
                    assert before==server.get("/v1/investigations/"+iid),"Frozen evidence changed"
                    assert not errors,"Uncaught client error"
                    assert all(url.startswith(server.base+"/") for url in requests),"External request"
                    assert not any("GeoVectorMap-" in url or "maplibre-gl-worker-" in url for url in requests),"Eager map load"
                    engine["request_count"]=len(requests)
                    engine["status"]="passed"
                finally:browser.close()
                # Each engine must begin with an empty workspace.
                server.close()
                if name!="webkit":server=LocalFixtureProcess(free_port(),database=None)
        report["status"]="passed"
    finally:
        server.close()
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report,indent=2))
if __name__=="__main__":main()
