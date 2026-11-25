"""Offline tests only. No external DB connection or secrets."""
import unittest
import io
import json
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import MagicMock, patch
from backend.neon_preflight import connection_parameters, inspect_connection, run_preflight, PreflightRefused, main

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

    @patch("backend.neon_preflight.run_preflight")
    def test_operator_cli_reports_only_aggregate_or_generic_error(self, run):
        run.return_value={"status":"empty_development_preflight","read_only":True}
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            self.assertEqual(main({}),0)
        self.assertEqual(json.loads(out.getvalue()),run.return_value)
        self.assertEqual(err.getvalue(),"")
        run.side_effect=RuntimeError("invented-secret-bearing-diagnostic")
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            self.assertEqual(main({}),1)
        self.assertEqual(out.getvalue(),"")
        self.assertEqual(err.getvalue(),"Neon preflight refused or failed\n")


class RestrictedServicePreflightTests(unittest.TestCase):
    def settings(self):
        return {"HPI_NEON_MODE":"development-restricted-preflight","HPI_NEON_DEVELOPMENT_HOST":HOST,
                "HPI_NEON_READER_DSN":DSN.replace("hpi_private_owner","hpi_historical_reader").replace("invented-test-password","invented-reader-password-only"),
                "HPI_NEON_BUYER_DSN":DSN.replace("hpi_private_owner","hpi_buyer_runtime").replace("invented-test-password","invented-buyer-password-only")}

    def test_separate_restricted_strict_tls_settings(self):
        from backend.neon_service_preflight import service_parameters
        with patch.dict("os.environ",{},clear=True):
            reader,buyer=service_parameters(self.settings())
            self.assertEqual((reader["user"],buyer["user"]),("hpi_historical_reader","hpi_buyer_runtime"))
            for value in (reader,buyer):
                self.assertEqual((value["host"],value["sslmode"],value["channel_binding"],value["sslrootcert"]),(HOST,"verify-full","require","system"))
            for change in (
                {"HPI_NEON_READER_DSN":DSN},
                {"HPI_NEON_BUYER_DSN":self.settings()["HPI_NEON_READER_DSN"]},
                {"HPI_NEON_BUYER_DSN":self.settings()["HPI_NEON_BUYER_DSN"].replace("invented-buyer-password-only","invented-reader-password-only")},
                {"HPI_NEON_DEVELOPMENT_HOST":"ep-unapproved.c-10.eu-central-1.aws.neon.tech"},
                {"HPI_NEON_MODE":"other"},
            ):
                with self.subTest(change=change),self.assertRaises(PreflightRefused):
                    service_parameters(dict(self.settings(),**change))

    @patch("backend.neon_service_preflight.psycopg.connect")
    def test_no_default_connection_and_sanitised_failure(self,connect):
        from backend.neon_service_preflight import run_preflight
        with self.assertRaises(PreflightRefused):
            run_preflight({})
        connect.assert_not_called()
        with patch.dict("os.environ",{},clear=True):
            connect.side_effect=RuntimeError("invented secret diagnostic")
            with self.assertRaisesRegex(PreflightRefused,"^Restricted cloud service preflight refused or failed$"):
                run_preflight(self.settings())

    def test_provider_credential_and_masked_placeholder(self):
        from backend.neon_service_preflight import service_parameters, ServicePreflightRefused
        with patch.dict("os.environ",{},clear=True):
            cfg=self.settings()
            cfg["HPI_NEON_READER_DSN"]=cfg["HPI_NEON_READER_DSN"].replace("invented-reader-password-only","fictional-R4nd0m")
            self.assertEqual(service_parameters(cfg)[0]["user"],"hpi_historical_reader")
            cfg["HPI_NEON_READER_DSN"]=cfg["HPI_NEON_READER_DSN"].replace("fictional-R4nd0m","****************")
            with self.assertRaises(ServicePreflightRefused) as caught:
                service_parameters(cfg)
            self.assertEqual(caught.exception.code,"reader_credential_shape")

    def test_cli_diagnostic_never_echoes_exception(self):
        from backend.neon_service_preflight import main, ServicePreflightRefused
        for code,expected in (("reader_configuration","reader_configuration"),
                              ("buyer_connection","buyer_connection"),
                              ("invented-secret-should-not-appear","unexpected_failure")):
            err=io.StringIO()
            with patch("backend.neon_service_preflight.run_preflight",side_effect=ServicePreflightRefused(code)),redirect_stderr(err):
                self.assertEqual(main({}),1)
            self.assertEqual(err.getvalue(),"Restricted cloud service preflight refused or failed: "+expected+"\n")

    @patch("backend.neon_service_preflight.psycopg.connect")
    def test_buyer_configuration_reasons_are_fixed_and_connect_never_runs(self, connect):
        from backend.neon_service_preflight import main
        buyer = self.settings()["HPI_NEON_BUYER_DSN"]
        cases = (
            ("", "missing"),
            ("psql 'invented secret input'", "parse"),
            (buyer+"&hostaddr=127.0.0.1", "options"),
            (buyer.replace(HOST, "ep-other.c-10.eu-central-1.aws.neon.tech"), "endpoint"),
            (buyer.replace("fictional.c-", "fictional-pooler.c-"), "endpoint"),
            (buyer.replace("/hpi_private?", "/other?"), "database"),
            (buyer.replace("hpi_buyer_runtime", "hpi_historical_reader"), "role"),
            (buyer.replace(":invented-buyer-password-only@", ":@"), "password"),
            (buyer.replace(HOST, HOST+":5433"), "port"),
            (buyer.replace("channel_binding=require", "channel_binding=prefer"), "tls"),
            (buyer.replace("sslmode=require", "sslmode=disable"), "tls"),
            (buyer+"&sslrootcert=/tmp/invented-secret", "tls"),
        )
        with patch.dict("os.environ", {}, clear=True):
            for dsn, reason in cases:
                with self.subTest(reason=reason):
                    config = dict(self.settings(), HPI_NEON_BUYER_DSN=dsn)
                    out, err = io.StringIO(), io.StringIO()
                    with redirect_stdout(out), redirect_stderr(err):
                        self.assertEqual(main(config), 1)
                    self.assertEqual(out.getvalue(), "")
                    self.assertEqual(err.getvalue(),
                        "Restricted cloud service preflight refused or failed: buyer_configuration_"+reason+"\n")
        connect.assert_not_called()

    @patch("backend.neon_service_preflight.psycopg.connect")
    def test_connection_failure_classified_without_details(self,connect):
        from backend.neon_service_preflight import run_preflight, ServicePreflightRefused
        connect.side_effect=RuntimeError("secret-bearing connection error")
        with patch.dict("os.environ",{},clear=True),self.assertRaises(ServicePreflightRefused) as caught:
            run_preflight(self.settings())
        self.assertEqual(caught.exception.code,"reader_connection")
