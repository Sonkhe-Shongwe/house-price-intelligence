"""SQLite-to-matcher end-to-end tests using invented transactions only."""
from datetime import date, datetime, timezone
from pathlib import Path
import sqlite3
import unittest

from backend.investigation_contract import ContractError
from backend.synthetic_investigation_store import EvidenceStoreError, SyntheticInvestigationStore

SCHEMA = Path(__file__).resolve().parents[1] / "schema_draft.sql"
TODAY = date(2026, 11, 22)
NOW = datetime(2026, 11, 22, 16, 0, tzinfo=timezone.utc)
BUILD = "synthetic-build"
SUBJECT = "00000000000001"


def enquiry(**updates):
    subject = {"pin": SUBJECT, "building_area_sqft": 1600, "asking_price_usd": "500000.00",
               "label": "Synthetic example"}
    subject.update(updates)
    return {"township_code": "17", "class_code": "203", "analysis_date": "2024-07-01",
            "subject": subject}


class SyntheticServiceTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA.read_text(encoding="utf-8"))
        self.db.execute("PRAGMA foreign_keys = ON")
        for src, role in (("sale-snap", "sales"), ("assess-snap", "assessment"),
                          ("geo-snap", "geography")):
            self.db.execute("INSERT INTO source_snapshots (snapshot_id, dataset_id, extracted_at_utc, source_query) VALUES(?,?,?,?)",
                            (src, "synthetic-" + role, "2026-11-22T00:00:00Z", "fabricated"))
        self.db.execute("INSERT INTO curated_builds VALUES(?,?,?,?)",
                        (BUILD, "2026-11-22T00:00:00Z", "0" * 64, "synthetic_fixture"))
        for src, role in (("sale-snap", "sales"), ("assess-snap", "assessment"),
                          ("geo-snap", "geography")):
            self.db.execute("INSERT INTO curated_build_sources VALUES (?,?,?)", (BUILD, src, role))
        self.add_parcel(SUBJECT, tax_year=2023)
        for number in range(2, 5):
            self.add_parcel(f"{number:014d}", tax_year=2023)
            self.add_sale(number)
        self.db.commit()
        self.store = SyntheticInvestigationStore(self.db, build_id=BUILD)

    def tearDown(self):
        self.db.close()

    def add_parcel(self, pin, *, tax_year, cls="203", area=1600, nbhd="17", lat=42.04, lon=-87.68):
        self.db.execute("INSERT INTO parcels VALUES (?,?)", (pin, "17"))
        self.db.execute("INSERT INTO assessment_records VALUES(?,?,?,?,?,?,?,?)",
                        (f"assessment-{pin}", "assess-snap", pin, tax_year, "1", None, cls, area))
        self.db.execute("INSERT INTO parcel_geographies VALUES(?,?,?,?,?,?,?)",
                        ("geo-snap", pin, tax_year, nbhd, lat, lon, 1))

    def add_sale(self, number, *, pin=None, day="2024-02-01", doc=None, snapshot="sale-snap"):
        pin = pin or f"{number:014d}"
        txn = f"txn-{number}"
        doc = doc or f"DOC-{number}"
        self.db.execute("INSERT INTO sale_transactions VALUES(?,?,?,?,?,?)",
                        (txn, snapshot, f"row-{number}", doc, day, 52500000))
        self.db.execute("INSERT INTO sale_transaction_parcels VALUES(?,?)", (txn, pin))
        self.db.execute("INSERT INTO curated_build_transactions VALUES(?,?)", (BUILD, txn))
        return txn

    def test_sqlite_to_matcher_to_saved_reopen(self):
        result = self.store.create(enquiry(), today=TODAY, investigation_id="inv-1", recorded_at=NOW)
        self.assertEqual(result["status"], "supported_neighbourhood")
        self.assertEqual(result["selected_count"], 3)
        self.assertEqual(result["data_build"]["source_snapshot_ids"],
                         ["assess-snap", "geo-snap", "sale-snap"])
        self.assertEqual(result["data_build"]["public_property_display_approved"], False)
        self.assertEqual(result["valuation"], None)
        self.assertEqual(len(result["comparables"]), 3)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM comparable_evidence").fetchone()[0], 3)
        self.assertEqual(self.store.reopen("inv-1"), result)
        self.assertEqual(self.db.execute("SELECT match_policy_version FROM investigations").fetchone()[0],
                         SyntheticInvestigationStore.POLICY_VERSION)

    def test_fallback_marked_exploratory(self):
        self.db.execute("UPDATE parcel_geographies SET neighborhood_code = '18', latitude = 42.041, longitude = -87.681 WHERE pin != ?", (SUBJECT,))
        result = self.store.create(enquiry(), today=TODAY, investigation_id="fallback")
        self.assertEqual(result["status"], "exploratory_spatial")
        self.assertEqual(result["selected_count"], 3)
        self.assertIsNone(result["valuation"])
        self.assertTrue(any("exploratory" in w.lower() for w in result["warnings"]))
        self.assertEqual(self.store.reopen("fallback"), result)

    def test_unknown_pin_and_missing_pin_save_insufficient_drafts(self):
        for pin in (None, "00000000000099"):
            with self.subTest(pin=pin):
                result = self.store.create(enquiry(pin=pin), today=TODAY)
                self.assertEqual(result["status"], "insufficient_data")
                self.assertEqual(result["selected_count"], 0)
                self.assertIsNone(self.db.execute("SELECT subject_pin FROM investigations WHERE investigation_id=?", (result["investigation_id"],)).fetchone()[0])
                self.assertEqual(self.store.reopen(result["investigation_id"]), result)

    def test_out_of_scope_returns_explicit_state(self):
        req = enquiry()
        req["class_code"] = "211"
        result = self.store.create(req, today=TODAY)
        self.assertEqual(result["status"], "out_of_coverage")
        self.assertEqual(result["selected_count"], 0)

    def test_multi_parcel_transaction_excluded(self):
        self.db.execute("INSERT INTO sale_transaction_parcels VALUES(?,?)", ("txn-2", SUBJECT))
        result = self.store.create(enquiry(), today=TODAY)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["selected_count"], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM comparable_evidence").fetchone()[0], 0)

    def test_ambiguous_prior_assessment_not_guessed(self):
        self.db.execute("INSERT INTO assessment_records VALUES(?,?,?,?,?,?,?,?)",
                        ("duplicate-card", "assess-snap", "00000000000002", 2023, "2", None, "203", 1600))
        result = self.store.create(enquiry(), today=TODAY)
        self.assertEqual(result["status"], "insufficient_data")

    def test_sale_from_unregistered_build_source_is_excluded(self):
        self.db.execute("INSERT INTO source_snapshots(snapshot_id,dataset_id,extracted_at_utc,source_query) VALUES(?,?,?,?)",
                        ("unlisted", "not-this-build", "2026-11-22T00:00:00Z", "synthetic"))
        self.db.execute("UPDATE sale_transactions SET snapshot_id = 'unlisted' WHERE transaction_id='txn-2'")
        result = self.store.create(enquiry(), today=TODAY)
        self.assertEqual(result["status"], "insufficient_data")

    def test_candidate_assessment_source_not_registered_is_excluded(self):
        self.db.execute("INSERT INTO source_snapshots(snapshot_id,dataset_id,extracted_at_utc,source_query) VALUES(?,?,?,?)",
                        ("outside-assessment", "not-in-build", "2026-11-22T00:00:00Z", "synthetic"))
        self.db.execute("UPDATE assessment_records SET snapshot_id='outside-assessment' WHERE pin='00000000000002'")
        result = self.store.create(enquiry(), today=TODAY)
        self.assertEqual(result["status"], "insufficient_data")

    def test_rejects_real_research_build_even_when_it_exists(self):
        self.db.execute("UPDATE curated_builds SET build_kind='historical_research' WHERE build_id=?", (BUILD,))
        with self.assertRaisesRegex(EvidenceStoreError, "disabled"):
            self.store.create(enquiry(), today=TODAY)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 0)

    def test_source_claiming_synthetic_cannot_point_at_real_dataset(self):
        self.db.execute("UPDATE source_snapshots SET dataset_id='wvhk-k5uv' WHERE snapshot_id='sale-snap'")
        with self.assertRaisesRegex(EvidenceStoreError, "non-fixture"):
            self.store.create(enquiry(), today=TODAY)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 0)

    def test_wrong_comparable_explanation_detected_on_reopen(self):
        self.store.create(enquiry(), today=TODAY, investigation_id="rebound")
        self.db.execute("UPDATE comparable_evidence SET explanation='altered text' "
                        "WHERE investigation_id='rebound' AND rank=1")
        with self.assertRaisesRegex(EvidenceStoreError, "identities"):
            self.store.reopen("rebound")

    def test_missing_required_build_role_fails_closed(self):
        self.db.execute("DELETE FROM curated_build_sources WHERE source_role='geography'")
        with self.assertRaisesRegex(EvidenceStoreError, "missing source role"):
            self.store.create(enquiry(), today=TODAY)

    def test_identity_conflict_between_duplicate_transactions_is_atomic(self):
        # Two same-PIN, same-date, same-document transactions are ambiguous,
        # even if the matcher chooses the PIN only once.
        self.add_sale(22, pin="00000000000002", day="2024-02-01", doc="DOC-2")
        with self.assertRaisesRegex(EvidenceStoreError, "ambiguous"):
            self.store.create(enquiry(), today=TODAY, investigation_id="bad")
        self.assertIsNone(self.db.execute("SELECT 1 FROM investigations WHERE investigation_id='bad'").fetchone())
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM comparable_evidence").fetchone()[0], 0)

    def test_duplicate_investigation_identifier_no_partial_write(self):
        first = self.store.create(enquiry(), today=TODAY, investigation_id="same")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.create(enquiry(label="another"), today=TODAY, investigation_id="same")
        self.assertEqual(self.store.reopen("same"), first)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 1)

    def test_bad_buyer_field_rejected_before_store(self):
        with self.assertRaises(ContractError):
            self.store.create(enquiry(lat=42.04), today=TODAY)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 0)

    def test_detects_tampered_response_on_reopen(self):
        result = self.store.create(enquiry(), today=TODAY, investigation_id="tamper")
        self.db.execute("UPDATE investigation_results SET response_json = '{}' WHERE investigation_id='tamper'")
        with self.assertRaisesRegex(EvidenceStoreError, "modified"):
            self.store.reopen("tamper")

    def test_detects_inconsistent_evidence_count(self):
        result = self.store.create(enquiry(), today=TODAY, investigation_id="missing")
        self.db.execute("DELETE FROM comparable_evidence WHERE investigation_id='missing' AND rank=1")
        with self.assertRaisesRegex(EvidenceStoreError, "count"):
            self.store.reopen("missing")

    def test_empty_or_bad_build_id_refused(self):
        with self.assertRaises(EvidenceStoreError):
            SyntheticInvestigationStore(self.db, build_id="")
        with self.assertRaises(EvidenceStoreError):
            SyntheticInvestigationStore(self.db, build_id="absent").create(enquiry(), today=TODAY)

    def test_no_foreign_keys_blocked(self):
        other = sqlite3.connect(":memory:")
        try:
            with self.assertRaises(EvidenceStoreError):
                SyntheticInvestigationStore(other, build_id=BUILD)
        finally:
            other.close()


if __name__ == "__main__":
    unittest.main()
