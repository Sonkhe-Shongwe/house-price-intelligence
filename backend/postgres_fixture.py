"""PostgreSQL 17 synthetic compatibility harness, not a network service.

Reuses canonical matcher, investigation store and shortlist service. Only
static SQL dialect differences are adapted here. SQLite stays the runtime.
"""
from pathlib import Path
from hashlib import sha256
import re
import psycopg
from psycopg import sql
from backend.synthetic_demo import in_memory_demo, BUILD_ID
from backend.durable_fixture import _IMMUTABLE_SOURCE_TABLES
from backend.synthetic_investigation_store import SyntheticInvestigationStore, EvidenceStoreError

ROOT = Path(__file__).parent / "postgres_migrations"
SCRIPTS = {i: ROOT / f"{i:04d}.sql" for i in (1, 2, 3)}
SCHEMA = "hpi_candidate"
TABLES = (*_IMMUTABLE_SOURCE_TABLES, "investigations", "comparable_evidence",
          "investigation_results", "shortlists", "shortlist_investigations")


def migrate(conn, target=3):
    if target not in SCRIPTS:
        raise ValueError("Invalid migration target")
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(194321)")
        tables = conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'hpi_candidate'"
        ).fetchall()
        names = {r[0] for r in tables}
        if "schema_migrations" not in names:
            if names:
                raise EvidenceStoreError("Unknown unversioned candidate")
            conn.execute("CREATE SCHEMA IF NOT EXISTS hpi_candidate")
            conn.execute("""CREATE TABLE hpi_candidate.schema_migrations (
                version INTEGER PRIMARY KEY, script_sha256 TEXT NOT NULL)""")
        conn.execute("SET LOCAL search_path TO hpi_candidate, pg_catalog")
        rows = conn.execute("SELECT version, script_sha256 FROM schema_migrations ORDER BY version").fetchall()
        if [r[0] for r in rows] != list(range(1, len(rows)+1)) or len(rows) > target:
            raise EvidenceStoreError("Unknown migration history or downgrade")
        for version, digest in rows:
            if sha256(SCRIPTS[version].read_bytes()).hexdigest() != digest:
                raise EvidenceStoreError("Migration checksum mismatch")
        for version in range(len(rows)+1, target+1):
            content = SCRIPTS[version].read_bytes()
            conn.execute(content.decode("utf-8"), prepare=False)
            conn.execute("INSERT INTO schema_migrations VALUES (%s,%s)",
                         (version, sha256(content).hexdigest()))
    return target


class FixtureConnection:
    """Deliberately narrow compatibility surface for trusted static SQL only."""
    def __init__(self, conn):
        if not conn.autocommit:
            raise ValueError("Explicit transactions require autocommit connection")
        self.raw = conn
        self.raw.execute("SET search_path TO hpi_candidate, pg_catalog")
        self._tx = None

    def execute(self, statement, params=()):
        statement = statement.replace("instr(c.search_key, ?)","strpos(c.search_key, ?)")
        statement = statement.replace("ORDER BY rowid","ORDER BY member_order")
        if "%" in statement:
            raise ValueError("Unexpected placeholder dialect")
        return self.raw.execute(statement.replace("?", "%s"), params)

    def __enter__(self):
        if self._tx is not None:
            raise RuntimeError("Nested compatibility transaction")
        self._tx = self.raw.transaction()
        self._tx.__enter__()
        return self

    def __exit__(self, *exc):
        tx, self._tx = self._tx, None
        return tx.__exit__(*exc)


def seed(conn):
    """Only canonical invented seed, never external imports or SQLite files."""
    source, _ = in_memory_demo()
    try:
        with conn.transaction():
            conn.execute("SET LOCAL search_path TO hpi_candidate, pg_catalog")
            if any(conn.execute(sql.SQL("SELECT EXISTS (SELECT 1 FROM {})").format(sql.Identifier(table))).fetchone()[0]
                   for table in TABLES):
                raise EvidenceStoreError("Refusing to overwrite populated candidate")
            for table in _IMMUTABLE_SOURCE_TABLES:
                cur = source.execute(f"SELECT * FROM {table}")
                columns = [x[0] for x in cur.description]
                insert = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table), sql.SQL(",").join(map(sql.Identifier, columns)),
                    sql.SQL(",").join([sql.Placeholder()] * len(columns)))
                with conn.cursor() as dest:
                    dest.executemany(insert, cur.fetchall())
    finally:
        source.close()


class PostgresFixtureStore(SyntheticInvestigationStore):
    """No SQLite PRAGMA emulation. Require actual PostgreSQL fixture migration."""
    def __init__(self, conn):
        self.connection = FixtureConnection(conn)
        self.build_id = BUILD_ID
        history = conn.execute("SELECT version, script_sha256 FROM schema_migrations ORDER BY version").fetchall()
        expected = [(i, sha256(p.read_bytes()).hexdigest()) for i,p in SCRIPTS.items()]
        if history != expected:
            raise EvidenceStoreError("Candidate migration history rejected")
        source, _ = in_memory_demo()
        try:
            for table in _IMMUTABLE_SOURCE_TABLES:
                expected_rows = source.execute(f"SELECT * FROM {table}").fetchall()
                actual = conn.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))).fetchall()
                if sorted(actual, key=repr) != sorted(expected_rows, key=repr):
                    raise EvidenceStoreError("Candidate source differs from trusted synthetic seed")
        finally:
            source.close()
        self._build()
