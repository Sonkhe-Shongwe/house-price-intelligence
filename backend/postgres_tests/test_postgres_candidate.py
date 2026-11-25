"""Real PostgreSQL service tests; no production host or user data."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone, date
import psycopg
from backend.postgres_fixture import migrate, seed, PostgresFixtureStore, ROOT
from backend.synthetic_demo import in_memory_demo, example_request
from backend.synthetic_shortlists import SyntheticShortlistService, ShortlistError
from backend.synthetic_investigation_store import EvidenceStoreError

DSN = os.environ["HPI_PG_DSN"]
NOW = datetime(2026,11,24,tzinfo=timezone.utc)
I1 = "11111111-1111-4111-8111-111111111111"
I2 = "22222222-2222-4222-8222-222222222222"

class PostgresCandidateTests(unittest.TestCase):
    def setUp(self):
        self.conn=psycopg.connect(DSN,autocommit=True)
        self.assertEqual((self.conn.info.host,self.conn.info.dbname,self.conn.info.user),("127.0.0.1","hpi_fixture","postgres"))
        self.conn.execute("DROP SCHEMA IF EXISTS hpi_candidate CASCADE")
    def tearDown(self):
        self.conn.close()
    def setup_seed(self):
        migrate(self.conn)
        seed(self.conn)
        return PostgresFixtureStore(self.conn)
    def test_upgrade_and_history_checksum_refusal(self):
        migrate(self.conn,1)
        self.conn.execute("SET search_path TO hpi_candidate, pg_catalog")
        self.conn.execute("INSERT INTO parcels VALUES ('00000000000001','17')")
        self.conn.execute("INSERT INTO synthetic_address_index VALUES ('fictional-1','00000000000001','Fictional','fictional')")
        migrate(self.conn,3)
        self.assertEqual(self.conn.execute("SELECT pin FROM synthetic_address_candidates").fetchone()[0],"00000000000001")
        self.conn.execute("UPDATE schema_migrations SET script_sha256='bad' WHERE version=1")
        with self.assertRaises(EvidenceStoreError):migrate(self.conn)
    def test_migration_failure_is_atomic(self):
        migrate(self.conn,1)
        self.conn.execute("SET search_path TO hpi_candidate, pg_catalog")
        self.conn.execute("CREATE TABLE synthetic_address_candidates (unexpected INT)")
        with self.assertRaises(psycopg.errors.DuplicateTable):
            migrate(self.conn,3)
        self.assertEqual(self.conn.execute("SELECT version FROM schema_migrations").fetchall(),[(1,)])
        self.assertIsNone(self.conn.execute("SELECT to_regclass('hpi_candidate.idx_fixture_sale_link_parcel')").fetchone()[0])
        self.conn.execute("DROP TABLE synthetic_address_candidates")
        migrate(self.conn,3)
    def test_unknown_schema_and_foreign_key_rollback(self):
        self.conn.execute("CREATE SCHEMA hpi_candidate")
        self.conn.execute("CREATE TABLE hpi_candidate.unrecognised (x INT)")
        with self.assertRaises(EvidenceStoreError):migrate(self.conn)
        self.conn.execute("DROP SCHEMA hpi_candidate CASCADE")
        store=self.setup_seed()
        with self.assertRaises(psycopg.errors.ForeignKeyViolation):
            with self.conn.transaction():
                self.conn.execute("INSERT INTO parcels VALUES ('00000000000099','17')")
                self.conn.execute("INSERT INTO sale_transaction_parcels VALUES ('missing','00000000000099')")
        self.assertIsNone(self.conn.execute("SELECT pin FROM parcels WHERE pin='00000000000099'").fetchone())
    def test_same_canonical_results_and_shortlist_restart_backup(self):
        pg=self.setup_seed()
        sq, sqlite=in_memory_demo()
        try:
            payload=example_request()
            expected=sqlite.create(payload,investigation_id=I1,recorded_at=NOW)
            first=pg.create(payload,investigation_id=I1,recorded_at=NOW)
            self.assertEqual(first,expected)
            self.assertEqual(pg.search_synthetic_addresses("105 Fictional Court"),sqlite.search_synthetic_addresses("105 Fictional Court"))
            payload["subject"]["pin"]="99999999999999"
            weak=pg.create(payload,investigation_id=I2,recorded_at=NOW)
            self.assertEqual(weak,sqlite.create(payload,investigation_id=I2,recorded_at=NOW))
            service=SyntheticShortlistService(pg)
            sid=service.create({"label":"Fictional comparison"})["shortlist_id"]
            service.add(sid,{"investigation_id":I1})
            service.add(sid,{"investigation_id":I2})
            saved=service.set_note(sid,I1,{"note_text":"Preserve fictional note"})
            self.assertEqual([e["investigation_id"] for e in saved["entries"]],[I1,I2])
            self.assertEqual(pg.history(),sqlite.history())
            with self.assertRaises(ShortlistError):service.add(sid,{"investigation_id":I1})
            self.conn.close()
            self.conn=psycopg.connect(DSN,autocommit=True)
            reopened=PostgresFixtureStore(self.conn)
            self.assertEqual(reopened.reopen(I1),first)
            self.assertEqual(SyntheticShortlistService(reopened).get(sid),saved)
            # Actual dump and restore into an independent disposable database.
            container=os.environ["HPI_PG_CONTAINER"]
            self.conn.execute("CREATE DATABASE hpi_restore")
            try:
                with tempfile.TemporaryFile() as dump:
                    subprocess.run(["docker","exec",container,"pg_dump","-U","postgres","-d","hpi_fixture","-Fc","--schema=hpi_candidate"],stdout=dump,check=True)
                    dump.seek(0)
                    subprocess.run(["docker","exec","-i",container,"pg_restore","-U","postgres","-d","hpi_restore","--exit-on-error"],stdin=dump,check=True)
                with psycopg.connect(DSN,dbname="hpi_restore",autocommit=True) as restored:
                    r=PostgresFixtureStore(restored)
                    self.assertEqual(r.reopen(I1),first)
                    self.assertEqual(r.reopen(I2),weak)
                    self.assertEqual(r.history(),reopened.history())
                    self.assertEqual(SyntheticShortlistService(r).get(sid),saved)
            finally:self.conn.execute("DROP DATABASE hpi_restore")
            self.conn.execute("UPDATE sale_transactions SET price_usd_cents=price_usd_cents+1 WHERE transaction_id='txn-2'")
            with self.assertRaises(EvidenceStoreError):reopened.reopen(I1)
            with self.assertRaises(EvidenceStoreError):PostgresFixtureStore(self.conn)
        finally:sq.close()
    def test_ownership_isolation_default_deny_and_cross_owner_fk(self):
        store=self.setup_seed()
        self.conn.execute((ROOT.parent/"postgres_ownership_candidate.sql").read_text(),prepare=False)
        self.conn.execute("INSERT INTO workspace_owners VALUES ('fictional-alice'),('fictional-bob')")
        self.conn.execute("CREATE ROLE hpi_app_test NOLOGIN NOSUPERUSER NOBYPASSRLS")
        try:
            self.conn.execute("GRANT USAGE ON SCHEMA hpi_candidate TO hpi_app_test")
            self.conn.execute("GRANT SELECT ON ALL TABLES IN SCHEMA hpi_candidate TO hpi_app_test")
            self.conn.execute("GRANT INSERT ON investigations, investigation_results, comparable_evidence, shortlists, shortlist_investigations TO hpi_app_test")
            self.conn.execute("GRANT UPDATE(note_text), DELETE ON shortlist_investigations TO hpi_app_test")
            self.conn.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA hpi_candidate TO hpi_app_test")
            self.conn.execute("SET ROLE hpi_app_test")
            try:
                self.conn.execute("SELECT set_config('hpi.owner_id','fictional-alice',false)")
                alice=store.create(example_request(),investigation_id=I1,recorded_at=NOW)
                svc=SyntheticShortlistService(store)
                sid=svc.create({"label":"Alice fictional"})["shortlist_id"]
                svc.add(sid,{"investigation_id":I1})
                self.conn.execute("SELECT set_config('hpi.owner_id','fictional-bob',false)")
                bob=store.create(example_request(),investigation_id=I2,recorded_at=NOW)
                self.assertEqual([x["investigation_id"] for x in store.history()["investigations"]],[I2])
                self.assertEqual(svc.list()["shortlists"],[])
                with self.assertRaises(EvidenceStoreError):store.reopen(I1)
                with self.assertRaises(ShortlistError):svc.get(sid)
                self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM comparable_evidence WHERE investigation_id=%s",(I1,)).fetchone()[0],0)
                self.assertEqual(self.conn.execute("UPDATE shortlist_investigations SET note_text='blocked' WHERE shortlist_id=%s",(sid,)).rowcount,0)
                bob_sid=svc.create({"label":"Bob fictional"})["shortlist_id"]
                with self.assertRaises(psycopg.errors.ForeignKeyViolation):
                    self.conn.execute("INSERT INTO shortlist_investigations(shortlist_id,investigation_id,note_text) VALUES (%s,%s,'blocked')",(bob_sid,I1))
                self.conn.execute("RESET hpi.owner_id")
                self.assertEqual(store.history()["investigations"],[])
                self.assertEqual(svc.list()["shortlists"],[])
                with self.assertRaises(psycopg.Error):store.create(example_request())
                self.conn.execute("SELECT set_config('hpi.owner_id','fictional-alice',false)")
                self.assertEqual(store.reopen(I1),alice)
                self.assertEqual(svc.get(sid)["entries"][0]["note_text"],"")
            finally:self.conn.execute("RESET ROLE")
        finally:
            self.conn.execute("DROP OWNED BY hpi_app_test")
            self.conn.execute("DROP ROLE hpi_app_test")
