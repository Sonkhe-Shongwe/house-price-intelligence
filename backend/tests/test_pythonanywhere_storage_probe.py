"""Local SQLite lock and rollback evidence, not hosted filesystem evidence."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.durable_fixture import open_file_demo
from backend.synthetic_demo import example_request


class PythonAnywhereStorageProbe(unittest.TestCase):
    def test_contended_writer_fails_and_rollback_preserves_fixture(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invented.sqlite"
            a, store = open_file_demo(path, private_file=True)
            try:
                saved = store.create(example_request())
                b, other = open_file_demo(path, private_file=True)
                try:
                    b.execute("PRAGMA busy_timeout=0")
                    a.execute("BEGIN IMMEDIATE")
                    a.execute("UPDATE investigation_results SET result_sha256=? WHERE investigation_id=?",
                              ("0"*64, saved["investigation_id"]))
                    with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                        b.execute("BEGIN IMMEDIATE")
                    self.assertEqual(other.reopen(saved["investigation_id"]), saved)
                    a.rollback()
                    b.execute("BEGIN IMMEDIATE")
                    b.rollback()
                    self.assertEqual(other.reopen(saved["investigation_id"]), saved)
                finally:
                    b.close()
            finally:
                a.close()
            c, reopened = open_file_demo(path, private_file=True)
            try:
                self.assertEqual(reopened.reopen(saved["investigation_id"]), saved)
            finally:
                c.close()
