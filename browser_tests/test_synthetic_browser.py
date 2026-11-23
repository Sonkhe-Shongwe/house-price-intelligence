"""Real Chromium acceptance tests against the committed, synthetic-only WSGI/SQLite app.

The demo runs in a disposable subprocess; browser requests cross the actual
localhost HTTP boundary. No API mocking, network publisher data, deployment,
persistent database or owner Windows installation is involved.

GitHub Actions installs the pinned Playwright test dependency separately.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


class SyntheticBrowserAcceptanceTests(unittest.TestCase):
    """Browser + HTTP + Python matcher + in-memory SQLite, on one source tree."""

    @classmethod
    def setUpClass(cls):
        cls.log = tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
        cls.server = None
        cls.playwright = None
        cls.browser = None
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            cls.base_url = f"http://127.0.0.1:{port}"
            cls.server = subprocess.Popen(
                [sys.executable, "-m", "backend.run_synthetic_api",
                 "--fixture-only", "--port", str(port)],
                cwd=ROOT, stdout=cls.log, stderr=subprocess.STDOUT,
            )
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if cls.server.poll() is not None:
                    break
                try:
                    with urlopen(cls.base_url + "/health", timeout=0.5) as reply:
                        payload = json.load(reply)
                        if reply.status == 200 and payload == {
                            "status": "ok", "mode": "synthetic_fixture_only"
                        }:
                            break
                except (OSError, URLError, ValueError):
                    time.sleep(0.15)
            else:
                raise RuntimeError("Synthetic localhost server did not become healthy")
            if cls.server.poll() is not None:
                raise RuntimeError("Synthetic localhost server exited before acceptance tests")

            cls.playwright = sync_playwright().start()
            cls.browser = cls.playwright.chromium.launch(headless=True)
        except Exception:
            cls._stop_server()
            if cls.playwright is not None:
                cls.playwright.stop()
            raise

    @classmethod
    def _stop_server(cls):
        if cls.server is not None:
            if cls.server.poll() is None:
                cls.server.terminate()
                try:
                    cls.server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    cls.server.kill()
                    cls.server.wait(timeout=5)
            cls.server = None
        if cls.log is not None:
            cls.log.close()

    @classmethod
    def tearDownClass(cls):
        try:
            if cls.browser is not None:
                cls.browser.close()
            if cls.playwright is not None:
                cls.playwright.stop()
        finally:
            cls._stop_server()

    def setUp(self):
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()

    def test_supported_investigation_and_reopen_same_frozen_evidence(self):
        self.page.goto(self.base_url + "/")
        expect(self.page.locator("#result-state")).to_have_text("AWAITING INVESTIGATION")

        with self.page.expect_response(
            lambda response: response.request.method == "POST"
            and response.url == self.base_url + "/v1/investigations"
        ) as creation:
            self.page.locator("#submit-button").click()

        created = creation.value
        self.assertEqual(created.status, 201)
        result = created.json()
        self.assertEqual(result["status"], "supported_neighbourhood")
        self.assertEqual(result["selected_count"], 3)
        self.assertEqual(len(result["comparables"]), 3)
        self.assertIsNone(result["valuation"])
        self.assertEqual(result["data_build"]["source_kind"], "synthetic_fixture")
        self.assertTrue(all(sale["sale_date"] < result["analysis_date"]
                            for sale in result["comparables"]))

        expect(self.page.locator("#status-pill")).to_have_text("Same-neighbourhood evidence")
        expect(self.page.locator("#stat-count")).to_have_text("3")
        expect(self.page.locator("#comparables .comp")).to_have_count(3)
        investigation_id = result["investigation_id"]
        self.assertRegex(investigation_id, UUID_PATTERN)
        expect(self.page.locator("#reopen-id")).to_have_value(investigation_id)

        # New tab and same running SQLite process. The reopened response must
        # be identical: no fresh matching, changed prices or fabricated data.
        reopened_page = self.context.new_page()
        with reopened_page.expect_response(
            lambda response: response.request.method == "GET"
            and response.url == self.base_url + "/v1/investigations/" + investigation_id
        ) as reopened:
            reopened_page.goto(self.base_url + "/#investigation/" + investigation_id)
        self.assertEqual(reopened.value.status, 200)
        self.assertEqual(reopened.value.json(), result)
        expect(reopened_page.locator("#stat-count")).to_have_text("3")
        expect(reopened_page.locator("#comparables .comp")).to_have_count(3)
        self.assertEqual(reopened_page.url.split("#", 1)[1], "investigation/" + investigation_id)

    def test_unknown_parcel_safely_abstains_and_can_reopen(self):
        self.page.goto(self.base_url + "/")
        self.page.locator("#example-unknown").click()
        expect(self.page.locator("#pin")).to_have_value("00000000000099")
        with self.page.expect_response(
            lambda response: response.request.method == "POST"
            and response.url == self.base_url + "/v1/investigations"
        ) as creation:
            self.page.locator("#submit-button").click()
        self.assertEqual(creation.value.status, 201)
        result = creation.value.json()
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["selected_count"], 0)
        self.assertEqual(result["comparables"], [])
        self.assertIsNone(result["valuation"])
        expect(self.page.locator("#status-pill")).to_have_text("Insufficient evidence")
        expect(self.page.locator("#stat-count")).to_have_text("0")
        expect(self.page.locator("#comparables .comp")).to_have_count(0)
        expect(self.page.locator("#unsupported")).to_contain_text(
            "No comparable sale prices or numerical valuation have been produced."
        )
        with self.page.expect_response(
            lambda response: response.request.method == "GET"
            and response.url == self.base_url + "/v1/investigations/" + result["investigation_id"]
        ) as reopened:
            self.page.locator("#reopen-form button").click()
        self.assertEqual(reopened.value.status, 200)
        self.assertEqual(reopened.value.json(), result)

    def test_address_search_selection_investigation_and_reopen(self):
        self.page.goto(self.base_url + "/")
        with self.page.expect_response(
            lambda response: response.url == self.base_url + "/v1/addresses/search"
            and response.request.method == "POST"
        ) as search:
            self.page.locator("#address-search-button").click()
        self.assertEqual(search.value.status, 200)
        self.assertEqual(len(search.value.json()["candidates"]), 4)
        expect(self.page.locator("#address-results .address-option")).to_have_count(4)
        expect(self.page.locator("#pin")).to_have_value("")
        with self.page.expect_response(
            lambda response: "/v1/addresses/fictional-1" in response.url
        ) as choice:
            self.page.get_by_role("button", name="101 Fictional Way, Demonstration District").click()
        self.assertEqual(choice.value.status, 200)
        expect(self.page.locator("#pin")).to_have_value("00000000000001")
        expect(self.page.locator("#selected-address")).to_contain_text("101 Fictional Way")
        with self.page.expect_response(
            lambda response: response.url == self.base_url + "/v1/investigations"
            and response.request.method == "POST"
        ) as saved:
            self.page.locator("#submit-button").click()
        self.assertEqual(saved.value.status, 201)
        self.assertEqual(saved.value.json()["selected_count"], 3)
        self.assertEqual(saved.value.json()["subject"]["address_id"], "fictional-1")
        self.assertEqual(saved.value.json()["subject"]["identity_status"], "synthetic_mapping_only")
        self.assertEqual(saved.value.json()["comparables"][0]["sale_price_usd"], "525000.00")
        self.assertNotIn("sale_price", saved.value.json()["comparables"][0])
        expect(self.page.locator("#comparables .comp")).to_have_count(3)
        expect(self.page.locator(".comp-price").first).to_have_text("$525,000.00")
        investigation_id = saved.value.json()["investigation_id"]
        reopened = self.context.new_page()
        with reopened.expect_response(
            lambda response: response.url == self.base_url + "/v1/investigations/" + investigation_id
        ) as original:
            reopened.goto(self.base_url + "/#investigation/" + investigation_id)
        self.assertEqual(original.value.json(), saved.value.json())

    def test_identical_fictional_address_requires_explicit_parcel_choice(self):
        self.page.goto(self.base_url + "/")
        self.page.locator("#address-query").fill("105 Fictional Court")
        with self.page.expect_response(
            lambda response: response.url == self.base_url + "/v1/addresses/search"
        ) as searched:
            self.page.locator("#address-search-button").click()
        self.assertEqual(len(searched.value.json()["candidates"]), 2)
        expect(self.page.locator("#address-search-feedback")).to_contain_text(
            "One address has multiple parcels"
        )
        expect(self.page.locator("#address-results .address-option")).to_have_count(2)
        expect(self.page.locator("#pin")).to_have_value("")
        with self.page.expect_response(
            lambda response: response.url.endswith("/v1/addresses/fictional-6")
        ) as selected:
            self.page.get_by_role("button", name="105 Fictional Court, Demonstration District · Synthetic parcel option B").click()
        self.assertEqual(selected.value.json()["pin"], "00000000000006")
        expect(self.page.locator("#pin")).to_have_value("00000000000006")
        expect(self.page.locator("#selected-address")).to_contain_text("building unverified")
        with self.page.expect_response(
            lambda response: response.url == self.base_url + "/v1/investigations"
        ) as created:
            self.page.locator("#submit-button").click()
        self.assertEqual(created.value.status, 201)
        self.assertEqual(created.value.json()["subject"]["address_id"], "fictional-6")
        self.assertEqual(created.value.json()["subject"]["pin"], "00000000000006")
        self.assertEqual(created.value.json()["subject"]["identity_scope"], "parcel_only")
        self.assertIs(created.value.json()["subject"]["building_identity_verified"], False)

    def test_manual_pin_edit_clears_address_selection(self):
        self.page.goto(self.base_url + "/")
        with self.page.expect_response(
            lambda response: response.url == self.base_url + "/v1/addresses/search"
        ):
            self.page.locator("#address-search-button").click()
        with self.page.expect_response(
            lambda response: response.url.endswith("/v1/addresses/fictional-1")
        ):
            self.page.get_by_role("button", name="101 Fictional Way, Demonstration District").click()
        expect(self.page.locator("#selected-address")).to_be_visible()
        self.page.locator("#pin").fill("00000000000099")
        expect(self.page.locator("#selected-address")).to_be_hidden()
        with self.page.expect_response(
            lambda response: response.url == self.base_url + "/v1/investigations"
        ) as created:
            self.page.locator("#submit-button").click()
        self.assertEqual(created.value.status, 201)
        self.assertEqual(created.value.json()["status"], "insufficient_data")
        self.assertNotIn("address_id", created.value.json()["subject"])

    def test_no_address_match_does_not_guess_or_investigate_old_pin(self):
        self.page.goto(self.base_url + "/")
        self.page.locator("#address-query").fill("Nonexistent Imaginary Road")
        with self.page.expect_response(
            lambda response: response.url == self.base_url + "/v1/addresses/search"
        ) as search:
            self.page.locator("#address-search-button").click()
        self.assertEqual(search.value.json()["status"], "no_match")
        expect(self.page.locator("#address-search-feedback")).to_contain_text("No invented address matched")
        expect(self.page.locator("#address-results .address-option")).to_have_count(0)
        expect(self.page.locator("#pin")).to_have_value("")
        posted = []
        self.page.on("request", lambda request: posted.append(request.url)
                     if request.url == self.base_url + "/v1/investigations"
                     and request.method == "POST" else None)
        self.page.locator("#submit-button").click()
        self.assertEqual(posted, [])
        expect(self.page.locator("#result-state")).to_have_text("AWAITING INVESTIGATION")

    def test_invalid_asking_price_does_not_send_a_request(self):
        self.page.goto(self.base_url + "/")
        self.page.locator("#price").fill("not-a-price")
        posted = []
        self.page.on(
            "request", lambda request: posted.append(request.url)
            if request.method == "POST" else None
        )
        self.page.locator("#submit-button").click()
        expect(self.page.locator("#form-feedback")).to_contain_text(
            "Enter the asking price using up to two decimal places."
        )
        self.assertEqual(posted, [])
        expect(self.page.locator("#result-state")).to_have_text("AWAITING INVESTIGATION")

    def test_durable_fixture_reopens_after_real_server_restart(self):
        """Chromium -> HTTP -> file-backed SQLite -> server restart -> reopen."""
        with tempfile.TemporaryDirectory() as folder:
            fixture_path = Path(folder) / "browser-fictional.sqlite"
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            base = f"http://127.0.0.1:{port}"
            restarted_server = None

            def launch():
                process = subprocess.Popen(
                    [sys.executable, "-m", "backend.run_synthetic_api",
                     "--fixture-only", "--port", str(port),
                     "--fixture-db", str(fixture_path)],
                    cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                )
                for _ in range(80):
                    if process.poll() is not None:
                        raise RuntimeError("Durable synthetic server exited unexpectedly")
                    try:
                        with urlopen(base + "/health", timeout=0.4) as response:
                            if response.status == 200:
                                return process
                    except (OSError, URLError):
                        time.sleep(0.15)
                process.terminate()
                process.wait(timeout=5)
                raise RuntimeError("Durable synthetic server did not become healthy")

            try:
                restarted_server = launch()
                self.page.goto(base + "/")
                with self.page.expect_response(
                    lambda response: response.url == base + "/v1/investigations"
                    and response.request.method == "POST"
                ) as creation:
                    self.page.locator("#submit-button").click()
                saved = creation.value.json()
                self.assertEqual(creation.value.status, 201)
                self.assertEqual(saved["selected_count"], 3)
                self.assertIsNone(saved["valuation"])
                self.assertEqual(saved["comparables"][0]["sale_price_usd"], "525000.00")
                restarted_server.terminate()
                restarted_server.wait(timeout=5)
                restarted_server = None

                restarted_server = launch()
                later = self.context.new_page()
                with later.expect_response(
                    lambda response: response.url == base + "/v1/investigations/"
                    + saved["investigation_id"]
                ) as reopened:
                    later.goto(base + "/#investigation/" + saved["investigation_id"])
                self.assertEqual(reopened.value.status, 200)
                self.assertEqual(reopened.value.json(), saved)
                expect(later.locator("#comparables .comp")).to_have_count(3)
                expect(later.locator("#stat-count")).to_have_text("3")
            finally:
                if restarted_server is not None and restarted_server.poll() is None:
                    restarted_server.terminate()
                    restarted_server.wait(timeout=5)



if __name__ == "__main__":
    unittest.main()
