"""HTTP boundary tests using ONLY invented, in-memory synthetic records."""
from datetime import date
from io import BytesIO
import http.client
import json
import sqlite3
import threading
import unittest
from wsgiref.simple_server import make_server
from wsgiref.util import setup_testing_defaults

from backend.synthetic_demo import SUBJECT_PIN, example_request, in_memory_demo
from backend.synthetic_http import MAX_BODY_BYTES, create_app

TODAY = date(2026, 11, 22)


class SyntheticHttpTests(unittest.TestCase):
    def setUp(self):
        self.db, store = in_memory_demo()
        self.app = create_app(store, today=TODAY)

    def tearDown(self):
        self.db.close()

    def invoke(self, method="GET", path="/health", *, payload=None, raw=None, content_type="application/json",
               host="127.0.0.1:8765", remote="127.0.0.1", origin=None, declared_length=None,
               extra=None, query=""):
        if raw is None:
            raw = b"" if payload is None else json.dumps(payload).encode("utf-8")
        env = {}
        setup_testing_defaults(env)
        env.update({"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
                    "REMOTE_ADDR": remote, "HTTP_HOST": host,
                    "CONTENT_TYPE": content_type, "CONTENT_LENGTH": (str(declared_length) if declared_length is not None else str(len(raw))),
                    "wsgi.input": BytesIO(raw)})
        if origin is not None:
            env["HTTP_ORIGIN"] = origin
        if extra:
            env.update(extra)
        observed = {}

        def respond(status, headers, exc_info=None):
            observed["status"] = int(status.split()[0]); observed["headers"] = dict(headers)

        data = b"".join(self.app(env, respond))
        observed["body"] = json.loads(data)
        observed["raw"] = data
        return observed

    def test_health_local_no_data_leak(self):
        r = self.invoke()
        self.assertEqual(r["status"], 200)
        self.assertEqual(r["body"], {"status": "ok", "mode": "synthetic_fixture_only"})
        self.assertEqual(r["headers"]["Cache-Control"], "no-store")
        self.assertEqual(r["headers"]["X-Synthetic-Only"], "true")
        self.assertNotIn("Access-Control-Allow-Origin", r["headers"])

    def test_address_search_returns_multiple_options_without_guessing(self):
        found = self.invoke("POST", "/v1/addresses/search",
                            payload={"query": "FICTIONAL   WAY"})
        self.assertEqual(found["status"], 200)
        self.assertEqual(found["body"]["source_kind"], "synthetic_fixture")
        self.assertEqual(found["body"]["status"], "matches")
        self.assertEqual(len(found["body"]["candidates"]), 4)
        self.assertEqual(len({x["address_id"] for x in found["body"]["candidates"]}), 4)
        self.assertTrue(all("pin" not in x for x in found["body"]["candidates"]))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 0)

    def test_selected_address_resolves_to_server_owned_parcel_and_investigates(self):
        found = self.invoke("POST", "/v1/addresses/search", payload={"query": "101 fictional"})
        self.assertEqual(len(found["body"]["candidates"]), 1)
        aid = found["body"]["candidates"][0]["address_id"]
        result = self.invoke(path="/v1/addresses/" + aid)
        self.assertEqual(result["status"], 200)
        self.assertEqual(result["body"]["identity_status"], "synthetic_mapping_only")
        self.assertEqual(result["body"]["pin"], SUBJECT_PIN)
        request = example_request()
        request["subject"]["pin"] = result["body"]["pin"]
        created = self.invoke("POST", "/v1/investigations", payload=request)
        self.assertEqual(created["status"], 201)
        self.assertEqual(created["body"]["selected_count"], 3)
        self.assertIsNone(created["body"]["valuation"])
        self.assertEqual(self.invoke(path=created["headers"]["Location"])["body"], created["body"])

    def test_selected_address_is_bound_by_server_even_without_client_pin(self):
        req = example_request()
        req["subject"].update(pin=None, address_id="fictional-1")
        created = self.invoke("POST", "/v1/investigations", payload=req)
        self.assertEqual(created["status"], 201)
        self.assertEqual(created["body"]["subject"]["pin"], SUBJECT_PIN)
        self.assertEqual(created["body"]["subject"]["address_id"], "fictional-1")
        self.assertEqual(created["body"]["subject"]["identity_status"], "synthetic_mapping_only")
        self.assertEqual(created["body"]["selected_count"], 3)
        self.assertEqual(self.invoke(path=created["headers"]["Location"])["body"], created["body"])

    def test_stale_or_unknown_address_id_fails_without_a_saved_record(self):
        for address_id, pin, code in (
            ("fictional-1", "00000000000002", "identity_conflict"),
            ("fictional-99", SUBJECT_PIN, "address_not_found"),
        ):
            req = example_request()
            req["subject"].update(address_id=address_id, pin=pin)
            with self.subTest(address_id=address_id):
                result = self.invoke("POST", "/v1/investigations", payload=req)
                self.assertEqual(result["status"], 422)
                self.assertEqual(result["body"]["field"], "subject.address_id")
                self.assertEqual(result["body"]["code"], code)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 0)

    def test_exact_money_json_contract_does_not_expose_float_prices(self):
        created = self.invoke("POST", "/v1/investigations", payload=example_request())
        self.assertEqual(created["status"], 201)
        self.assertEqual(created["body"]["contract_version"], "p3-draft-v0.3")
        for sale in created["body"]["comparables"]:
            self.assertEqual(sale["sale_price_usd"], "525000.00")
            self.assertNotIn("sale_price", sale)

    def test_unknown_and_malformed_address_fail_safely(self):
        none = self.invoke("POST", "/v1/addresses/search",
                           payload={"query": "Nonexistent Imaginary Road"})
        self.assertEqual(none["status"], 200)
        self.assertEqual(none["body"]["status"], "no_match")
        self.assertEqual(none["body"]["candidates"], [])
        self.assertEqual(self.invoke(path="/v1/addresses/not-indexed")["status"], 404)
        for body in ({}, {"query": "a"}, {"query": "xx' OR 1=1 --"},
                     {"query": "Fictional", "pin": SUBJECT_PIN},
                     {"query": ["fictional"]}, {"query": "a" * 81}):
            with self.subTest(body=body):
                self.assertEqual(self.invoke("POST", "/v1/addresses/search", payload=body)["status"], 422)
        self.assertEqual(self.invoke("GET", "/v1/addresses/search")["status"], 405)
        self.assertEqual(self.invoke("POST", "/v1/addresses/fictional-1")["status"], 405)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 0)

    def test_address_search_respects_fixture_and_origin_guards(self):
        self.assertEqual(self.invoke("POST", "/v1/addresses/search",
                                     payload={"query": "Fictional Way"},
                                     origin="http://untrusted.invalid")["status"], 403)
        self.db.execute("UPDATE curated_builds SET build_kind='historical_research'")
        result = self.invoke("POST", "/v1/addresses/search",
                             payload={"query": "Fictional Way"})
        self.assertEqual(result["status"], 503)
        self.assertEqual(result["body"], {"error": "evidence_unavailable"})

    def test_create_then_get_reopens_exact_database_evidence(self):
        create = self.invoke("POST", "/v1/investigations", payload=example_request())
        self.assertEqual(create["status"], 201)
        self.assertEqual(create["body"]["status"], "supported_neighbourhood")
        self.assertEqual(create["body"]["selected_count"], 3)
        self.assertEqual(len(create["body"]["comparables"]), 3)
        self.assertIsNone(create["body"]["valuation"])
        self.assertTrue(create["body"]["data_build"]["source_kind"], "synthetic_fixture")
        route = create["headers"]["Location"]
        self.assertEqual(self.invoke(path=route)["body"], create["body"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM comparable_evidence").fetchone()[0], 3)

    def test_fallback_warning_not_a_valuation(self):
        self.db.execute("UPDATE parcel_geographies SET neighborhood_code='18',latitude=42.041,longitude=-87.681 WHERE pin != ?", (SUBJECT_PIN,))
        r = self.invoke("POST", "/v1/investigations", payload=example_request())
        self.assertEqual(r["status"], 201)
        self.assertEqual(r["body"]["status"], "exploratory_spatial")
        self.assertTrue(any("exploratory" in x.lower() for x in r["body"]["warnings"]))
        self.assertIsNone(r["body"]["valuation"])

    def test_unresolved_pin_is_saved_as_insufficient_draft(self):
        req = example_request(); req["subject"]["pin"] = None
        r = self.invoke("POST", "/v1/investigations", payload=req)
        self.assertEqual(r["status"], 201)
        self.assertEqual(r["body"]["status"], "insufficient_data")
        self.assertEqual(r["body"]["reason"], "parcel_identity_not_resolved")
        self.assertEqual(self.invoke(path=r["headers"]["Location"])["body"], r["body"])

    def test_unknown_pin_abstains_instead_of_404(self):
        req = example_request(); req["subject"]["pin"] = "00000000000099"
        r = self.invoke("POST", "/v1/investigations", payload=req)
        self.assertEqual(r["status"], 201)
        self.assertEqual(r["body"]["reason"], "parcel_not_found_in_curated_build")

    def test_unsupported_class_returns_supported_http_status_with_out_of_coverage(self):
        req = example_request(); req["class_code"] = "211"
        r = self.invoke("POST", "/v1/investigations", payload=req)
        self.assertEqual(r["status"], 201)
        self.assertEqual(r["body"]["status"], "out_of_coverage")

    def test_invalid_buyer_field_gets_422_without_writes(self):
        req = example_request(); req["subject"]["lat"] = 42.04
        r = self.invoke("POST", "/v1/investigations", payload=req)
        self.assertEqual(r["status"], 422)
        self.assertEqual(r["body"]["field"], "subject")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 0)

    def test_client_cannot_choose_build_or_enable_demo_mode(self):
        for key, value in (("data_build", {"build_id": "synthetic-build"}), ("synthetic_demo", True),
                           ("investigation_id", "client-id")):
            req = example_request(); req[key] = value
            with self.subTest(key=key):
                r = self.invoke("POST", "/v1/investigations", payload=req)
                self.assertEqual(r["status"], 422)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 0)

    def test_wrong_content_type_415(self):
        self.assertEqual(self.invoke("POST", "/v1/investigations", payload=example_request(), content_type="text/plain")["status"], 415)

    def test_json_charset_accepted(self):
        r = self.invoke("POST", "/v1/investigations", payload=example_request(), content_type="application/json; charset=utf-8")
        self.assertEqual(r["status"], 201)

    def test_malformed_json_400(self):
        for bad in (b"{", b"", b'\xff', b'{"a":NaN}', b'{"a":Infinity}', b'{"a":"\\ud800"}',
                    b'{"subject":{},"subject":{}}'):
            with self.subTest(bad=bad):
                r = self.invoke("POST", "/v1/investigations", raw=bad)
                self.assertEqual(r["status"], 400)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 0)

    def test_missing_length_411(self):
        r = self.invoke("POST", "/v1/investigations", raw=b'{}', extra={"CONTENT_LENGTH": ""})
        self.assertEqual(r["status"], 411)

    def test_body_too_big_413(self):
        r = self.invoke("POST", "/v1/investigations", raw=b"x", declared_length=MAX_BODY_BYTES+1)
        self.assertEqual(r["status"], 413)
        r = self.invoke("POST", "/v1/investigations", raw=b"x", extra={"CONTENT_LENGTH": "9"*5000})
        self.assertEqual(r["status"], 413)

    def test_partial_body_400(self):
        self.assertEqual(self.invoke("POST", "/v1/investigations", raw=b"{}", declared_length=3)["status"], 400)

    def test_json_list_not_an_object_422(self):
        self.assertEqual(self.invoke("POST", "/v1/investigations", raw=b"[]")["status"], 422)

    def test_unknown_route_404(self):
        self.assertEqual(self.invoke(path="/v1/listings")["status"], 404)
        self.assertEqual(self.invoke(path="/v1/investigations/abc")["status"], 404)

    def test_unknown_valid_id_404(self):
        r = self.invoke(path="/v1/investigations/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        self.assertEqual(r["status"], 404)
        self.assertEqual(r["body"]["error"], "investigation_not_found")

    def test_methods_rejected_with_allow_header(self):
        self.assertEqual(self.invoke("GET", "/v1/investigations")["headers"]["Allow"], "POST")
        self.assertEqual(self.invoke("POST", "/health")["status"], 405)
        self.assertEqual(self.invoke("OPTIONS", "/v1/investigations")["status"], 405)

    def test_query_string_rejected(self):
        self.assertEqual(self.invoke(path="/health", query="a=b")["status"], 400)

    def test_rejects_nonloopback_or_wrong_host_or_origin(self):
        for args in ({"remote": "10.0.0.1"}, {"remote": None}, {"host": "evil.invalid"},
                     {"host": "127.0.0.1.bad.invalid"}, {"origin": "https://evil.invalid"},
                     {"extra": {"HTTP_X_FORWARDED_FOR": "127.0.0.1"}},
                     {"extra": {"HTTP_X_FORWARDED_HOST": "localhost"}},
                     {"extra": {"HTTP_X_REAL_IP": "127.0.0.1"}}):
            with self.subTest(args=args):
                self.assertEqual(self.invoke(**args)["status"], 403)

    def test_rejects_chunked_request(self):
        r = self.invoke("POST", "/v1/investigations", payload=example_request(),
                        extra={"HTTP_TRANSFER_ENCODING": "chunked"})
        self.assertEqual(r["status"], 400)

    def test_server_unavailable_does_not_reveal_internal_detail(self):
        self.db.execute("UPDATE source_snapshots SET dataset_id='real-feed' WHERE snapshot_id='sale-snap'")
        r = self.invoke("POST", "/v1/investigations", payload=example_request())
        self.assertEqual(r["status"], 503)
        self.assertEqual(r["body"], {"error": "evidence_unavailable"})
        self.assertNotIn("real-feed", str(r))

    def test_tampered_saved_evidence_fails_closed(self):
        created = self.invoke("POST", "/v1/investigations", payload=example_request())
        self.db.execute("UPDATE investigation_results SET response_json='{}'")
        r = self.invoke(path=created["headers"]["Location"])
        self.assertEqual(r["status"], 503)
        self.assertEqual(r["body"], {"error": "evidence_unavailable"})

    def test_loopback_real_http_post_then_get(self):
        # A real HTTP request is sent over OS loopback, but SQLite stays on
        # the creating thread, and no external network services are contacted.
        server = make_server("127.0.0.1", 0, self.app)
        server.timeout = 5
        port = server.server_port
        results = []

        def client():
            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                body = json.dumps(example_request()).encode()
                conn.request("POST", "/v1/investigations", body=body,
                             headers={"Content-Type": "application/json"})
                res = conn.getresponse()
                created = json.loads(res.read())
                results.append((res.status, res.getheader("Location"), created))
                conn.request("GET", results[0][1])
                res = conn.getresponse()
                results.append((res.status, json.loads(res.read())))
                conn.close()
            except Exception as exc:
                results.append(exc)

        try:
            thread = threading.Thread(target=client, daemon=True)
            thread.start()
            server.handle_request()
            server.handle_request()
            thread.join(timeout=5)
            self.assertEqual(len(results), 2, results)
            self.assertEqual(results[0][0], 201)
            self.assertEqual(results[0][2]["selected_count"], 3)
            self.assertEqual(results[1][0], 200)
            self.assertEqual(results[1][1], results[0][2])
        finally:
            server.server_close()


if __name__ == "__main__":
    unittest.main()
