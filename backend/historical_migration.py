"""Checksum-tracked historical extension for the existing canonical schema.
Restricted to the disposable ingestion database; never modifies fixture runtime.
"""
from hashlib import sha256
from pathlib import Path
from backend.postgres_fixture import SCRIPTS
from backend.postgres_ingestion import _check
from backend.curated_ingestion_candidate import ImportRefused

SCRIPT=Path(__file__).parent/"historical_migrations"/"0001.sql"
TABLES={"historical_build_manifests","historical_address_states"}

def migration_history(conn):
    expected=[(i,sha256(p.read_bytes()).hexdigest()) for i,p in SCRIPTS.items()]
    if conn.execute("SELECT version,script_sha256 FROM hpi_candidate.schema_migrations ORDER BY version").fetchall()!=expected:
        raise ImportRefused("Canonical migration history mismatch")
    if conn.execute("SELECT version,script_sha256 FROM hpi_candidate.historical_migrations ORDER BY version").fetchall()!=[(1,sha256(SCRIPT.read_bytes()).hexdigest())]:
        raise ImportRefused("Historical migration history mismatch")

def migrate_historical(conn):
    _check(conn)
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(194323)")
        conn.execute("SET LOCAL search_path TO hpi_candidate,pg_catalog")
        expected=[(i,sha256(p.read_bytes()).hexdigest()) for i,p in SCRIPTS.items()]
        if conn.execute("SELECT version,script_sha256 FROM schema_migrations ORDER BY version").fetchall()!=expected:
            raise ImportRefused("Canonical migration history mismatch")
        present={row[0] for row in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='hpi_candidate'")}
        if "historical_migrations" in present:
            migration_history(conn)
            if not TABLES<=present:
                raise ImportRefused("Incomplete historical migration")
            return
        # Previous unversioned development schema cannot be silently adopted.
        if TABLES & present:
            raise ImportRefused("Unversioned historical schema; reviewed migration required")
        conn.execute("CREATE TABLE historical_migrations(version INTEGER PRIMARY KEY,script_sha256 TEXT NOT NULL)")
        raw=SCRIPT.read_bytes()
        conn.execute(raw.decode(),prepare=False)
        conn.execute("INSERT INTO historical_migrations VALUES(1,%s)",(sha256(raw).hexdigest(),))
