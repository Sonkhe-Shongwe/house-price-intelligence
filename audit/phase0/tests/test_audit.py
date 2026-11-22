"""Unit tests with fabricated records, not official dataset counts."""
import unittest
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from audit import (normalize_pin, whole_count, sale_reject_reasons, building_rows_by_key,
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
    def test_whole_count_accepts_integral_decimal_number_fields(self):
        for value in (1, 1.0, "1", "1.0", "1.000", "1e0"):
            self.assertEqual(whole_count(value), 1)
        for value in ("1.5", "NaN", "Infinity", "", None, True, False, "abc"):
            self.assertIsNone(whole_count(value))
        self.assertEqual(whole_count("2.0"), 2)

    def test_sale_parcel_count_decimal(self):
        s = sample_sale()
        s["num_parcels_sale"] = "1.0"
        self.assertEqual(sale_reject_reasons(s), [])
        s["num_parcels_sale"] = "2.0"
        self.assertIn("not_one_parcel_sale", sale_reject_reasons(s))
        s["num_parcels_sale"] = "1.5"
        self.assertIn("missing_num_parcels_sale", sale_reject_reasons(s))

    def test_building_card_count_decimal(self):
        b = sample_building()
        b["pin_num_cards"] = "1.0"
        rec, reason = join_sale_to_prior_building(sample_sale(), building_rows_by_key([b]))
        self.assertIsNone(reason)
        self.assertEqual(rec["sqft"], 1600)
        b["pin_num_cards"] = "2.0"
        rec, reason = join_sale_to_prior_building(sample_sale(), building_rows_by_key([b]))
        self.assertIsNone(rec)
        self.assertEqual(reason, "multi_card_count")
        b["pin_num_cards"] = "1.5"
        rec, reason = join_sale_to_prior_building(sample_sale(), building_rows_by_key([b]))
        self.assertIsNone(rec)
        self.assertEqual(reason, "invalid_card_count")

    def test_year_breakdown(self):
        result = run_analysis([sample_sale()], [sample_building()], township="17", start="2022-01-01", end="2025-01-01")
        self.assertEqual(result["screened_sales_by_year"], {"2024": 1})
        self.assertEqual(result["joined_sales_by_year"], {"2024": 1})
        self.assertEqual(result["single_prior_record_card_value_counts"], {"1": 1})

    def test_offline_reanalysis_preserves_original_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            sale = sample_sale()
            building = sample_building()
            building["pin_num_cards"] = "1.0"
            (out / "sales_selected_fields.jsonl").write_text(json.dumps(sale) + "\n", encoding="utf-8")
            (out / "buildings_selected_fields.jsonl").write_text(json.dumps(building) + "\n", encoding="utf-8")
            original = {"source_sale_rows": 1, "source_building_rows": 1,
                        "audited_township_code": "17", "sale_start_inclusive": "2022-01-01",
                        "sale_end_exclusive": "2025-01-01",
                        "extraction_capped": {"sales": False, "buildings": False}}
            (out / "audit_summary.json").write_text(json.dumps(original), encoding="utf-8")
            (out / "audit_report.md").write_text(
                "Data set update timestamps (Unix seconds when supplied): sales 100, characteristics 200\n",
                encoding="utf-8")
            script = Path(__file__).resolve().parents[1] / "reanalyze.py"
            completed = subprocess.run([sys.executable, str(script), "--out", str(out)],
                                       capture_output=True, text=True, check=True)
            revised = json.loads((out / "audit_summary_v2.json").read_text(encoding="utf-8"))
            self.assertEqual(revised["joined_sale_candidates"], 1)
            self.assertIn("Reanalysis complete", completed.stdout)
            self.assertIn("sales 100, characteristics 200", (out / "audit_report_v2.md").read_text(encoding="utf-8"))
            self.assertEqual(json.loads((out / "audit_summary.json").read_text(encoding="utf-8")), original)

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
