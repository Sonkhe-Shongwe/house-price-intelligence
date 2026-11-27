"""Disposable ZA storage rehearsal, with no path-taking API or HTTP activation.

Only an internally generated private temporary directory is used. The existing
in-memory guard and ordinary US file launcher remain unchanged. Single local
connection, no production authentication, confidentiality or concurrent writers.
"""
from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import stat
from tempfile import TemporaryDirectory

from backend.durable_fixture import _fixture_signature
from backend.sa_fixture_persistence import (
    FictionalStore, OWNERS, PersistenceError, _owner, _id, canonical, sqlite_store,
)
from backend.sa_fixture_shortlist import FictionalShortlist, _note
from backend.schema_migrations import migrate_fixture
from backend.synthetic_demo import BUILD_ID, in_memory_demo
from backend.synthetic_investigation_store import SyntheticInvestigationStore

SCRIPT = Path(__file__).with_name("sa_fixture_restart_v1.sql")


def _digest():
    return sha256(SCRIPT.read_bytes()).hexdigest()


def _seal(owner, snapshot):
    return sha256(canonical([owner, snapshot]).encode("utf-8")).hexdigest()


def _install_restart(conn):
    if conn.in_transaction:
        raise PersistenceError("Restart extension requires idle fixture")
    with conn:
        conn.execute("BEGIN IMMEDIATE")
        for stmt in SCRIPT.read_text(encoding="utf-8").split(";"):
            if stmt.strip():
                conn.execute(stmt)
        conn.execute("INSERT INTO sa_restart_migrations VALUES (?,?)", (1, _digest()))
        for owner in sorted(OWNERS):
            snapshot = {"ids": [], "notes": {}}
            conn.execute("INSERT INTO sa_restart_shortlists VALUES (?,?,?)",
                         (owner, canonical(snapshot), _seal(owner, snapshot)))


def _seed():
    conn, _ = in_memory_demo()
    try:
        sqlite_store(conn, "fictional-alice")
        _install_restart(conn)
        return conn
    except Exception:
        conn.close()
        raise


class RestartShortlist(FictionalShortlist):
    """Reuse the exact membership/note policy; persist only its mutable state."""

    def __init__(self, store):
        super().__init__(store)
        self._load()

    def _load(self):
        row = self._store._db.execute(
            "SELECT snapshot_json,snapshot_sha256 FROM sa_restart_shortlists WHERE owner_key=?",
            (self._store._owner,)).fetchone()
        try:
            if row is None:
                raise ValueError("Missing snapshot")
            snapshot = json.loads(row[0])
            if (not isinstance(snapshot, dict) or set(snapshot) != {"ids", "notes"}
                    or row[0] != canonical(snapshot)
                    or row[1] != _seal(self._store._owner, snapshot)):
                raise ValueError("Invalid snapshot seal")
            ids, notes = snapshot["ids"], snapshot["notes"]
            if (not isinstance(ids, list) or len(ids) > 3
                    or any(not isinstance(i, str) for i in ids)
                    or len(set(ids)) != len(ids)
                    or not isinstance(notes, dict) or set(notes) != set(ids)):
                raise ValueError("Invalid snapshot members")
            for iid in ids:
                _id(iid)
                _note(notes[iid])
            self._rows(ids)
        except (ValueError, TypeError, KeyError, PersistenceError) as exc:
            raise PersistenceError("Restart shortlist rejected") from exc
        self._ids, self._notes = ids, notes

    def get(self):
        self._load()
        return super().get()

    def _write_snapshot(self):
        snapshot = {"ids": self._ids, "notes": self._notes}
        result = self._store._db.execute(
            "UPDATE sa_restart_shortlists SET snapshot_json=?,snapshot_sha256=? WHERE owner_key=?",
            (canonical(snapshot), _seal(self._store._owner, snapshot), self._store._owner))
        if result.rowcount != 1:
            raise PersistenceError("Restart snapshot unavailable")

    def mutate(self, payload):
        conn = self._store._db
        if conn.in_transaction:
            raise PersistenceError("Restart mutation requires idle fixture")
        self._load()
        previous = (self._ids, self._notes)
        try:
            with conn:
                conn.execute("BEGIN IMMEDIATE")
                result = super().mutate(payload)
                self._write_snapshot()
            return result
        except Exception:
            self._ids, self._notes = previous
            raise


class DisposableRestartRehearsal:
    """Own a fresh temporary file for one bounded rehearsal, never adopt a path."""

    def __enter__(self):
        if hasattr(self, "_directory"):
            raise PersistenceError("Rehearsal already used")
        self._directory = TemporaryDirectory(prefix="hpi-za-restart-")
        self._active = False
        self._closed = False
        self._path = Path(self._directory.name) / "fictional.sqlite"
        try:
            reference = _seed()
            try:
                self._signature = _fixture_signature(reference)
                self._base_ledger = reference.execute(
                    "SELECT * FROM schema_migrations ORDER BY version").fetchall()
                fd = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
                os.close(fd)
                target = sqlite3.connect(self._path.as_uri()+"?mode=rw", uri=True)
                try:
                    reference.backup(target)
                finally:
                    target.close()
            finally:
                reference.close()
            info = self._path.stat(follow_symlinks=False)
            self._identity = (info.st_dev, info.st_ino)
            return self
        except Exception:
            self._directory.cleanup()
            self._closed = True
            raise

    def __exit__(self, *exc):
        self._closed = True
        self._directory.cleanup()

    @contextmanager
    def open(self, owner="fictional-alice"):
        _owner(owner)
        if self._closed or self._active:
            raise PersistenceError("Rehearsal unavailable or already open")
        info = self._path.stat(follow_symlinks=False)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or (info.st_dev, info.st_ino) != self._identity
                or self._path.parent.is_symlink()
                or (os.name == "posix" and (info.st_mode & 0o077 or info.st_uid != os.getuid()))):
            raise PersistenceError("Restart target changed")
        conn = sqlite3.connect(self._path.as_uri()+"?mode=rw", uri=True)
        self._active = True
        try:
            if (conn.execute("PRAGMA integrity_check").fetchone() != ("ok",)
                    or conn.execute("PRAGMA user_version").fetchone() != (3,)
                    or _fixture_signature(conn) != self._signature
                    or conn.execute("SELECT * FROM schema_migrations ORDER BY version").fetchall() != self._base_ledger
                    or conn.execute("SELECT * FROM sa_restart_migrations").fetchall() != [(1, _digest())]
                    or conn.execute("SELECT owner_key FROM sa_restart_shortlists ORDER BY owner_key").fetchall()
                        != [(o,) for o in sorted(OWNERS)]):
                raise PersistenceError("Restart schema, source or ledger rejected")
            migrate_fixture(conn, target_version=3)
            # Validate every saved enquiry and both owners' complete membership
            # before exposing either workspace; do not recompute frozen evidence.
            for key in sorted(OWNERS):
                store = FictionalStore(conn, key)
                for (iid,) in conn.execute(
                        "SELECT investigation_id FROM sa_fixture_investigations WHERE owner_key=?", (key,)):
                    store.reopen(iid)
                RestartShortlist(store)
            store = FictionalStore(conn, owner)
            us = SyntheticInvestigationStore(conn, build_id=BUILD_ID)
            us._build()
            yield conn, us, store, RestartShortlist(store)
        finally:
            conn.close()
            self._active = False
