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
                            "investigation_results","shortlists","shortlist_investigations","parcels")
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
                        "shared_transactions":0,"parcel_keys_with_other_references":4}
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
            finally:
                admin.execute("DROP DATABASE hpi_ingest_fixture")
