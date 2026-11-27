"""Actual opt-in React ZA page through the localhost fixture server."""
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[3]


class SouthAfricanBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log=tempfile.TemporaryFile(mode="w+t",encoding="utf-8")
        with socket.socket() as sk:
            sk.bind(("127.0.0.1",0))
            cls.base=f"http://127.0.0.1:{sk.getsockname()[1]}"
        cls.server=subprocess.Popen([sys.executable,"-m","backend.run_synthetic_api","--fixture-only",
                                     "--frontend","react","--sa-fixture","--sa-saved-fixture","--port",cls.base.rsplit(":",1)[1]],
                                    cwd=ROOT,stdout=cls.log,stderr=subprocess.STDOUT)
        try:
            for _ in range(100):
                if cls.server.poll() is not None:
                    raise RuntimeError("ZA fixture launcher exited")
                try:
                    with urlopen(cls.base+"/health",timeout=.4) as res:
                        if res.status==200: break
                except OSError: time.sleep(.15)
            else: raise RuntimeError("ZA fixture server unavailable")
            cls.driver=sync_playwright().start()
            options={"executable_path":os.environ["HPI_BROWSER_EXECUTABLE"],"args":["--no-sandbox"]} if os.environ.get("HPI_BROWSER_EXECUTABLE") else {}
            cls.browser=cls.driver.chromium.launch(headless=True,**options)
        except Exception:
            cls.server.terminate();cls.server.wait(timeout=5);cls.log.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.driver.stop();cls.server.terminate()
        try: cls.server.wait(timeout=5)
        except subprocess.TimeoutExpired: cls.server.kill();cls.server.wait(timeout=5)
        cls.log.close()

    def setUp(self):
        self.context=self.browser.new_context(viewport={"width":1366,"height":850})
        self.page=self.context.new_page();self.errors=[];self.external=[]
        self.page.on("pageerror",lambda e:self.errors.append(str(e)))
        self.page.on("request",lambda req:self.external.append(req.url) if not req.url.startswith(self.base+"/") else None)
        self.assertEqual(self.page.goto(self.base+"/za-fictional").status,200)
        expect(self.page.get_by_test_id("za-study")).to_be_visible()

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors,[]);self.assertEqual(self.external,[])

    def submit(self):
        self.page.get_by_test_id("za-submit").click()
        expect(self.page.get_by_test_id("za-result")).to_be_visible()

    def test_real_response_and_us_preserved(self):
        self.submit()
        expect(self.page.get_by_test_id("za-comparable")).to_have_count(5)
        expect(self.page.get_by_test_id("za-result")).to_contain_text("R 2 500 000.01")
        expect(self.page.get_by_test_id("za-result")).to_contain_text("365 days")
        self.assertEqual(self.page.request.get(self.base+"/v1/investigations/history").json()["investigations"],[])
        self.page.get_by_label("Evidence mode").select_option("retrospective")
        expect(self.page.get_by_test_id("za-result")).to_have_count(0)
        self.submit()
        expect(self.page.get_by_test_id("za-result")).to_contain_text("Retrospective only")
        self.page.get_by_role("link",name="US fictional buyer workspace").click()
        expect(self.page.get_by_test_id("buyer-workflow")).to_be_visible()

    def test_ambiguous_and_invalid_no_stale_result(self):
        self.submit()
        self.page.get_by_label("Fictional erf").select_option("fictional-erf-000010")
        self.submit()
        expect(self.page.get_by_test_id("za-result")).to_contain_text("cannot be resolved exactly")
        expect(self.page.get_by_test_id("za-comparable")).to_have_count(0)
        self.page.get_by_label("Fictional asking price (ZAR)").fill("1.001")
        self.page.get_by_test_id("za-submit").click()
        expect(self.page.get_by_role("alert")).to_contain_text("two decimal places")
        expect(self.page.get_by_test_id("za-result")).to_have_count(0)

    def test_browser_only_two_property_journey(self):
        # All buyer mutations go through the UI; direct API reads are assertions only.
        saved_path=self.base+"/v2/fictional/za/saved"
        shortlist_path=self.base+"/v2/fictional/za/shortlist"
        count=self.page.get_by_test_id("za-shortlist-count")
        expect(count).to_have_text("0 of 3 properties")
        before=self.page.request.get(saved_path).json()["investigations"]
        self.assertEqual(self.page.request.get(shortlist_path).json()["investigations"],[])
        self.assertLessEqual(len(before),28)
        writes=[]
        self.page.on("request",lambda req:writes.append(req.url.removeprefix(self.base))
                     if req.method=="POST" else None)
        price=self.page.get_by_label("Fictional asking price (ZAR)")
        parcel=self.page.get_by_label("Fictional erf")
        save=self.page.get_by_test_id("za-save")
        result=self.page.get_by_test_id("za-result")
        saved_id=self.page.get_by_test_id("za-saved-id")
        ids=[];snapshots=[]
        for i,(token,amount) in enumerate([("000001","2750000.07"),("000010","1850000.09")]):
            parcel.select_option("fictional-erf-"+token)
            price.fill(amount)
            self.submit()
            if i==0:
                expect(self.page.get_by_test_id("za-comparable")).to_have_count(5)
                expect(result).to_contain_text("R 2 750 000.07")
            else:
                expect(result).to_contain_text("cannot be resolved exactly")
                expect(self.page.get_by_test_id("za-comparable")).to_have_count(0)
            self.assertEqual(len(self.page.request.get(saved_path).json()["investigations"]),len(before)+i)
            save.click()
            expect(saved_id).to_be_visible()
            iid=saved_id.inner_text().split(": ",1)[1]
            ids.append(iid)
            snapshot=self.page.request.get(saved_path+"/"+iid).json()
            snapshots.append(snapshot)
            explanation=self.page.get_by_test_id("za-explanation")
            expect(explanation).to_contain_text(snapshot["evidence"]["data_build"])
            expect(explanation).to_contain_text(snapshot["evidence"]["policy_version"])
            expect(explanation).to_contain_text(snapshot["evidence"]["analysis_date"])
            if i==0:
                from decimal import Decimal
                def difference(a,b):
                    d=Decimal(b)-Decimal(a)
                    return "Same extent" if not d else format(abs(d).normalize(),"f")+" m² "+("larger" if d>0 else "smaller")
                evidence=snapshot["evidence"]
                cells=self.page.get_by_test_id("za-comparable-differences")
                expect(cells).to_have_count(5)
                for n,sale in enumerate(evidence["comparables"]):
                    expect(cells.nth(n)).to_have_text("Dwelling: "+difference(evidence["subject"]["dwelling_extent"],sale["dwelling_extent"])+"; land: "+difference(evidence["subject"]["land_extent"],sale["land_extent"])+".")
                expect(explanation).to_contain_text("ranking excludes prices")
            else:
                expect(self.page.get_by_test_id("za-next-action")).to_have_text("Confirm the parcel identity before comparing sale evidence.")
            self.assertEqual(snapshot["request"]["subject_key"]["value"],"fictional-erf-"+token)
            self.assertEqual(snapshot["request"]["asking_price"],amount)
            self.assertEqual(snapshot["evidence"]["subject"]["asking_price"]["minor_units"],
                             (275000007,185000009)[i])
            expect(save).to_be_disabled()
            select=self.page.get_by_label("Saved investigation to shortlist")
            select.select_option(iid)
            self.page.get_by_test_id("za-shortlist-add").click()
            expect(count).to_have_text(f"{i+1} of 3 properties")
        self.assertEqual(len(set(ids)),2)
        self.assertEqual(len(self.page.request.get(saved_path).json()["investigations"]),len(before)+2)
        comparison=self.page.get_by_test_id("za-comparison")
        expect(comparison).to_contain_text("R 2 750 000.07")
        expect(comparison).to_contain_text("R 1 850 000.09")
        expect(comparison).to_contain_text("No comparable sale amounts")
        expect(comparison).to_contain_text("Invented registered-sale consideration")
        expect(comparison).to_contain_text("User-reported asking price")
        expect(comparison).to_contain_text("Confirm the parcel identity before comparing sale evidence.")
        expect(comparison).to_contain_text("za-fictional-pinelands-v1")
        frozen_text=comparison.inner_text()
        self.assertEqual(self.page.request.get(shortlist_path).json()["investigations"],snapshots)
        self.page.reload()
        expect(count).to_have_text("2 of 3 properties")
        expect(comparison).to_have_text(frozen_text,use_inner_text=True)
        for i,iid in enumerate(ids):
            self.page.get_by_role("button",name="Reopen "+iid).click()
            expect(self.page.get_by_text("Reopened frozen evidence; not recalculated.")).to_be_visible()
            expect(saved_id).to_have_text("Saved ID: "+iid)
            expect(price).to_have_value(("2750000.07","1850000.09")[i])
            expect(self.page.get_by_test_id("za-comparable")).to_have_count(5 if i==0 else 0)
            self.assertEqual(self.page.request.get(saved_path+"/"+iid).json(),snapshots[i])
            expect(self.page.get_by_test_id("za-explanation")).to_contain_text(snapshots[i]["evidence"]["data_build"])
            if i==1:
                expect(self.page.get_by_test_id("za-next-action")).to_contain_text("Confirm the parcel identity")
        self.assertEqual(self.page.request.get(shortlist_path).json()["investigations"],snapshots)
        for i,iid in enumerate(ids):
            self.page.get_by_role("button",name="Remove "+iid).click()
            expect(count).to_have_text(f"{1-i} of 3 properties")
            expect(comparison).to_have_count(0)
        self.assertEqual(self.page.request.get(shortlist_path).json()["investigations"],[])
        self.assertEqual(len(self.page.request.get(saved_path).json()["investigations"]),len(before)+2)
        self.assertEqual(writes,["/v2/fictional/za/investigate","/v2/fictional/za/saved",
                                "/v2/fictional/za/shortlist"]*2+["/v2/fictional/za/shortlist"]*2)
        self.assertEqual(self.page.request.get(self.base+"/v1/investigations/history").json()["investigations"],[])
        self.assertEqual(self.page.request.get(self.base+"/v1/shortlists").json()["shortlists"],[])
        self.page.get_by_role("link",name="US fictional buyer workspace").click()
        expect(self.page.get_by_test_id("buyer-workflow")).to_be_visible()

    def test_explanation_unsupported_and_corrupt_reason(self):
        self.page.get_by_label("Fictional erf").select_option("fictional-erf-000015")
        self.submit()
        expect(self.page.get_by_test_id("za-next-action")).to_contain_text("relevant property class and locality")
        expect(self.page.get_by_test_id("za-comparable")).to_have_count(0)
        path="**/v2/fictional/za/investigate"
        def corrupt(route):
            response=route.fetch()
            value=response.json();value["reason"]="primary_window"
            route.fulfill(response=response,json=value)
        self.page.route(path,corrupt)
        self.page.get_by_test_id("za-submit").click()
        expect(self.page.get_by_role("alert")).to_contain_text("Investigation unavailable")
        expect(self.page.get_by_test_id("za-explanation")).to_have_count(0)
        self.page.unroute(path,corrupt)
        self.submit()
        expect(self.page.get_by_test_id("za-next-action")).to_contain_text("relevant property class and locality")

    def test_cross_market_response_refused_and_retry(self):
        path="**/v2/fictional/za/investigate"
        def corrupt(route):
            response=route.fetch()
            value=response.json();value["currency"]="USD"
            route.fulfill(response=response,json=value)
        self.page.route(path,corrupt)
        self.page.get_by_test_id("za-submit").click()
        expect(self.page.get_by_role("alert")).to_contain_text("Investigation unavailable")
        expect(self.page.get_by_test_id("za-result")).to_have_count(0)
        self.page.unroute(path,corrupt)
        self.submit()
        expect(self.page.get_by_test_id("za-comparable")).to_have_count(5)

    def test_save_reload_reopen_and_retry(self):
        self.submit()
        before=len(self.page.request.get(self.base+"/v2/fictional/za/saved").json()["investigations"])
        path="**/v2/fictional/za/saved"
        def lost_reply(route):
            if route.request.method=="POST":
                route.fetch()
                route.abort()
            else: route.continue_()
        self.page.route(path,lost_reply)
        self.page.get_by_test_id("za-save").click()
        expect(self.page.get_by_text("Save not confirmed.",exact=False)).to_be_visible()
        self.page.unroute(path,lost_reply)
        self.page.get_by_test_id("za-save").click()
        expect(self.page.get_by_test_id("za-saved-id")).to_be_visible()
        saved_id=self.page.get_by_test_id("za-saved-id").inner_text().split(": ",1)[1]
        self.assertEqual(len(self.page.request.get(self.base+"/v2/fictional/za/saved").json()["investigations"]),before+1)
        expect(self.page.get_by_test_id("za-save")).to_be_disabled()
        self.page.reload()
        self.page.get_by_role("button",name="Reopen "+saved_id).click()
        expect(self.page.get_by_test_id("za-comparable")).to_have_count(5)
        expect(self.page.get_by_text("Reopened frozen evidence; not recalculated.")).to_be_visible()
        expect(self.page.get_by_test_id("za-result")).to_contain_text("R 2 500 000.01")
        self.assertEqual(self.page.request.get(self.base+"/v1/investigations/history").json()["investigations"],[])

    def test_saved_api_parcel_outside_initial_choices(self):
        import uuid
        iid=str(uuid.uuid4())
        req={"contract_version":"hpi-investigation-v2-fictional","market":"ZA","currency":"ZAR",
             "area_unit":"m2","subject_key":{"namespace":"za-fictional-erf","value":"fictional-erf-000002"},
             "analysis_date":"2025-07-01","mode":"as_of","asking_price":"1.01"}
        saved=self.page.request.post(self.base+"/v2/fictional/za/saved",data={"retry_id":iid,"request":req})
        self.assertEqual(saved.status,200)
        self.page.reload()
        self.page.get_by_role("button",name="Reopen "+iid).click()
        expect(self.page.get_by_label("Fictional erf")).to_have_value("fictional-erf-000002")
        expect(self.page.get_by_test_id("za-result")).to_be_visible()
        expect(self.page.get_by_label("Fictional asking price (ZAR)")).to_have_value("1.01")

    def test_shortlist_frozen_comparison_limits_and_reload(self):
        import uuid
        path=self.base+"/v2/fictional/za/shortlist"
        for row in self.page.request.get(path).json()["investigations"]:
            self.page.request.post(path,data={"action":"remove","investigation_id":row["investigation_id"]})
        ids=[]
        for token,price in [("000001","2500000.01"),("000010","1.02"),("000015",None),("000002","3.04"),("000001","4.05")]:
            iid=str(uuid.uuid4());ids.append(iid)
            req={"contract_version":"hpi-investigation-v2-fictional","market":"ZA","currency":"ZAR","area_unit":"m2",
                 "subject_key":{"namespace":"za-fictional-erf","value":"fictional-erf-"+token},
                 "analysis_date":"2025-07-01","mode":"as_of","asking_price":price}
            self.assertEqual(self.page.request.post(self.base+"/v2/fictional/za/saved",data={"retry_id":iid,"request":req}).status,200)
        self.page.reload()
        select=self.page.get_by_label("Saved investigation to shortlist")
        add=self.page.get_by_test_id("za-shortlist-add")
        count=self.page.get_by_test_id("za-shortlist-count")
        expect(count).to_have_text("0 of 3 properties")
        def choose(i,n):
            select.select_option(ids[i]);add.click();expect(count).to_have_text(f"{n} of 3 properties")
        choose(0,1)
        expect(self.page.get_by_test_id("za-comparison")).to_have_count(0)
        select.select_option(ids[4]);expect(add).to_be_disabled()
        choose(1,2)
        comparison=self.page.get_by_test_id("za-comparison")
        expect(comparison).to_contain_text("R 2 500 000.01")
        expect(comparison).to_contain_text("R 1.02")
        expect(comparison).to_contain_text("No comparable sale amounts")
        choose(2,3)
        select.select_option(ids[3]);expect(add).to_be_disabled()
        self.page.reload()
        expect(count).to_have_text("3 of 3 properties")
        expect(comparison).to_contain_text("R 2 500 000.01")
        self.page.get_by_role("button",name="Remove "+ids[1]).click()
        expect(count).to_have_text("2 of 3 properties")
        self.page.set_viewport_size({"width":320,"height":850})
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"))
        self.assertEqual(self.page.request.get(self.base+"/v1/investigations/history").json()["investigations"],[])
        for iid in (ids[0],ids[2]):
            self.page.get_by_role("button",name="Remove "+iid).click()
            expect(self.page.get_by_role("button",name="Remove "+iid)).to_have_count(0)

    def prepare_recovery_shortlist(self):
        import uuid
        path=self.base+"/v2/fictional/za/shortlist"
        for row in self.page.request.get(path).json()["investigations"]:
            self.assertEqual(self.page.request.post(path,data={"action":"remove",
                "investigation_id":row["investigation_id"]}).status,200)
        saved=[]
        for token,price in [("000001","2500000.03"),("000010","1.02"),("000015",None)]:
            iid=str(uuid.uuid4())
            req={"contract_version":"hpi-investigation-v2-fictional","market":"ZA","currency":"ZAR","area_unit":"m2",
                 "subject_key":{"namespace":"za-fictional-erf","value":"fictional-erf-"+token},
                 "analysis_date":"2025-07-01","mode":"as_of","asking_price":price}
            res=self.page.request.post(self.base+"/v2/fictional/za/saved",data={"retry_id":iid,"request":req})
            self.assertEqual(res.status,200)
            saved.append(res.json())
        self.page.reload()
        expect(self.page.get_by_test_id("za-shortlist-count")).to_have_text("0 of 3 properties")
        return path,saved

    def test_shortlist_lost_add_and_remove_response_reconciles_once(self):
        path,saved=self.prepare_recovery_shortlist()
        ids=[r["investigation_id"] for r in saved]
        select=self.page.get_by_label("Saved investigation to shortlist")
        add=self.page.get_by_test_id("za-shortlist-add")
        count=self.page.get_by_test_id("za-shortlist-count")
        select.select_option(ids[0]);add.click()
        expect(count).to_have_text("1 of 3 properties")
        requests=[]
        def lose_write(route):
            requests.append(route.request.method)
            if route.request.method=="POST":
                self.assertEqual(route.fetch().status,200)
                route.abort()
            else:
                route.continue_()
        self.page.route(path,lose_write)
        select.select_option(ids[1]);add.click()
        expect(self.page.get_by_text("Change response not confirmed.",exact=False)).to_be_visible()
        expect(count).to_have_text("2 of 3 properties")
        expect(add).to_be_disabled()
        self.assertEqual(requests,["POST","GET"])
        self.assertEqual(self.page.request.get(path).json()["investigations"],saved[:2])
        comparison=self.page.get_by_test_id("za-comparison")
        expect(comparison).to_contain_text("R 2 500 000.03")
        expect(comparison).to_contain_text("No comparable sale amounts")
        self.assertEqual(self.page.request.get(self.base+"/v2/fictional/za/saved/"+ids[0]).json(),saved[0])
        requests.clear()
        self.page.get_by_role("button",name="Remove "+ids[1]).click()
        expect(count).to_have_text("1 of 3 properties")
        expect(self.page.get_by_text("Change response not confirmed.",exact=False)).to_be_visible()
        expect(comparison).to_have_count(0)
        self.assertEqual(requests,["POST","GET"])
        self.assertEqual(self.page.request.get(path).json()["investigations"],saved[:1])
        self.page.unroute(path,lose_write)
        self.page.get_by_role("button",name="Remove "+ids[0]).click()
        expect(count).to_have_text("0 of 3 properties")
        self.assertEqual(self.page.request.get(path).json()["investigations"],[])
        self.assertEqual(self.page.request.get(self.base+"/v1/investigations/history").json()["investigations"],[])

    def test_shortlist_failed_reconciliation_and_corrupt_refresh_fail_closed(self):
        path,saved=self.prepare_recovery_shortlist()
        ids=[r["investigation_id"] for r in saved]
        select=self.page.get_by_label("Saved investigation to shortlist")
        add=self.page.get_by_test_id("za-shortlist-add")
        count=self.page.get_by_test_id("za-shortlist-count")
        comparison=self.page.get_by_test_id("za-comparison")
        refresh=self.page.get_by_role("button",name="Refresh shortlist")
        for i in range(2):
            select.select_option(ids[i]);add.click()
            expect(count).to_have_text(f"{i+1} of 3 properties")
        expect(comparison).to_be_visible()
        requests=[]
        def lose_write_and_read(route):
            requests.append(route.request.method)
            if route.request.method=="POST":
                self.assertEqual(route.fetch().status,200)
            route.abort()
        self.page.route(path,lose_write_and_read)
        select.select_option(ids[2]);add.click()
        expect(self.page.get_by_text("Shortlist unavailable. Refresh before retrying.")).to_be_visible()
        expect(comparison).to_have_count(0)
        expect(self.page.get_by_test_id("za-shortlist-member")).to_have_count(0)
        expect(add).to_be_disabled()
        expect(select).to_be_disabled()
        self.assertEqual(requests,["POST","GET"])
        self.assertEqual(self.page.request.get(path).json()["investigations"],saved)
        refresh.click()
        expect(self.page.get_by_text("Shortlist unavailable. Refresh to try again.")).to_be_visible()
        expect(add).to_be_disabled()
        self.assertEqual(requests,["POST","GET","GET"])
        self.page.unroute(path,lose_write_and_read)
        def wrong_market(route):
            res=route.fetch()
            body=res.json();body["market"]="US"
            route.fulfill(response=res,json=body)
        self.page.route(path,wrong_market)
        refresh.click()
        expect(self.page.get_by_text("Shortlist unavailable. Refresh to try again.")).to_be_visible()
        expect(comparison).to_have_count(0)
        expect(add).to_be_disabled()
        self.page.unroute(path,wrong_market)
        refresh.click()
        expect(count).to_have_text("3 of 3 properties")
        expect(comparison).to_contain_text("R 2 500 000.03")
        expect(comparison).to_contain_text("R 1.02")
        expect(comparison).to_contain_text("No comparable sale amounts")
        expect(add).to_be_disabled()
        self.assertEqual(self.page.request.get(path).json()["investigations"],saved)
        self.assertEqual(self.page.request.get(self.base+"/v1/shortlists").json()["shortlists"],[])
        for i,iid in enumerate(ids):
            self.page.get_by_role("button",name="Remove "+iid).click()
            expect(count).to_have_text(f"{2-i} of 3 properties")

    def test_shortlist_notes_edit_clear_reload_and_frozen_evidence(self):
        path,saved=self.prepare_recovery_shortlist()
        ids=[r["investigation_id"] for r in saved[:2]]
        select=self.page.get_by_label("Saved investigation to shortlist")
        count=self.page.get_by_test_id("za-shortlist-count")
        for i,iid in enumerate(ids):
            select.select_option(iid)
            self.page.get_by_test_id("za-shortlist-add").click()
            expect(count).to_have_text(f"{i+1} of 3 properties")
        first=self.page.get_by_label("Decision note for Erf 000001")
        second=self.page.get_by_label("Decision note for Erf 000010")
        save_first=self.page.get_by_role("button",name="Save note "+ids[0])
        save_second=self.page.get_by_role("button",name="Save note "+ids[1])
        comparison=self.page.get_by_test_id("za-comparison")
        expect(first).to_have_value("")
        first.fill("x"*801)
        expect(save_first).to_be_disabled()
        first.fill("Fictional <b>question</b>")
        save_first.click()
        expect(comparison).to_contain_text("Fictional <b>question</b>")
        expect(comparison.locator("b")).to_have_count(0)
        second.fill("Check unresolved identity")
        save_second.click()
        expect(comparison).to_contain_text("Check unresolved identity")
        expect(save_second).to_be_disabled()
        self.assertEqual(self.page.request.get(path).json()["investigations"],saved[:2])
        self.assertEqual(self.page.request.get(path).json()["notes"],
                         {ids[0]:"Fictional <b>question</b>",ids[1]:"Check unresolved identity"})
        self.page.reload()
        expect(first).to_have_value("Fictional <b>question</b>")
        expect(second).to_have_value("Check unresolved identity")
        first.fill("")
        save_first.click()
        expect(save_first).to_be_disabled()
        expect(comparison).not_to_contain_text("Fictional <b>question</b>")
        self.page.get_by_role("button",name="Remove "+ids[1]).click()
        expect(count).to_have_text("1 of 3 properties")
        select.select_option(ids[1])
        self.page.get_by_test_id("za-shortlist-add").click()
        expect(count).to_have_text("2 of 3 properties")
        expect(second).to_have_value("")
        self.assertEqual(self.page.request.get(path).json()["notes"],{ids[0]:"",ids[1]:""})
        self.assertEqual(self.page.request.get(path).json()["investigations"],saved[:2])
        self.assertEqual(self.page.request.get(self.base+"/v1/shortlists").json()["shortlists"],[])
        self.page.set_viewport_size({"width":320,"height":850})
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"))
        for i,iid in enumerate(ids):
            self.page.get_by_role("button",name="Remove "+iid).click()
            expect(count).to_have_text(f"{1-i} of 3 properties")

    def test_mobile_reflow(self):
        for width in (768,375,320):
            self.page.set_viewport_size({"width":width,"height":850})
            self.submit()
            self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"))
            expect(self.page.get_by_role("region",name="Fictional comparable sales")).to_be_visible()
        target=os.environ.get("HPI_BUYER_SCREENSHOTS")
        if target:
            Path(target).mkdir(parents=True,exist_ok=True)
            self.page.screenshot(path=str(Path(target)/"za-mobile.png"),full_page=True)
            self.page.set_viewport_size({"width":1366,"height":850})
            self.page.screenshot(path=str(Path(target)/"za-desktop.png"),full_page=True)
