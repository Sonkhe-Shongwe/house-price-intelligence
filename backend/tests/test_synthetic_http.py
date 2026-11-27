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
from backend.synthetic_http import MAX_BODY_BYTES, SA_INVESTIGATION_PATH, SA_SAVED_PATH, create_app
from backend import sa_investigation_v2 as sa
from unittest.mock import patch

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

    def sa_request(self):
        return {"contract_version": sa.VERSION, "market": "ZA", "currency": "ZAR",
                "area_unit": "m2", "subject_key": sa.wire_key("fictional-erf-000001"),
                "analysis_date": "2025-07-01", "mode": "as_of", "asking_price": "2500000.01"}

    def enable_sa(self):
        self.db.close()
        self.db, store = in_memory_demo()
        self.app = create_app(store, today=TODAY, sa_fixture=True)

    def test_sa_saved_opt_in_idempotence_and_frozen_reopen(self):
        self.enable_sa()
        self.assertEqual(self.invoke(path=SA_SAVED_PATH)["status"],404)
        self.db.close()
        self.db, store = in_memory_demo()
        self.app = create_app(store,today=TODAY,sa_fixture=True,sa_saved_fixture=True)
        req=self.sa_request()
        retry="12345678-1234-4123-8123-123456789abc"
        envelope={"retry_id":retry,"request":req}
        self.assertEqual(self.invoke(path=SA_SAVED_PATH)["body"]["investigations"],[])
        first=self.invoke("POST",SA_SAVED_PATH,payload=envelope)
        self.assertEqual(first["status"],200)
        self.assertEqual(first["body"]["investigation_id"],retry)
        self.assertEqual(first["body"]["request"],req)
        self.assertEqual(first["body"]["evidence"],sa.investigate(req,today=TODAY))
        with patch.object(sa,"investigate",side_effect=RuntimeError("no recomputation")):
            self.assertEqual(self.invoke("POST",SA_SAVED_PATH,payload=envelope)["body"],first["body"])
            self.assertEqual(self.invoke(path=SA_SAVED_PATH+"/"+retry)["body"],first["body"])
        self.assertEqual(len(self.invoke(path=SA_SAVED_PATH)["body"]["investigations"]),1)
        self.assertEqual(self.invoke("POST",SA_SAVED_PATH,payload=envelope|{"request":req|{"asking_price":"1"}})["status"],409)
        self.assertEqual(self.invoke("POST",SA_SAVED_PATH,payload=envelope|{"owner_key":"fictional-bob"})["status"],422)
        self.assertEqual(self.invoke("POST",SA_SAVED_PATH,payload=envelope|{"evidence":first["body"]["evidence"]})["status"],422)
        self.assertEqual(self.invoke("POST",SA_SAVED_PATH,payload=envelope,origin="https://evil.invalid")["status"],403)
        self.assertEqual(self.invoke(path=SA_SAVED_PATH,query="owner=fictional-bob")["status"],400)
        self.assertEqual(self.invoke(path="/v1/investigations/history")["body"]["investigations"],[])
        self.assertEqual(self.invoke(path="/v1/investigations/"+retry)["status"],404)
        self.db.execute("UPDATE sa_fixture_investigations SET asking_cents=1")
        self.db.commit()
        self.assertEqual(self.invoke(path=SA_SAVED_PATH+"/"+retry)["status"],404)
        self.assertEqual(self.invoke(path=SA_SAVED_PATH)["status"],503)

    def test_sa_shortlist_frozen_distinct_and_isolated(self):
        import uuid
        path = "/v2/fictional/za/shortlist"
        self.assertEqual(self.invoke(path=path)["status"],404)
        self.enable_sa()
        self.assertEqual(self.invoke(path=path)["status"],404)
        self.db.close()
        self.db, store = in_memory_demo()
        self.app = create_app(store,today=TODAY,sa_fixture=True,sa_saved_fixture=True)
        def save(token, price):
            iid = str(uuid.uuid4())
            req = self.sa_request() | {"subject_key": sa.wire_key(token), "asking_price": price}
            result = self.invoke("POST",SA_SAVED_PATH,payload={"retry_id":iid,"request":req})
            self.assertEqual(result["status"],200)
            return result["body"]
        a,b,c,d,duplicate = [save(token,price) for token,price in [
            ("fictional-erf-000001","2500000.01"),("fictional-erf-000010","1.02"),
            ("fictional-erf-000015",None),("fictional-erf-000002","3.04"),
            ("fictional-erf-000001","4.05")]]
        def command(row, action="add", **extra):
            return self.invoke("POST",path,payload={"action":action,"investigation_id":row["investigation_id"]},**extra)
        self.assertFalse(self.invoke(path=path)["body"]["comparison_ready"])
        with patch.object(sa,"investigate",side_effect=RuntimeError("no recomputation")):
            self.assertEqual(command(a)["body"]["investigations"],[a])
            self.assertEqual(command(a)["body"]["investigations"],[a])
            self.assertEqual(command(duplicate)["status"],409)
            self.assertTrue(command(b)["body"]["comparison_ready"])
            self.assertEqual(command(c)["body"]["investigations"],[a,b,c])
            self.assertEqual(command(d)["status"],409)
            self.assertEqual(self.invoke(path=path)["body"]["investigations"],[a,b,c])
            self.assertEqual(command(b,"remove")["body"]["investigations"],[a,c])
            self.assertEqual(command(b,"remove")["body"]["investigations"],[a,c])
            self.assertEqual(command(d)["body"]["investigations"],[a,c,d])
        self.assertEqual(command(b,origin="https://evil.invalid")["status"],403)
        self.assertEqual(self.invoke("POST",path,payload={"action":"add","investigation_id":a["investigation_id"],"owner":"fictional-bob"})["status"],422)
        self.assertEqual(self.invoke(path="/v1/investigations/history")["body"]["investigations"],[])
        self.assertEqual(self.invoke(path="/v1/shortlists")["body"]["shortlists"],[])
        def note(row, value, **extra):
            return self.invoke("POST",path,payload={"action":"note","investigation_id":row["investigation_id"],"note_text":value},**extra)
        aid,cid,did = (row["investigation_id"] for row in (a,c,d))
        self.assertEqual(self.invoke(path=path)["body"]["notes"],{aid:"",cid:"",did:""})
        original = self.db.total_changes
        with patch.object(sa,"investigate",side_effect=RuntimeError("no recomputation")):
            self.assertEqual(note(a,"Fictional <b>question</b>\nCheck extent")["status"],200)
            self.assertEqual(note(c,"x"*800)["status"],200)
            self.assertEqual(note(a,"Fictional <b>question</b>\nCheck extent")["status"],200)
            self.assertEqual(command(a)["body"]["notes"][aid],"Fictional <b>question</b>\nCheck extent")
            self.assertEqual(note(d,"\U0001f3e0"*800)["status"],200)
            for bad in ("x"*801, "bad\x00", "bad\x7f", "bad\ud800", 42, None):
                self.assertEqual(note(a,bad)["status"],422)
            self.assertEqual(note(b,"not a member")["status"],409)
            self.assertEqual(note(a,"forbidden",origin="https://evil.invalid")["status"],403)
            self.assertEqual(self.invoke("POST",path,payload={"action":"note","investigation_id":aid,"note_text":"x","owner":"fictional-bob"})["status"],422)
            self.assertEqual(self.invoke(path=path)["body"]["investigations"],[a,c,d])
            self.assertEqual(note(c,"")["body"]["notes"][cid],"")
            self.assertEqual(command(d,"remove")["body"]["notes"],{aid:"Fictional <b>question</b>\nCheck extent",cid:""})
            self.assertEqual(command(d)["body"]["notes"][did],"")
        self.assertEqual(self.db.total_changes,original)
        self.assertEqual(self.invoke(path=SA_SAVED_PATH+"/"+aid)["body"],a)
        self.db.execute("UPDATE sa_fixture_investigations SET asking_cents=1 WHERE investigation_id=?",(a["investigation_id"],))
        self.db.commit()
        self.assertEqual(self.invoke(path=path)["status"],503)
        self.assertEqual(command(c,"remove")["status"],503)
        self.assertEqual(command(a,"remove")["body"]["investigations"],[c,d])

    def test_sa_default_disabled_and_opt_in_no_writes(self):
        self.assertEqual(self.invoke("POST", SA_INVESTIGATION_PATH, payload=self.sa_request())["status"], 404)
        self.enable_sa()
        before = self.db.total_changes
        q = self.invoke("POST", SA_INVESTIGATION_PATH, payload=self.sa_request(),
                        origin="http://127.0.0.1:8765")
        self.assertEqual(q["status"], 200)
        self.assertEqual(q["body"], sa.investigate(self.sa_request(), today=TODAY))
        self.assertEqual(q["body"]["selected_count"], 5)
        self.assertEqual(q["body"]["subject"]["asking_price"]["minor_units"], 250000001)
        self.assertFalse(q["body"]["real_data_approved"])
        self.assertIsNone(q["body"]["valuation"])
        self.assertNotIn("Location", q["headers"])
        self.assertEqual(q["headers"]["Cache-Control"], "no-store")
        self.assertEqual(q["headers"]["X-Synthetic-Only"], "true")
        self.assertNotIn("Access-Control-Allow-Origin", q["headers"])
        self.assertEqual(self.invoke("POST", SA_INVESTIGATION_PATH, payload=self.sa_request())["body"], q["body"])
        self.assertEqual(self.db.total_changes, before)
        self.assertEqual(self.invoke(path="/v1/investigations/history")["body"]["investigations"], [])
        us = self.invoke("POST", "/v1/investigations", payload=example_request())
        self.assertEqual(us["status"], 201)
        self.assertEqual(us["body"]["selected_count"], 3)
        self.assertEqual(self.invoke(path=us["headers"]["Location"])["body"], us["body"])
        self.assertEqual(len(self.invoke(path="/v1/investigations/history")["body"]["investigations"]), 1)

    def test_sa_abstention_and_strict_contract_errors(self):
        self.enable_sa()
        req = self.sa_request()
        before = self.db.total_changes
        q = self.invoke("POST", SA_INVESTIGATION_PATH,
                        payload=req | {"subject_key": sa.wire_key("fictional-erf-000010")})
        self.assertEqual(q["status"], 200)
        self.assertEqual(q["body"]["status"], "insufficient_data")
        self.assertEqual(q["body"]["comparables"], [])
        for update in ({"currency": "USD"}, {"market": "US"}, {"area_unit": "sqft"},
                       {"data_build": "real"}, {"asking_price": 1.01}, {"coordinates": [0,0]},
                       {"subject_key": {"namespace":"sg26","value":"actual"}},
                       {"mode":"production"}, {"real_data_approved": True}):
            with self.subTest(update=update):
                q = self.invoke("POST", SA_INVESTIGATION_PATH, payload=req | update)
                self.assertEqual(q["status"], 422)
                self.assertEqual(q["body"], {"error": "invalid_sa_fixture_request"})
        with patch.object(sa, "investigate", side_effect=RuntimeError("private-path")):
            q = self.invoke("POST", SA_INVESTIGATION_PATH, payload=req)
        self.assertEqual(q["status"], 500)
        self.assertEqual(q["body"], {"error": "internal_error"})
        self.assertEqual(self.db.total_changes, before)

    def test_sa_reuses_http_boundary(self):
        self.enable_sa()
        req = self.sa_request()
        for args in ({"remote":"10.0.0.1"}, {"host":"evil.invalid"},
                     {"origin":"https://evil.invalid"}, {"extra":{"HTTP_X_FORWARDED_FOR":"127.0.0.1"}},
                     {"extra":{"HTTP_SEC_FETCH_SITE":"cross-site"}}):
            self.assertEqual(self.invoke("POST",SA_INVESTIGATION_PATH,payload=req,**args)["status"],403)
        for args, status in (
                ({"query":"build=real"},400), ({"content_type":"text/plain"},415),
                ({"extra":{"CONTENT_LENGTH":""}},411), ({"declared_length":MAX_BODY_BYTES+1},413),
                ({"declared_length":1000},400), ({"extra":{"HTTP_TRANSFER_ENCODING":"chunked"}},400)):
            with self.subTest(args=args):
                self.assertEqual(self.invoke("POST",SA_INVESTIGATION_PATH,payload=req,**args)["status"],status)
        for raw in (b'{"market":"ZA","market":"US"}', b'{', b'{"x":NaN}', b'{"x":"\\ud800"}', b'\xff'):
            self.assertEqual(self.invoke("POST",SA_INVESTIGATION_PATH,raw=raw)["status"],400)
        self.assertEqual(self.invoke(path=SA_INVESTIGATION_PATH)["headers"]["Allow"],"POST")
        self.assertEqual(self.invoke("OPTIONS",SA_INVESTIGATION_PATH)["status"],405)
        self.assertEqual(self.invoke(path=SA_INVESTIGATION_PATH+"/saved")["status"],404)

    def test_sa_real_loopback_http(self):
        self.enable_sa()
        server = make_server("127.0.0.1", 0, self.app)
        server.timeout = 5
        results = []
        def client():
            try:
                conn = http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=5)
                conn.request("POST",SA_INVESTIGATION_PATH,body=json.dumps(self.sa_request()),
                             headers={"Content-Type":"application/json"})
                res = conn.getresponse()
                results.append((res.status,json.loads(res.read())))
                conn.close()
            except Exception as exc:
                results.append(exc)
        try:
            thread = threading.Thread(target=client,daemon=True)
            thread.start()
            server.handle_request()
            thread.join(timeout=5)
            self.assertEqual(results,[(200,sa.investigate(self.sa_request(),today=TODAY))])
        finally:
            server.server_close()

    def test_history_is_bounded_read_only_and_preserves_weak_evidence(self):
        path="/v1/investigations/history"
        self.assertEqual(self.invoke(path=path)["body"]["investigations"], [])
        ids=[]
        for index in range(31):
            payload=example_request()
            payload["subject"]["label"]=f"Fictional enquiry {index}"
            if index == 30:
                payload["subject"]["pin"]="99999999999999"
            result=self.invoke("POST","/v1/investigations",payload=payload)
            self.assertEqual(result["status"],201)
            ids.append(result["body"]["investigation_id"])
        changes=self.db.total_changes
        history=self.invoke(path=path)
        self.assertEqual(history["status"],200)
        body=history["body"]
        self.assertEqual(body["contract_version"],"synthetic-history-v1")
        self.assertTrue(body["truncated"])
        self.assertEqual(len(body["investigations"]),30)
        self.assertEqual(len({i["investigation_id"] for i in body["investigations"]}),30)
        for item in body["investigations"]:
            original=self.invoke(path="/v1/investigations/"+item["investigation_id"])["body"]
            self.assertEqual(item["selected_count"],original["selected_count"])
            self.assertEqual(item["status"],original["status"])
            self.assertEqual(item["asking_price_usd"],original["subject"]["asking_price_usd"])
            self.assertNotIn("comparables",item)
        self.assertEqual(self.db.total_changes,changes)
        self.assertEqual(self.invoke("POST",path,payload={})["status"],405)
        self.assertEqual(self.invoke(path=path,query="limit=1000")["status"],400)
        self.assertEqual(self.invoke(path=path,origin="http://evil.invalid")["status"],403)

    def test_history_rejects_corrupt_frozen_result(self):
        result=self.invoke("POST","/v1/investigations",payload=example_request())
        iid=result["body"]["investigation_id"]
        self.db.execute("UPDATE investigation_results SET result_sha256=? WHERE investigation_id=?",
                        ("f"*64,iid))
        response=self.invoke(path="/v1/investigations/history")
        self.assertEqual(response["status"],503)
        self.assertEqual(response["body"],{"error":"evidence_unavailable"})

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

    def test_shared_street_label_requires_distinct_selected_candidate(self):
        found = self.invoke("POST", "/v1/addresses/search",
                            payload={"query": "105 Fictional Court"})
        self.assertEqual(found["status"], 200)
        options = found["body"]["candidates"]
        self.assertEqual(len(options), 2)
        self.assertEqual({x["display_address"] for x in options},
                         {"105 Fictional Court, Demonstration District"})
        self.assertTrue(all(x["ambiguous_address"] and x["parcel_hint"] for x in options))
        self.assertTrue(all("pin" not in x for x in options))
        selected_pins = set()
        for option in options:
            selected = self.invoke(path="/v1/addresses/" + option["address_id"])
            self.assertEqual(selected["status"], 200)
            self.assertEqual(selected["body"]["identity_scope"], "parcel_only")
            self.assertIs(selected["body"]["building_identity_verified"], False)
            selected_pins.add(selected["body"]["pin"])
            req = example_request()
            req["subject"].update(pin=None, address_id=option["address_id"])
            created = self.invoke("POST", "/v1/investigations", payload=req)
            self.assertEqual(created["status"], 201)
            self.assertEqual(created["body"]["subject"]["pin"], selected["body"]["pin"])
            self.assertEqual(created["body"]["subject"]["identity_scope"], "parcel_only")
            self.assertEqual(self.invoke(path=created["headers"]["Location"])["body"],
                             created["body"])
        self.assertEqual(len(selected_pins), 2)

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

    def test_shortlist_http_two_properties_notes_and_frozen_evidence(self):
        first = self.invoke("POST", "/v1/investigations", payload=example_request())["body"]
        unknown_request = example_request()
        unknown_request["subject"]["pin"] = "00000000000099"
        unknown_request["subject"]["label"] = "Unknown fictional house"
        second = self.invoke("POST", "/v1/investigations", payload=unknown_request)["body"]
        created = self.invoke("POST", "/v1/shortlists", payload={"label": "My fictional shortlist"})
        self.assertEqual(created["status"], 201)
        sid = created["body"]["shortlist_id"]
        path = "/v1/shortlists/" + sid
        self.assertEqual(created["headers"]["Location"], path)
        self.assertEqual(self.invoke(path=path)["body"], created["body"])
        listed = self.invoke(path="/v1/shortlists")
        self.assertEqual(listed["status"], 200)
        self.assertEqual(listed["body"]["shortlists"][0]["entry_count"], 0)

        for result in (first, second):
            added = self.invoke(
                "POST", path + "/entries",
                payload={"investigation_id": result["investigation_id"]})
            self.assertEqual(added["status"], 201)
        self.assertEqual(added["body"]["entries"][0]["investigation"], first)
        self.assertEqual(added["body"]["entries"][1]["investigation"], second)
        self.assertEqual([e["investigation"]["selected_count"] for e in added["body"]["entries"]],
                         [3, 0])
        self.assertIsNone(added["body"]["entries"][1]["investigation"]["valuation"])
        self.assertEqual(self.invoke(path=path)["body"], added["body"])

        before = self.db.execute(
            "SELECT response_json, result_sha256 FROM investigation_results WHERE investigation_id=?",
            (first["investigation_id"],),
        ).fetchone()
        edit_path = path + "/entries/" + first["investigation_id"]
        updated = self.invoke("PATCH", edit_path, payload={"note_text": "Inspect the roof"})
        self.assertEqual(updated["status"], 200)
        self.assertEqual(updated["body"]["entries"][0]["note_text"], "Inspect the roof")
        self.assertEqual(self.db.execute(
            "SELECT response_json, result_sha256 FROM investigation_results WHERE investigation_id=?",
            (first["investigation_id"],),
        ).fetchone(), before)
        removed = self.invoke("DELETE", edit_path)
        self.assertEqual(removed["status"], 200)
        self.assertEqual(len(removed["body"]["entries"]), 1)
        self.assertEqual(self.invoke(path="/v1/investigations/" + first["investigation_id"])["body"], first)

    def test_shortlist_http_rejects_bad_methods_unknown_ids_and_invalid_note(self):
        sid = self.invoke("POST", "/v1/shortlists", payload={"label": "My shortlist"})["body"]["shortlist_id"]
        path = "/v1/shortlists/" + sid
        self.assertEqual(self.invoke("PUT", path)["status"], 405)
        self.assertEqual(self.invoke("OPTIONS", "/v1/shortlists")["status"], 405)
        self.assertEqual(self.invoke("POST", path + "/entries", payload={"note_text": "no ID"})["status"], 422)
        self.assertEqual(self.invoke("POST", "/v1/shortlists", payload={"label": "A", "extra": 1})["status"], 422)
        self.assertEqual(self.invoke("PATCH", path + "/entries/" + "0" * 36,
                                     payload={"note_text": "hi"})["status"], 404)
        self.assertEqual(self.invoke(path="/v1/shortlists/00000000-0000-4000-8000-000000000000")["status"], 404)
        self.assertEqual(self.invoke("POST", "/v1/shortlists", raw=b'{"label":"a","label":"b"}')["status"], 400)
        self.assertEqual(self.invoke("POST", "/v1/shortlists",
                                     payload={"label": "x"}, origin="https://hostile.example")["status"], 403)

    def test_shortlist_http_duplicate_property_limit_and_invalid_note(self):
        sid = self.invoke("POST", "/v1/shortlists", payload={"label": "Three homes"})["body"]["shortlist_id"]
        path = "/v1/shortlists/" + sid
        ids = []
        for number in (1, 2, 3, 4):
            request = example_request()
            request["subject"]["pin"] = f"{number:014d}"
            created = self.invoke("POST", "/v1/investigations", payload=request)
            self.assertEqual(created["status"], 201)
            ids.append(created["body"]["investigation_id"])
        for iid in ids[:3]:
            self.assertEqual(self.invoke("POST", path + "/entries",
                                         payload={"investigation_id": iid})["status"], 201)
        self.assertEqual(self.invoke("POST", path + "/entries",
                                     payload={"investigation_id": ids[3]})["status"], 409)
        self.assertEqual(self.invoke("PATCH", path + "/entries/" + ids[0],
                                     payload={"note_text": "X" * 801})["status"], 422)
        self.assertEqual(self.invoke(path=path)["body"]["entries"][0]["note_text"], "")

    def test_shortlist_http_tampered_comparable_fails_closed(self):
        sid = self.invoke("POST", "/v1/shortlists", payload={"label": "Protected"})["body"]["shortlist_id"]
        saved = self.invoke("POST", "/v1/investigations", payload=example_request())["body"]
        path = "/v1/shortlists/" + sid
        self.assertEqual(self.invoke("POST", path + "/entries",
                                     payload={"investigation_id": saved["investigation_id"]})["status"], 201)
        self.db.execute("UPDATE comparable_evidence SET sale_price_usd_cents=sale_price_usd_cents+1")
        self.db.commit()
        result = self.invoke(path=path)
        self.assertEqual(result["status"], 503)
        self.assertEqual(result["body"], {"error": "evidence_unavailable"})
        self.assertEqual(self.invoke("DELETE", path + "/entries/" + saved["investigation_id"])["status"], 503)

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
