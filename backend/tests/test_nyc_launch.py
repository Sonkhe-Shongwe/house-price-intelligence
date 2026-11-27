"""Offline launcher contract tests. No HTTP, credentials, real workspace or records."""
from datetime import date
from dataclasses import replace
import sys
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from tools.nyc_launch import (
    validate_manifest, private_directory, consume, supervised, MARKER, main,
    reviewed_plan, enforce_fixed_plan, execute_reviewed, disposable_preflight,
    non_dumpable_worker, fixed_sources,
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

    def test_fixed_plan_refuses_scope_and_revision_changes(self):
        today = date(2026, 11, 27)
        plan, sources = reviewed_plan(today)
        enforce_fixed_plan(plan, sources, today)
        self.assertEqual(plan.version, "26v3")
        self.assertEqual(plan.covered_from, date(2025, 11, 1))
        self.assertEqual(plan.covered_through, date(2026, 10, 31))
        for modified in (replace(plan, version="26v4"),
                         replace(plan, covered_from=date(2025, 10, 1)),
                         replace(plan, historical_area_verified=True)):
            with self.assertRaisesRegex(QualificationError, "reviewed_plan_conflict"):
                enforce_fixed_plan(modified, sources, today)
        changed = fixed_sources()
        changed["usep-8jbt"]["revision"] = "1:2"
        with self.assertRaisesRegex(QualificationError, "reviewed_plan_conflict"):
            enforce_fixed_plan(plan, changed, today)

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux worker controls")
    def test_worker_process_controls(self):
        self.assertEqual(supervised(non_dumpable_worker, 2),
                         {"status": "completed", "result": {
                             "core_dumps_disabled": True, "process_dumpable": False}})

    def test_execution_wiring_and_marker_order(self):
        today = date(2026, 11, 27)
        plan, sources = reviewed_plan(today)
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            calls = []
            def fake_supervisor(task):
                if task is non_dumpable_worker:
                    return {"status": "completed", "result": {
                        "core_dumps_disabled": True, "process_dumpable": False}}
                self.assertTrue((workspace / MARKER).is_file())
                return {"status": "completed", "result": task()}
            def fake_live(p, s):
                calls.append((p, s))
                return {"subject_count": 30}
            with patch("tools.nyc_launch.canonical_workspace", return_value=workspace), \
                 patch("tools.nyc_launch.supervised", side_effect=fake_supervisor), \
                 patch("tools.nyc_launch.live_report", side_effect=fake_live):
                self.assertEqual(execute_reviewed(workspace, plan, sources, "a"*40, today),
                                 {"status":"completed", "result":{"subject_count":30}})
                with self.assertRaisesRegex(QualificationError, "attempt_already_consumed"):
                    execute_reviewed(workspace, plan, sources, "a"*40, today)
                self.assertEqual(len(calls), 1)

    def test_plan_preflight_never_consumes_or_dispatches_records(self):
        today = date(2026, 11, 27)
        plan, sources = reviewed_plan(today)
        workspace = Path("/invented")
        with patch("tools.nyc_launch.canonical_workspace", return_value=workspace), \
             patch("tools.nyc_launch.supervised", return_value={"status":"completed"}) as runner, \
             patch("tools.nyc_launch.consume") as marker, \
             patch("tools.nyc_launch.live_report") as live:
            disposable_preflight(workspace, plan, sources, today)
            runner.assert_called_once()
            marker.assert_not_called()
            live.assert_not_called()
            with self.assertRaisesRegex(QualificationError, "noncanonical_workspace"):
                disposable_preflight(Path("/other"), plan, sources, today)

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
