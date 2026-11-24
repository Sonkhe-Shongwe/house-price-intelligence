"""Actual browser automated accessibility evidence, not WCAG certification.
Only aggregate rule counts and impacts are emitted. No DOM/HTML or identifiers.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from test_persistent_restart import LocalFixtureProcess,free_port

def main():
    script=Path(os.environ["HPI_AXE_SCRIPT"]).read_text()
    output=Path(os.environ["HPI_ACCESSIBILITY_REPORT"])
    result={"scope":"fictional workspace, supported dossier and two-property comparison",
            "engine":"axe-core 4.10.3","status":"blocked","views":[]}
    server=LocalFixtureProcess(free_port(),database=None)
    try:
        with sync_playwright() as pw:
            opts={"headless":True,"args":["--no-sandbox"]}
            if os.environ.get("HPI_BROWSER_EXECUTABLE"):opts["executable_path"]=os.environ["HPI_BROWSER_EXECUTABLE"]
            browser=pw.chromium.launch(**opts)
            try:
                page=browser.new_page(viewport={"width":1440,"height":900})
                page.goto(server.base+"/")
                def scan(label):
                    if not page.evaluate("typeof window.axe !== 'undefined'"):page.evaluate(script)
                    raw=page.evaluate("""async () => {
                        const result=await axe.run({runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});
                        return {passes:result.passes.length,incomplete:result.incomplete.length,
                          violations:result.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.length}))};
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
                page.get_by_test_id("dossier-compare").click()
                page.get_by_test_id("workspace-create").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("0 / 3")
                page.get_by_test_id("workspace-add-current").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("1 / 3")
                page.get_by_test_id("nav-investigate").click()
                page.get_by_test_id("buyer-manual-pin").fill("99999999999999")
                page.get_by_test_id("buyer-create").click()
                expect(page.get_by_test_id("buyer-insufficient")).to_be_visible(timeout=15000)
                page.get_by_test_id("dossier-compare").click()
                page.get_by_test_id("workspace-add-current").click()
                expect(page.get_by_test_id("workspace-count")).to_have_text("2 / 3")
                scan("comparison_desktop")
                page.set_viewport_size({"width":320,"height":800})
                scan("comparison_mobile")
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
