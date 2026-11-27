"""Invented metadata and mocked worker controls; no network."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import nyc_entry_launch as launch
from tools import nyc_address_frame as frame
from tools.nyc_qualification import QualificationError


def payload(**extra):
    a,b=map(int,frame.REVISION.split(":"))
    raw={"id":frame.DATASET,"rowsUpdatedAt":a,"viewLastModified":b,
         "description":"Invented public description","attribution":"Invented agency",
         "attributionLink":"https://www.nyc.gov/site/planning/index.page",
         "metadata":{"custom_fields":{"Dataset Information":{"Agency":"Invented"}}},
         "columns":[{"cachedContents":{"top":["NEVER RETURN"]}}],
         "owner":{"name":"NEVER RETURN"}}
    raw.update(extra)
    return json.dumps(raw).encode()


class EntryLauncherTests(unittest.TestCase):
    def test_exact_context_and_excluded_values(self):
        result=launch.notice_context(payload())
        self.assertEqual(result["revision"],frame.REVISION)
        self.assertEqual(result["custom_fields"]["Dataset Information"]["Agency"],"Invented")
        self.assertNotIn("NEVER RETURN",json.dumps(result))
        self.assertEqual(result["record_requests"],0)
        self.assertTrue(result["manual_review_required"])

    def test_context_refuses_wrong_pin_or_shape(self):
        for bad in (payload(id="wrong"),payload(rowsUpdatedAt=1),payload(rows=[]),
                    payload(description="x"*(launch.MAX_CONTEXT+1)),
                    payload(metadata={"custom_fields":{"A":{"B":["nested"]}}})):
            with self.assertRaises(QualificationError):
                launch.notice_context(bad)

    def test_execute_disabled_before_workspace_or_network(self):
        with patch.object(launch,"workspace") as ws, patch.object(launch,"_fetch") as fetch:
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc=launch.main(["--execute","--reviewed-commit","a"*40])
            self.assertEqual(rc,1)
            self.assertEqual(json.loads(stdout.getvalue())["reason"],"activation_pending")
            ws.assert_not_called()
            fetch.assert_not_called()

    def test_preflight_reports_swap_without_acquisition(self):
        for absent in (True,False):
            with tempfile.TemporaryDirectory() as tmp, patch.object(launch,"git_clean_exact"), \
                    patch.object(launch,"supervised",return_value={"status":"completed",
                        "result":{"core_dumps_disabled":True,"process_dumpable":False,
                                  "guest_swap_absent":absent}}):
                result=launch.preflight(Path(tmp),"a"*40)
                self.assertEqual(result["preflight_passed"],absent)
                self.assertFalse(result["attempt_consumed"])
                self.assertFalse(result["host_protection_independently_verified"])
                self.assertEqual(result["record_requests"],0)

    def test_preflight_rejects_invalid_worker(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(launch,"git_clean_exact"), \
                patch.object(launch,"supervised",return_value={"status":"completed",
                   "result":{"core_dumps_disabled":False,"process_dumpable":False,
                             "guest_swap_absent":True}}):
            with self.assertRaises(QualificationError):
                launch.preflight(Path(tmp),"a"*40)

    @unittest.skipUnless(os.name=="posix","POSIX marker")
    def test_new_marker_preserves_old_and_refuses_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            old=directory/"nyc-qualification-2026-11-27.consumed"
            old.write_text("preserve")
            launch.consume(directory,"a"*40)
            self.assertEqual(old.read_text(),"preserve")
            self.assertEqual((directory/launch.MARKER).stat().st_mode & 0o777,0o600)
            with self.assertRaisesRegex(QualificationError,"attempt_already_consumed"):
                launch.consume(directory,"a"*40)
            with patch.object(launch,"git_clean_exact"):
                with self.assertRaisesRegex(QualificationError,"attempt_already_consumed"):
                    launch.preflight(directory,"a"*40)

    def test_guest_swap_probe(self):
        header="Filename Type Size Used Priority\n"
        for data,expected in ((header,True),(header+"/dev/invented file 1 0 -2\n",False)):
            with patch("builtins.open",return_value=io.StringIO(data)):
                self.assertEqual(launch.guest_swap_absent(),expected)
        with patch("builtins.open",return_value=io.StringIO("bad\n")):
            with self.assertRaises(QualificationError):
                launch.guest_swap_absent()

    def test_private_interactive_review_required(self):
        with patch.object(launch,"workspace",return_value=Path("/invented")), \
                patch.object(launch,"git_clean_exact"), patch.object(launch,"_fetch") as fetch:
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc=launch.main(["--review-notices","--reviewed-commit","a"*40])
            self.assertEqual(rc,1)
            self.assertEqual(json.loads(stdout.getvalue())["reason"],
                             "private_interactive_review_required")
            fetch.assert_not_called()


if __name__=="__main__":
    unittest.main()
