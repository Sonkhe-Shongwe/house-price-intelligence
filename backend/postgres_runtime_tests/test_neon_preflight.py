"""Offline tests only. No external DB connection or secrets."""
import unittest
from unittest.mock import MagicMock, patch
from backend.neon_preflight import connection_parameters, inspect_connection, run_preflight, PreflightRefused

HOST = "ep-example-fictional.c-10.eu-central-1.aws.neon.tech"
DSN = f"postgresql://hpi_private_owner:invented-test-password@{HOST}/hpi_private?sslmode=require&channel_binding=require"

class NeonPreflightTests(unittest.TestCase):
    def test_strict_tls_and_direct_host(self):
        p=connection_parameters(DSN,HOST)
        self.assertEqual(p["sslmode"],"verify-full")
        self.assertEqual(p["sslrootcert"],"system")
        self.assertEqual(p["channel_binding"],"require")
        self.assertEqual(p["gssencmode"],"disable")
        self.assertEqual(p["host"],HOST)

    def test_reject_wrong_target_and_unsafe_options(self):
        for dsn,host in [
            (DSN,"ep-other.c-10.eu-central-1.aws.neon.tech"),
            (DSN.replace("fictional.c-","fictional-pooler.c-"),HOST.replace("fictional.c-","fictional-pooler.c-")),
            (DSN.replace("eu-central-1","us-east-1"),HOST.replace("eu-central-1","us-east-1")),
            (DSN.replace("/hpi_private?","/other?"),HOST),
            (DSN.replace("hpi_private_owner","hpi_reader"),HOST),
            (DSN.replace("sslmode=require","sslmode=disable"),HOST),
            (DSN.replace("channel_binding=require","channel_binding=prefer"),HOST),
            (DSN+"&hostaddr=127.0.0.1",HOST),
            (DSN+"&options=-csearch_path%3Dpublic",HOST),
            (DSN+"&sslrootcert=/tmp/untrusted",HOST),
            (DSN.replace(":invented-test-password@",":@"),HOST),
        ]:
            with self.subTest(dsn=dsn),self.assertRaises(PreflightRefused):
                connection_parameters(dsn,host)

    def mock_conn(self,identity=None,count=0,roles=None):
        conn=MagicMock()
        conn.execute.side_effect=[MagicMock(),MagicMock(),
            MagicMock(**{"fetchone.return_value":identity or ("hpi_private","hpi_private_owner","hpi_private_owner",170012,False,True,True,True)}),
            MagicMock(**{"fetchone.return_value":(count,)}),
            MagicMock(**{"fetchall.return_value":roles if roles is not None else [("hpi_private_owner",)]})]
        return conn

    def test_read_only_empty_preflight(self):
        conn=self.mock_conn()
        report=inspect_connection(conn)
        self.assertEqual(report["application_relations"],0)
        self.assertFalse(report["real_data_activated"])
        self.assertIn("READ ONLY",conn.execute.call_args_list[0].args[0])
        self.assertEqual(conn.execute.call_count,5)

    def test_refuse_existing_data_roles_or_identity_drift(self):
        for conn in [self.mock_conn(count=1),self.mock_conn(roles=[("hpi_private_owner",),("hpi_app",)]),
                     self.mock_conn(identity=("hpi_private","hpi_private_owner","hpi_private_owner",180000,False,True,True,True))]:
            with self.assertRaises(PreflightRefused):
                inspect_connection(conn)

    @patch("backend.neon_preflight.psycopg.connect")
    def test_no_implicit_connection_or_secret_error(self,connect):
        with self.assertRaises(PreflightRefused):
            run_preflight({})
        connect.assert_not_called()
        with patch.dict("os.environ",{},clear=True):
            connect.side_effect=RuntimeError("secret-bearing error")
            with self.assertRaisesRegex(PreflightRefused,"^Cloud connection or read-only inspection failed$"):
                run_preflight({"HPI_NEON_MODE":"development-empty-preflight","HPI_NEON_OWNER_DSN":DSN,
                               "HPI_NEON_DEVELOPMENT_HOST":HOST})
