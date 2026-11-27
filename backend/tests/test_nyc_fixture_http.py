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
