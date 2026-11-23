"""Fabricate a deliberately tiny demo build for loopback-only HTTP tests.

Never touches publisher data or writes to a file. There are no real PINs,
addresses, user identities or sale records in this fixture.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3

from backend.synthetic_investigation_store import SyntheticInvestigationStore

SUBJECT_PIN = "00000000000001"
BUILD_ID = "synthetic-build"
SCHEMA = Path(__file__).with_name("schema_draft.sql")


def in_memory_demo() -> tuple[sqlite3.Connection, SyntheticInvestigationStore]:
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute("PRAGMA foreign_keys = ON")
        for snapshot, role in (("sale-snap", "sales"), ("assess-snap", "assessment"),
                               ("geo-snap", "geography")):
            conn.execute(
                "INSERT INTO source_snapshots (snapshot_id, dataset_id, extracted_at_utc, source_query) VALUES (?,?,?,?)",
                (snapshot, "synthetic-" + role, "2026-11-22T00:00:00Z", "fabricated"),
            )
        conn.execute("INSERT INTO curated_builds VALUES (?,?,?,?)",
                     (BUILD_ID, "2026-11-22T00:00:00Z", "0" * 64, "synthetic_fixture"))
        for snapshot, role in (("sale-snap", "sales"), ("assess-snap", "assessment"),
                               ("geo-snap", "geography")):
            conn.execute("INSERT INTO curated_build_sources VALUES (?,?,?)", (BUILD_ID, snapshot, role))
        for idx in range(1, 5):
            pin = f"{idx:014d}"
            conn.execute("INSERT INTO parcels VALUES (?,?)", (pin, "17"))
            conn.execute("INSERT INTO assessment_records VALUES (?,?,?,?,?,?,?,?)",
                         (f"assessment-{pin}", "assess-snap", pin, 2023, "1", None, "203", 1600))
            conn.execute("INSERT INTO parcel_geographies VALUES (?,?,?,?,?,?,?)",
                         ("geo-snap", pin, 2023, "17", 42.04, -87.68, 1))
            if idx != 1:
                txn = f"txn-{idx}"
                conn.execute("INSERT INTO sale_transactions VALUES (?,?,?,?,?,?)",
                             (txn, "sale-snap", f"row-{idx}", f"DOC-{idx}", "2024-02-01", 52500000))
                conn.execute("INSERT INTO sale_transaction_parcels VALUES(?,?)", (txn, pin))
                conn.execute("INSERT INTO curated_build_transactions VALUES (?,?)", (BUILD_ID, txn))
        # Every label below is fictional. The index is populated only inside
        # the disposable in-memory fixture, never from a publisher dataset.
        for idx in range(1, 5):
            conn.execute(
                "INSERT INTO synthetic_address_index VALUES (?,?,?,?)",
                (f"fictional-{idx}", f"{idx:014d}",
                 f"{100 + idx} Fictional Way, Demonstration District",
                 f"{100 + idx} fictional way demonstration district"),
            )
        conn.commit()
        return conn, SyntheticInvestigationStore(conn, build_id=BUILD_ID)
    except Exception:
        conn.close()
        raise


def example_request():
    return {"township_code": "17", "class_code": "203", "analysis_date": "2024-07-01",
            "subject": {"pin": SUBJECT_PIN, "building_area_sqft": 1600,
                        "asking_price_usd": "500000.00", "label": "Synthetic buyer example"}}
