"""Offline cloud target/fixture guard tests; never connect to Neon."""
import unittest
import psycopg
from unittest.mock import MagicMock,patch
from backend.neon_synthetic_seed import fixture_plan,seed_statements
from backend.neon_synthetic_journey import NeonSyntheticJourney,open_neon_synthetic_journey,_connect_service,MODE
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

    def test_provider_cloud_mode_and_owner_guards(self):
        import tempfile
        from pathlib import Path
        from backend.persistent_oidc import PersistentBoundary
        from backend.oidc_provider_config import CALLBACK
        from backend.neon_provider_buyer import NeonProviderBuyer,open_neon_provider_buyer,MODE as PROVIDER_MODE
        from backend.oidc_identity_http import buyer_identity_application,neon_buyer_identity_application
        issuer="https://example-fixture.us.auth0.com/"
        with tempfile.TemporaryDirectory() as tmp:
            def make(mapping):
                return PersistentBoundary(session_file=Path(tmp)/"sessions.sqlite",issuer=issuer,
                    client_id="fixture",authorize_endpoint=issuer+"authorize",redirect_uri=CALLBACK,
                    public_keys={"fixture":"not-used"},owner_map=mapping)
            boundary=make({(issuer,"auth0|alice"):"provider-owner"})
            self.assertEqual(NeonProviderBuyer._identity_owners(boundary),frozenset({"provider-owner"}))
            for invalid in ({(issuer,"auth0|alice"):"fixture-owner-a"},
                            {(issuer,"auth0|alice"):"provider-owner",(issuer,"auth0|bob"):"other"}):
                with patch("backend.neon_provider_buyer.service_parameters") as params:
                    with self.assertRaises(ImportRefused),open_neon_provider_buyer(
                        {"HPI_NEON_MODE":PROVIDER_MODE},"unused",make(invalid)):
                        pass
                    params.assert_not_called()
            with patch("backend.neon_provider_buyer.service_parameters") as params:
                with self.assertRaises(ImportRefused),open_neon_provider_buyer(
                    {"HPI_NEON_MODE":MODE},"unused",boundary):
                    pass
                with patch("backend.neon_provider_buyer.load_historical_seal",return_value={"build_id":"wrong"}):
                    with self.assertRaises(ImportRefused),open_neon_provider_buyer(
                        {"HPI_NEON_MODE":PROVIDER_MODE},"unused",boundary):
                        pass
                params.assert_not_called()
            # No cloud connection here: verify the exact adapter selected and scoped contexts.
            from contextlib import contextmanager
            rd,wr=object(),object()
            opened=[];closed=[]
            @contextmanager
            def connect(config,kind,progress):
                opened.append((kind,config["application_name"]))
                try:yield rd if kind=="reader" else wr
                finally:closed.append(kind)
            seal={"build_id":fixture_plan()[0],"relational_sha256":"1"*64}
            with patch("backend.neon_provider_buyer.load_historical_seal",return_value=seal), \
                 patch("backend.neon_provider_buyer.service_parameters",return_value=({},{})) as params, \
                 patch("backend.neon_provider_buyer._connect_service",side_effect=connect), \
                 patch("backend.neon_provider_buyer.NeonProviderBuyer",wraps=NeonProviderBuyer) as cls:
                cls._identity_owners=NeonProviderBuyer._identity_owners
                cls.side_effect=lambda *a,**k: "constructed"
                with open_neon_provider_buyer({"HPI_NEON_MODE":PROVIDER_MODE,"HPI_NEON_DEVELOPMENT_HOST":HOST},
                        "unused",boundary) as service:
                    self.assertEqual(service,"constructed")
                cls.assert_called_once_with(rd,wr,seal,boundary,expected_host=HOST)
                self.assertEqual(params.call_args.args[0]["HPI_NEON_MODE"],"development-restricted-preflight")
            self.assertEqual(opened,[("reader","hpi_provider_invented_journey"),("buyer","hpi_provider_invented_journey")])
            self.assertEqual(closed,["buyer","reader"])
            cloud=NeonProviderBuyer.__new__(NeonProviderBuyer)
            cloud.boundary=boundary;cloud._startup_verified=False
            with self.assertRaises(ValueError):neon_buyer_identity_application(boundary,None,cloud,{})
            with self.assertRaises(ValueError):buyer_identity_application(boundary,None,cloud,{})

    @patch("backend.neon_synthetic_journey.psycopg.connect")
    def test_reader_authentication_stage_never_discloses_driver_message(self,connect):
        connect.side_effect=psycopg.OperationalError("password authentication failed: private-marker")
        stages=[]
        with self.assertRaises(psycopg.OperationalError),_connect_service({},"reader",stages.append):
            self.fail("No connection should be yielded")
        self.assertEqual(stages,["reader_connection","reader_connection_authentication"])

    @patch("backend.neon_synthetic_journey.psycopg.connect")
    def test_buyer_connection_stage_does_not_misclassify_later_errors(self,connect):
        stages=[]
        with self.assertRaises(psycopg.OperationalError),_connect_service({},"buyer",stages.append):
            raise psycopg.OperationalError("password authentication failed: private-marker")
        self.assertEqual(stages,["buyer_connection"])
        connect.return_value.__exit__.assert_called_once()
