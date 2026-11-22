"""Test bounded matching policies with explicitly invented sale records."""
from datetime import date, timedelta
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from matcher import MatchPolicy, match_property
from evaluate import evaluate


def rec(pin, days_ago, *, hood="A", lat=42.02, lon=-87.69, area=1500, price=500000,
        doc=None, cls="203", township="17", date_anchor=date(2024, 6, 1)):
    return {"pin": pin, "sale_date": (date_anchor - timedelta(days=days_ago)).isoformat(),
            "doc_no": doc or pin, "class": cls, "township_code": township,
            "sqft": area, "nbhd_code": hood, "lat": lat, "lon": lon, "sale_price": price,
            "characteristics_year": 2023}


class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.subject = rec("subject", 0, price=700000)
        self.local = [rec(str(i), days_ago=i * 8 + 10, area=1450 + i*15, price=450000+i*1000)
                      for i in range(1, 6)]

    def test_local_tier_first_even_if_other_homes_closer(self):
        others = [rec("near"+str(i), 10+i, hood="B", lat=42.02001) for i in range(5)]
        r = match_property(self.subject, self.local + others)
        self.assertEqual(r["tier"], "same_neighborhood")
        self.assertEqual(r["selected_count"], 5)
        self.assertTrue(all(c["same_neighborhood"] for c in r["comparables"]))

    def test_fallback_only_within_two_km_and_labelled(self):
        outside_hood = [rec("other"+str(i), i+3, hood="B", lat=42.02 + i*.0005) for i in range(3)]
        r = match_property(self.subject, outside_hood)
        self.assertEqual(r["tier"], "spatial_fallback")
        self.assertTrue(all("bounded" in c["explanation"] for c in r["comparables"]))
        self.assertTrue(all(c["distance_km"] <= 2 for c in r["comparables"]))

    def test_abstains_when_no_sufficient_geography(self):
        all_far = [rec(str(i), 10+i, hood="B", lat=42.15) for i in range(5)]
        r = match_property(self.subject, all_far)
        self.assertEqual(r["status"], "insufficient_data")
        self.assertEqual(r["selected_count"], 0)
        self.assertEqual(r["reason"], "insufficient_local_and_nearby_sales")

    def test_missing_coordinates_abstains_if_local_thin(self):
        s = {**self.subject, "lat": None, "lon": None}
        r = match_property(s, self.local[:2])
        self.assertEqual(r["reason"], "missing_subject_coordinates")
        self.assertEqual(r["local_candidate_count"], 2)

    def test_no_coordinate_needed_for_three_local_comps(self):
        s = {**self.subject, "lat": None, "lon": None}
        r = match_property(s, self.local[:3])
        self.assertEqual(r["tier"], "same_neighborhood")

    def test_filters_future_today_class_township_size_doc_and_pin(self):
        cases = [
            rec("x", -2), rec("today", 0), rec("old", 400),
            rec("wrongclass", 20, cls="205"), rec("wrongtown", 20, township="18"),
            rec("wrongsize", 20, area=3000), rec("doc", 20, doc="subject"),
            rec("subject", 20),
        ] + self.local[:2]
        r = match_property(self.subject, cases)
        self.assertEqual(r["eligible_unique_properties"], 2)
        self.assertEqual(r["status"], "insufficient_data")

    def test_duplicate_pin_one_sale_per_house_selects_most_recent(self):
        population = [rec("duplicate", 90, price=1), rec("duplicate", 20, price=1000000),
                      self.local[0], self.local[1]]
        r = match_property(self.subject, population)
        self.assertEqual(r["eligible_unique_properties"], 3)
        self.assertEqual(r["selected_count"], 3)
        self.assertEqual([x["sale_date"] for x in r["comparables"] if x["pin"] == "duplicate"],
                         [rec("duplicate", 20)["sale_date"]])

    def test_price_changes_never_change_rank(self):
        first = match_property(self.subject, self.local)
        changed = [dict(x, sale_price=999999999-x["sale_price"]) for x in self.local]
        second = match_property(self.subject, changed)
        self.assertEqual([x["pin"] for x in first["comparables"]],
                         [x["pin"] for x in second["comparables"]])

    def test_boundary_radius_exactly_and_bad_coords(self):
        good = [rec(str(i), 15+i, hood="B", lat=42.03) for i in range(3)]
        bad = rec("bad", 18, hood="B", lat=float("nan"))
        r = match_property(self.subject, good+[bad])
        self.assertEqual(r["selected_count"], 3)
        self.assertTrue(all(c["pin"] != "bad" for c in r["comparables"]))

    def test_no_eligible_prior_sales_reason(self):
        r = match_property(self.subject, [rec("future", -5)])
        self.assertEqual(r["reason"], "no_eligible_prior_sales")

    def test_unsupported_class_never_matched(self):
        r = match_property({**self.subject, "class":"205"}, self.local)
        self.assertEqual(r["reason"], "unsupported_property_scope")

    def test_invalid_policy(self):
        for kw in [{"radius_km":0}, {"min_comps":6,"max_comps":5}, {"history_days":0}]:
            with self.assertRaises(ValueError): MatchPolicy(**kw)

    def test_buyer_analysis_date_supported(self):
        subject = dict(self.subject, analysis_date="2024-08-01")
        result = match_property(subject, self.local[:3])
        self.assertEqual(result["analysis_date"], "2024-08-01")
        self.assertEqual(result["tier"], "same_neighborhood")

    def test_aggregate_evaluation_has_no_identifiers(self):
        records = [rec("historical"+str(i), 500-i*10) for i in range(5)]
        records.extend([rec("eval"+str(i), 20-i, price=600000) for i in range(3)])
        result = evaluate(records)
        self.assertEqual(result["subject_count"], 3)
        self.assertNotIn("historical0", str(result))
        self.assertNotIn("eval0", str(result))
        self.assertEqual(sum(result["tier_counts"].values()), 3)


if __name__ == '__main__':
    unittest.main()
