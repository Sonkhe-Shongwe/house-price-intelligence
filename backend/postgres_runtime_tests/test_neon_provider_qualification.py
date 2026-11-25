"""Offline qualification launcher boundary and lifecycle tests."""
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock,patch
from datetime import datetime,timezone
from backend.neon_provider_qualification import (deadline,bounded_application,
    provider_configuration,open_server,_outside_checkout)
from backend.neon_provider_buyer import MODE


class ProviderQualificationTests(unittest.TestCase):
    def test_deadline_refuses_invalid_and_never_extends_after_clock_change(self):
        end="2026-11-25T12:00:00Z"
        timestamp=datetime(2026,11,25,12,tzinfo=timezone.utc).timestamp()
        wall=[timestamp-60]; steady=[100]
        remaining=deadline(end,clock=lambda:wall[0],steady=lambda:steady[0])
        self.assertEqual(remaining(),60)
        wall[0]-=3600;steady[0]+=61
        self.assertLessEqual(remaining(),0)
        for invalid in ("tomorrow","2026-11-25T12:00:00+00:00","2026-11-25T11:00:00Z","2026-11-25T13:00:01Z"):
            with self.assertRaises(ValueError):
                deadline(invalid,clock=lambda:timestamp,steady=lambda:0)
        wall[0]=timestamp-60;steady[0]=100
        remaining=deadline(end,clock=lambda:wall[0],steady=lambda:steady[0])
        app=MagicMock(return_value=[b"allowed"])
        start=MagicMock()
        guarded=bounded_application(app,remaining)
        self.assertEqual(guarded({},start),[b"allowed"])
        wall[0]=timestamp
        self.assertIn(b"qualification_window_closed",b"".join(guarded({},start)))
        self.assertEqual(app.call_count,1)
        self.assertEqual(start.call_args.args[0],"503 Service Unavailable")

    def test_session_store_isolated_per_window_and_not_identity_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch("backend.neon_provider_qualification.configuration",
                    side_effect=lambda root:{"session_file":root/"sessions-old.sqlite","owner_by_subject":{"auth0|alice":"owner"}}):
                a=provider_configuration(root,"2026-11-25T12:00:00Z")
                b=provider_configuration(root,"2026-11-25T12:00:00Z")
                c=provider_configuration(root,"2026-11-25T13:00:00Z")
                self.assertEqual(a["session_file"],b["session_file"])
                self.assertNotEqual(a["session_file"],c["session_file"])
                self.assertNotEqual(a["session_file"],root/"sessions-old.sqlite")
            with patch("backend.neon_provider_qualification.configuration",return_value={"owner_by_subject":{}}):
                with self.assertRaises(ValueError):provider_configuration(root,"unused")
        with self.assertRaises(ValueError):_outside_checkout(Path(__file__).resolve())

    def test_connection_cleanup_and_deadline_before_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);seal=root/"seal.json";remaining=MagicMock(return_value=60)
            events=[];service=object();boundary=object();exchange=object()
            @contextmanager
            def connect(*args):
                events.append("connections opened")
                try:yield service
                finally:events.append("connections closed")
            server=MagicMock()
            @contextmanager
            def listener(*args,**kwargs):
                events.append("listener opened")
                try:yield server
                finally:events.append("listener closed")
            with patch("backend.neon_provider_qualification.provider_configuration",return_value={}), \
                 patch("backend.neon_provider_qualification._file",return_value=root/"unused"), \
                 patch("backend.neon_provider_qualification.ssl.SSLContext"), \
                 patch("backend.neon_provider_qualification.prepare_auth0",return_value=(boundary,exchange)), \
                 patch("backend.neon_provider_qualification.NeonProviderBuyer._identity_owners"), \
                 patch("backend.neon_provider_qualification.load_react_assets",return_value={}), \
                 patch("backend.neon_provider_qualification.neon_buyer_identity_application",return_value=lambda e,s:[]), \
                 patch("backend.neon_provider_qualification.open_neon_provider_buyer",side_effect=connect) as opened, \
                 patch("backend.neon_provider_qualification.make_server",side_effect=listener) as listen:
                settings={"HPI_NEON_MODE":MODE}
                remaining.return_value=0
                with self.assertRaises(ValueError),open_server(root,seal,"unused","fictional",settings,remaining=remaining):
                    pass
                opened.assert_not_called()
                remaining.return_value=60
                with self.assertRaises(RuntimeError),open_server(root,seal,"unused","fictional",settings,remaining=remaining) as running:
                    self.assertIs(running,server)
                    raise RuntimeError("simulated operator failure")
                self.assertEqual(events,["connections opened","listener opened","listener closed","connections closed"])
                self.assertEqual(listen.call_args.args[:2],("127.0.0.1",8766))
