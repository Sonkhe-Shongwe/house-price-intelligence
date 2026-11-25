"""Offline cloud target/fixture guard tests; never connect to Neon."""
import unittest
from unittest.mock import MagicMock,patch
from backend.neon_synthetic_seed import fixture_plan,seed_statements
from backend.neon_synthetic_journey import NeonSyntheticJourney,open_neon_synthetic_journey,MODE
from backend.curated_ingestion_candidate import ImportRefused
from backend.private_beta_rehearsal import PrivateBetaRehearsal
from backend.historical_reader import ROLE
from backend.neon_preflight import DATABASE

HOST="ep-example-fictional.c-10.eu-central-1.aws.neon.tech"


class NeonSyntheticJourneyTests(unittest.TestCase):
    def test_seed_is_fixed_and_guarded(self):
        first=seed_statements()
        self.assertEqual(first,seed_statements())
        self.assertEqual(len(fixture_plan()[2]["sale_transactions"]),4)
        self.assertIn("hpi_private_owner",first[2])
        self.assertIn("hpi_ingest_fixture",seed_statements(disposable=True)[2])
        self.assertIn("ACCESS EXCLUSIVE",first[5])
        self.assertIn("NOT rolcanlogin",first[6])
        self.assertFalse(any(s.lstrip().upper().startswith(("DELETE","UPDATE","DROP","ALTER","TRUNCATE")) for s in first))

    @patch("backend.neon_synthetic_journey.psycopg.connect")
    def test_refuse_implicit_mode_and_unapproved_build(self,connect):
        with self.assertRaises(ImportRefused),open_neon_synthetic_journey({},"unused",None):
            pass
        with patch("backend.neon_synthetic_journey.load_historical_seal",return_value={"build_id":"historical-"+"0"*64,"relational_sha256":"1"*64}):
            with self.assertRaises(ImportRefused),open_neon_synthetic_journey({"HPI_NEON_MODE":MODE},"unused",None):
                pass
        connect.assert_not_called()

    @patch("backend.neon_synthetic_journey._identity")
    def test_strict_cloud_connection_guard(self,identity):
        svc=NeonSyntheticJourney.__new__(NeonSyntheticJourney)
        svc.expected_host=HOST
        conn=MagicMock()
        conn.autocommit=True
        conn.info.host=HOST;conn.info.port=5432;conn.info.dbname=DATABASE;conn.info.user=ROLE
        conn.pgconn.ssl_in_use=True
        p={"sslmode":"verify-full","sslrootcert":"system","channel_binding":"require","gssencmode":"disable"}
        conn.info.get_parameters.return_value=p
        svc._check_connection(conn,ROLE)
        identity.assert_called_once_with(conn,ROLE,DATABASE)
        identity.reset_mock()
        for key,bad in (("sslmode","require"),("channel_binding","prefer"),("sslrootcert","other"),("gssencmode","prefer")):
            conn.info.get_parameters.return_value=dict(p,**{key:bad})
            with self.assertRaises(ImportRefused):svc._check_connection(conn,ROLE)
        conn.info.get_parameters.return_value=p
        conn.pgconn.ssl_in_use=False
        with self.assertRaises(ImportRefused):svc._check_connection(conn,ROLE)
        conn.pgconn.ssl_in_use=True
        conn.info.host="ep-other.c-10.eu-central-1.aws.neon.tech"
        with self.assertRaises(ImportRefused):svc._check_connection(conn,ROLE)
        identity.assert_not_called()
        # The original loopback class still refuses cloud connections.
        with self.assertRaises(ImportRefused):PrivateBetaRehearsal._check_connection(conn,ROLE)
