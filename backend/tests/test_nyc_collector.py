"""Mocked source integration: no network, real addresses or records."""
from contextlib import contextmanager
from dataclasses import replace
from datetime import date, timedelta
import io
import json
import unittest
from urllib.parse import urlsplit, parse_qs

from tools.nyc_collector import Collector, FixturePlan
from tools.nyc_qualification import FIELDS, projection, bbl, QualificationError, CURRENT_SNAPSHOT


class Response:
    status = 200

    def __init__(self, value):
        self.raw = json.dumps(value).encode()
        self.body = io.BytesIO(self.raw)
        self.headers = {"Content-Type": "application/json",
                        "Content-Length": str(len(self.raw))}

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def read1(self, size):
        return self.body.read(size)


class SourceFixture:
    def __init__(self):
        self.calls = []
        self.change = None
        self.metadata_reads = {}
        self.subjects = [
            dict(bbl=bbl(4, 1, i), borough="QN", zipcode="11361", bldgclass="A2",
                 numbldgs="1", unitsres="1", unitstotal="1", bldgarea="1000",
                 version="fixture", areasource="2", address=f"INVENTED SUBJECT {i}") for i in range(1, 31)]
        self.sales = [
            dict(borough="4", block="2", lot=str(i), neighborhood="BAYSIDE",
                 zip_code="11361", building_class_at_time_of_sale="A2",
                 gross_square_feet="1000", residential_units="1", commercial_units="0",
                 total_units="1", sale_date="2026-09-01T00:00:00.000", sale_price="123456")
            for i in range(1, 5)]
        self.attrs = [dict(self.subjects[0], bbl=bbl(4, 2, i)) for i in range(1, 5)]
        for a in self.attrs:
            del a["address"]
        self.masters = [
            dict(document_id=f"fictional{i}", doc_type="DEED",
                 document_date="2026-09-01T00:00:00", document_amt="123456",
                 recorded_datetime="2026-09-02T00:00:00", percent_trans="100")
            for i in range(1, 5)]
        self.legals = [
            dict(document_id=f"fictional{i}", borough="4", block="2", lot=str(i),
                 partial_lot="E", property_type="D1", easement="N", air_rights="N",
                 subterranean_rights="N") for i in range(1, 5)]

    @contextmanager
    def transport(self, path, timeout):
        self.calls.append(path)
        url = urlsplit(path)
        dataset = url.path.rsplit("/", 1)[1].removesuffix(".json")
        if url.path.startswith("/api/views/"):
            self.metadata_reads[dataset] = self.metadata_reads.get(dataset, 0)+1
            value = dict(id=dataset, rowsUpdatedAt=1, viewLastModified=1,
                         columns=[dict(fieldName=f, dataTypeName=(
                             "number" if f in ("bbl", "zipcode") else "text"))
                             for f in projection(dataset, subject=dataset == "64uk-42ks")])
            if self.change == "drift" and self.metadata_reads[dataset] > 1:
                value["rowsUpdatedAt"] = 2
        else:
            q = {k:v[0] for k,v in parse_qs(url.query).items()}
            if dataset == "64uk-42ks":
                rows = self.subjects if "borough = 'QN'" in q["$where"] else self.attrs
            elif dataset == "usep-8jbt":
                rows = self.sales
            elif dataset == "bnx9-e6tj":
                rows = self.masters
            else:
                rows = self.legals
            if q["$select"].startswith("count(distinct") or " as keys" in q["$select"]:
                value = [dict(n=str(len(rows)), keys=str(len(rows)),
                              addresses=str(len(rows) - (self.change == "ambiguous")))]
            elif q["$select"] == "count(*) as n":
                value = [{"n": str(501 if self.change == "overcount"
                                  and dataset == "usep-8jbt" else len(rows))}]
            else:
                value = rows[:int(q["$limit"])]
                if self.change == "short" and dataset == "usep-8jbt":
                    value = value[:-1]
                if self.change == "extra_field" and dataset == "usep-8jbt":
                    value = [dict(value[0], address="INVENTED LEAK"), *value[1:]]
        response = Response(value)
        if self.change == "oversize":
            response.headers["Content-Length"] = str(21*1024*1024)
        if self.change == "redirect":
            response.status = 302
        if self.change == "truncated":
            response.body = io.BytesIO(response.raw[:-1])
        yield response


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.src = SourceFixture()
        cutoff = date(2026, 11, 1)
        self.plan = FixturePlan(cutoff, cutoff-timedelta(days=365),
                                cutoff-timedelta(days=1), cutoff, "fixture", True)

    def run_collect(self):
        return Collector(self.src.transport).run_fixture(self.plan)

    def test_mock_pipeline_and_redaction(self):
        result = self.run_collect()
        self.assertEqual(result["subject_statuses"], {"supported": 30})
        self.assertEqual(result["qualified_sales"], 4)
        self.assertTrue(result["fixture_only"])
        self.assertNotIn("INVENTED SUBJECT", str(result))
        self.assertNotIn("fictional1", str(result))
        self.assertNotIn(self.src.subjects[0]["bbl"], str(result))
        self.assertEqual(result["requests"], len(self.src.calls))
        self.assertLess(next(i for i,p in enumerate(self.src.calls) if "resource/64uk" in p),
                        next(i for i,p in enumerate(self.src.calls) if "resource/usep" in p))

    def test_no_historical_area_no_deeds(self):
        self.plan = replace(self.plan, historical_area_verified=False)
        r = self.run_collect()
        self.assertEqual(r["sale_exclusions"], {"dated_area_unqualified": 4})
        self.assertFalse(r["engineering_floor_met"])
        self.assertFalse(any("/resource/bnx9" in p for p in self.src.calls))

    def test_snapshot_success_and_distinct_dates(self):
        self.plan = replace(self.plan, mode=CURRENT_SNAPSHOT, historical_area_verified=False)
        result = self.run_collect()
        self.assertEqual(result["qualified_sales"], 4)
        self.assertEqual(result["comparison_mode"], CURRENT_SNAPSHOT)
        self.assertEqual(result["snapshot_version"], "fixture")
        self.assertFalse(result["historical_asof_verified"])
        self.assertFalse(result["sale_time_area_verified"])
        self.assertEqual(result["sales_covered_through"], "2026-10-31")
        self.assertEqual(result["snapshot_date"], "2026-11-01")

    def test_snapshot_rejects_mixed_area_and_wrong_subject(self):
        self.plan = replace(self.plan, mode=CURRENT_SNAPSHOT, historical_area_verified=False)
        self.src.attrs[0]["areasource"] = "7"
        self.src.attrs[1]["bldgarea"] = "1100"
        r = self.run_collect()
        self.assertEqual(r["sale_exclusions"], {"snapshot_area_unqualified": 2})
        self.assertFalse(r["engineering_floor_met"])
        self.src = SourceFixture()
        self.src.subjects[0]["areasource"] = "5"
        with self.assertRaisesRegex(QualificationError, "subject_area_method_conflict"):
            self.run_collect()

    def test_snapshot_cannot_claim_historical_evidence(self):
        self.plan = replace(self.plan, mode=CURRENT_SNAPSHOT)
        with self.assertRaisesRegex(QualificationError, "mixed_temporal_evidence"):
            self.run_collect()
        self.assertEqual(self.src.calls, [])

    def test_failure_modes(self):
        for mode, reason in (("drift", "source_revision_changed"),
                             ("ambiguous", "ambiguous_subject_frame"),
                             ("overcount", "count_limit"), ("short", "incomplete_result"),
                             ("extra_field", "unexpected_source_field"),
                             ("oversize", "byte_limit"), ("redirect", "http_status"),
                             ("truncated", "incomplete_response")):
            with self.subTest(mode=mode):
                self.src = SourceFixture()
                self.src.change = mode
                with self.assertRaisesRegex(QualificationError, reason):
                    self.run_collect()

    def test_one_attempt(self):
        c = Collector(self.src.transport)
        c.run_fixture(self.plan)
        with self.assertRaisesRegex(QualificationError, "attempt_already_consumed"):
            c.run_fixture(self.plan)


if __name__ == "__main__":
    unittest.main()
