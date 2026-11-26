import hashlib
import json
import unittest
from dataclasses import replace
from unittest.mock import patch

from tools.acquisition_feasibility import FixtureAttempt, POLICIES, Refused


def page(*rows):
    return json.dumps([{"area_id": k, "count": v} for k, v in rows]).encode()


class AcquisitionFeasibilityTest(unittest.TestCase):
    def valid(self):
        return {"s1": page(("001", 3)), "s2": page(("002", 7))}

    def test_two_independent_formats_and_provenance(self):
        responses = self.valid()
        schools = FixtureAttempt("fictional-schools", responses).run()
        csv = b"area_id,count\n001,11\n003,4\n"
        services = FixtureAttempt("fictional-services", {"c1": csv}).run()
        self.assertEqual((schools["count_total"], services["count_total"]), (10, 15))
        self.assertEqual((schools["requests"], services["requests"]), (2, 1))
        self.assertEqual(schools["rows"][0]["area_id"], "001")
        self.assertEqual(services["rows"][0]["area_id"], "001")
        self.assertEqual(schools["sha256"], [hashlib.sha256(v).hexdigest() for v in responses.values()])
        self.assertEqual(services["sha256"], [hashlib.sha256(csv).hexdigest()])
        self.assertEqual(schools["bytes"], sum(map(len, responses.values())))
        self.assertEqual(schools, FixtureAttempt("fictional-schools", responses).run())

    def test_unknown_source_and_page_scope(self):
        with self.assertRaises(Refused):
            FixtureAttempt("not-approved", {})
        for responses in ({"s1": page(("001", 1))}, {**self.valid(), "s3": b"[]"}):
            run = FixtureAttempt("fictional-schools", responses)
            with self.assertRaises(Refused):
                run.run()
            self.assertEqual(run.requests, [])

    def test_malformed_and_unexpected_fields_stop_before_next_page(self):
        bad = [b"{", b'[{"area_id":"001","count":1,"count":2}]',
               b'[{"area_id":"001","count":1,"extra":"unexpected"}]',
               page(("001", True)), page(("001", -1)), page((1, 1)), b"\xff"]
        for raw in bad:
            with self.subTest(raw=raw):
                run = FixtureAttempt("fictional-schools", {"s1": raw, "s2": page(("002", 7))})
                with self.assertRaises(Refused):
                    run.run()
                self.assertEqual(run.requests, ["s1"])
                with self.assertRaisesRegex(Refused, "consumed"):
                    run.run()
                self.assertEqual(run.requests, ["s1"])

    def test_duplicate_cross_page(self):
        run = FixtureAttempt("fictional-schools", {"s1": page(("001", 3)), "s2": page(("001", 7))})
        with self.assertRaisesRegex(Refused, "duplicate identifier"):
            run.run()

    def test_csv_contract(self):
        for raw in (b"count,area_id\n3,001\n", b"area_id,count\n001,3,extra\n",
                    b"area_id,count\n001,3.0\n", b"area_id,count\n001,2\n001,3\n",
                    b"area_id,count\n"):
            with self.subTest(raw=raw), self.assertRaises(Refused):
                FixtureAttempt("fictional-services", {"c1": raw}).run()

    def test_byte_budget_total_and_single_response(self):
        for responses, dispatched in (({"s1": b"x" * 2049, "s2": b"[]"}, ["s1"]),
             ({"s1": page(("001", 3)) + b" " * 1100, "s2": page(("002", 7)) + b" " * 1100}, ["s1", "s2"])):
            run = FixtureAttempt("fictional-schools", responses)
            with self.assertRaisesRegex(Refused, "byte cap"):
                run.run()
            self.assertEqual(run.requests, dispatched)

    def test_request_and_row_caps(self):
        for field, value, reason in (("max_requests", 1, "request cap"), ("max_rows", 1, "row cap")):
            with patch.dict(POLICIES, {"fictional-schools": replace(POLICIES["fictional-schools"], **{field: value})}):
                run = FixtureAttempt("fictional-schools", self.valid())
                with self.assertRaisesRegex(Refused, reason):
                    run.run()
                self.assertEqual(len(run.requests), 1 if field == "max_requests" else 2)

    def test_success_cannot_replay(self):
        run = FixtureAttempt("fictional-schools", self.valid())
        run.run()
        with self.assertRaisesRegex(Refused, "consumed"):
            run.run()
        self.assertEqual(run.requests, ["s1", "s2"])


if __name__ == "__main__":
    unittest.main()
