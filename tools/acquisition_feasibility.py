"""AE0 offline feasibility only. No network, disk writes or real source authority."""
import csv
import hashlib
import io
import json
from dataclasses import dataclass


class Refused(ValueError):
    """Fixture contract violation; no partial result returned."""


@dataclass(frozen=True)
class Policy:
    source: str
    kind: str
    pages: tuple
    max_requests: int
    max_bytes: int
    max_rows: int


POLICIES = {
    "fictional-schools": Policy("fictional-schools", "json", ("s1", "s2"), 2, 2048, 10),
    "fictional-services": Policy("fictional-services", "csv", ("c1",), 1, 2048, 10),
}


def unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise Refused("duplicate JSON key")
        obj[key] = value
    return obj


def parse(kind, payload):
    try:
        text = payload.decode("utf-8")
        if kind == "json":
            rows = json.loads(text, object_pairs_hook=unique)
            if not isinstance(rows, list):
                raise Refused("expected JSON array")
        elif kind == "csv":
            reader = csv.reader(io.StringIO(text, newline=""), strict=True)
            if next(reader, None) != ["area_id", "count"]:
                raise Refused("unexpected CSV header")
            rows = []
            for row in reader:
                if len(row) != 2 or not row[1].isascii() or not row[1].isdigit() or len(row[1]) > 9:
                    raise Refused("invalid CSV row")
                rows.append({"area_id": row[0], "count": int(row[1])})
        else:
            raise Refused("unsupported format")
    except (UnicodeError, json.JSONDecodeError, csv.Error, RecursionError) as exc:
        raise Refused("malformed fixture") from exc
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"area_id", "count"}:
            raise Refused("unexpected fields")
        key, value = row["area_id"], row["count"]
        if (not isinstance(key, str) or len(key) != 3 or not key.isascii()
                or not key.isdigit() or type(value) is not int or not 0 <= value <= 999999999):
            raise Refused("invalid identity or count")
    return rows


class FixtureAttempt:
    """Single-use in-memory fixture run, not durable approval or production transport."""
    def __init__(self, source, responses):
        if source not in POLICIES:
            raise Refused("unapproved fixture source")
        self.policy = POLICIES[source]
        self.responses = dict(responses)
        self.consumed = False
        self.requests = []

    def run(self):
        if self.consumed:
            raise Refused("attempt consumed")
        self.consumed = True
        policy = self.policy
        if set(self.responses) != set(policy.pages):
            raise Refused("fixture page scope mismatch")
        rows, hashes, seen = [], [], set()
        total_bytes = 0
        for page in policy.pages:
            if len(self.requests) >= policy.max_requests:
                raise Refused("request cap")
            self.requests.append(page)
            raw = self.responses[page]
            if not isinstance(raw, bytes) or not raw:
                raise Refused("invalid response")
            total_bytes += len(raw)
            if len(raw) > policy.max_bytes or total_bytes > policy.max_bytes:
                raise Refused("byte cap")
            for row in parse(policy.kind, raw):
                if len(rows) >= policy.max_rows:
                    raise Refused("row cap")
                if row["area_id"] in seen:
                    raise Refused("duplicate identifier")
                seen.add(row["area_id"])
                rows.append(row)
            hashes.append(hashlib.sha256(raw).hexdigest())
        if not rows:
            raise Refused("empty evidence")
        return {"source": policy.source, "rows": rows, "count_total": sum(r["count"] for r in rows),
                "requests": len(self.requests), "bytes": total_bytes, "sha256": hashes}
