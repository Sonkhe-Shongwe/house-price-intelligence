import unittest
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from tools.nyc_qualification import (
    Budget, QualificationError, Subject, Sale, Master, Legal, bbl, batches,
    complete_rows, projection, validate_projection, qualify, MAX_BYTES,
    MAX_REQUESTS, subject_query, sales_query, master_query, legal_query,
    comparable_attribute_query, verify_metadata,
)


class NYCQualificationTests(unittest.TestCase):
    def setUp(self):
        self.cutoff = date(2026, 11, 1)
        self.day = self.cutoff - timedelta(days=60)
        self.subjects = [Subject(bbl(4, 1, i), 1000, self.cutoff, "fixture", True, True)
                         for i in range(1, 31)]
        self.sales = [Sale(bbl(4, 2, i), self.day, 12345678, 1000, True, True)
                      for i in range(1, 5)]
        self.masters = [Master(f"fictional{i}", "DEED", self.day, self.day,
                               s.cents, Decimal("100"))
                        for i, s in enumerate(self.sales)]
        self.legals = [Legal(m.doc, s.key, True, True, True)
                       for m, s in zip(self.masters, self.sales)]

    def q(self, **kwargs):
        args = dict(subjects=self.subjects, sales=self.sales, masters=self.masters,
                    legals=self.legals, cutoff=self.cutoff,
                    covered_from=self.cutoff-timedelta(days=365),
                    covered_through=self.cutoff-timedelta(days=1),
                    frame_complete=True, source_complete=True,
                    source_versions_stable=True)
        args.update(kwargs)
        return qualify(**args)

    def test_aggregate_success_and_nonclaims(self):
        r = self.q()
        self.assertEqual(r["subject_statuses"], {"supported": 30})
        self.assertEqual(r["qualified_sales"], 4)
        self.assertTrue(r["engineering_floor_met"])
        self.assertFalse(r["historical_asof_verified"])
        self.assertFalse(r["market_approved"])
        self.assertNotIn(self.sales[0].key, str(r))
        self.assertNotIn(self.masters[0].doc, str(r))

    def test_ambiguity_and_multilot(self):
        r = self.q(legals=self.legals + [
            replace(self.legals[0], key=bbl(1, 3, 1)),
            self.legals[1],
        ])
        self.assertEqual(r["qualified_sales"], 2)
        self.assertEqual(r["subject_statuses"], {"insufficient": 30})
        self.assertFalse(r["engineering_floor_met"])

    def test_missing_dated_area_and_same_day(self):
        r = self.q(sales=[replace(self.sales[0], dated_area=False),
                         replace(self.sales[1], day=self.cutoff), *self.sales[2:]])
        self.assertEqual(r["sale_exclusions"],
                         {"dated_area_unqualified": 1, "outside_earlier_window": 1})
        self.assertFalse(r["engineering_floor_met"])

    def test_partial_and_non_deed(self):
        r = self.q(legals=[replace(self.legals[0], whole=False), *self.legals[1:]],
                   masters=[self.masters[0], replace(self.masters[1], kind="MTGE"),
                            *self.masters[2:]])
        self.assertEqual(r["qualified_sales"], 2)

    def test_document_amount_and_percentage(self):
        r = self.q(masters=[replace(self.masters[0], cents=1),
                            replace(self.masters[1], percent=Decimal("50")),
                            *self.masters[2:]])
        self.assertEqual(r["qualified_sales"], 2)

    def test_duplicate_sale_and_ambiguous_document(self):
        r = self.q(sales=self.sales+[self.sales[0]],
                   masters=self.masters+[replace(self.masters[1], doc="otherdoc")],
                   legals=self.legals+[replace(self.legals[1], doc="otherdoc")])
        self.assertEqual(r["sale_exclusions"]["duplicate_sale"], 2)
        self.assertEqual(r["sale_exclusions"]["missing_or_ambiguous_deed"], 1)

    def test_subject_denominator_and_area(self):
        r = self.q(subjects=[replace(self.subjects[0], unique_address=False),
                             replace(self.subjects[1], area=2000), *self.subjects[2:]])
        self.assertEqual(r["subject_statuses"],
                         {"unresolved_subject": 1, "insufficient": 1, "supported": 28})

    def test_missing_completeness_or_drift(self):
        for flag in ("frame_complete", "source_complete", "source_versions_stable"):
            with self.assertRaisesRegex(QualificationError, "incomplete_source_evidence"):
                self.q(**{flag: False})
        with self.assertRaisesRegex(QualificationError, "subject_frame_identity"):
            self.q(subjects=self.subjects[::-1])

    def test_coverage_limit_not_claimed(self):
        r = self.q(covered_from=self.cutoff-timedelta(days=90))
        self.assertFalse(r["lookback_fully_covered"])

    def test_bounds_and_minimisation(self):
        self.assertEqual(bbl(4, 1, 2), "4000010002")
        for bad in ("1.0", "1e0", True, 0):
            with self.assertRaises(QualificationError):
                bbl(4, bad, 1)
        self.assertEqual([len(x) for x in batches([bbl(4, 4, i) for i in range(1, 37)])], [35, 1])
        with self.assertRaises(QualificationError):
            batches([self.sales[0].key]*2)
        with self.assertRaises(QualificationError):
            complete_rows([1], 2, 500)
        with self.assertRaises(QualificationError):
            complete_rows([], 501, 500)
        self.assertNotIn("address", projection("64uk-42ks"))
        self.assertIn("address", projection("64uk-42ks", subject=True))
        with self.assertRaises(QualificationError):
            validate_projection("8h5j-fqxa", [{"street_name":"fictional"}])
        with self.assertRaises(QualificationError):
            projection("parties")

    def test_fixed_query_templates(self):
        q = subject_query()
        self.assertEqual(q.limit, 30)
        self.assertEqual(q.order, "bbl ASC")
        self.assertIn("zipcode = '11361'", q.where)
        self.assertIn("address", q.fields)
        self.assertEqual(q.parameters(count=True)["$select"], "count(*) as n")
        q = sales_query(self.cutoff-timedelta(days=400),
                        self.cutoff-timedelta(days=1), self.cutoff)
        self.assertIn("2025-11-01T00:00:00", q.where)
        self.assertIn("2026-11-01T00:00:00", q.where)
        self.assertIn("BAYSIDE", q.where)
        self.assertNotIn("address", q.fields)
        q = master_query(self.sales)
        self.assertIn("123456.78", q.where)
        self.assertNotIn("recorded_borough", q.where)
        q = legal_query([m.doc for m in self.masters])
        self.assertNotIn("borough", q.where)
        self.assertNotIn("street_name", q.fields)
        self.assertNotIn("address", comparable_attribute_query(
            [s.key for s in self.sales]).fields)
        with self.assertRaises(QualificationError):
            legal_query(["bad' OR 1=1"])
        with self.assertRaises(QualificationError):
            master_query([replace(self.sales[0], cents=True)])
        with self.assertRaises(QualificationError):
            comparable_attribute_query(["bad"])

    def test_metadata_stability(self):
        m = {"id":"64uk-42ks", "revision":"fictional-version",
             "fields":list(projection("64uk-42ks", subject=True))}
        verify_metadata("64uk-42ks", m, m, subject=True)
        with self.assertRaisesRegex(QualificationError, "source_revision_changed"):
            verify_metadata("64uk-42ks", m, dict(m, revision="different"), subject=True)
        with self.assertRaisesRegex(QualificationError, "source_schema_unverified"):
            verify_metadata("64uk-42ks", m, dict(m, fields=[]), subject=True)

    def test_budget(self):
        budget = Budget()
        self.assertEqual(budget.reserve(0), MAX_BYTES)
        budget.account(100, 500, "sales", 1)
        budget.reserve(1)
        with self.assertRaisesRegex(QualificationError, "sale_limit"):
            budget.account(1, 1, "sales", 1)
        with self.assertRaisesRegex(QualificationError, "byte_limit"):
            budget.account(MAX_BYTES, 0, "metadata", 1)
        with self.assertRaisesRegex(QualificationError, "time_limit"):
            budget.reserve(1800)
        budget = Budget()
        for _ in range(MAX_REQUESTS):
            budget.reserve(0)
        with self.assertRaisesRegex(QualificationError, "request_limit"):
            budget.reserve(0)


if __name__ == "__main__":
    unittest.main()
