"""Offline launcher contract tests. No HTTP, credentials, real workspace or records."""
from datetime import date
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from tools.nyc_launch import (
    validate_manifest, private_directory, consume, supervised, MARKER, main,
)
from tools.nyc_qualification import FIELDS, projection, QualificationError


@unittest.skipUnless(os.name == "posix", "POSIX supervisor")
class LauncherTests(unittest.TestCase):
    def manifest(self):
        return dict(reviewed_commit="a"*40, source_review="invented",
                    protection_review="invented", ci_review="invented",
                    cutoff="2026-11-27", covered_from="2025-11-27",
                    covered_through="2026-10-31", snapshot="2026-11-23",
                    version="26v3", sources={
                        d: {"revision": "1:2", "types": {
                            f: "text" for f in projection(d, subject=d == "64uk-42ks")}}
                        for d in FIELDS})

    def test_exact_manifest_shape(self):
        raw = self.manifest()
        plan, pins = validate_manifest(raw, date(2026, 11, 27))
        self.assertEqual(plan.mode, "current_snapshot")
        self.assertFalse(plan.historical_area_verified)
        self.assertEqual(pins, raw["sources"])
        for key, value in (("cutoff", "2026-11-26"),
                           ("covered_through", "2026-11-27"),
                           ("version", "other"), ("source_review", "")):
            with self.subTest(key=key), self.assertRaises(QualificationError):
                validate_manifest(dict(raw, **{key:value}), date(2026, 11, 27))
        raw["sources"]["64uk-42ks"]["types"]["owner"] = "text"
        with self.assertRaisesRegex(QualificationError, "invalid_reviewed_sources"):
            validate_manifest(raw, date(2026, 11, 27))

    def test_attempt_marker_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            consume(directory, "a"*40)
            self.assertEqual((directory / MARKER).stat().st_mode & 0o777, 0o600)
            with self.assertRaisesRegex(QualificationError, "attempt_already_consumed"):
                consume(directory, "a"*40)

    def test_workspace_checks_and_ci_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve()
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(private_directory(directory), directory)
                directory.chmod(0o755)
                with self.assertRaisesRegex(QualificationError, "private_directory_permissions"):
                    private_directory(directory)
            with patch.dict(os.environ, {"CI":"true"}):
                with self.assertRaisesRegex(QualificationError, "ci_forbidden"):
                    private_directory(directory)

    def test_watchdog_and_redaction(self):
        self.assertEqual(supervised(lambda: {"count": 3}, 2),
                         {"status":"completed", "result":{"count":3}})
        def crash():
            raise RuntimeError("INVENTED PRIVATE RECORD")
        self.assertEqual(supervised(crash, 2),
                         {"status":"blocked", "reason":"worker_failure"})
        with self.assertRaisesRegex(QualificationError, "hard_deadline"):
            supervised(lambda: time.sleep(5), .1)

    def test_no_live_activation_even_with_structural_plan(self):
        with patch("tools.nyc_launch.private_directory", return_value=Path("/invented")), \
             patch("tools.nyc_launch.read_manifest", return_value=self.manifest()), \
             patch("tools.nyc_launch.validate_manifest", return_value=(None, None)), \
             patch("tools.nyc_launch.git_clean_exact"), \
             patch("tools.nyc_launch.live_report") as live, \
             patch("tools.nyc_launch.consume") as marker, \
             patch("builtins.print") as output:
            self.assertEqual(main(["--workspace", "/invented", "--execute"]), 1)
            live.assert_not_called()
            marker.assert_not_called()
            self.assertIn("live_activation_not_accepted", output.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
