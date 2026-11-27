"""Single-owner, server-lifetime shortlist for the opt-in fictional ZA fixture."""
from backend.sa_fixture_persistence import PersistenceError, _id


class ShortlistConflict(PersistenceError):
    pass


def _note(value):
    if (not isinstance(value, str) or len(value) > 800
            or any((ord(c) < 32 and c not in "\n\t") or
                   127 <= ord(c) <= 159 or 0xD800 <= ord(c) <= 0xDFFF
                   for c in value)):
        raise ValueError("Invalid fictional decision note")
    return value


class FictionalShortlist:
    def __init__(self, store):
        self._store = store
        self._ids = []
        self._notes = {}

    def _rows(self, ids):
        rows = [self._store.reopen(iid) for iid in ids]
        parcels = [row["request"]["subject_key"]["value"] for row in rows]
        if len(set(parcels)) != len(parcels):
            raise ShortlistConflict("Duplicate fictional parcel")
        return rows

    def _envelope(self, rows):
        return {"market": "ZA", "source_kind": "synthetic_fixture",
                "investigations": rows, "comparison_ready": len(rows) >= 2,
                "notes": dict(self._notes)}

    def get(self):
        return self._envelope(self._rows(self._ids))

    def mutate(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("Invalid shortlist request")
        action = payload.get("action")
        if action not in ("add", "remove", "note"):
            raise ValueError("Invalid shortlist action")
        expected = {"action", "investigation_id"}
        if action == "note":
            expected.add("note_text")
        if set(payload) != expected:
            raise ValueError("Invalid shortlist request")
        iid = payload["investigation_id"]
        try:
            _id(iid)
        except PersistenceError as exc:
            raise ValueError("Invalid shortlist identifier") from exc
        # Validate frozen snapshots before changing either membership or notes.
        candidate = list(self._ids)
        notes = dict(self._notes)
        if action == "add" and iid not in candidate:
            if len(candidate) == 3:
                raise ShortlistConflict("Three fictional properties maximum")
            candidate.append(iid)
            notes[iid] = ""
        elif action == "remove" and iid in candidate:
            candidate.remove(iid)
            notes.pop(iid)
        elif action == "note":
            value = _note(payload["note_text"])
            if iid not in candidate:
                raise ShortlistConflict("Fictional property not shortlisted")
            notes[iid] = value
        rows = self._rows(candidate)
        self._ids, self._notes = candidate, notes
        return self._envelope(rows)
