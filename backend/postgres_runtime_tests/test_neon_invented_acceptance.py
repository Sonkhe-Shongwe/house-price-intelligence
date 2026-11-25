"""Execute the new browser acceptance harness against the disposable CI DB."""
import os
import secrets
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
import psycopg
from psycopg import sql
from backend.neon_invented_acceptance import _fixture_admin, _write_seal, browser_journey
from backend.neon_synthetic_seed import fixture_intake,seed_statements
from backend.historical_reader import seal_historical,provision_reader,ROLE as READER
from backend.buyer_ownership import ROLE as BUYER,_prepare_empty_buyer_schema
from backend.private_beta_rehearsal import PrivateBetaRehearsal

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
                    @contextmanager
                    def open_service(boundary):
                        with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=READER,password=rp,autocommit=True) as reader, psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=BUYER,password=bp,autocommit=True) as writer:
                            yield PrivateBetaRehearsal.from_seal_file(reader,writer,path,boundary)
                    report=browser_journey(root,open_service)
                    self.assertEqual(report["status"],"invented_browser_journey_verified")
                    self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.investigations").fetchone()[0],2)
                    self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.comparable_evidence").fetchone()[0],3)
                    self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.shortlists").fetchone()[0],1)
                    self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.shortlist_investigations").fetchone()[0],2)
            finally:
                with psycopg.connect(ADMIN,autocommit=True) as admin:
                    for role in (READER,BUYER):
                        admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))
