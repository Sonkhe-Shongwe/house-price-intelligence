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

    def test_execute_requires_ci_review_before_workspace_or_network(self):
        with patch.object(launch,"workspace") as ws, patch.object(launch,"_fetch") as fetch:
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                rc=launch.main(["--execute","--reviewed-commit","a"*40])
            self.assertEqual(rc,1)
            self.assertEqual(json.loads(stdout.getvalue())["reason"],"exact_ci_review_required")
            ws.assert_not_called()
            fetch.assert_not_called()

    def test_preflight_reports_swap_without_acquisition(self):
        for absent,locked in ((True,False),(False,False),(False,True)):
            with tempfile.TemporaryDirectory() as tmp, patch.object(launch,"git_clean_exact"), \
                    patch.object(launch,"supervised",return_value={"status":"completed",
                        "result":{"core_dumps_disabled":True,"process_dumpable":False,
                                  "guest_swap_absent":absent,"memory_lock_verified":locked}}):
                result=launch.preflight(Path(tmp),"a"*40)
                self.assertEqual(result["preflight_passed"],absent or locked)
                self.assertFalse(result["attempt_consumed"])
                self.assertFalse(result["host_protection_independently_verified"])
                self.assertEqual(result["record_requests"],0)

    def test_preflight_rejects_invalid_worker(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(launch,"git_clean_exact"), \
                patch.object(launch,"supervised",return_value={"status":"completed",
                   "result":{"core_dumps_disabled":False,"process_dumpable":False,
                             "guest_swap_absent":True,"memory_lock_verified":False}}):
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


    def test_swap_alternative_requires_worker_lock(self):
        controls={"core_dumps_disabled":True,"process_dumpable":False}
        with patch.object(launch,"non_dumpable_worker",return_value=controls), \
                patch.object(launch,"guest_swap_absent",return_value=False), \
                patch.object(launch,"lock_current_and_future",return_value=True) as lock:
            self.assertTrue(launch.protection_probe()["memory_lock_verified"])
            lock.assert_called_once_with()
        with patch.object(launch,"non_dumpable_worker",return_value=controls), \
                patch.object(launch,"guest_swap_absent",return_value=False), \
                patch.object(launch,"lock_current_and_future",
                             side_effect=QualificationError("memory_lock_refused")):
            with self.assertRaises(QualificationError):
                launch.protection_probe()

    def test_no_swap_does_not_require_lock(self):
        with patch.object(launch,"non_dumpable_worker",return_value={
                "core_dumps_disabled":True,"process_dumpable":False}), \
                patch.object(launch,"guest_swap_absent",return_value=True), \
                patch.object(launch,"lock_current_and_future") as lock:
            self.assertFalse(launch.protection_probe()["memory_lock_verified"])
            lock.assert_not_called()

    def test_memory_status_strict(self):
        for data,expected in (("VmLck:\t1024 kB\nVmSwap:\t0 kB\n",(1048576,0)),
                              ("VmLck: 1 kB\nVmSwap: 2 kB\n",(1024,2048))):
            with patch("builtins.open",return_value=io.StringIO(data)):
                self.assertEqual(launch.memory_status(),expected)
        for bad in ("VmLck: 1 kB\n","VmLck: -1 kB\nVmSwap: 0 kB\n",
                    "VmLck: 1 kB\nVmLck: 2 kB\nVmSwap: 0 kB\n"):
            with patch("builtins.open",return_value=io.StringIO(bad)):
                with self.assertRaises(QualificationError):
                    launch.memory_status()

    def test_lock_syscall_refusal_and_future_mapping(self):
        from unittest.mock import MagicMock
        libc=MagicMock()
        with patch.object(launch.sys,"platform","linux"), \
                patch("ctypes.CDLL",return_value=libc), \
                patch("resource.getrlimit",return_value=(64*1024*1024,)*2), \
                patch.object(launch,"memory_status",side_effect=[(4096,0),(1052672,0)]), \
                patch("mmap.mmap") as mapping:
            libc.mlockall.return_value=0
            self.assertTrue(launch.lock_current_and_future())
            libc.mlockall.assert_called_once_with(3)
            mapping.assert_called_once()
        for observations in ([(4096,1024)],[(4096,0),(4096,0)]):
            with patch.object(launch.sys,"platform","linux"), \
                    patch("ctypes.CDLL",return_value=libc), \
                    patch("resource.getrlimit",return_value=(64*1024*1024,)*2), \
                    patch.object(launch,"memory_status",side_effect=observations), \
                    patch("mmap.mmap"):
                with self.assertRaises(QualificationError):
                    launch.lock_current_and_future()
        libc.mlockall.return_value=-1
        with patch.object(launch.sys,"platform","linux"), patch("ctypes.CDLL",return_value=libc):
            with self.assertRaisesRegex(QualificationError,"memory_lock_refused"):
                launch.lock_current_and_future()


    def test_fixed_transport_refuses_other_source_and_query(self):
        from urllib.parse import urlencode
        resource=f"/resource/{frame.DATASET}.json"
        good=[f"/api/views/{frame.DATASET}.json",
              resource+"?"+urlencode(frame.count_parameters()),
              resource+"?"+urlencode(frame.row_parameters(10))]
        with patch.object(launch,"https_response") as tls:
            for path in good:
                launch.fixed_response(path,15)
            self.assertEqual(tls.call_count,3)
            for path in ("/api/views/usep-8jbt.json",good[2]+"&x=1",
                         resource+"?%24select=owner&%24limit=10"):
                with self.assertRaises(QualificationError):
                    launch.fixed_response(path,15)
            self.assertEqual(tls.call_count,3)

    def test_actual_worker_order_and_aggregate_result(self):
        from backend.tests.test_nyc_address_frame_transport import Script, metadata, row
        context={"attribution":launch.AGENCY,"attributionLink":launch.AGENCY_LINK,
                 "description":launch.AGENCY_LINK+" Current version: 26v3",
                 "metadata":{"custom_fields":{"Dataset Information":{"Agency":launch.AGENCY},
                    "Update":{"Automation":"Yes","Data Change Frequency":"Quarterly",
                              "Update Frequency":"Quarterly"}}}}
        m=metadata(**context)
        script=Script([m,[{"n":"1"}],[row()],[{"n":"1"}],m])
        order=[]
        def guarded(path,timeout):
            self.assertEqual(order,["locked"])
            return script(path,timeout)
        def locked():
            order.append("locked")
            return True
        with patch.object(launch,"non_dumpable_worker",return_value={
                "core_dumps_disabled":True,"process_dumpable":False}), \
                patch.object(launch,"guest_swap_absent",return_value=False), \
                patch.object(launch,"lock_current_and_future",side_effect=locked), \
                patch.object(launch,"memory_status",return_value=(4096,0)), \
                patch.object(launch,"https_response",side_effect=guarded):
            result=launch.actual_worker()
        self.assertEqual(len(script.calls),5)
        self.assertTrue(result["recorded_frame_qualified"])
        self.assertFalse(result["fixture_only"])
        self.assertFalse(result["actual_entry_verified"])
        self.assertNotIn("INVENTED",json.dumps(result))

    def test_notice_drift_refuses_before_count(self):
        from backend.tests.test_nyc_address_frame_transport import Script, metadata
        script=Script([metadata(termsOfUse="invented restriction")])
        with patch.object(launch,"https_response",side_effect=script):
            with self.assertRaisesRegex(QualificationError,"frame_rehearsal_refused"):
                launch._EntrySession().run()
        self.assertEqual(len(script.calls),1)

    def test_actual_worker_refuses_lock_failure_before_network(self):
        with patch.object(launch,"non_dumpable_worker",return_value={
                "core_dumps_disabled":True,"process_dumpable":False}), \
                patch.object(launch,"guest_swap_absent",return_value=False), \
                patch.object(launch,"lock_current_and_future",return_value=False), \
                patch.object(launch,"https_response") as tls:
            with self.assertRaisesRegex(QualificationError,"memory_lock_refused"):
                launch.actual_worker()
            tls.assert_not_called()

    @unittest.skipUnless(os.name=="posix","POSIX marker")
    def test_execute_consumes_before_worker_and_retains_on_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            def timeout(task,seconds):
                self.assertIs(task,launch.actual_worker)
                self.assertEqual(seconds,180)
                self.assertTrue((directory/launch.MARKER).exists())
                raise QualificationError("hard_deadline")
            with patch.object(launch,"workspace",return_value=directory), \
                    patch.object(launch,"preflight",return_value={"preflight_passed":True}), \
                    patch.object(launch,"supervised",side_effect=timeout) as worker:
                result=launch.execute_reviewed(directory,"a"*40)
                self.assertEqual(result,{"status":"blocked","reason":"entry_session_refused",
                                         "attempt_consumed":True})
                with self.assertRaisesRegex(QualificationError,"attempt_already_consumed"):
                    launch.execute_reviewed(directory,"a"*40)
                worker.assert_called_once()

    def test_failed_preflight_never_consumes_or_launches(self):
        directory=Path("/invented")
        with patch.object(launch,"workspace",return_value=directory), \
                patch.object(launch,"preflight",return_value={"preflight_passed":False}), \
                patch.object(launch,"consume") as marker, \
                patch.object(launch,"supervised") as worker:
            with self.assertRaisesRegex(QualificationError,"process_protection_unverified"):
                launch.execute_reviewed(directory,"a"*40)
            marker.assert_not_called()
            worker.assert_not_called()

    def test_completed_zero_unique_is_no_go(self):
        directory=Path("/invented")
        with patch.object(launch,"workspace",return_value=directory), \
                patch.object(launch,"preflight",return_value={"preflight_passed":True}), \
                patch.object(launch,"consume"), \
                patch.object(launch,"supervised",return_value={"status":"completed","result":{
                    "contract":"nyc-address-frame-actual-v1","fixture_only":False,
                    "recorded_frame_qualified":False}}):
            result=launch.execute_reviewed(directory,"a"*40)
            self.assertEqual(result["status"],"no_go")
            self.assertTrue(result["attempt_consumed"])


if __name__=="__main__":
    unittest.main()
