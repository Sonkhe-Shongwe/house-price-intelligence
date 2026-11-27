"""Single-owner, server-lifetime shortlist for the opt-in fictional ZA fixture."""
from backend.sa_fixture_persistence import PersistenceError, _id


class ShortlistConflict(PersistenceError):
    pass


class FictionalShortlist:
    def __init__(self, store):
        self._store = store
        self._ids = []

    def _rows(self, ids):
        rows = [self._store.reopen(iid) for iid in ids]
        parcels = [row["request"]["subject_key"]["value"] for row in rows]
        if len(set(parcels)) != len(parcels):
            raise ShortlistConflict("Duplicate fictional parcel")
        return rows

    def _envelope(self, rows):
        return {"market": "ZA", "source_kind": "synthetic_fixture",
                "investigations": rows, "comparison_ready": len(rows) >= 2}

    def get(self):
        return self._envelope(self._rows(self._ids))

    def mutate(self, payload):
        if not isinstance(payload, dict) or set(payload) != {"action", "investigation_id"}:
            raise ValueError("Invalid shortlist request")
        action, iid = payload["action"], payload["investigation_id"]
        if action not in ("add", "remove"):
            raise ValueError("Invalid shortlist action")
        try:
            _id(iid)
        except PersistenceError as exc:
            raise ValueError("Invalid shortlist identifier") from exc
        # Idempotent membership commands permit recovery from lost responses.
        # Validate all remaining frozen snapshots before changing membership.
        candidate = list(self._ids)
        if action == "add" and iid not in candidate:
            if len(candidate) == 3:
                raise ShortlistConflict("Three fictional properties maximum")
            candidate.append(iid)
        elif action == "remove" and iid in candidate:
            candidate.remove(iid)
        rows = self._rows(candidate)
        self._ids = candidate
        return self._envelope(rows)
