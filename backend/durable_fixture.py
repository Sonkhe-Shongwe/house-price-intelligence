"""Optional durable storage for the invented, localhost-only P3 fixture.

An explicit --fixture-db path is required. Existing databases are never
reseeded, silently upgraded or adopted from an unknown schema. A new database
is prepared completely in a sibling temporary file and published without
overwriting any path that appeared concurrently.

This is not a real-property importer, production database or account store.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import stat
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


# Only buyer investigations, selected evidence and shortlist records may vary
# between verified fixture launches. All recorded-source and candidate identity
# rows must match the trusted invented seed exactly, including source prices.
_IMMUTABLE_SOURCE_TABLES = (
    "source_snapshots",
    "curated_builds",
    "curated_build_sources",
    "parcels",
    "buildings",
    "sale_transactions",
    "sale_transaction_parcels",
    "assessment_records",
    "parcel_geographies",
    "curated_build_transactions",
    "synthetic_address_index",
    "synthetic_address_candidates",
)


def _fixture_signature(conn: sqlite3.Connection):
    """Compare full invented-source rows and schema, not forgeable source labels.

    Canonical row sorting tolerates SQLite row order changes. This is strictly
    a tiny demo database check, not a general real-data signature mechanism.
    """
    schema = conn.execute(
        """SELECT type, name, sql FROM sqlite_master
           WHERE name NOT LIKE 'sqlite_%' AND type IN ('table', 'index', 'view', 'trigger')
           ORDER BY type, name"""
    ).fetchall()
    sources = []
    for table in _IMMUTABLE_SOURCE_TABLES:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        sources.append((table, tuple(sorted(
            json.dumps(row, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
            for row in rows
        ))))
    return schema, sources


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
    # A metadata-only synthetic marker cannot prove that a database still
    # contains invented records. The protected fixture rows and schema must
    # match the trusted seed; only saved buyer investigations may change.
    expected_conn, _ = in_memory_demo()
    try:
        expected = _fixture_signature(expected_conn)
    finally:
        expected_conn.close()
    try:
        actual = _fixture_signature(conn)
    except (sqlite3.Error, TypeError, ValueError) as exc:
        raise FixturePersistenceError("Unexpected synthetic fixture schema or source records") from exc
    if actual != expected:
        raise FixturePersistenceError("Synthetic fixture schema or source records differ from trusted seed")
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


def open_file_demo(path: str | Path, *, private_file: bool = False) -> tuple[sqlite3.Connection, SyntheticInvestigationStore]:
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
    if private_file:
        details = target.stat(follow_symlinks=False)
        if (not stat.S_ISREG(details.st_mode) or details.st_nlink != 1
                or target.parent.is_symlink()
                or (os.name == "posix" and (details.st_mode & 0o077
                    or details.st_uid != os.getuid()))):
            raise FixturePersistenceError("Fixture file must be private, regular and owned")
    conn = sqlite3.connect(target.as_uri() + "?mode=rw", uri=True)
    try:
        store = _verify_durable_fixture(conn)
        return conn, store
    except Exception:
        conn.close()
        raise


__all__ = ["FixturePersistenceError", "open_file_demo"]
