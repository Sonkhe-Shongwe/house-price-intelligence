from pathlib import Path
import tempfile
import unittest
from backend.react_assets import load_react_assets
from backend.durable_fixture import open_file_demo, FixturePersistenceError
import sqlite3
import os

class ReactAssetTests(unittest.TestCase):
    def test_exact_assets_only_and_reject_unknown_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"index.html").write_text("<html></html>")
            (root/"assets").mkdir()
            (root/"assets"/"index-abc12345.js").write_text("void 0")
            assets=load_react_assets(root)
            self.assertEqual(set(assets),{"/","/buyer-workflow","/assets/index-abc12345.js"})
            (root/"assets"/"private.txt").write_text("not a build asset")
            with self.assertRaises(ValueError):
                load_react_assets(root)

    def test_private_fixture_rejects_unselected_source_tamper(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"fixture.sqlite3"
            conn,_=open_file_demo(path,private_file=True)
            conn.close()
            with sqlite3.connect(path) as conn:
                conn.execute("UPDATE sale_transactions SET price_usd_cents=price_usd_cents+1 WHERE transaction_id='txn-2'")
            before=path.read_bytes()
            with self.assertRaisesRegex(FixturePersistenceError,"trusted seed"):
                open_file_demo(path,private_file=True)
            self.assertEqual(path.read_bytes(),before)

    @unittest.skipUnless(os.name=="posix","POSIX mode check")
    def test_private_fixture_rejects_world_readable_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"fixture.sqlite3"
            conn,_=open_file_demo(path,private_file=True)
            conn.close()
            path.chmod(0o644)
            with self.assertRaisesRegex(FixturePersistenceError,"private"):
                open_file_demo(path,private_file=True)
