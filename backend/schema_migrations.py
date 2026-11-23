"""Controlled, fixture-only SQLite schema migration runner for P3/P4 tests.

The frozen draft SQL serves as v1. Future schema changes go in numbered
migration scripts, never in-place edits to that baseline. No production data
is migrated here; unversioned or unexpected databases are rejected.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sqlite3
from typing import Final

ROOT: Final = Path(__file__).resolve().parent
BASELINE: Final = ROOT / "schema_draft.sql"
SCRIPTS: Final = {
    1: BASELINE,
    2: ROOT / "migrations" / "0002_fixture_query_indexes.sql",
}
CURRENT_SCHEMA_VERSION: Final = 2


class SchemaMigrationError(RuntimeError):
    """Unsafe or unrecognised database state; fail without rewriting data."""


def _load_script(version: int) -> str:
    return SCRIPTS[version].read_text(encoding="utf-8")


def _script_digest(script: str) -> str:
    return hashlib.sha256(script.encode("utf-8")).hexdigest()


def _version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _verify_history(conn: sqlite3.Connection) -> int:
    """Require a contiguous version history with immutable script checksums."""
    try:
        rows = conn.execute(
            "SELECT version, script_sha256 FROM schema_migrations ORDER BY version"
        ).fetchall()
    except sqlite3.Error as exc:
        raise SchemaMigrationError("Unrecognised migration history") from exc
    recorded = [row[0] for row in rows]
    if (not recorded or recorded != list(range(1, len(rows) + 1))
            or recorded[-1] > CURRENT_SCHEMA_VERSION
            or _version(conn) != recorded[-1]):
        raise SchemaMigrationError("Unknown, incomplete or inconsistent schema version")
    for version, checksum in rows:
        if checksum != _script_digest(_load_script(version)):
            raise SchemaMigrationError("Previously applied migration checksum differs")
    if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise SchemaMigrationError("Foreign-key violations in existing database")
    return recorded[-1]


def migrate_fixture(conn: sqlite3.Connection, *, target_version: int = CURRENT_SCHEMA_VERSION) -> int:
    """Migrate a new/versioned disposable database, preserving populated records.

    SQLite executescript commits any *pre-existing* transaction implicitly, so
    refuse open transactions, then put each migration in an explicit SQL BEGIN /
    COMMIT block. On failure, roll back both schema and version bookkeeping.
    This deliberately cannot adopt an unknown unversioned database.
    """
    if type(target_version) is not int or not 1 <= target_version <= CURRENT_SCHEMA_VERSION:
        raise SchemaMigrationError("Unsupported target version")
    if conn.in_transaction:
        raise SchemaMigrationError("Cannot migrate during an open transaction")

    conn.execute("PRAGMA foreign_keys = ON")
    if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise SchemaMigrationError("Foreign keys must be enabled")

    tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    )}
    if "schema_migrations" not in tables:
        if tables or _version(conn) != 0:
            raise SchemaMigrationError("Unversioned existing database cannot be adopted")
        previous_version = 0
    else:
        previous_version = _verify_history(conn)
        if previous_version > target_version:
            raise SchemaMigrationError("Downgrade is not supported")

    for version in range(previous_version + 1, target_version + 1):
        script = _load_script(version)
        if version == 1:
            # v1 source contains the standalone PRAGMA used by draft tests.
            # SQLite PRAGMA foreign_keys must run outside transactions.
            script, count = re.subn(
                r"(?m)^PRAGMA foreign_keys = ON;[ \t]*\n", "", script
            )
            if count != 1:
                raise SchemaMigrationError("Baseline requires exactly one foreign-key PRAGMA")
            bootstrap = """CREATE TABLE schema_migrations (
                version INTEGER PRIMARY KEY CHECK (version >= 1),
                script_sha256 TEXT NOT NULL CHECK (length(script_sha256) = 64)
            );"""
        else:
            bootstrap = ""
        digest = _script_digest(_load_script(version))
        sql = (
            "BEGIN IMMEDIATE;\n" + script + "\n" + bootstrap + "\n"
            + f"INSERT INTO schema_migrations VALUES ({version}, '{digest}');\n"
            + f"PRAGMA user_version = {version};\n"
            + "COMMIT;\n"
        )
        try:
            conn.executescript(sql)
        except sqlite3.Error as exc:
            conn.rollback()
            raise SchemaMigrationError(f"Fixture schema migration {version} failed") from exc
        if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise SchemaMigrationError("Foreign-key violations after migration")
    return _verify_history(conn)


__all__ = ["CURRENT_SCHEMA_VERSION", "SchemaMigrationError", "migrate_fixture"]
