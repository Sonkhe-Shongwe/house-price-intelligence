"""Hosted PostgreSQL, source-shaped invented rows only; no API extraction."""
import copy
import os
import unittest
import psycopg
from backend.postgres_ingestion import initialise
from backend.historical_postgres import import_historical, review_historical
from backend.curated_ingestion_candidate import ImportRefused
from backend.synthetic_investigation_store import SyntheticInvestigationStore, EvidenceStoreError
from backend.postgres_fixture import FixtureConnection
from backend.tests.test_real_source_intake import sample

ADMIN=os.environ["HPI_PG_DSN"]

def population():
    args=sample()
    rows=args["rows"]
    for i in range(2,5):
        p=f"{i:014d}"
        rows["sales"].append(dict(rows["sales"][0],pin=p,doc_no=f"FICT-{i}",
                                 sale_date=f"2025-01-0{i}T00:00:00"))
        for role in ("assessment","geography","address"):
            rows[role].append(dict(rows[role][0],pin=p))
    return args

class HistoricalImportTests(unittest.TestCase):
    def test_transactional_inactive_import_review_revision_and_tamper(self):
        with psycopg.connect(ADMIN,autocommit=True) as admin:
            admin.execute("CREATE DATABASE hpi_ingest_fixture")
            try:
                with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",autocommit=True) as conn:
                    initialise(conn)
                    args=population()
                    one=import_historical(conn,**args)
                    self.assertEqual(import_historical(conn,**args),one)
                    self.assertEqual(conn.execute("SELECT count(*) FROM sale_transactions").fetchone()[0],4)
                    self.assertEqual(conn.execute("SELECT DISTINCT price_usd_cents FROM sale_transactions").fetchall(),[(52500001,)])
                    self.assertEqual(conn.execute("SELECT DISTINCT public_display_approved FROM source_snapshots").fetchall(),[(0,)])
                    req={"township_code":"17","class_code":"203","analysis_date":"2025-04-01",
                         "subject":{"pin":"00000000000001","building_area_sqft":1600}}
                    result=review_historical(conn,req,**args)
                    self.assertEqual(result["status"],"supported_neighbourhood")
                    self.assertEqual(result["selected_count"],3)
                    self.assertNotIn("comparables",result)
                    self.assertIsNone(result["valuation"])
                    self.assertEqual(conn.execute("SELECT count(*) FROM investigations").fetchone()[0],0)
                    store=SyntheticInvestigationStore.__new__(SyntheticInvestigationStore)
                    store.connection=FixtureConnection(conn);store.build_id=one
                    with self.assertRaises(EvidenceStoreError):store._build()
                    newer=copy.deepcopy(args);newer["rows"]["sales"][0]["sale_price"]="525000.02"
                    two=import_historical(conn,**newer)
                    self.assertNotEqual(one,two)
                    self.assertEqual(conn.execute("SELECT count(*) FROM sale_transactions").fetchone()[0],8)
                    self.assertEqual(review_historical(conn,req,**args),result)
                    conn.execute("DELETE FROM historical_address_states WHERE snapshot_id IN (SELECT snapshot_id FROM curated_build_sources WHERE build_id=%s AND source_role='other')",(one,))
                    with self.assertRaises(ImportRefused):import_historical(conn,**args)
                    with self.assertRaises(ImportRefused):review_historical(conn,req,**args)
                    self.assertEqual(conn.execute("SELECT count(*) FROM curated_builds").fetchone()[0],2)
            finally:
                admin.execute("DROP DATABASE hpi_ingest_fixture")
