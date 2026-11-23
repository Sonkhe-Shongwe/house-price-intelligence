"""Synthetic-only versioning, source identity and transactional migration safety."""
from __future__ import annotations

import sqlite3
import unittest
from unittest.mock import patch

from backend import schema_migrations
from backend.schema_migrations import (
    CURRENT_SCHEMA_VERSION,
    SchemaMigrationError,
    migrate_fixture,
)
from backend.synthetic_demo import example_request, in_memory_demo


class FixtureMigrationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")

    def tearDown(self):
        self.db.close()

    def test_clean_create_version_history_and_idempotent_reapply(self):
        self.assertEqual(migrate_fixture(self.db), CURRENT_SCHEMA_VERSION)
        rows = self.db.execute(
            "SELECT version, script_sha256 FROM schema_migrations ORDER BY version"
        ).fetchall()
        self.assertEqual([r[0] for r in rows], [1, 2, 3])
        self.assertTrue(all(len(r[1]) == 64 for r in rows))
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone()[0], 3)
        self.assertEqual(self.db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(migrate_fixture(self.db), CURRENT_SCHEMA_VERSION)
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM schema_migrations"
        ).fetchone()[0], 2)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_upgrade_populated_fixture_retains_frozen_investigations(self):
        self.db.close()
        self.db, store = in_memory_demo(schema_version=1)
        saved = store.create(example_request(), investigation_id="saved-fixture")
        source_before = self.db.execute(
            "SELECT transaction_id, price_usd_cents FROM sale_transactions ORDER BY transaction_id"
        ).fetchall()
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone()[0], 1)
        self.assertEqual(migrate_fixture(self.db), 3)
        self.assertEqual(store.reopen("saved-fixture"), saved)
        self.assertEqual(self.db.execute(
            "SELECT transaction_id, price_usd_cents FROM sale_transactions ORDER BY transaction_id"
        ).fetchall(), source_before)
        indexes = {name for (name,) in self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )}
        self.assertIn("idx_fixture_sale_link_parcel", indexes)
        self.assertIn("idx_fixture_assessment_parcel_year", indexes)

    def test_v2_to_v3_backfills_original_address_ids_without_loss(self):
        self.db.close()
        self.db, store = in_memory_demo(schema_version=2)
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertEqual(migrate_fixture(self.db), 3)
        result = store.search_synthetic_addresses("Fictional Way")
        self.assertEqual(len(result["candidates"]), 4)
        self.assertTrue(all(not x["ambiguous_address"] for x in result["candidates"]))
        self.assertEqual(store.resolve_synthetic_address("fictional-1")["pin"],
                         "00000000000001")
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_v3_allows_shared_street_label_and_multiple_aliases(self):
        self.db.close()
        self.db, store = in_memory_demo()
        options = store.search_synthetic_addresses("105 Fictional Court")["candidates"]
        self.assertEqual(len(options), 2)
        self.assertEqual(len({x["display_address"] for x in options}), 1)
        self.assertTrue(all(x["ambiguous_address"] for x in options))
        self.assertEqual(len({store.resolve_synthetic_address(x["address_id"])["pin"]
                              for x in options}), 2)
        self.db.execute(
            "INSERT INTO synthetic_address_candidates VALUES (?,?,?,?,?)",
            ("alternate-1", "Alternate Fictional Street, Demo",
             "alternate fictional street demo", "00000000000001", "Alias"),
        )
        self.assertEqual(store.resolve_synthetic_address("alternate-1")["pin"], "00000000000001")

    def test_unversioned_database_rejected_without_modification(self):
        self.db.execute("CREATE TABLE external_records(secret TEXT)")
        self.db.execute("INSERT INTO external_records VALUES ('keep')")
        self.db.commit()
        with self.assertRaisesRegex(SchemaMigrationError, "Unversioned"):
            migrate_fixture(self.db)
        self.assertEqual(self.db.execute(
            "SELECT secret FROM external_records"
        ).fetchone()[0], "keep")
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone()[0], 0)
        self.assertIsNone(self.db.execute(
            "SELECT name FROM sqlite_master WHERE name='schema_migrations'"
        ).fetchone())

    def test_modified_history_and_unknown_version_are_rejected(self):
        migrate_fixture(self.db, target_version=1)
        self.db.execute("UPDATE schema_migrations SET script_sha256=? WHERE version=1",
                        ("x" * 64,))
        self.db.commit()
        with self.assertRaisesRegex(SchemaMigrationError, "checksum"):
            migrate_fixture(self.db)
        self.db.execute(
            "UPDATE schema_migrations SET script_sha256=? WHERE version=1",
            (schema_migrations._script_digest(schema_migrations._load_script(1)),),
        )
        self.db.execute("PRAGMA user_version=99")
        self.db.commit()
        with self.assertRaisesRegex(SchemaMigrationError, "schema version"):
            migrate_fixture(self.db)

    def test_downgrade_or_open_transaction_is_refused(self):
        migrate_fixture(self.db)
        with self.assertRaisesRegex(SchemaMigrationError, "Downgrade"):
            migrate_fixture(self.db, target_version=1)
        self.db.execute("CREATE TABLE scratch_data (item TEXT)")
        self.db.execute("INSERT INTO scratch_data VALUES ('keep')")
        with self.assertRaisesRegex(SchemaMigrationError, "open transaction"):
            migrate_fixture(self.db)
        self.assertEqual(self.db.execute(
            "SELECT item FROM scratch_data"
        ).fetchone()[0], "keep")

    def test_failed_upgrade_rolls_back_schema_and_version(self):
        migrate_fixture(self.db, target_version=1)
        original = schema_migrations._load_script
        def broken_script(version):
            if version == 2:
                return (
                    "CREATE INDEX idx_fixture_temp ON parcels(pin);\n"
                    "INSERT INTO missing_upgrade_table VALUES (1);"
                )
            return original(version)
        with patch.object(schema_migrations, "_load_script", side_effect=broken_script):
            with self.assertRaisesRegex(SchemaMigrationError, "migration 2 failed"):
                migrate_fixture(self.db)
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone()[0], 1)
        self.assertEqual(self.db.execute(
            "SELECT version FROM schema_migrations"
        ).fetchall(), [(1,)])
        self.assertIsNone(self.db.execute(
            "SELECT name FROM sqlite_master WHERE name='idx_fixture_temp'"
        ).fetchone())
        self.assertEqual(migrate_fixture(self.db, target_version=2), 2)

    def test_schema_version_must_be_integer_and_valid(self):
        for bad in (0, -1, 4, True, "2", 1.0):
            with self.subTest(bad=bad), self.assertRaises(SchemaMigrationError):
                migrate_fixture(self.db, target_version=bad)
        self.assertFalse(self.db.execute(
            "SELECT name FROM sqlite_master WHERE name='schema_migrations'"
        ).fetchone())


if __name__ == "__main__":
    unittest.main()
