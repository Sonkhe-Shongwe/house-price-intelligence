"""Durable synthetic SQLite recovery, refusal and frozen-evidence integrity tests."""
from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from backend.durable_fixture import FixturePersistenceError, open_file_demo
from backend.schema_migrations import SchemaMigrationError
from backend.synthetic_demo import example_request, in_memory_demo
from backend.synthetic_investigation_store import EvidenceStoreError


class DurableFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "fictional.sqlite"

    def test_create_close_restart_reopens_identical_frozen_evidence(self):
        conn, store = open_file_demo(self.path)
        try:
            saved = store.create(example_request())
            self.assertEqual(saved["selected_count"], 3)
            self.assertIsNone(saved["valuation"])
            self.assertTrue(self.path.is_file())
            self.assertEqual(store.reopen(saved["investigation_id"]), saved)
        finally:
            conn.close()
        second, reopened_store = open_file_demo(self.path)
        try:
            self.assertEqual(reopened_store.reopen(saved["investigation_id"]), saved)
            self.assertEqual(second.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 1)
            self.assertEqual(second.execute("SELECT COUNT(*) FROM source_snapshots").fetchone()[0], 3)
            self.assertEqual(second.execute("PRAGMA user_version").fetchone()[0], 3)
        finally:
            second.close()

    def test_in_memory_mode_remains_disposable(self):
        first, store = in_memory_demo()
        try:
            saved = store.create(example_request())
            self.assertEqual(store.reopen(saved["investigation_id"]), saved)
        finally:
            first.close()
        second, other = in_memory_demo()
        try:
            with self.assertRaisesRegex(EvidenceStoreError, "not found"):
                other.reopen(saved["investigation_id"])
        finally:
            second.close()

    def test_unknown_database_refused_without_overwrite(self):
        with sqlite3.connect(self.path) as conn:
            conn.execute("CREATE TABLE private_source (secret TEXT NOT NULL)")
            conn.execute("INSERT INTO private_source VALUES ('leave unchanged')")
        with self.assertRaises((SchemaMigrationError, FixturePersistenceError)):
            open_file_demo(self.path)
        with sqlite3.connect(self.path) as conn:
            self.assertEqual(conn.execute("SELECT secret FROM private_source").fetchone(),
                             ("leave unchanged",))

    def test_existing_older_schema_is_not_automatically_mutated(self):
        original, _ = in_memory_demo(schema_version=2)
        try:
            disk = sqlite3.connect(self.path)
            try:
                original.backup(disk)
            finally:
                disk.close()
        finally:
            original.close()
        with self.assertRaisesRegex(SchemaMigrationError, "explicit reviewed migration"):
            open_file_demo(self.path)
        with sqlite3.connect(self.path) as conn:
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertIsNone(conn.execute(
                "SELECT name FROM sqlite_master WHERE name='synthetic_address_candidates'"
            ).fetchone())

    def test_modified_fixture_source_manifest_is_rejected_after_restart(self):
        conn, _ = open_file_demo(self.path)
        conn.close()
        with sqlite3.connect(self.path) as untrusted:
            untrusted.execute(
                "UPDATE source_snapshots SET dataset_id='non-synthetic-source' "
                "WHERE snapshot_id='sale-snap'"
            )
        with self.assertRaisesRegex(FixturePersistenceError, "not the original synthetic"):
            open_file_demo(self.path)

    def test_tampered_underlying_sale_is_not_reopened_after_restart(self):
        conn, store = open_file_demo(self.path)
        try:
            saved = store.create(example_request())
        finally:
            conn.close()
        with sqlite3.connect(self.path) as changed:
            changed.execute(
                "UPDATE sale_transactions SET price_usd_cents=price_usd_cents+1 "
                "WHERE transaction_id='txn-2'"
            )
        reopened, store2 = open_file_demo(self.path)
        try:
            with self.assertRaisesRegex(EvidenceStoreError, "sale price"):
                store2.reopen(saved["investigation_id"])
        finally:
            reopened.close()

    def test_nonsqlite_existing_file_is_not_overwritten(self):
        payload = b"not-a-sqlite-database; preserve this file"
        self.path.write_bytes(payload)
        with self.assertRaises(sqlite3.DatabaseError):
            open_file_demo(self.path)
        self.assertEqual(self.path.read_bytes(), payload)

    def test_directory_target_is_rejected(self):
        self.path.mkdir()
        with self.assertRaisesRegex(FixturePersistenceError, "regular"):
            open_file_demo(self.path)


if __name__ == "__main__":
    unittest.main()
