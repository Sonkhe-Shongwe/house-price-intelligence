"""Actual browser automated accessibility evidence, not WCAG certification.
Only aggregate rule counts and impacts are emitted. No DOM/HTML or identifiers.
"""
import json
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from test_persistent_restart import LocalFixtureProcess,free_port

def main():
    script=Path(os.environ["HPI_AXE_SCRIPT"]).read_text()
    output=Path(os.environ["HPI_ACCESSIBILITY_REPORT"])
    result={"scope":"fictional workspace, dossiers, comparison, virtual interactive map and lightweight/failure schematic; WCAG 2.2 AA tagged automated rules",
            "engine":"axe-core 4.10.3","status":"blocked","views":[]}
    server=LocalFixtureProcess(free_port(),database=None,synthetic_map=True)
    try:
        with sync_playwright() as pw:
            opts={"headless":True,"args":["--no-sandbox","--enable-unsafe-swiftshader","--use-angle=swiftshader"]}
            if os.environ.get("HPI_BROWSER_EXECUTABLE"):opts["executable_path"]=os.environ["HPI_BROWSER_EXECUTABLE"]
            browser=pw.chromium.launch(**opts)
            try:
                page=browser.new_page(viewport={"width":1440,"height":900})
                page.goto(server.base+"/")
                def scan(label):
                    if not page.evaluate("typeof window.axe !== 'undefined'"):page.evaluate(script)
                    raw=page.evaluate("""async () => {
                        const result=await axe.run({runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});
                        return {passes:result.passes.length,incomplete:result.incomplete.length,
                          violations:result.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.length,colors:[...new Set(v.nodes.flatMap(n=>n.any.map(c=>c.data&&typeof c.data.fgColor==='string'&&typeof c.data.bgColor==='string'?c.data.fgColor+'/'+c.data.bgColor:null).filter(Boolean)))]}))};
                    }""")
                    result["views"].append({"view":label,**raw})
                expect(page.get_by_test_id("history-panel")).to_be_visible()
                scan("workspace")
                page.get_by_test_id("workspace-new-investigation").click()
                page.get_by_test_id("buyer-manual-pin").fill("00000000000001")
                page.get_by_test_id("buyer-create").click()
                expect(page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
                page.get_by_test_id("buyer-sale").first.click()
                scan("supported_dossier")
                # One controlled Chromium software-GPU lab sample, not field Web Vitals.
                requests=[]
                page.on("request",lambda req:requests.append(req.url))
                started=time.perf_counter()
                page.get_by_test_id("geo-load-schematic").click()
                expect(page.get_by_test_id("geo-static-fallback")).to_be_visible(timeout=15000)
                result["map_lab"]={"measurement":"single hosted Chromium software-GPU sample",
                    "schematic_ready_ms":round((time.perf_counter()-started)*1000)}
                result["map_lab"]["schematic_requests"]=len(requests)
                assert not any("GeoVectorMap-" in u or "maplibre-gl-worker-" in u for u in requests)
                expect(page.get_by_test_id("geo-selected-sale")).to_contain_text("$525,000.00")
                scan("schematic_desktop")
                page.set_viewport_size({"width":320,"height":800})
                scan("schematic_mobile")
                page.set_viewport_size({"width":1440,"height":900})
                request_start=len(requests)
                started=time.perf_counter()
                page.get_by_test_id("geo-mode-interactive").click()
                expect(page.get_by_test_id("geo-ready")).to_be_visible(timeout=20000)
                result["map_lab"]["interactive_ready_ms"]=round((time.perf_counter()-started)*1000)
                result["map_lab"]["interactive_additional_requests"]=len(requests)-request_start
                result["map_lab"]["document_resource_timing"]=page.evaluate("""() => {
                    const entries=performance.getEntriesByType('resource').filter(e=>/GeoVectorMap-|maplibre-gl-worker-/.test(e.name));
                    return {entries:entries.length,encoded_body_bytes:entries.reduce((n,e)=>n+e.encodedBodySize,0),
                        transfer_bytes:entries.reduce((n,e)=>n+e.transferSize,0)};
                }""")
                assert sum(u.endswith("/map") for u in requests)==1
                assert all(u.startswith(server.base+"/") for u in requests)
                expect(page.get_by_test_id("geo-pin-1")).to_have_attribute("aria-pressed","true")
                scan("interactive_desktop")
                page.set_viewport_size({"width":320,"height":800})
                scan("interactive_mobile")
                page.set_viewport_size({"width":1440,"height":900})
                page.get_by_test_id("dossier-compare").click()
                page.get_by_test_id("workspace-create").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("0 / 3")
                page.get_by_test_id("workspace-add-current").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("1 / 3")
                page.get_by_test_id("nav-investigate").click()
                page.get_by_test_id("buyer-manual-pin").fill("99999999999999")
                page.get_by_test_id("buyer-create").click()
                expect(page.get_by_test_id("buyer-insufficient")).to_be_visible(timeout=15000)
                scan("insufficient_dossier")
                page.get_by_test_id("dossier-compare").click()
                page.get_by_test_id("workspace-add-current").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("2 / 3")
                scan("comparison_desktop")
                page.set_viewport_size({"width":320,"height":800})
                scan("comparison_mobile")
                # Separate cold context with GPU unavailable; no reuse of the prior renderer.
                fallback=browser.new_page(viewport={"width":320,"height":800},has_touch=True,reduced_motion="reduce")
                fallback.add_init_script("""const original=HTMLCanvasElement.prototype.getContext;
                    HTMLCanvasElement.prototype.getContext=function(type,...args){
                        if(['webgl','webgl2','experimental-webgl'].includes(type))return null;
                        return original.call(this,type,...args);
                    };""")
                page=fallback
                page.goto(server.base+"/buyer-workflow")
                page.get_by_test_id("buyer-manual-pin").fill("00000000000001")
                page.get_by_test_id("buyer-create").click()
                expect(page.get_by_test_id("buyer-result")).to_be_visible(timeout=15000)
                page.get_by_test_id("geo-load").click()
                expect(page.get_by_test_id("geo-fallback")).to_be_visible(timeout=20000)
                expect(page.get_by_test_id("geo-static-fallback")).to_be_visible()
                scan("renderer_failure_mobile")
                result["status"]="completed"
                result["gate_passed"]=all(not v["violations"] for v in result["views"])
            finally:browser.close()
    finally:
        server.close()
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
    if result["status"]!="completed":raise SystemExit(1)
    # Findings remain visible and must be reviewed, not silently suppressed.
    if not result["gate_passed"]:raise SystemExit(2)
if __name__=="__main__":main()
