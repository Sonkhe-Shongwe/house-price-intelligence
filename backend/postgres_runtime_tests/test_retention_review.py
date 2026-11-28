"""Actual disposable PostgreSQL review, two invented source revisions, no deletion."""
import copy
from datetime import datetime, timezone, timedelta
import os
import unittest
import psycopg

from backend.curated_ingestion_candidate import ImportRefused
from backend.historical_postgres import import_historical
from backend.postgres_ingestion import initialise
from backend.retention_review import review_retention
from test_historical_import import population

ADMIN=os.environ["HPI_PG_DSN"]


class RetentionReviewTests(unittest.TestCase):
    def test_expiry_counts_and_shared_references_without_mutation(self):
        with psycopg.connect(ADMIN,autocommit=True) as admin:
            admin.execute("CREATE DATABASE hpi_ingest_fixture")
            try:
                with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",autocommit=True) as conn:
                    initialise(conn)
                    data=population()
                    first=import_historical(conn,**data)
                    revised=copy.deepcopy(data)
                    revised["rows"]["sales"][0]["sale_price"]="525000.02"
                    second=import_historical(conn,**revised)
                    self.assertNotEqual(first,second)
                    for key,build in (("retention-fixture-a",first),("retention-fixture-b",second)):
                        conn.execute("""INSERT INTO hpi_candidate.investigations
                            (investigation_id,build_id,subject_pin,analysis_date,user_input_json,
                             match_policy_version,evidence_status,created_at_utc)
                            VALUES (%s,%s,'00000000000001','2025-04-01','{}','fixture',
                            'insufficient_data','2026-11-24T00:00:00Z')""",(key,build))
                        conn.execute("""INSERT INTO hpi_candidate.investigation_results
                            VALUES (%s,'{}',%s,'2026-11-24T00:00:00Z')""",(key,"a"*64))
                    conn.execute("INSERT INTO hpi_candidate.shortlists VALUES ('retention-fixture','Invented','2026-11-24T00:00:00Z')")
                    for key in ("retention-fixture-a","retention-fixture-b"):
                        conn.execute("""INSERT INTO hpi_candidate.shortlist_investigations
                          (shortlist_id,investigation_id) VALUES ('retention-fixture',%s)""",(key,))
                    tables=("curated_builds","source_snapshots","sale_transactions","investigations",
                            "investigation_results","shortlists","shortlist_investigations","parcels",
                            "comparable_evidence","curated_build_transactions","curated_build_sources")
                    def counts():
                        return tuple(conn.execute("SELECT count(*) FROM hpi_candidate."+t).fetchone()[0] for t in tables)
                    before=counts()
                    start=datetime.fromisoformat(data["extracted_at_utc"].replace("Z","+00:00"))
                    boundary=start+timedelta(days=30)
                    report=review_retention(conn,first,now=boundary-timedelta(microseconds=1))
                    self.assertEqual(report["status"],"within_retention_window")
                    self.assertEqual(report["deadline_utc"],boundary.isoformat())
                    self.assertEqual(review_retention(conn,first,now=boundary)["status"],"expired")
                    expected={"source_snapshots":4,"sale_transactions":4,"assessment_records":4,
                        "geographies":4,"address_states":4,"investigations":1,"frozen_results":1,
                        "comparable_evidence":0,"shortlist_memberships":1,"affected_shortlists":1,
                        "mixed_shortlists":1,"parcel_keys":4,"shared_snapshots":0,
                        "shared_transactions":0,"parcel_keys_with_other_references":4,
                        "sale_transaction_parcel_links":4,"other_comparable_evidence":0,
                        "other_investigations_with_evidence_dependencies":0}
                    self.assertEqual(report["counts"],expected)
                    self.assertFalse(report["deletion_authorised"])
                    self.assertTrue(report["external_copy_inventory_required"])
                    for raw in (first,second,"retention-fixture","00000000000001"):
                        self.assertNotIn(raw,str(report))
                    with self.assertRaises(ImportRefused):
                        review_retention(conn,"historical-"+"0"*64,now=boundary)
                    with self.assertRaises(ImportRefused):
                        review_retention(conn,first,now=start-timedelta(seconds=1))
                    with self.assertRaises(ImportRefused):
                        review_retention(conn,first,now=datetime(2026,12,24))
                    self.assertEqual(counts(),before)

                    # Deliberately introduce shared and inconsistent references
                    # that are relationally legal but must never be silently
                    # overlooked during disposal review. Use invented data only.
                    def sale(build):
                        return conn.execute("""SELECT t.transaction_id,t.snapshot_id,t.price_usd_cents
                            FROM hpi_candidate.sale_transactions t
                            JOIN hpi_candidate.curated_build_transactions c USING(transaction_id)
                            WHERE c.build_id=%s ORDER BY t.transaction_id LIMIT 1""",(build,)).fetchone()
                    txn, snap, cents = sale(first)
                    other_txn, _, other_cents = sale(second)
                    conn.execute("""INSERT INTO hpi_candidate.curated_build_sources
                        (build_id,snapshot_id,source_role) VALUES (%s,%s,'sales')""",(second,snap))
                    conn.execute("""INSERT INTO hpi_candidate.curated_build_transactions
                        (build_id,transaction_id) VALUES (%s,%s)""",(second,txn))
                    for rank, transaction, price in ((1,txn,cents),(2,other_txn,other_cents)):
                        conn.execute("""INSERT INTO hpi_candidate.comparable_evidence
                            (investigation_id,build_id,rank,transaction_id,selection_tier,
                             explanation,source_snapshot_id,sale_price_usd_cents)
                            VALUES ('retention-fixture-b',%s,%s,%s,'same_neighborhood','Invented',%s,%s)""",
                            (second,rank,transaction,snap,price))
                    before_shared=counts()
                    shared=review_retention(conn,first,now=boundary)
                    self.assertEqual(shared["counts"]["shared_snapshots"],1)
                    self.assertEqual(shared["counts"]["shared_transactions"],1)
                    self.assertEqual(shared["counts"]["other_comparable_evidence"],2)
                    self.assertEqual(shared["counts"]["other_investigations_with_evidence_dependencies"],1)
                    self.assertEqual(shared["counts"]["comparable_evidence"],0)
                    self.assertFalse(shared["deletion_authorised"])
                    self.assertEqual(counts(),before_shared)
            finally:
                admin.execute("DROP DATABASE hpi_ingest_fixture")
