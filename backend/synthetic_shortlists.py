"""Single-user, local-only shortlist over frozen fictional investigations.

This deliberately uses the existing v1 SQLite shortlist tables. Mutable notes
and membership remain separate from immutable investigation and sale evidence.
The HTTP server provides no authentication; never use this with real users.
"""
from __future__ import annotations

from datetime import datetime, timezone
import re
import sqlite3
import uuid
from typing import Any

from backend.synthetic_investigation_store import EvidenceStoreError, SyntheticInvestigationStore

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
MAX_ENTRIES = 3
MAX_NOTE = 800


class ShortlistError(ValueError):
    def __init__(self, code: str, status: int = 422):
        self.code = code
        self.status = status
        super().__init__(code)


def _uuid(value: Any) -> str:
    if not isinstance(value, str) or not UUID_RE.fullmatch(value):
        raise ShortlistError("invalid_identifier")
    return value


def _note(value: Any) -> str:
    if (not isinstance(value, str) or len(value) > MAX_NOTE
            or any(ord(c) < 32 and c not in "\n\t" for c in value)):
        raise ShortlistError("invalid_note")
    return value


def _require_object(payload: Any, fields: set[str], required: set[str]) -> dict:
    if not isinstance(payload, dict) or set(payload) - fields or not required.issubset(payload):
        raise ShortlistError("invalid_shortlist_request")
    return payload


class SyntheticShortlistService:
    """An independent P6 buyer workflow on trusted P3 synthetic evidence."""

    def __init__(self, store: SyntheticInvestigationStore):
        self.store = store
        self.conn = store.connection

    def create(self, payload: Any) -> dict[str, Any]:
        payload = _require_object(payload, {"label"}, {"label"})
        label = payload["label"]
        if (not isinstance(label, str) or not 1 <= len(label.strip()) <= 80
                or any(ord(c) < 32 for c in label)):
            raise ShortlistError("invalid_shortlist_label")
        self.store._build()
        sid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self.conn:
            self.conn.execute(
                "INSERT INTO shortlists (shortlist_id, label, created_at_utc) VALUES (?,?,?)",
                (sid, label.strip(), now),
            )
        return self.get(sid)

    def list(self) -> dict[str, Any]:
        self.store._build()
        rows = self.conn.execute(
            """SELECT s.shortlist_id, s.label, s.created_at_utc,
                      COUNT(m.investigation_id)
               FROM shortlists s LEFT JOIN shortlist_investigations m
                 ON m.shortlist_id=s.shortlist_id
               GROUP BY s.shortlist_id
               ORDER BY s.created_at_utc DESC, s.shortlist_id DESC
               LIMIT 30"""
        ).fetchall()
        return {"source_kind": "synthetic_fixture", "shortlists": [
            {"shortlist_id": sid, "label": label, "created_at_utc": created,
             "entry_count": count}
            for sid, label, created, count in rows
        ]}

    def get(self, shortlist_id: str) -> dict[str, Any]:
        sid = _uuid(shortlist_id)
        self.store._build()
        row = self.conn.execute(
            "SELECT label, created_at_utc FROM shortlists WHERE shortlist_id=?",
            (sid,),
        ).fetchone()
        if row is None:
            raise ShortlistError("shortlist_not_found", 404)
        members = self.conn.execute(
            """SELECT investigation_id, note_text
               FROM shortlist_investigations WHERE shortlist_id=?
               ORDER BY rowid""", (sid,),
        ).fetchall()
        if len(members) > MAX_ENTRIES:
            raise EvidenceStoreError("Stored shortlist exceeds three investigations")
        entries = []
        for iid, note in members:
            policy_row = self.conn.execute(
                "SELECT match_policy_version FROM investigations WHERE investigation_id=? AND build_id=?",
                (iid, self.store.build_id),
            ).fetchone()
            if policy_row is None or policy_row[0] != self.store.POLICY_VERSION:
                raise EvidenceStoreError("Stored shortlist refers to an unrecognised matching rule version")
            # Do not return cached or re-matched evidence. Verify the frozen
            # response hash, source cents, snapshot roles and identity every time.
            investigation = self.store.reopen(iid)
            entries.append({"investigation_id": iid, "note_text": note or "",
                            "match_policy_version": policy_row[0],
                            "investigation": investigation})
        return {"source_kind": "synthetic_fixture", "shortlist_id": sid,
                "label": row[0], "created_at_utc": row[1],
                "max_entries": MAX_ENTRIES, "entries": entries}

    def add(self, shortlist_id: str, payload: Any) -> dict[str, Any]:
        sid = _uuid(shortlist_id)
        payload = _require_object(payload, {"investigation_id", "note_text"},
                                  {"investigation_id"})
        iid = _uuid(payload["investigation_id"])
        note = _note(payload.get("note_text", ""))
        existing = self.get(sid)
        try:
            new_result = self.store.reopen(iid)
        except EvidenceStoreError as exc:
            if str(exc) == "Investigation not found":
                raise ShortlistError("investigation_not_found", 404) from exc
            raise
        if any(e["investigation_id"] == iid for e in existing["entries"]):
            raise ShortlistError("duplicate_investigation", 409)
        if len(existing["entries"]) >= MAX_ENTRIES:
            raise ShortlistError("shortlist_full", 409)
        pin = new_result["subject"].get("pin")
        if pin is not None and any(
            e["investigation"]["subject"].get("pin") == pin
            for e in existing["entries"]
        ):
            raise ShortlistError("duplicate_property", 409)
        with self.conn:
            self.conn.execute(
                """INSERT INTO shortlist_investigations
                   (shortlist_id, investigation_id, note_text) VALUES (?,?,?)""",
                (sid, iid, note),
            )
        return self.get(sid)

    def set_note(self, shortlist_id: str, investigation_id: str, payload: Any) -> dict[str, Any]:
        sid, iid = _uuid(shortlist_id), _uuid(investigation_id)
        payload = _require_object(payload, {"note_text"}, {"note_text"})
        note = _note(payload["note_text"])
        self.get(sid)  # refuse editing a shortlist with tampered frozen evidence
        with self.conn:
            cursor = self.conn.execute(
                """UPDATE shortlist_investigations SET note_text=?
                   WHERE shortlist_id=? AND investigation_id=?""",
                (note, sid, iid),
            )
            if cursor.rowcount != 1:
                raise ShortlistError("shortlist_entry_not_found", 404)
        return self.get(sid)

    def remove(self, shortlist_id: str, investigation_id: str) -> dict[str, Any]:
        sid, iid = _uuid(shortlist_id), _uuid(investigation_id)
        self.get(sid)
        with self.conn:
            cursor = self.conn.execute(
                """DELETE FROM shortlist_investigations
                   WHERE shortlist_id=? AND investigation_id=?""",
                (sid, iid),
            )
            if cursor.rowcount != 1:
                raise ShortlistError("shortlist_entry_not_found", 404)
        return self.get(sid)


__all__ = ["ShortlistError", "SyntheticShortlistService"]
