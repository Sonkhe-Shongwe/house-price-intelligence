"""Hosted PostgreSQL, source-shaped invented rows only; no API extraction."""
import copy
import os
import unittest
import psycopg
from backend.postgres_ingestion import initialise
from backend.historical_postgres import import_historical, review_historical, search_historical_address
from backend.curated_ingestion_candidate import ImportRefused
from backend.synthetic_investigation_store import SyntheticInvestigationStore, EvidenceStoreError
from backend.postgres_fixture import FixtureConnection
from backend.neon_synthetic_seed import fixture_intake

ADMIN=os.environ["HPI_PG_DSN"]

def population():
    return fixture_intake()

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
                    chosen=search_historical_address(conn,"  1 FICTIONAL COURT ","2025-04-01",**args)
                    self.assertEqual(chosen["status"],"one_eligible_candidate")
                    self.assertFalse(chosen["building_identity_verified"])
                    token=chosen["address_id"]
                    from_address=copy.deepcopy(req)
                    from_address["subject"]={"address_id":token,"building_area_sqft":1600}
                    self.assertEqual(review_historical(conn,from_address,**args),result)
                    self.assertEqual(search_historical_address(conn,"1 Fictional Court","2024-04-01",**args)["status"],"no_match")
                    conflict=copy.deepcopy(from_address);conflict["subject"]["pin"]="00000000000002"
                    with self.assertRaisesRegex(ImportRefused,"identity conflict"):
                        review_historical(conn,conflict,**args)
                    store=SyntheticInvestigationStore.__new__(SyntheticInvestigationStore)
                    store.connection=FixtureConnection(conn);store.build_id=one
                    with self.assertRaises(EvidenceStoreError):store._build()
                    newer=copy.deepcopy(args);newer["rows"]["sales"][0]["sale_price"]="525000.02"
                    two=import_historical(conn,**newer)
                    self.assertNotEqual(one,two)
                    self.assertEqual(conn.execute("SELECT count(*) FROM sale_transactions").fetchone()[0],8)
                    self.assertEqual(review_historical(conn,req,**args),result)
                    with self.assertRaisesRegex(ImportRefused,"not resolved"):
                        review_historical(conn,from_address,**newer)
                    ambiguous=copy.deepcopy(args)
                    ambiguous["rows"]["address"][1]["prop_address_full"]="1 Fictional Court"
                    import_historical(conn,**ambiguous)
                    match=search_historical_address(conn,"1 Fictional Court","2025-04-01",**ambiguous)
                    self.assertEqual((match["status"],match["candidate_count"],match["address_id"]),("ambiguous",2,None))
                    # Late relational conflict after new build/snapshot inserts
                    # must roll back the entire transaction.
                    bad=copy.deepcopy(args);pin="00000000000005"
                    for role,items in bad["rows"].items():
                        added=dict(items[0],pin=pin)
                        if role=="sales":added["doc_no"]="FICT-5"
                        items.append(added)
                    conn.execute("INSERT INTO parcels(pin,township_code) VALUES(%s,%s)",(pin,"18"))
                    before=tuple(conn.execute("SELECT count(*) FROM "+t).fetchone()[0]
                                 for t in ("curated_builds","source_snapshots","sale_transactions","historical_address_states"))
                    with self.assertRaises(ImportRefused):import_historical(conn,**bad)
                    self.assertEqual(tuple(conn.execute("SELECT count(*) FROM "+t).fetchone()[0]
                                 for t in ("curated_builds","source_snapshots","sale_transactions","historical_address_states")),before)
                    conn.execute("DELETE FROM historical_address_states WHERE snapshot_id IN (SELECT snapshot_id FROM curated_build_sources WHERE build_id=%s AND source_role='other')",(one,))
                    with self.assertRaises(ImportRefused):import_historical(conn,**args)
                    with self.assertRaises(ImportRefused):review_historical(conn,req,**args)
                    self.assertEqual(conn.execute("SELECT count(*) FROM curated_builds").fetchone()[0],3)
            finally:
                admin.execute("DROP DATABASE hpi_ingest_fixture")
