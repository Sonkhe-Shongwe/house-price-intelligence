"""Optional durable storage for the invented, localhost-only P3 fixture.

An explicit --fixture-db path is required. Existing databases are never
reseeded, silently upgraded or adopted from an unknown schema. A new database
is prepared completely in a sibling temporary file and published without
overwriting any path that appeared concurrently.

This is not a real-property importer, production database or account store.
"""
from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import tempfile

from backend.schema_migrations import CURRENT_SCHEMA_VERSION, SchemaMigrationError, migrate_fixture
from backend.synthetic_demo import BUILD_ID, in_memory_demo
from backend.synthetic_investigation_store import SyntheticInvestigationStore


class FixturePersistenceError(RuntimeError):
    """Unsafe target path, non-fixture data or incomplete durable state."""


_EXPECTED_SOURCES = [
    ("assess-snap", "synthetic-assessment", "fabricated"),
    ("geo-snap", "synthetic-geography", "fabricated"),
    ("sale-snap", "synthetic-sales", "fabricated"),
]
_EXPECTED_ROLES = [
    ("assess-snap", "assessment"),
    ("geo-snap", "geography"),
    ("sale-snap", "sales"),
]


def _verify_durable_fixture(conn: sqlite3.Connection) -> SyntheticInvestigationStore:
    """Accept only our known versioned fixture, not a caller-supplied data build."""
    if conn.execute("PRAGMA integrity_check").fetchone() != ("ok",):
        raise FixturePersistenceError("SQLite integrity check failed")
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version != CURRENT_SCHEMA_VERSION:
        raise SchemaMigrationError(
            "Existing fixture schema version is not current; explicit reviewed migration required"
        )
    migrate_fixture(conn)  # validates checksums, migration history and foreign keys
    sources = conn.execute(
        "SELECT snapshot_id, dataset_id, source_query FROM source_snapshots ORDER BY snapshot_id"
    ).fetchall()
    builds = conn.execute(
        "SELECT build_id, build_hash_sha256, build_kind FROM curated_builds"
    ).fetchall()
    roles = conn.execute(
        """SELECT snapshot_id, source_role FROM curated_build_sources
           WHERE build_id = ? ORDER BY snapshot_id""", (BUILD_ID,)
    ).fetchall()
    if (sources != _EXPECTED_SOURCES or
            builds != [(BUILD_ID, "0" * 64, "synthetic_fixture")] or
            roles != _EXPECTED_ROLES):
        raise FixturePersistenceError("Database is not the original synthetic fixture build")
    store = SyntheticInvestigationStore(conn, build_id=BUILD_ID)
    store._build()  # checks curated-build membership and fixture source markers
    return store


def open_file_demo(path: str | Path) -> tuple[sqlite3.Connection, SyntheticInvestigationStore]:
    """Open a fictional database and retain investigations across restarts.

    The default server still uses :memory:. A new path is seeded from the
    existing trusted demo and hard-linked into place without replacing files.
    """
    target = Path(path).expanduser().absolute()
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise FixturePersistenceError("Fixture database must be a regular, non-symlink file")
    if not target.parent.is_dir():
        raise FixturePersistenceError("Fixture database parent directory must already exist")
    if not target.exists():
        memory, _ = in_memory_demo()
        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(
                prefix=".hpi-synthetic-", suffix=".sqlite", dir=target.parent
            )
            os.close(fd)
            dest = sqlite3.connect(temporary)
            try:
                memory.backup(dest)
            finally:
                dest.close()
            os.link(temporary, target)  # fails if someone created the target
        finally:
            memory.close()
            if temporary is not None:
                os.unlink(temporary)

    if target.is_symlink() or not target.is_file():
        raise FixturePersistenceError("Fixture database path changed during opening")
    conn = sqlite3.connect(target)
    try:
        store = _verify_durable_fixture(conn)
        return conn, store
    except Exception:
        conn.close()
        raise


__all__ = ["FixturePersistenceError", "open_file_demo"]
