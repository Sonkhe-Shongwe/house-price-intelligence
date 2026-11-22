"""Offline fixture-only checks for a proposed P3 property investigation contract."""
from datetime import date
import json
from pathlib import Path
import unittest

from backend.investigation_contract import ContractError, build_investigation, validate_request

TODAY = date(2026, 11, 22)
BUILD = {"build_id": "fixture-build-2024-a", "built_at_utc": "2026-11-22T16:00:00Z", "source_kind": "synthetic_fixture", "source_snapshot_ids": ["fixture-sales", "fixture-geography", "fixture-buildings"]}
PIN = "00000000000001"


def request(**subject_changes):
    subject = {"pin": PIN, "building_area_sqft": 1600, "asking_price_usd": "650000.00", "label": "First option"}
    subject.update(subject_changes)
    return {"township_code": "17", "class_code": "203", "analysis_date": "2024-07-01", "subject": subject}


def resolved(**changes):
    r = {"build_id": BUILD["build_id"], "pin": PIN, "township_code": "17", "class": "203", "sqft": 1600,
         "nbhd_code": "17", "lat": 42.04, "lon": -87.68, "characteristics_year": 2023}
    r.update(changes)
    return r


def sale(pin, day, neighborhood="17", lat=42.04, lon=-87.68, sqft=1600):
    return {"build_id": BUILD["build_id"], "pin": pin, "doc_no": "DOC" + pin, "sale_date": day,
            "sale_price": 525000, "sqft": sqft, "class": "203", "township_code": "17",
            "nbhd_code": neighborhood, "lat": lat, "lon": lon, "characteristics_year": 2023}


class InvestigationContractTests(unittest.TestCase):
    def test_neighborhood_support_synthetic_only(self):
        population = [sale(f"{i:014d}", "2024-02-01") for i in (2, 3, 4)]
        result = build_investigation(request(), resolved_subject=resolved(),
                                     candidate_sales=population, data_build=BUILD,
                                     synthetic_demo=True, today=TODAY)
        self.assertEqual(result["status"], "supported_neighbourhood")
        self.assertEqual(result["selected_count"], 3)
        self.assertEqual(len(result["comparables"]), 3)
        self.assertIsNone(result["valuation"])
        self.assertFalse(result["data_build"]["historical_as_of_verified"])

    def test_real_source_properties_redacted_by_default(self):
        population = [sale(f"{i:014d}", "2024-02-01") for i in (2, 3, 4)]
        result = build_investigation(request(), resolved_subject=resolved(),
                                     candidate_sales=population, data_build=BUILD, today=TODAY)
        self.assertEqual(result["status"], "supported_neighbourhood")
        self.assertEqual(result["selected_count"], 3)
        self.assertEqual(result["comparables"], [])
        self.assertTrue(result["evidence_details_redacted"])
        self.assertNotIn("00000000000002", str(result))
        self.assertNotIn("525000", str(result))

    def test_spatial_fallback_is_exploratory_and_valuation_null(self):
        population = [sale(f"{i:014d}", "2024-02-01", neighborhood="18",
                           lat=42.041, lon=-87.681) for i in (2, 3, 4)]
        result = build_investigation(request(), resolved_subject=resolved(),
                                     candidate_sales=population, data_build=BUILD,
                                     synthetic_demo=True, today=TODAY)
        self.assertEqual(result["status"], "exploratory_spatial")
        self.assertEqual(result["selected_count"], 3)
        self.assertIsNone(result["valuation"])
        self.assertTrue(any("exploratory" in w.lower() for w in result["warnings"]))

    def test_no_support_abstains(self):
        result = build_investigation(request(), resolved_subject=resolved(),
                                     candidate_sales=[sale("00000000000002", "2024-02-01")],
                                     data_build=BUILD, today=TODAY)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["selected_count"], 0)
        self.assertIsNone(result["valuation"])

    def test_out_of_scope_is_not_a_bad_request(self):
        obj = request()
        obj["class_code"] = "211"
        result = build_investigation(obj, resolved_subject=None,
                                     candidate_sales=[], data_build=BUILD, today=TODAY)
        self.assertEqual(result["status"], "out_of_coverage")
        self.assertEqual(result["comparables"], [])

    def test_pin_required_for_matching_not_for_draft(self):
        result = build_investigation(request(pin=None), resolved_subject=None,
                                     candidate_sales=[], data_build=BUILD, today=TODAY)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["reason"], "parcel_identity_not_resolved")

    def test_unknown_or_unverified_coordinates_are_not_accepted_from_client(self):
        with self.assertRaises(ContractError) as cm:
            validate_request({**request(lat=42.04)}, today=TODAY)
        self.assertEqual(cm.exception.code, "unknown_fields")

    def test_strict_decimal_user_price(self):
        for bad in (-1, 600000.0, "1.234", "NaN", "-1", "0", "100000000000", "R500"):
            with self.subTest(bad=bad), self.assertRaises(ContractError):
                validate_request(request(asking_price_usd=bad), today=TODAY)
        self.assertEqual(validate_request(request(asking_price_usd="12.5"), today=TODAY)["subject"]["asking_price_usd"], "12.50")

    def test_invalid_and_future_dates(self):
        obj = request(); obj["analysis_date"] = "2024-02-30"
        with self.assertRaises(ContractError): validate_request(obj, today=TODAY)
        obj["analysis_date"] = "2027-01-01"
        with self.assertRaises(ContractError): validate_request(obj, today=TODAY)

    def test_identity_conflict_is_error(self):
        with self.assertRaises(ContractError) as cm:
            build_investigation(request(), resolved_subject=resolved(pin="00000000000099"),
                                 candidate_sales=[], data_build=BUILD, today=TODAY)
        self.assertEqual(cm.exception.code, "identity_conflict")

    def test_original_matcher_protects_against_future_and_duplicate_pin(self):
        population = [sale("00000000000002", "2024-03-01"),
                      sale("00000000000002", "2024-05-01"),
                      sale("00000000000003", "2024-06-01"),
                      sale("00000000000004", "2024-07-01"),
                      sale("00000000000005", "2024-08-01")]
        r = build_investigation(request(), resolved_subject=resolved(),
                                candidate_sales=population, data_build=BUILD,
                                synthetic_demo=True, today=TODAY)
        self.assertEqual(r["status"], "insufficient_data")
        self.assertEqual(r["selected_count"], 0)

    def test_synthetic_demo_cannot_be_enabled_for_research_source(self):
        source = {**BUILD, "source_kind": "historical_research"}
        with self.assertRaises(ContractError) as cm:
            build_investigation(request(), resolved_subject=resolved(),
                                candidate_sales=[], data_build=source,
                                synthetic_demo=True, today=TODAY)
        self.assertEqual(cm.exception.code, "restricted_to_synthetic_fixture")

    def test_missing_snapshot_timezone_fails_closed(self):
        with self.assertRaises(ContractError) as cm:
            build_investigation(request(), resolved_subject=resolved(), candidate_sales=[],
                                 data_build={"build_id":"x", "built_at_utc":"2026-11-22T16:00:00", "source_kind":"synthetic_fixture", "source_snapshot_ids": ["fixture-sales"]},today=TODAY)
        self.assertEqual(cm.exception.code, "offset_timestamp_required")

    def test_unapproved_resolved_year_in_future_fails(self):
        with self.assertRaises(ContractError):
            build_investigation(request(), resolved_subject=resolved(characteristics_year=2025),
                                 candidate_sales=[],data_build=BUILD,today=TODAY)

    def test_document_exposes_no_claim_of_historical_asof(self):
        r = build_investigation(request(), resolved_subject=resolved(),
                                candidate_sales=[],data_build=BUILD,today=TODAY)
        self.assertFalse(r["data_build"]["historical_as_of_verified"])
        self.assertFalse(r["data_build"]["public_property_display_approved"])


    def test_mismatched_subject_build_is_rejected(self):
        with self.assertRaises(ContractError) as cm:
            build_investigation(request(), resolved_subject=resolved(build_id="from-other-build"),
                                candidate_sales=[], data_build=BUILD, today=TODAY)
        self.assertEqual(cm.exception.field, "resolved_subject")
        self.assertEqual(cm.exception.code, "missing_or_mismatched_build")

    def test_missing_subject_build_is_rejected(self):
        obj = resolved()
        del obj["build_id"]
        with self.assertRaises(ContractError) as cm:
            build_investigation(request(), resolved_subject=obj,
                                candidate_sales=[], data_build=BUILD, today=TODAY)
        self.assertEqual(cm.exception.code, "missing_or_mismatched_build")

    def test_mismatched_candidate_build_is_rejected(self):
        bad = sale("00000000000002", "2024-02-01")
        bad["build_id"] = "other-build"
        with self.assertRaises(ContractError) as cm:
            build_investigation(request(), resolved_subject=resolved(),
                                candidate_sales=[bad], data_build=BUILD, today=TODAY)
        self.assertEqual(cm.exception.field, "candidate_sales[0]")
        self.assertEqual(cm.exception.code, "missing_or_mismatched_build")

    def test_candidates_reject_same_year_characteristics(self):
        bad = sale("00000000000002", "2024-02-01")
        bad["characteristics_year"] = 2024
        with self.assertRaises(ContractError) as cm:
            build_investigation(request(), resolved_subject=resolved(),
                                candidate_sales=[bad], data_build=BUILD, today=TODAY)
        self.assertEqual(cm.exception.code, "invalid_sale_or_characteristics_year")

    def test_candidates_reject_invalid_sale_date(self):
        bad = sale("00000000000002", "2024-02-30")
        with self.assertRaises(ContractError) as cm:
            build_investigation(request(), resolved_subject=resolved(),
                                candidate_sales=[bad], data_build=BUILD, today=TODAY)
        self.assertEqual(cm.exception.code, "invalid_sale_or_characteristics_year")

    def test_resolved_subject_rejects_same_year_characteristics(self):
        with self.assertRaises(ContractError) as cm:
            build_investigation(request(), resolved_subject=resolved(characteristics_year=2024),
                                candidate_sales=[], data_build=BUILD, today=TODAY)
        self.assertEqual(cm.exception.code, "invalid_or_future_record_year")

    def test_future_build_rejected(self):
        build = {**BUILD, "built_at_utc": "2027-01-01T12:00:00Z"}
        with self.assertRaises(ContractError) as cm:
            build_investigation(request(), resolved_subject=resolved(),
                                candidate_sales=[], data_build=build, today=TODAY)
        self.assertEqual(cm.exception.code, "future_build")

    def test_duplicate_source_snapshots_rejected(self):
        build = {**BUILD, "source_snapshot_ids": ["fixture-sales", "fixture-sales"]}
        with self.assertRaises(ContractError) as cm:
            build_investigation(request(), resolved_subject=resolved(),
                                candidate_sales=[], data_build=build, today=TODAY)
        self.assertEqual(cm.exception.code, "invalid_source_list")

    def test_historical_research_never_discloses_individual_sale_details(self):
        build = {**BUILD, "source_kind": "historical_research"}
        result = build_investigation(request(), resolved_subject=resolved(),
                                     candidate_sales=[sale(f"{i:014d}", "2024-02-01") for i in (2, 3, 4)],
                                     data_build=build, today=TODAY)
        self.assertEqual(result["status"], "supported_neighbourhood")
        self.assertEqual(result["selected_count"], 3)
        self.assertEqual(result["comparables"], [])
        self.assertTrue(result["evidence_details_redacted"])
        self.assertIsNone(result["valuation"])


    def test_synthetic_example_stays_in_sync_with_contract(self):
        root = Path(__file__).resolve().parents[1] / "examples"
        stored_request = json.loads((root / "synthetic_request.json").read_text())
        expected_response = json.loads((root / "synthetic_response.json").read_text())
        generated = build_investigation(
            stored_request, resolved_subject=resolved(),
            candidate_sales=[sale(f"{i:014d}", "2024-02-01") for i in (2, 3, 4)],
            data_build=BUILD, synthetic_demo=True, today=TODAY,
        )
        self.assertEqual(generated, expected_response)
        self.assertEqual(expected_response["contract_version"], "p3-draft-v0.2")


if __name__ == "__main__":
    unittest.main()
