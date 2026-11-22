"""Unit tests with fabricated records, not official dataset counts."""
import unittest
from audit import (normalize_pin, sale_reject_reasons, building_rows_by_key,
                   join_sale_to_prior_building, eligible_comparables, run_analysis)


def sample_sale(pin="12345678901234", date_="2024-06-01T00:00:00", price="350000", doc="AB123"):
    return {"pin": pin, "sale_date": date_, "sale_price": price, "doc_no": doc,
            "township_code": "17", "is_multisale": False, "num_parcels_sale": "1",
            "sale_filter_less_than_10k": False, "sale_filter_deed_type": False,
            "sale_filter_same_sale_within_365": False}


def sample_building(pin="12345678901234", year="2023", card="1", sqft="1600"):
    return {"pin": pin, "year": year, "card": card, "class": "TEST_CLASS",
            "township_code": "17", "char_bldg_sf": sqft, "pin_num_cards": "1",
            "pin_is_multicard": False}


class AuditTests(unittest.TestCase):
    def test_leading_zero_pin(self):
        self.assertEqual(normalize_pin("00012345678901"), "00012345678901")
        self.assertEqual(normalize_pin("12345678901"), "00012345678901")

    def test_multisale_exclusion(self):
        s = sample_sale()
        s["is_multisale"] = True
        s["num_parcels_sale"] = "2"
        self.assertIn("multi_parcel_sale", sale_reject_reasons(s))
        self.assertIn("not_one_parcel_sale", sale_reject_reasons(s))

    def test_required_flag_missing_blocks(self):
        s = sample_sale()
        del s["sale_filter_deed_type"]
        self.assertIn("missing_or_invalid_sale_filter_deed_type", sale_reject_reasons(s))

    def test_prior_year_join(self):
        record, reason = join_sale_to_prior_building(sample_sale(),
                         building_rows_by_key([sample_building()]))
        self.assertIsNone(reason)
        self.assertEqual(record["sqft"], 1600)
        wrong, reason = join_sale_to_prior_building(sample_sale(),
                         building_rows_by_key([sample_building(year="2024")]))
        self.assertIsNone(wrong)
        self.assertEqual(reason, "no_prior_building")

    def test_multibuilding_exclusion(self):
        b1 = sample_building(card="1")
        b2 = sample_building(card="2")
        record, reason = join_sale_to_prior_building(sample_sale(), building_rows_by_key([b1, b2]))
        self.assertIsNone(record)
        self.assertEqual(reason, "multiple_prior_buildings")

    def test_future_and_same_parcel_exclusion(self):
        subj = {"pin": "00000000000001", "doc_no": "X", "class": "C", "township_code": "17",
                "sqft": 1000., "sale_date": "2024-06-01", "sale_price": 300000}
        prev = dict(subj, pin="00000000000002", doc_no="Y", sale_date="2024-01-01")
        future = dict(subj, pin="00000000000003", doc_no="Z", sale_date="2024-07-01")
        same = dict(subj, sale_date="2024-01-01")
        self.assertEqual(eligible_comparables(subj, [prev, future, same]), [prev])

    def test_duplicate_screened(self):
        sales = [sample_sale(), sample_sale()]
        result = run_analysis(sales, [sample_building()], township="17", start="2022-01-01", end="2025-01-01")
        self.assertEqual(result["sales_after_screen"], 1)
        self.assertEqual(result["sale_reasons_not_mutually_exclusive"]["duplicate_sale_identity"], 1)


if __name__ == "__main__":
    unittest.main()
