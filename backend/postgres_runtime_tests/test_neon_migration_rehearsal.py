"""Disposable PG17 privilege-shape rehearsal, never a Neon connection."""
import os
import secrets
import unittest
import psycopg
from psycopg import sql
from backend.postgres_fixture import migrate, SCRIPTS
from backend.postgres_ingestion import _initialise_schema, initialise
from backend.historical_migration import _migrate_historical_schema, migration_history
from backend.historical_reader import ROLE as READER, READ_TABLES, _provision_reader, _verify_reader_privileges, provision_reader
from backend.curated_ingestion_candidate import ImportRefused
from hashlib import sha256
from backend.buyer_ownership import ROLE as BUYER, _prepare_empty_buyer_schema, _verify_staged_buyer

ADMIN = os.environ["HPI_PG_DSN"]
DB = "hpi_neon_migration_fixture"
ROLE = "hpi_neon_migration_owner_fixture"


class NeonMigrationRehearsalTests(unittest.TestCase):
    def test_canonical_migrations_as_nonsuperuser_database_owner(self):
        password = secrets.token_urlsafe(32)
        with psycopg.connect(ADMIN, autocommit=True) as admin:
            self.assertEqual((admin.info.host, admin.info.dbname, admin.info.user),
                             ("127.0.0.1", "hpi_fixture", "postgres"))
            self.assertIsNone(admin.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB,)).fetchone())
            self.assertIsNone(admin.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (ROLE,)).fetchone())
            admin.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER CREATEROLE CREATEDB BYPASSRLS PASSWORD {}").format(
                sql.Identifier(ROLE), sql.Literal(password)))
            try:
                admin.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(DB), sql.Identifier(ROLE)))
                try:
                    with psycopg.connect(ADMIN, dbname=DB, user=ROLE, password=password, autocommit=True) as conn:
                        flags = conn.execute("SELECT rolsuper,rolcreaterole,rolcreatedb,rolbypassrls FROM pg_roles WHERE rolname=current_user").fetchone()
                        self.assertEqual(flags, (False, True, True, True))
                        self.assertEqual(migrate(conn), 3)
                        self.assertEqual(migrate(conn), 3)
                        history = conn.execute("SELECT version,script_sha256 FROM hpi_candidate.schema_migrations ORDER BY version").fetchall()
                        self.assertEqual(history, [(i, sha256(p.read_bytes()).hexdigest()) for i,p in SCRIPTS.items()])
                        self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.sale_transactions").fetchone()[0], 0)
                        self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.investigations").fetchone()[0], 0)
                        owners = conn.execute("SELECT DISTINCT pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='hpi_candidate' AND c.relkind IN ('r','p','S')").fetchall()
                        self.assertEqual(owners, [(ROLE,)])
                finally:
                    admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(DB)))
            finally:
                admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(ROLE)))

    def test_historical_schema_and_reader_as_nonsuperuser_owner(self):
        password, reader_password = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with psycopg.connect(ADMIN, autocommit=True) as admin:
            self.assertEqual((admin.info.host, admin.info.dbname, admin.info.user),
                             ("127.0.0.1", "hpi_fixture", "postgres"))
            self.assertIsNone(admin.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB,)).fetchone())
            for role in (ROLE, READER):
                self.assertIsNone(admin.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone())
            admin.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER CREATEROLE CREATEDB BYPASSRLS PASSWORD {}").format(
                sql.Identifier(ROLE), sql.Literal(password)))
            try:
                admin.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(DB), sql.Identifier(ROLE)))
                try:
                    with psycopg.connect(ADMIN, dbname=DB, user=ROLE, password=password, autocommit=True) as conn:
                        # The original disposable public entry points remain guarded.
                        with self.assertRaises(ImportRefused):
                            initialise(conn)
                        with self.assertRaises(ImportRefused):
                            provision_reader(conn, reader_password)
                        # All schema changes and role grants form one transaction.
                        with self.assertRaisesRegex(RuntimeError, "rollback rehearsal"):
                            with conn.transaction():
                                _initialise_schema(conn)
                                _migrate_historical_schema(conn)
                                _provision_reader(conn, reader_password)
                                raise RuntimeError("rollback rehearsal")
                        self.assertIsNone(conn.execute("SELECT to_regnamespace('hpi_candidate')").fetchone()[0])
                        self.assertIsNone(conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (READER,)).fetchone())
                        with conn.transaction():
                            _initialise_schema(conn)
                            _migrate_historical_schema(conn)
                            _provision_reader(conn, reader_password)
                        _migrate_historical_schema(conn)
                        migration_history(conn)
                        with self.assertRaises(ImportRefused):
                            _provision_reader(conn, reader_password)
                        with psycopg.connect(ADMIN, dbname=DB, user=READER, password=reader_password, autocommit=True) as rd:
                            _verify_reader_privileges(rd)
                            for table in READ_TABLES:
                                rd.execute(sql.SQL("SELECT * FROM {} LIMIT 0").format(sql.Identifier("hpi_candidate", table)))
                            self.assertEqual(rd.execute("SELECT count(*) FROM hpi_candidate.sale_transactions").fetchone()[0], 0)
                            for query in (
                                "SELECT * FROM hpi_candidate.investigations",
                                "DELETE FROM hpi_candidate.sale_transactions",
                                "CREATE TABLE hpi_candidate.forbidden(id int)",
                                "CREATE TABLE public.forbidden(id int)",
                                "CREATE TEMP TABLE forbidden(id int)",
                                "CREATE SCHEMA forbidden",
                            ):
                                with self.subTest(query=query), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                                    rd.execute(query)
                            conn.execute(sql.SQL("GRANT SELECT ON hpi_candidate.investigations TO {}").format(sql.Identifier(READER)))
                            with self.assertRaises(ImportRefused):
                                _verify_reader_privileges(rd)
                finally:
                    admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(DB)))
            finally:
                if admin.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (READER,)).fetchone():
                    admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(READER)))
                admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(ROLE)))

    def test_empty_buyer_ownership_and_staged_role(self):
        password, reader_password = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with psycopg.connect(ADMIN, autocommit=True) as admin:
            self.assertEqual((admin.info.host,admin.info.dbname,admin.info.user),("127.0.0.1","hpi_fixture","postgres"))
            self.assertIsNone(admin.execute("SELECT 1 FROM pg_database WHERE datname=%s",(DB,)).fetchone())
            for role in (ROLE,READER,BUYER):
                self.assertIsNone(admin.execute("SELECT 1 FROM pg_roles WHERE rolname=%s",(role,)).fetchone())
            admin.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER CREATEROLE CREATEDB BYPASSRLS PASSWORD {}").format(sql.Identifier(ROLE),sql.Literal(password)))
            try:
                admin.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(DB),sql.Identifier(ROLE)))
                try:
                    with psycopg.connect(ADMIN,dbname=DB,user=ROLE,password=password,autocommit=True) as conn:
                        _initialise_schema(conn)
                        _migrate_historical_schema(conn)
                        _provision_reader(conn,reader_password)
                        with self.assertRaisesRegex(RuntimeError,"rollback buyer"):
                            with conn.transaction():
                                _prepare_empty_buyer_schema(conn)
                                raise RuntimeError("rollback buyer")
                        self.assertIsNone(conn.execute("SELECT to_regclass('hpi_candidate.workspace_owners')").fetchone()[0])
                        self.assertIsNone(conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s",(BUYER,)).fetchone())
                        _prepare_empty_buyer_schema(conn)
                        # Policy expression deparsing must not depend on the
                        # caller's search path, and verification must preserve it.
                        for path in ('"$user", public', 'pg_catalog'):
                            conn.execute("SELECT set_config('search_path',%s,false)",(path,))
                            before=conn.execute("SELECT current_setting('search_path')").fetchone()[0]
                            _verify_staged_buyer(conn)
                            self.assertEqual(conn.execute("SELECT current_setting('search_path')").fetchone()[0],before)
                        self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.workspace_owners").fetchone()[0],0)
                        # Only the disposable CI superuser may SET ROLE into
                        # the staged NOLOGIN principal. Do not grant membership
                        # to the non-superuser migration owner or change login.
                        with psycopg.connect(ADMIN,dbname=DB,autocommit=True) as exercise:
                            self.assertEqual((exercise.info.host,exercise.info.dbname,exercise.info.user),("127.0.0.1",DB,"postgres"))
                            self.assertTrue(exercise.execute("SELECT rolsuper FROM pg_roles WHERE rolname=current_user").fetchone()[0])
                            with self.assertRaisesRegex(RuntimeError,"rollback buyer exercise"):
                                with exercise.transaction():
                                    exercise.execute("INSERT INTO hpi_candidate.workspace_owners VALUES ('fixture-owner-a'),('fixture-owner-b')")
                                    exercise.execute("INSERT INTO hpi_candidate.shortlists(shortlist_id,label,created_at_utc,owner_id) VALUES ('fixture-a','A','2026-01-01','fixture-owner-a'),('fixture-b','B','2026-01-01','fixture-owner-b')")
                                    exercise.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(BUYER)))
                                    self.assertEqual(exercise.execute("SELECT current_user").fetchone()[0],BUYER)
                                    self.assertEqual(exercise.execute("SELECT shortlist_id FROM hpi_candidate.shortlists").fetchall(),[])
                                    exercise.execute("SELECT set_config('hpi.owner_id','fixture-owner-a',true)")
                                    self.assertEqual(exercise.execute("SELECT shortlist_id FROM hpi_candidate.shortlists").fetchall(),[("fixture-a",)])
                                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                                        with exercise.transaction():
                                            exercise.execute("INSERT INTO hpi_candidate.shortlists(shortlist_id,label,created_at_utc,owner_id) VALUES ('fixture-cross','Cross','2026-01-01','fixture-owner-b')")
                                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                                        with exercise.transaction():
                                            exercise.execute("SELECT * FROM hpi_candidate.sale_transactions")
                                    exercise.execute("SELECT set_config('hpi.owner_id','fixture-owner-b',true)")
                                    self.assertEqual(exercise.execute("SELECT shortlist_id FROM hpi_candidate.shortlists").fetchall(),[("fixture-b",)])
                                    raise RuntimeError("rollback buyer exercise")
                        self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.workspace_owners").fetchone()[0],0)
                        self.assertEqual(conn.execute("SELECT count(*) FROM hpi_candidate.shortlists").fetchone()[0],0)
                        with self.assertRaisesRegex(RuntimeError,"rollback policy drift"):
                            with conn.transaction():
                                conn.execute("ALTER POLICY own_shortlists ON hpi_candidate.shortlists USING (true)")
                                with self.assertRaisesRegex(ImportRefused,"Buyer policy definition drift"):
                                    _verify_staged_buyer(conn)
                                raise RuntimeError("rollback policy drift")
                        _verify_staged_buyer(conn)
                        with self.assertRaises(ImportRefused):
                            _prepare_empty_buyer_schema(conn)
                        with psycopg.connect(ADMIN,dbname=DB,user=READER,password=reader_password,autocommit=True) as rd:
                            _verify_reader_privileges(rd)
                            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                                rd.execute("SELECT * FROM hpi_candidate.workspace_owners")
                        conn.execute(sql.SQL("GRANT SELECT ON hpi_candidate.sale_transactions TO {}").format(sql.Identifier(BUYER)))
                        with self.assertRaises(ImportRefused):
                            _verify_staged_buyer(conn)
                finally:
                    admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(DB)))
            finally:
                for role in (BUYER,READER,ROLE):
                    if admin.execute("SELECT 1 FROM pg_roles WHERE rolname=%s",(role,)).fetchone():
                        admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
