import json
import os
from pathlib import Path
import tempfile
import unittest
from backend.curated_ingestion_candidate import ImportRefused
from backend.historical_seal_config import load_historical_seal

@unittest.skipUnless(os.name=="posix","POSIX private file boundary")
class SealConfigTests(unittest.TestCase):
    def test_private_file_and_rejections(self):
        seal={"build_id":"historical-"+"a"*64,"relational_sha256":"b"*64}
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"seal.json"
            p.write_text(json.dumps(seal));p.chmod(0o600)
            self.assertEqual(load_historical_seal(p),seal)
            p.chmod(0o644)
            with self.assertRaises(ImportRefused):load_historical_seal(p)
            p.chmod(0o600)
            alias=Path(root)/"alias"
            alias.symlink_to(p)
            with self.assertRaises(ImportRefused):load_historical_seal(alias)
            alias.unlink()
            os.link(p,alias)
            with self.assertRaises(ImportRefused):load_historical_seal(p)
            alias.unlink()
            for value in (json.dumps(dict(seal,public_display_approved=True)),
                          '{"build_id":"bad","build_id":"other","relational_sha256":"bad"}',
                          "x"*4097):
                p.write_text(value)
                with self.assertRaises(ImportRefused):load_historical_seal(p)
            p.write_text(json.dumps(seal));Path(root).chmod(0o755)
            with self.assertRaises(ImportRefused):load_historical_seal(p)
            Path(root).chmod(0o700)
