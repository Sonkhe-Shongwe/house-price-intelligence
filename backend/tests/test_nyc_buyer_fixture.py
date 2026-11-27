"""Invented-only exact subject entry and minimal buyer evidence tests."""
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
import unittest

from backend.nyc_buyer_fixture import FixtureAddress, FixtureSnapshot, investigate_fixture
from tools.nyc_qualification import FIELDS, Legal, Master, QualificationError, Sale, bbl


class NYCBuyerFixtureTests(unittest.TestCase):
    def setUp(self):
        cutoff = date(2026, 11, 27)
        publication = date(2026, 11, 23)
        self.plan = FixtureSnapshot(cutoff, date(2025, 11, 1), date(2026, 10, 31),
            publication, "fixture-nyc-one", tuple((d, "fixture-one") for d in FIELDS),
            frame_complete=True, source_complete=True, source_versions_stable=True,
            available=True)
        self.addresses = [FixtureAddress(bbl(4, 1, 1), "101 Fictional Avenue", "QN",
            11361, "A2", 1, 1, 1, 1000, "2", self.plan.version),
            FixtureAddress(bbl(4, 1, 2), "102 Fictional Avenue", "QN",
            11361, "A2", 1, 1, 1, 2000, "2", self.plan.version)]
        # Labels are explicitly invented and start with FICTIONAL to prevent
        # inadvertent use of real address-shaped source values.
        self.addresses = [replace(row, address="Fictional " + row.address) for row in self.addresses]
        self.sales = [Sale(bbl(4, 2, i), cutoff-timedelta(days=30+i), 12345601+i,
            area, True, False, area, publication, self.plan.version, "2")
            for i, area in enumerate((1000, 1100, 1250, 1251, 750, 900, 850), 1)]
        self.masters = [Master(f"INVENTED{i}", "DEED", s.day, s.day, s.cents, Decimal("100"))
                        for i, s in enumerate(self.sales)]
        self.legals = [Legal(m.doc, s.key, True, True, True)
                       for m, s in zip(self.masters, self.sales)]

    def run_fixture(self, **kwargs):
        args = dict(address=" fictional 101 fictional avenue ", asking_cents=99999999,
            plan=self.plan, addresses=self.addresses, sales=self.sales,
            masters=self.masters, legals=self.legals)
        args.update(kwargs)
        return investigate_fixture(**args)

    def test_supported_without_subject_sale_and_minimal_projection(self):
        result = self.run_fixture()
        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["selected_count"], 5)
        self.assertEqual(result["asking_price_usd"], "999999.99")
        self.assertEqual([x["snapshot_gross_area_sqft"] for x in result["comparables"]],
                         [1000, 1100, 900, 850, 1250])
        self.assertEqual(result["comparables"][0]["sale_price_usd"], "123456.02")
        self.assertFalse(result["provenance"]["lookback_fully_covered"])
        self.assertFalse(result["provenance"]["public_display_approved"])
        self.assertIsNone(result["valuation"])
        for value in [r.key for r in self.addresses] + [s.key for s in self.sales] + [m.doc for m in self.masters]:
            self.assertNotIn(value, str(result))
        self.assertNotIn(self.addresses[1].address, str(result))

    def test_no_fuzzy_or_ambiguous_entry(self):
        self.assertEqual(self.run_fixture(address="Fictional 101 Fictional Ave")["status"], "out_of_coverage")
        for duplicate in (replace(self.addresses[0], key=bbl(4, 3, 1), building_class="A1"),
                          replace(self.addresses[0], address="Fictional Other Avenue")):
            r = self.run_fixture(addresses=self.addresses+[duplicate])
            self.assertEqual(r["status"], "ambiguous_address")
            self.assertIsNone(r["subject"])
            self.assertEqual(r["comparables"], [])

    def test_wrong_class_units_method_release_and_zip_abstain(self):
        for changes in (dict(building_class="A1"), dict(residential_units=2), dict(buildings=True),
                        dict(zipcode=11362), dict(area_source="7"), dict(version="other"),
                        dict(area=0)):
            r = self.run_fixture(addresses=[replace(self.addresses[0], **changes), self.addresses[1]])
            self.assertEqual(r["status"], "out_of_coverage")
            self.assertEqual(r["comparables"], [])

    def test_insufficient_and_wrong_or_partial_deeds(self):
        r = self.run_fixture(address=self.addresses[1].address)
        self.assertEqual(r["status"], "insufficient_data")
        self.assertEqual(r["selected_count"], 0)
        self.assertEqual(r["comparables"], [])
        r = self.run_fixture(legals=[replace(l, whole=False) for l in self.legals[:-2]]+self.legals[-2:])
        self.assertEqual(r["status"], "insufficient_data")
        self.assertEqual(r["comparables"], [])

    def test_unavailable_or_incomplete_snapshot_suppresses_all_source_fields(self):
        for field in ("available", "frame_complete", "source_complete", "source_versions_stable"):
            r = self.run_fixture(plan=replace(self.plan, **{field:False}))
            self.assertEqual(r["status"], "evidence_unavailable")
            self.assertIsNone(r["subject"])
            self.assertEqual(r["comparables"], [])

    def test_prices_do_not_affect_selection_and_same_lot_excluded(self):
        r = self.run_fixture()
        changed = [replace(s, cents=s.cents*11) for s in self.sales]
        masters = [replace(m, cents=s.cents) for m,s in zip(self.masters,changed)]
        other = self.run_fixture(sales=changed, masters=masters)
        self.assertEqual([c["snapshot_gross_area_sqft"] for c in r["comparables"]],
                         [c["snapshot_gross_area_sqft"] for c in other["comparables"]])
        same = replace(self.sales[0], key=self.addresses[0].key)
        r = self.run_fixture(sales=[same]+self.sales[1:],
            legals=[replace(self.legals[0], key=same.key)]+self.legals[1:])
        self.assertNotIn(1000, [c["snapshot_gross_area_sqft"] for c in r["comparables"]])

    def test_rejects_nonfixture_and_bad_inputs(self):
        for kwargs in (dict(plan=replace(self.plan, source_kind="real")),
                       dict(plan=replace(self.plan, version="26v3")),
                       dict(plan=replace(self.plan, revisions=())),
                       dict(asking_cents=True), dict(address="\n"),
                       dict(addresses=[replace(self.addresses[0], address="not an invented label")])):
            with self.assertRaises(QualificationError):
                self.run_fixture(**kwargs)


if __name__ == "__main__":
    unittest.main()
