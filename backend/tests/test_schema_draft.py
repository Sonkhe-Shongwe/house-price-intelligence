"""SQLite foreign-key/grain smoke tests for a P3 schema PROPOSAL, not a migration."""
from pathlib import Path
import sqlite3
import unittest

SCHEMA = Path(__file__).resolve().parents[1] / "schema_draft.sql"


class DraftSQLTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("INSERT INTO source_snapshots(snapshot_id,dataset_id,extracted_at_utc,source_query) VALUES(?,?,?,?)",
                          ("synthetic", "test-source", "2026-11-22T00:00:00Z", "synthetic only"))
        self.conn.execute("INSERT INTO curated_builds VALUES(?,?,?,?)",
                          ("fixture-build", "2026-11-22T00:00:00Z", "0" * 64, "synthetic_fixture"))
        self.conn.execute("INSERT INTO curated_build_sources VALUES(?,?,?)",
                          ("fixture-build", "synthetic", "sales"))
        self.conn.execute("INSERT INTO parcels(pin,township_code) VALUES(?,?)",("00000000000001","17"))

    def tearDown(self):
        self.conn.close()

    def test_source_grain_allows_multi_parcel_transaction_without_duplication(self):
        self.conn.execute("INSERT INTO parcels(pin,township_code) VALUES(?,?)",("00000000000002","17"))
        self.conn.execute("INSERT INTO sale_transactions VALUES(?,?,?,?,?,?)",
                          ("txn-1", "synthetic", "row-1", "doc-1", "2024-01-01", 20000000))
        self.conn.executemany("INSERT INTO sale_transaction_parcels VALUES(?,?)",
                              [("txn-1","00000000000001"),("txn-1","00000000000002")])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM sale_transactions").fetchone()[0],1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM sale_transaction_parcels").fetchone()[0],2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO sale_transaction_parcels VALUES(?,?)",("txn-1","00000000000001"))

    def test_unresolved_building_identity_allowed_but_assessment_rows_unique(self):
        args = ("record-1","synthetic","00000000000001",2023,"1",None,"203",1600)
        self.conn.execute("INSERT INTO assessment_records VALUES (?,?,?,?,?,?,?,?)",args)
        self.assertEqual(self.conn.execute("SELECT building_id FROM assessment_records").fetchone()[0],None)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO assessment_records VALUES (?,?,?,?,?,?,?,?)",
                              ("record-2",)+args[1:])

    def test_source_snapshot_fk_and_status_constraints(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO investigations VALUES (?,?,?,?,?,?,?,?)",
                              ("inv-x","not-real","00000000000001","2024-06-01","{}","v1","insufficient_data","2026-11-22T00:00:00Z"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO investigations VALUES (?,?,?,?,?,?,?,?)",
                              ("inv-x","fixture-build","00000000000001","2024-06-01","{}","v1","guaranteed_valuation","2026-11-22T00:00:00Z"))

    def test_parcel_pin_not_normalised_to_integer(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO parcels VALUES (?,?)",("123", "17"))
        self.assertEqual(self.conn.execute("SELECT pin FROM parcels").fetchone()[0],"00000000000001")


    def test_curated_build_source_requires_known_snapshot(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO curated_build_sources VALUES(?,?,?)",
                              ("fixture-build", "missing-snapshot", "assessment"))

    def test_investigation_must_reference_known_curated_build(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO investigations VALUES(?,?,?,?,?,?,?,?)",
                              ("inv-no-build", "missing-build", "00000000000001", "2024-06-01",
                               "{}", "v0.2", "insufficient_data", "2026-11-22T00:00:00Z"))

    def test_comparable_evidence_must_belong_to_same_build(self):
        self.conn.execute("INSERT INTO curated_builds VALUES(?,?,?,?)",
                          ("other-build", "2026-11-22T00:00:00Z", "1" * 64, "synthetic_fixture"))
        self.conn.execute("INSERT INTO sale_transactions VALUES(?,?,?,?,?,?)",
                          ("txn-x", "synthetic", "row-x", "DOC-X", "2024-02-01", 20000000))
        self.conn.execute("INSERT INTO curated_build_transactions VALUES(?,?)", ("other-build", "txn-x"))
        self.conn.execute("INSERT INTO investigations VALUES(?,?,?,?,?,?,?,?)",
                          ("inv-a", "fixture-build", "00000000000001", "2024-07-01",
                           "{}", "v0.2", "supported_neighbourhood", "2026-11-22T00:00:00Z"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO comparable_evidence VALUES(?,?,?,?,?,?)",
                              ("inv-a", "fixture-build", 1, "txn-x", "same_neighborhood", "synthetic"))
        # A build with the transaction but a different investigation is also rejected.
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO comparable_evidence VALUES(?,?,?,?,?,?)",
                              ("inv-a", "other-build", 1, "txn-x", "same_neighborhood", "synthetic"))
        # Once specifically imported into the enquiry's build, linkage succeeds.
        self.conn.execute("INSERT INTO curated_build_transactions VALUES(?,?)", ("fixture-build", "txn-x"))
        self.conn.execute("INSERT INTO comparable_evidence VALUES(?,?,?,?,?,?)",
                          ("inv-a", "fixture-build", 1, "txn-x", "same_neighborhood", "synthetic"))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM comparable_evidence").fetchone()[0], 1)


    def test_assessment_cannot_point_to_building_on_other_parcel(self):
        self.conn.execute("INSERT INTO parcels VALUES(?,?)", ("00000000000002", "17"))
        self.conn.execute("INSERT INTO buildings VALUES(?,?,?)", ("building-2", "00000000000002", 1))
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO assessment_records VALUES(?,?,?,?,?,?,?,?)",
                              ("assessment-x", "synthetic", "00000000000001", 2023, "1", "building-2", "203", 1600))

    def test_parcel_geography_rejects_half_location(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO parcel_geographies VALUES(?,?,?,?,?,?,?)",
                              ("synthetic", "00000000000001", 2023, "17", 42.04, None, 1))


if __name__ == "__main__":
    unittest.main()
