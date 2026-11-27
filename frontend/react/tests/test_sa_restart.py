"""Managed fictional loopback server restart; no normal launcher file mode."""
from contextlib import contextmanager
from queue import Queue
from threading import Thread
from urllib.request import urlopen
from wsgiref.simple_server import make_server
import os
import unittest

from playwright.sync_api import sync_playwright, expect
from backend.sa_fixture_restart import DisposableRestartRehearsal


@contextmanager
def running_server(rehearsal):
    ready = Queue()
    failures = []

    def run():
        announced = False
        try:
            # SQLite connection creation, request handling and close all occur
            # on this one server thread.
            with rehearsal.http_app() as app:
                with make_server("127.0.0.1", 0, app) as server:
                    ready.put(server)
                    announced = True
                    server.serve_forever(poll_interval=.05)
        except Exception as exc:
            if announced:
                failures.append(exc)
            else:
                ready.put(exc)

    thread = Thread(target=run, daemon=True)
    thread.start()
    server = ready.get(timeout=20)
    if isinstance(server, Exception):
        thread.join(timeout=5)
        raise server
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base+"/health", timeout=5) as response:
            if response.status != 200:
                raise RuntimeError("Managed restart server unavailable")
        yield base
    finally:
        server.shutdown()
        thread.join(timeout=10)
        if thread.is_alive():
            raise RuntimeError("Managed restart server did not stop")
        if failures:
            raise failures[0]


class SouthAfricanRestartBrowserTests(unittest.TestCase):
    @contextmanager
    def workspace(self, browser, base):
        context = browser.new_context(viewport={"width":1366,"height":850})
        page = context.new_page()
        errors, external = [], []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("request", lambda r: external.append(r.url) if not r.url.startswith(base+"/") else None)
        try:
            self.assertEqual(page.goto(base+"/za-fictional").status, 200)
            expect(page.get_by_test_id("za-study")).to_be_visible()
            yield page
        finally:
            context.close()
            self.assertEqual(errors, [])
            self.assertEqual(external, [])

    def test_managed_http_restart_recovers_frozen_workspace(self):
        with DisposableRestartRehearsal() as rehearsal, sync_playwright() as driver:
            options = {"executable_path":os.environ["HPI_BROWSER_EXECUTABLE"],"args":["--no-sandbox"]} if os.environ.get("HPI_BROWSER_EXECUTABLE") else {}
            browser = driver.chromium.launch(headless=True, **options)
            try:
                ids, snapshots = [], []
                notes = ["Fictional extent question", "Unresolved identity"]
                prices = ["2750000.07", "1850000.09"]
                tokens = ["000001", "000010"]
                saved_path = "/v2/fictional/za/saved"
                shortlist_path = "/v2/fictional/za/shortlist"
                with running_server(rehearsal) as base, self.workspace(browser, base) as page:
                    count = page.get_by_test_id("za-shortlist-count")
                    expect(count).to_have_text("0 of 3 properties")
                    for i, token in enumerate(tokens):
                        page.get_by_label("Fictional erf").select_option("fictional-erf-"+token)
                        page.get_by_label("Fictional asking price (ZAR)").fill(prices[i])
                        page.get_by_test_id("za-submit").click()
                        expect(page.get_by_test_id("za-result")).to_be_visible()
                        expect(page.get_by_test_id("za-comparable")).to_have_count(5 if i==0 else 0)
                        page.get_by_test_id("za-save").click()
                        saved_id = page.get_by_test_id("za-saved-id")
                        expect(saved_id).to_be_visible()
                        iid = saved_id.inner_text().split(": ",1)[1]
                        ids.append(iid)
                        snapshots.append(page.request.get(base+saved_path+"/"+iid).json())
                        self.assertEqual(snapshots[-1]["evidence"]["subject"]["asking_price"]["minor_units"],
                                         [275000007,185000009][i])
                        page.get_by_label("Saved investigation to shortlist").select_option(iid)
                        page.get_by_test_id("za-shortlist-add").click()
                        expect(count).to_have_text(f"{i+1} of 3 properties")
                        page.get_by_label("Decision note for Erf "+token).fill(notes[i])
                        button = page.get_by_role("button",name="Save note "+iid)
                        button.click()
                        expect(page.get_by_text("Decision note saved.", exact=True)).to_be_visible()
                        expect(button).to_be_disabled()
                    comparison = page.get_by_test_id("za-comparison")
                    expect(comparison).to_contain_text("No comparable sale amounts")
                    for note in notes:
                        expect(comparison).to_contain_text(note)
                    frozen_text = comparison.inner_text()
                    frozen = page.request.get(base+shortlist_path).json()
                    self.assertEqual(frozen["investigations"],snapshots)
                    self.assertEqual(frozen["notes"],dict(zip(ids,notes)))
                    self.assertEqual(len(page.request.get(base+saved_path).json()["investigations"]),2)
                    self.assertEqual(page.request.get(base+"/v1/investigations/history").json()["investigations"],[])
                    self.assertEqual(page.request.get(base+"/v1/shortlists").json()["shortlists"],[])
                # Context manager closed the HTTP listener and its SQLite
                # connection. No browser state or app closure is reused.
                self.assertFalse(rehearsal._active)
                with self.assertRaises(OSError):
                    urlopen(base+"/health", timeout=1)
                with running_server(rehearsal) as base2, self.workspace(browser, base2) as page:
                    writes = []
                    page.on("request",lambda req:writes.append(req.url) if req.method=="POST" else None)
                    expect(page.get_by_test_id("za-shortlist-count")).to_have_text("2 of 3 properties")
                    expect(page.get_by_test_id("za-comparison")).to_have_text(frozen_text,use_inner_text=True)
                    self.assertEqual(page.request.get(base2+shortlist_path).json(),frozen)
                    for i, iid in enumerate(ids):
                        expect(page.get_by_label("Decision note for Erf "+tokens[i])).to_have_value(notes[i])
                        page.get_by_role("button",name="Reopen "+iid).click()
                        expect(page.get_by_text("Reopened frozen evidence; not recalculated.")).to_be_visible()
                        expect(page.get_by_test_id("za-saved-id")).to_have_text("Saved ID: "+iid)
                        expect(page.get_by_label("Fictional asking price (ZAR)")).to_have_value(prices[i])
                        expect(page.get_by_test_id("za-comparable")).to_have_count(5 if i==0 else 0)
                        self.assertEqual(page.request.get(base2+saved_path+"/"+iid).json(),snapshots[i])
                    self.assertEqual(writes,[])
                    self.assertEqual(page.request.get(base2+"/v1/investigations/history").json()["investigations"],[])
                    self.assertEqual(page.request.get(base2+"/v1/shortlists").json()["shortlists"],[])
                    page.get_by_role("link",name="US fictional buyer workspace").click()
                    expect(page.get_by_test_id("buyer-workflow")).to_be_visible()
            finally:
                browser.close()
        self.assertFalse(rehearsal._path.exists())
