"""Exercise NYC opt-in, request/response boundary and actual loopback HTTP."""
from io import BytesIO
import http.client
import json
import tempfile
from pathlib import Path
import threading
import unittest
from wsgiref.simple_server import make_server
from wsgiref.util import setup_testing_defaults
from unittest.mock import patch

from backend.nyc_fixture_http import NYC_PATH, CONTRACT, fixture
from backend.synthetic_demo import in_memory_demo
from backend.synthetic_http import create_app


class NYCFixHttpTests(unittest.TestCase):
    def setUp(self):
        self.db, self.store = in_memory_demo()
        self.app = create_app(self.store, nyc_fixture=True)
        self.req = {"contract_version": CONTRACT, "address": "Fictional NYC Home A",
                    "asking_price_usd": "650000.01"}

    def tearDown(self):
        self.db.close()

    def invoke(self, method="POST", path=NYC_PATH, payload=None, raw=None, **extra):
        if raw is None:
            raw = json.dumps(self.req if payload is None else payload).encode()
        env = {}
        setup_testing_defaults(env)
        env.update({"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "",
                    "REMOTE_ADDR": "127.0.0.1", "HTTP_HOST": "localhost:8765",
                    "CONTENT_TYPE": "application/json", "CONTENT_LENGTH": str(len(raw)),
                    "wsgi.input": BytesIO(raw)})
        env.update(extra)
        result = {}
        def respond(status, headers):
            result.update(status=int(status.split()[0]), headers=dict(headers))
        result["body"] = json.loads(b"".join(self.app(env, respond)))
        return result

    def test_default_closed_and_opt_in_type(self):
        self.app = create_app(self.store)
        self.assertEqual(self.invoke()["status"], 404)
        with self.assertRaises(ValueError):
            create_app(self.store, nyc_fixture="yes")
        with tempfile.TemporaryDirectory() as tmp:
            self.db.execute("ATTACH DATABASE ? AS persistent_fixture", (str(Path(tmp)/"fixture.sqlite"),))
            try:
                with self.assertRaises(ValueError):
                    create_app(self.store, nyc_fixture=True)
            finally:
                self.db.execute("DETACH DATABASE persistent_fixture")

    def test_supported_and_no_persistence(self):
        before = self.db.total_changes
        r = self.invoke()
        self.assertEqual(r["status"], 200)
        self.assertEqual(r["headers"]["Cache-Control"], "no-store")
        self.assertEqual(r["headers"]["X-Synthetic-Only"], "true")
        body = r["body"]
        self.assertEqual(body["status"], "supported")
        self.assertEqual(body["selected_count"], 4)
        self.assertEqual(body["asking_price_usd"], "650000.01")
        self.assertIsNone(body["valuation"])
        self.assertFalse(body["provenance"]["public_display_approved"])
        _, addresses, sales, masters, _ = fixture()
        for value in [a.key for a in addresses]+[s.key for s in sales]+[m.doc for m in masters]:
            self.assertNotIn(value, str(body))
        self.assertEqual(self.db.total_changes, before)
        self.assertEqual(self.invoke("GET", "/v1/investigations/history")["body"]["investigations"], [])

    def test_abstention_and_no_fuzzy_match(self):
        for address, status in (("Fictional NYC Home B", "insufficient_data"),
                                ("Fictional NYC Ambiguous", "ambiguous_address"),
                                ("Fictional NYC Unsupported", "out_of_coverage"),
                                ("Fictional NYC Unknown", "out_of_coverage"),
                                ("Fictional NYC Home", "out_of_coverage")):
            result = self.invoke(payload=self.req | {"address":address})
            self.assertEqual(result["status"], 200)
            self.assertEqual(result["body"]["status"], status)
            self.assertEqual(result["body"]["comparables"], [])

    def test_strict_request_and_transport(self):
        for payload in (self.req | {"source_rows":[]}, self.req | {"owner":"x"},
                        self.req | {"address":"nonfictional address"},
                        self.req | {"asking_price_usd":650000.01},
                        self.req | {"asking_price_usd":"0"},
                        self.req | {"asking_price_usd":"1.001"},
                        self.req | {"contract_version":"real"}):
            self.assertEqual(self.invoke(payload=payload)["status"], 422)
        self.assertEqual(self.invoke(raw=b'{"address":"x","address":"y"}')["status"],400)
        self.assertEqual(self.invoke("GET")["status"],405)
        self.assertEqual(self.invoke(QUERY_STRING="source=real")["status"],400)
        self.assertEqual(self.invoke(HTTP_ORIGIN="https://evil.invalid")["status"],403)
        self.assertEqual(self.invoke(REMOTE_ADDR="192.0.2.1")["status"],403)
        self.assertEqual(self.invoke(HTTP_X_FORWARDED_FOR="127.0.0.1")["status"],403)

    def test_error_redaction(self):
        with patch("backend.synthetic_http.investigate_nyc_fixture",
                   side_effect=RuntimeError("invented private identifier")):
            result = self.invoke()
            self.assertEqual(result["status"],500)
            self.assertEqual(result["body"],{"error":"internal_error"})

    def test_lifecycle_refusals_precede_matching_and_no_persistence(self):
        from backend.nyc_fixture_http import _authority, _REHEARSAL_NOW
        from datetime import timedelta
        from dataclasses import replace
        current = _authority(_REHEARSAL_NOW)
        first = current.sources[0]
        states = [
            replace(current, sources=(replace(first, permission="revoked"), *current.sources[1:])),
            replace(current, sources=(replace(first, accuracy="disputed"), *current.sources[1:])),
            replace(current, sources=(replace(first, protection="lost"), *current.sources[1:])),
            replace(current, sources=(replace(first, deadline=_REHEARSAL_NOW), *current.sources[1:])),
            replace(current, sources=(replace(first, operations=frozenset()), *current.sources[1:])),
            replace(current, sources=current.sources[:-1]),
            replace(current, observed_at=_REHEARSAL_NOW-timedelta(seconds=1)),
            replace(current, owner="fixture-other-owner"),
        ]
        before = self.db.total_changes
        for state in states:
            with self.subTest(state=state), patch("backend.nyc_fixture_http._authority", return_value=state), patch(
                    "backend.nyc_fixture_http.investigate_fixture") as matcher:
                result = self.invoke()
                self.assertEqual(result["status"], 503)
                self.assertEqual(result["body"], {"error":"nyc_evidence_unavailable"})
                self.assertEqual(result["headers"]["Cache-Control"], "no-store")
                matcher.assert_not_called()
        self.assertEqual(self.db.total_changes, before)
        self.assertEqual(self.invoke()["body"]["status"], "supported")

    def test_lifecycle_seal_mismatch_and_guard_failure(self):
        from dataclasses import replace
        plan, *rows = fixture()
        for bad in (replace(plan, version="fixture-nyc-other"),
                    replace(plan, revisions=tuple((d,"fixture-other") for d,_ in plan.revisions)),
                    replace(plan, revisions=plan.revisions[:-1]),
                    replace(plan, source_kind="real")):
            with self.subTest(plan=bad), patch("backend.nyc_fixture_http.fixture", return_value=(bad,*rows)), patch(
                    "backend.nyc_fixture_http.investigate_fixture") as matcher:
                result = self.invoke()
                self.assertEqual(result["status"], 503)
                self.assertEqual(result["body"], {"error":"nyc_evidence_unavailable"})
                matcher.assert_not_called()
        with patch("backend.nyc_fixture_http._authority", side_effect=RuntimeError("invented private seal")), patch(
                "backend.nyc_fixture_http.investigate_fixture") as matcher:
            result = self.invoke()
            self.assertEqual(result["status"], 500)
            self.assertEqual(result["body"], {"error":"internal_error"})
            matcher.assert_not_called()

    def test_request_cannot_choose_lifecycle_authority(self):
        for field, value in (("authority", {}), ("now", "2026-11-28"), ("operation", "read"),
                             ("permission", "reviewed"), ("source_revision", "fixture-http-one")):
            with self.subTest(field=field), patch("backend.nyc_fixture_http._authority") as authority:
                self.assertEqual(self.invoke(payload=self.req | {field:value})["status"], 422)
                authority.assert_not_called()

    def test_actual_loopback_lifecycle_refusal(self):
        from backend.nyc_fixture_http import _authority, _REHEARSAL_NOW
        from dataclasses import replace
        authority = _authority(_REHEARSAL_NOW)
        first = replace(authority.sources[0], permission="revoked")
        refused = replace(authority, sources=(first,*authority.sources[1:]))
        with patch("backend.nyc_fixture_http._authority", return_value=refused), make_server(
                "127.0.0.1", 0, self.app) as server:
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            try:
                conn.request("POST", NYC_PATH, json.dumps(self.req),
                             {"Content-Type":"application/json"})
                response = conn.getresponse()
                self.assertEqual(response.status,503)
                self.assertEqual(json.loads(response.read()),{"error":"nyc_evidence_unavailable"})
                self.assertEqual(response.getheader("Cache-Control"),"no-store")
            finally:
                conn.close()
                thread.join(5)
            self.assertFalse(thread.is_alive())

    def test_actual_loopback_http(self):
        with make_server("127.0.0.1", 0, self.app) as server:
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            try:
                conn.request("POST", NYC_PATH, json.dumps(self.req),
                             {"Content-Type":"application/json"})
                response = conn.getresponse()
                self.assertEqual(response.status,200)
                self.assertEqual(json.loads(response.read())["selected_count"],4)
            finally:
                conn.close()
                thread.join(5)
            self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
