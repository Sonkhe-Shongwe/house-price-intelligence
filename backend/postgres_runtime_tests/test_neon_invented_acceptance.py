"""Execute the new browser acceptance harness against the disposable CI DB."""
import os
import secrets
import subprocess
import tempfile
import unittest
from time import sleep
from contextlib import contextmanager
from pathlib import Path
import psycopg
from psycopg import sql
from backend.neon_invented_acceptance import _fixture_admin, _write_seal, browser_journey
from backend.neon_synthetic_seed import fixture_intake,seed_statements
from backend.historical_reader import seal_historical,provision_reader,ROLE as READER
from backend.buyer_ownership import ROLE as BUYER,_prepare_empty_buyer_schema
from backend.private_beta_rehearsal import PrivateBetaRehearsal
from backend.oidc_boundary import OidcBoundary
from backend.curated_ingestion_candidate import ImportRefused
from backend.neon_service_preflight import _inspect_services

ADMIN=os.environ["HPI_PG_DSN"]


class InventedAcceptanceTests(unittest.TestCase):
    def test_same_browser_harness_disposable_seed_and_connections(self):
        rp,bp=secrets.token_urlsafe(32),secrets.token_urlsafe(32)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            try:
                with _fixture_admin(ADMIN) as conn:
                    provision_reader(conn,rp)
                    conn.execute("ALTER ROLE hpi_historical_reader NOLOGIN")
                    _prepare_empty_buyer_schema(conn)
                    with conn.transaction():
                        for statement in seed_statements(disposable=True):
                            conn.execute(statement)
                    path=_write_seal(root,seal_historical(conn,**fixture_intake()))
                    conn.execute("ALTER ROLE hpi_historical_reader LOGIN")
                    conn.execute(sql.SQL("ALTER ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(BUYER),sql.Literal(bp)))
                    class SlowSearch(PrivateBetaRehearsal):
                        def search(self,*args,**kwargs):
                            sleep(6)
                            return super().search(*args,**kwargs)
                    stages=[]
                    @contextmanager
                    def open_service(boundary):
                        with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=READER,password=rp,autocommit=True) as reader, psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=BUYER,password=bp,autocommit=True) as writer:
                            yield SlowSearch.from_seal_file(reader,writer,path,boundary)
                    report=browser_journey(root,open_service,progress=stages.append)
                    self.assertEqual(stages,['startup','startup_verified','first_search','first_save','second_search','second_save','comparison_save','reconstruct','reopen_investigation','reopen_comparison','cross_owner_denial'])
                    self.assertEqual(report["status"],"invented_browser_journey_verified")
                    self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.investigations").fetchone()[0],2)
                    self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.comparable_evidence").fetchone()[0],3)
                    self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.shortlists").fetchone()[0],1)
                    self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.shortlist_investigations").fetchone()[0],2)
                    # Preserve the browser-created records, not a second hand-built
                    # fixture. Restore schema, data, sequence, RLS and schema ACLs
                    # with existing restricted roles in the disposable database.
                    self._check_restore(conn,root,path,rp,bp)
            finally:
                with psycopg.connect(ADMIN,autocommit=True) as admin:
                    for role in (READER,BUYER):
                        admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))

    def _check_restore(self,conn,root,seal_path,rp,bp):
        self.assertEqual((conn.info.host,conn.info.dbname,conn.info.user),
                         ("127.0.0.1","hpi_ingest_fixture","postgres"))
        container=os.environ["HPI_PG_CONTAINER"]
        self.assertRegex(container,r"^[a-f0-9]{64}$")
        ids=[r[0] for r in conn.execute("SELECT investigation_id FROM hpi_candidate.investigations ORDER BY investigation_id").fetchall()]
        sid=conn.execute("SELECT shortlist_id FROM hpi_candidate.shortlists").fetchone()[0]

        def observe():
            # Fresh offline identity sessions: the database recovery guarantee
            # covers records, not restoration of external authentication tokens.
            boundary=OidcBoundary(issuer="https://issuer.invalid",client_id="fixture",
                authorize_endpoint="https://issuer.invalid/authorize",
                redirect_uri="https://127.0.0.1:8766/auth/callback",
                public_keys={"fixture":"not-used-in-session-rehearsal"},
                owner_map={"a":"fixture-owner-a","b":"fixture-owner-b"})
            a=boundary._issue_session("fixture-owner-a")["cookie"]
            b=boundary._issue_session("fixture-owner-b")["cookie"]
            with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=READER,password=rp,autocommit=True) as rd, psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=BUYER,password=bp,autocommit=True) as wr:
                self.assertEqual(_inspect_services(rd,wr,database="hpi_ingest_fixture")["status"],"restricted_services_verified")
                svc=PrivateBetaRehearsal.from_seal_file(rd,wr,seal_path,boundary)
                saved=[svc.reopen(i,cookie=a) for i in ids]
                comparison=svc.reopen_comparison(sid,cookie=a)
                for i in ids:
                    with self.assertRaises(ImportRefused):
                        svc.reopen(i,cookie=b)
                with self.assertRaises(ImportRefused):
                    svc.reopen_comparison(sid,cookie=b)
                self.assertIsNone(wr.execute("SELECT nullif(current_setting('hpi.owner_id',true),'')").fetchone()[0])
                return saved,comparison

        before=observe()
        self.assertEqual(sorted(x["selected_count"] for x in before[0]),[0,3])
        self.assertEqual([x["note_text"] for x in before[1]["entries"]],["First property note",""])
        def docker(*args,**kwargs):
            result=subprocess.run(["docker","exec",*args],stderr=subprocess.DEVNULL,timeout=60,**kwargs)
            self.assertEqual(result.returncode,0,"Disposable recovery command failed")
        with tempfile.TemporaryFile(dir=root) as dump:
            docker(container,"pg_dump","-U","postgres","-d","hpi_ingest_fixture",
                "-Fc","--schema=hpi_candidate","--no-owner",stdout=dump)
            self.assertGreater(dump.tell(),0)
            # Only this test-owned loopback schema is removed. Existing role
            # definitions and database-level permissions deliberately survive.
            conn.execute("DROP SCHEMA hpi_candidate CASCADE")
            self.assertIsNone(conn.execute("SELECT to_regnamespace('hpi_candidate')").fetchone()[0])
            dump.seek(0)
            docker("-i",container,"pg_restore","-U","postgres","-d","hpi_ingest_fixture",
                "--exit-on-error","--single-transaction","--no-owner",stdin=dump,stdout=subprocess.DEVNULL)
        self.assertEqual(observe(),before)
        self.assertEqual(conn.execute("SELECT count(*) FROM pg_policies WHERE schemaname='hpi_candidate'").fetchone()[0],5)
