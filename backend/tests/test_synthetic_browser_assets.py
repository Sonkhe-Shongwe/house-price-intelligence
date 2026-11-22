"""Fixture-only WSGI HTML/assets and same-origin HTTP security tests.

No browser, third-party package, production data source or public server is required.
"""
from datetime import date
from io import BytesIO
from html.parser import HTMLParser
import http.client
import json
import re
import threading
import unittest
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server

from backend.synthetic_demo import example_request, in_memory_demo
from backend.synthetic_http import create_app


class SyntheticBrowserAssetTests(unittest.TestCase):
    def setUp(self):
        self.conn, store = in_memory_demo()
        self.app = create_app(store, today=date(2026, 11, 22))

    def tearDown(self):
        self.conn.close()

    def run_request(self, path, *, method="GET", origin=None, body=b"", extra=None):
        environ = {}
        setup_testing_defaults(environ)
        environ.update({"REQUEST_METHOD": method, "PATH_INFO": path,
                        "HTTP_HOST": "127.0.0.1:8765", "REMOTE_ADDR": "127.0.0.1",
                        "QUERY_STRING": "", "wsgi.input": BytesIO(body),
                        "CONTENT_TYPE": "application/json", "CONTENT_LENGTH": str(len(body))})
        if origin is not None:
            environ["HTTP_ORIGIN"] = origin
        if extra:
            environ.update(extra)
        result = {}
        def start(status, headers, exc_info=None):
            result["status"] = int(status.split()[0]); result["headers"] = dict(headers)
        result["body"] = b"".join(self.app(environ, start))
        return result

    def test_html_ids_unique_and_js_ids_present(self):
        class IdParser(HTMLParser):
            def __init__(self):
                super().__init__(); self.ids = []; self.labels = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if "id" in attrs: self.ids.append(attrs["id"])
                if tag == "label" and "for" in attrs: self.labels.append(attrs["for"])

        html = self.run_request("/")["body"].decode("utf-8")
        js = self.run_request("/assets/app.js")["body"].decode("utf-8")
        parser = IdParser(); parser.feed(html)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertTrue(set(parser.labels).issubset(set(parser.ids)))
        for field in re.findall(r"\bid\('([^']+)'\)", js):
            self.assertIn(field, parser.ids)
        self.assertNotIn("<script>", html)
        self.assertNotIn("onclick=", html)
        self.assertNotIn("<style", html)

    def test_real_loopback_http_browser_style_create_and_reopen(self):
        # WSGI stays on the SQLite-owning thread; client is independent.
        server = make_server("127.0.0.1", 0, self.app)
        server.timeout = 5
        port = server.server_port
        results = []
        def client():
            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                conn.request("GET", "/")
                response = conn.getresponse(); html = response.read().decode("utf-8")
                results.append((response.status, "SYNTHETIC DEMO" in html))
                conn.request("GET", "/assets/app.js")
                response = conn.getresponse(); js = response.read().decode("utf-8")
                results.append((response.status, "fetch(" in js))
                payload = json.dumps(example_request()).encode("utf-8")
                conn.request("POST", "/v1/investigations", body=payload,
                             headers={"Content-Type": "application/json",
                                      "Origin": f"http://127.0.0.1:{port}", "Sec-Fetch-Site": "same-origin"})
                response = conn.getresponse(); created = json.loads(response.read())
                results.append((response.status, created))
                conn.request("GET", f"/v1/investigations/{created['investigation_id']}")
                response = conn.getresponse(); reopened = json.loads(response.read())
                results.append((response.status, reopened))
                conn.close()
            except Exception as exc:
                results.append(exc)

        try:
            thread = threading.Thread(target=client, daemon=True)
            thread.start()
            for _ in range(4): server.handle_request()
            thread.join(timeout=5)
            self.assertEqual(len(results), 4, results)
            self.assertEqual(results[:2], [(200, True), (200, True)])
            self.assertEqual(results[2][0], 201)
            self.assertEqual(results[2][1]["selected_count"], 3)
            self.assertEqual(results[3], (200, results[2][1]))
        finally:
            server.server_close()

    def test_browser_assets_are_local_safe_and_explicitly_synthetic(self):
        expected = {"/": "text/html", "/assets/styles.css": "text/css",
                    "/assets/app.js": "text/javascript"}
        for route, content_type in expected.items():
            with self.subTest(route=route):
                response = self.run_request(route)
                self.assertEqual(response["status"], 200)
                self.assertIn(content_type, response["headers"]["Content-Type"])
                self.assertEqual(response["headers"]["X-Synthetic-Only"], "true")
                self.assertEqual(response["headers"]["Cache-Control"], "no-store")
                self.assertEqual(response["headers"]["X-Frame-Options"], "DENY")
                self.assertEqual(response["headers"]["X-Content-Type-Options"], "nosniff")
                self.assertIn("default-src 'none'", response["headers"]["Content-Security-Policy"])
                self.assertEqual(len(response["body"]), int(response["headers"]["Content-Length"]))
                self.assertNotIn("Access-Control-Allow-Origin", response["headers"])
        html = self.run_request("/")["body"].decode()
        self.assertIn("SYNTHETIC DEMO", html)
        self.assertIn('id="investigation-form"', html)
        self.assertIn('id="reopen-form"', html)
        self.assertIn('src="/assets/app.js"', html)
        js = self.run_request("/assets/app.js")["body"].decode()
        self.assertIn(".textContent", js)
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("localStorage", js)
        self.assertNotIn("https://", js)

    def test_static_asset_whitelist_and_methods(self):
        for path in ("/assets/../backend/schema_draft.sql", "/backend/synthetic_demo.py",
                     "/assets/other.js", "/favicon.ico", "/../../etc/passwd"):
            with self.subTest(path=path):
                self.assertEqual(self.run_request(path)["status"], 404)
        r = self.run_request("/", method="POST")
        self.assertEqual(r["status"], 405)
        self.assertEqual(r["headers"]["Allow"], "GET")

    def test_same_origin_browser_post_is_allowed(self):
        body = json.dumps(example_request()).encode("utf-8")
        result = self.run_request("/v1/investigations", method="POST", body=body,
                                  origin="http://127.0.0.1:8765",
                                  extra={"HTTP_SEC_FETCH_SITE": "same-origin"})
        self.assertEqual(result["status"], 201, result["body"])
        data = json.loads(result["body"])
        self.assertEqual(data["status"], "supported_neighbourhood")
        self.assertEqual(data["selected_count"], 3)
        self.assertIsNone(data["valuation"])
        self.assertIsNotNone(re.fullmatch(r"/v1/investigations/[0-9a-f-]+", result["headers"]["Location"]))
        reloaded = self.run_request(result["headers"]["Location"], extra={"HTTP_SEC_FETCH_SITE": "same-origin"})
        self.assertEqual(reloaded["status"], 200)
        self.assertEqual(json.loads(reloaded["body"]), data)

    def test_cross_origin_and_forwarded_requests_rejected(self):
        body = json.dumps(example_request()).encode("utf-8")
        for origin, extra in (("http://localhost:8765", None), ("http://127.0.0.1:8766", None),
                              ("http://evil.invalid", None), ("null", None),
                              ("http://127.0.0.1:8765", {"HTTP_SEC_FETCH_SITE": "cross-site"}),
                              ("http://127.0.0.1:8765", {"HTTP_X_FORWARDED_FOR": "127.0.0.1"})):
            with self.subTest(origin=origin, extra=extra):
                r = self.run_request("/v1/investigations", method="POST", origin=origin,
                                     body=body, extra=extra)
                self.assertEqual(r["status"], 403)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
