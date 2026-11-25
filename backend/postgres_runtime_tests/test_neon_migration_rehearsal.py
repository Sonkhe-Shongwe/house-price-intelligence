"""Disposable PG17 privilege-shape rehearsal, never a Neon connection."""
import os
import secrets
import unittest
import psycopg
from psycopg import sql
from backend.postgres_fixture import migrate, SCRIPTS
from hashlib import sha256

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
