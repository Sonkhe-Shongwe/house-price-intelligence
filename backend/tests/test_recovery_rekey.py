"""Offline GnuPG rekey proof: invented bytes, no database or external storage."""
import json
from pathlib import Path
import secrets
import shutil
import tempfile
import unittest

from backend.recovery_archive import (
    RecoveryRefused, pack_backup, rekey_backup, verify_backup, unpack_backup,
)


class RecoveryRekeyTests(unittest.TestCase):
    def setUp(self):
        # Required tool; absence is a qualification failure, not a skipped pass.
        self.assertIsNotNone(shutil.which("gpg"))
        self.assertIsNotNone(shutil.which("gpgconf"))
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.dump = self.root / "fixture.dump"
        self.seal = self.root / "fixture.json"
        self.dump.write_bytes(b"PGDMP invented fixture only")
        self.seal.write_text(json.dumps({"build_id": "historical-"+"a"*64,
                                         "relational_sha256": "b"*64}))
        self.dump.chmod(0o600)
        self.seal.chmod(0o600)
        self.old, self.new = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        self.source, self.target = self.root/"original.gpg", self.root/"replacement.gpg"
        pack_backup(self.dump, self.seal, self.source, self.old)

    def test_rekey_preserves_source_and_payload(self):
        original = self.source.read_bytes()
        rekey_backup(self.source, self.target, self.old, self.new)
        self.assertEqual(self.source.read_bytes(), original)
        self.assertNotEqual(self.target.read_bytes(), original)
        self.assertEqual(self.target.stat().st_mode & 0o777, 0o600)
        verify_backup(self.source, self.old)
        verify_backup(self.target, self.new)
        with self.assertRaises(RecoveryRefused):
            verify_backup(self.target, self.old)
        self.assertEqual(set(p.name for p in self.root.iterdir()),
                         {"fixture.dump","fixture.json","original.gpg","replacement.gpg"})
        dump, seal = unpack_backup(self.target, self.root/"verified", self.new)
        self.assertEqual(dump.read_bytes(),self.dump.read_bytes())
        self.assertEqual(json.loads(seal.read_text()),json.loads(self.seal.read_text()))

    def test_reject_same_key_wrong_key_or_existing_destination(self):
        original = self.source.read_bytes()
        with self.assertRaises(RecoveryRefused):
            rekey_backup(self.source,self.target,self.old,self.old)
        with self.assertRaises(RecoveryRefused):
            rekey_backup(self.source,self.target,self.new,self.old)
        self.assertFalse(self.target.exists())
        with self.assertRaises(RecoveryRefused):
            rekey_backup(self.source,self.source,self.old,self.new)
        self.target.write_bytes(b"existing")
        with self.assertRaises(RecoveryRefused):
            rekey_backup(self.source,self.target,self.old,self.new)
        self.assertEqual(self.target.read_bytes(),b"existing")
        self.assertEqual(self.source.read_bytes(),original)
