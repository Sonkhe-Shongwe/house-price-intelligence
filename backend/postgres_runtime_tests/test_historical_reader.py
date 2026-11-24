"""Actual PostgreSQL permission/manifest rehearsal, invented records only."""
import copy
import os
import secrets
import unittest
import psycopg
from backend.postgres_ingestion import initialise
from backend.historical_postgres import import_historical
from backend.historical_migration import migrate_historical
from backend.historical_reader import ROLE, PrivateHistoricalReader, provision_reader, seal_historical, _verified
from backend.historical_postgres import _evaluate_verified
from backend.historical_beta_projection import project_rehearsal
from backend.curated_ingestion_candidate import ImportRefused
from test_historical_import import population

ADMIN=os.environ["HPI_PG_DSN"]

class HistoricalReaderTests(unittest.TestCase):
    def test_migrate_seal_read_privileges_and_drift(self):
        with psycopg.connect(ADMIN,autocommit=True) as admin:
            admin.execute("CREATE DATABASE hpi_ingest_fixture")
            try:
                with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",autocommit=True) as conn:
                    initialise(conn)
                    migrate_historical(conn); migrate_historical(conn)
                    args=population()
                    build=import_historical(conn,**args)
                    seal=seal_historical(conn,**args)
                    self.assertEqual(seal["build_id"],build)
                    revised=copy.deepcopy(args);revised["rows"]["sales"][0]["sale_price"]="525000.02"
                    second=import_historical(conn,**revised)
                    self.assertNotEqual(second,build)
                    password=secrets.token_urlsafe(32)
                    provision_reader(conn,password)
                    with psycopg.connect(ADMIN,dbname="hpi_ingest_fixture",user=ROLE,password=password,autocommit=True) as rd:
                        reader=PrivateHistoricalReader(rd,seal)
                        match=reader.search("1 fictional court","2025-04-01")
                        self.assertEqual(match["status"],"one_eligible_candidate")
                        req={"township_code":"17","class_code":"203","analysis_date":"2025-04-01",
                             "subject":{"address_id":match["address_id"],"building_area_sqft":1600}}
                        result=reader.review(req)
                        self.assertEqual(result["selected_count"],3)
                        self.assertNotIn("comparables",result)
                        self.assertFalse(result["public_display_approved"])
                        self.assertIsNone(result["valuation"])
                        # Test-only projection: exact code-generated input, same sealed
                        # transaction and canonical matching result, no HTTP route.
                        with rd.transaction():
                            rd.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                            adapter,bid,ids,stamp=_verified(rd,seal)
                            evaluated=_evaluate_verified(adapter,bid,ids,stamp,req)
                            preview=project_rehearsal(*evaluated,ids)
                            self.assertEqual(preview["source_kind"],"historical_shape_rehearsal")
                            self.assertEqual(preview["selected_count"],result["selected_count"])
                            self.assertEqual(preview["status"],result["status"])
                            self.assertEqual([s["sale_price_usd"] for s in preview["sales"]],["525000.01"]*3)
                            self.assertEqual([s["assessment_year"] for s in preview["sales"]],[2024]*3)
                            self.assertEqual([s["assessed_area_sqft"] for s in preview["sales"]],[1600]*3)
                            self.assertFalse(preview["provenance"]["publisher_attributed"])
                            for forbidden in ("pin","document","latitude","longitude","address_id","relational_sha256"):
                                self.assertNotIn("'"+forbidden+"'",str(preview))
                            self.assertNotIn("FICT-",str(preview))
                            # Wrong source membership and duplicate transaction identities
                            # must not accidentally disclose a price.
                            with self.assertRaises(ImportRefused):
                                project_rehearsal(*evaluated,dict(ids,sales="wrong"))
                            broken=copy.deepcopy(evaluated)
                            key=next(iter(broken[2]))
                            broken[2][key].append(broken[2][key][0])
                            # Corrupt a selected key, not an arbitrary subject key.
                            first=broken[1][0]
                            key=(first["pin"],first["document"],first["sale_date"])
                            broken[2][key].append(broken[2][key][0])
                            with self.assertRaises(ImportRefused):
                                project_rehearsal(*broken,ids)
                        self.assertEqual(reader.review(req),result)
                        for statement in ("SELECT * FROM hpi_candidate.investigations",
                            "UPDATE hpi_candidate.sale_transactions SET price_usd_cents=1",
                            "INSERT INTO hpi_candidate.parcels VALUES ('00000000000009','17')",
                            "CREATE TABLE hpi_candidate.forbidden(x int)",
                            "CREATE TEMP TABLE forbidden(x int)"):
                            with self.subTest(statement=statement), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                                rd.execute(statement)
                        with self.assertRaises(ImportRefused):
                            PrivateHistoricalReader(rd,dict(seal,build_id=second)).review(req)
                        with self.assertRaises(ImportRefused):
                            seal_historical(rd,**args)
                        conn.execute("GRANT SELECT ON hpi_candidate.investigations TO "+ROLE)
                        with self.assertRaisesRegex(ImportRefused,"privilege drift"):
                            reader.review(req)
                        conn.execute("REVOKE SELECT ON hpi_candidate.investigations FROM "+ROLE)
                        conn.execute("GRANT SELECT(investigation_id) ON hpi_candidate.investigations TO "+ROLE)
                        with self.assertRaisesRegex(ImportRefused,"privilege drift"):
                            reader.review(req)
                        conn.execute("REVOKE SELECT(investigation_id) ON hpi_candidate.investigations FROM "+ROLE)
                        conn.execute("UPDATE hpi_candidate.historical_migrations SET script_sha256='wrong'")
                        with self.assertRaisesRegex(ImportRefused,"migration history"):
                            reader.review(req)
                        with self.assertRaises(ImportRefused):migrate_historical(conn)
                        # Restore exact known checksum via rollback of a deliberate change in future migrations;
                        # here the disposable test has already verified fail-closed migration.
                        from backend.historical_migration import SCRIPT
                        from hashlib import sha256
                        conn.execute("UPDATE hpi_candidate.historical_migrations SET script_sha256=%s",(sha256(SCRIPT.read_bytes()).hexdigest(),))
                        self.assertEqual(reader.review(req),result)
                        conn.execute("UPDATE hpi_candidate.sale_transactions SET price_usd_cents=price_usd_cents+1 WHERE snapshot_id IN (SELECT snapshot_id FROM hpi_candidate.curated_build_sources WHERE build_id=%s AND source_role='sales')",(build,))
                        with self.assertRaisesRegex(ImportRefused,"seal mismatch"):reader.review(req)
            finally:
                admin.execute("DROP DATABASE hpi_ingest_fixture")
                admin.execute("DROP ROLE IF EXISTS "+ROLE)
