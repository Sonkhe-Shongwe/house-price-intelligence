"""Guarded opt-in SQLite restart proof for FICTIONAL HPI data only.

The canonical backend and its in-memory demo are unchanged. Never open or
migrate arbitrary user databases: a candidate path is local, absolute,
operator-owned, non-symlink and either absent or marked with this fixture's
SQLite application_id plus its own bootstrap table. New files are seeded in a
private temporary file and exposed via an exclusive hard link only after all
fixture evidence has been committed and validated. This is NOT a production
database initializer, backup strategy, encryption or multi-user design.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import stat
import tempfile
from typing import Callable

from backend.schema_migrations import CURRENT_SCHEMA_VERSION
from backend.synthetic_demo import BUILD_ID, in_memory_demo
from backend.synthetic_investigation_store import SyntheticInvestigationStore
from backend.synthetic_shortlists import SyntheticShortlistService

APP_ID = 0x48504946  # 'HPIF': reserved for this isolated fictional fixture
CASE_TABLE = """CREATE TABLE preview_bootstrap (
    one INTEGER PRIMARY KEY CHECK (one = 1),
    cases_json TEXT NOT NULL
)"""


class FixturePathError(ValueError):
    pass


def _private_path(path: Path) -> Path:
    if not path.is_absolute() or path.suffix != ".sqlite3" or ".." in path.parts:
        raise FixturePathError("fixture_path_must_be_absolute_sqlite3")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise FixturePathError("fixture_parent_directory_unavailable")
    if path.is_symlink():
        raise FixturePathError("fixture_symlink_forbidden")
    if path.exists():
        details = path.stat(follow_symlinks=False)
        if (not stat.S_ISREG(details.st_mode) or details.st_nlink != 1 or
                details.st_mode & 0o077 or
                (hasattr(os, "getuid") and details.st_uid != os.getuid())):
            raise FixturePathError("fixture_file_must_be_private_regular_and_owned")
    return path


def _open_existing(path: Path) -> tuple[sqlite3.Connection, SyntheticInvestigationStore, dict]:
    conn = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=5)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        if conn.execute("PRAGMA application_id").fetchone()[0] != APP_ID:
            raise FixturePathError("not_an_hpi_fictional_fixture_file")
        if conn.execute("PRAGMA user_version").fetchone()[0] != CURRENT_SCHEMA_VERSION:
            raise FixturePathError("unsupported_fixture_schema_version")
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise FixturePathError("fixture_sqlite_integrity_check_failed")
        if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise FixturePathError("fixture_foreign_key_check_failed")
        store = SyntheticInvestigationStore(conn, build_id=BUILD_ID)
        store._build()  # rejects non-synthetic source snapshots/build roles
        rows = conn.execute("SELECT cases_json FROM preview_bootstrap WHERE one=1").fetchall()
        if len(rows) != 1:
            raise FixturePathError("fixture_case_marker_missing")
        cases = json.loads(rows[0][0])
        if (not isinstance(cases, dict) or cases.get("source_kind") != "synthetic_fixture"
                or not isinstance(cases.get("cases"), list)
                or [item.get("key") for item in cases["cases"]] != ["supported", "insufficient"]
                or not isinstance(cases.get("shortlist_id"), str)):
            raise FixturePathError("fixture_case_marker_invalid")
        expected = ["supported_neighbourhood", "insufficient_data"]
        for item, status in zip(cases["cases"], expected):
            doc = store.reopen(item["investigation_id"])
            if doc["status"] != status or doc["subject"]["label"] != item["label"]:
                raise FixturePathError("fixture_seed_reference_mismatch")
        demo_shortlist = SyntheticShortlistService(store).get(cases["shortlist_id"])
        if [e["investigation_id"] for e in demo_shortlist["entries"]] != [
            x["investigation_id"] for x in cases["cases"]
        ]:
            raise FixturePathError("fixture_seed_shortlist_reference_mismatch")
        return conn, store, cases
    except Exception:
        conn.close()
        raise


def open_or_seed_fixture_file(
    original_path: Path,
    seed_cases: Callable[[SyntheticInvestigationStore], dict],
) -> tuple[sqlite3.Connection, SyntheticInvestigationStore, dict]:
    """Create atomically if absent, otherwise reopen and validate frozen rows."""
    path = _private_path(original_path)
    if path.exists():
        return _open_existing(path)

    temporary: str | None = None
    source_db: sqlite3.Connection | None = None
    target_db: sqlite3.Connection | None = None
    try:
        fd, temporary = tempfile.mkstemp(
            prefix=".hpi-fixture-", suffix=".sqlite3", dir=path.parent
        )
        os.close(fd)
        source_db, _ = in_memory_demo()
        target_db = sqlite3.connect(temporary, timeout=5)
        source_db.backup(target_db)
        target_db.execute("PRAGMA foreign_keys = ON")
        seeded_store = SyntheticInvestigationStore(target_db, build_id=BUILD_ID)
        cases = seed_cases(seeded_store)
        target_db.execute(CASE_TABLE)
        target_db.execute(
            "INSERT INTO preview_bootstrap (one, cases_json) VALUES (1,?)",
            (json.dumps(cases, sort_keys=True, separators=(",", ":")),),
        )
        target_db.commit()
        target_db.execute(f"PRAGMA application_id = {APP_ID}")
        target_db.commit()
        if target_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise FixturePathError("new_fixture_integrity_failed")
        if target_db.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise FixturePathError("new_fixture_foreign_keys_failed")
        target_db.close()
        target_db = None
        source_db.close()
        source_db = None
        # Publish the complete file only if no concurrent caller already
        # created this name. Never replace an existing SQLite file.
        os.link(temporary, path)
    finally:
        if target_db is not None:
            target_db.close()
        if source_db is not None:
            source_db.close()
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)
    return _open_existing(_private_path(path))
