"""Disposable, SQLite-backed P3 investigation vertical slice using synthetic fixtures.

This is NOT an HTTP endpoint or a production data importer. A source selected by
an untrusted caller cannot enable public property-level disclosure: this entire
service refuses non-synthetic curated builds. PIN is an internal pilot lookup key,
not an owner-approved consumer-facing identification method.

Data selection is performed on one server-selected curated build. An individual
assessment, geography, or sale is eligible only when its source snapshot belongs
in that build with the required role. Missing/ambiguous historical rows abstain.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from datetime import date, datetime, timezone
import hashlib
import json
import re
import sqlite3
import uuid
from typing import Any, Mapping

from backend.investigation_contract import ContractError, build_investigation, validate_request
from backend.disclosure_guard import require_fixture_build, DisclosureDenied


class EvidenceStoreError(RuntimeError):
    """Bad curated build, ambiguous evidence, inconsistent storage or unsafe access."""


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _saved_cents(value: Any) -> int | None:
    """Interpret the existing numeric JSON sale-price field without float arithmetic.

    This does not change the provisional response-money contract; that remains
    a separate P3 decision. Refuse non-cent, non-finite or non-numeric values.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        cents = Decimal(str(value)) * 100
        if not cents.is_finite() or cents != cents.to_integral_value():
            return None
        return int(cents)
    except (InvalidOperation, ValueError, OverflowError):
        return None


def _money_text(cents: int) -> str:
    """Serialize trusted SQLite integer cents with no binary float conversion."""
    if type(cents) is not int or cents <= 0:
        raise EvidenceStoreError("Selected sale price must have positive integer cents")
    return f"{cents // 100}.{cents % 100:02d}"


def _exact_money_cents(value: Any) -> int | None:
    """Parse canonical two-decimal JSON strings without floating-point math."""
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)\.[0-9]{2}", value):
        return None
    dollars, cents = value.split(".")
    return int(dollars) * 100 + int(cents)


def _utc(timestamp: datetime | None) -> str:
    value = timestamp or datetime.now(timezone.utc)
    if value.tzinfo is None or value.utcoffset() is None:
        raise EvidenceStoreError("recorded_at must be timezone aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class SyntheticInvestigationStore:
    """Proof of database -> matcher -> persisted evidence, with no real source data."""

    POLICY_VERSION = "phase2-research-v1"

    def __init__(self, connection: sqlite3.Connection, *, build_id: str):
        if not isinstance(build_id, str) or not build_id:
            raise EvidenceStoreError("A trusted curated build ID is required")
        self.connection = connection
        self.build_id = build_id
        if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise EvidenceStoreError("SQLite foreign key enforcement must be enabled")

    def _build(self) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT build_id, built_at_utc, build_kind FROM curated_builds WHERE build_id = ?",
            (self.build_id,),
        ).fetchone()
        if row is None:
            raise EvidenceStoreError("Curated build not found")
        build_id, built_at, kind = row
        if kind != "synthetic_fixture":
            raise EvidenceStoreError("Real-source builds are disabled in this candidate")
        source_rows = self.connection.execute(
            """SELECT bs.snapshot_id, bs.source_role, ss.dataset_id, ss.source_query
               FROM curated_build_sources bs
               JOIN source_snapshots ss ON ss.snapshot_id = bs.snapshot_id
               WHERE bs.build_id = ? ORDER BY bs.snapshot_id, bs.source_role""",
            (self.build_id,),
        ).fetchall()
        # A database build_kind assertion is not, by itself, evidence that the
        # referenced publisher data were fabricated. This extra fixture-only
        # marker rejects accidentally imported real source snapshots. It is
        # still NOT a general proof that arbitrary data is synthetic.
        try:
            require_fixture_build(kind,[(dataset,query) for _,_,dataset,query in source_rows])
        except DisclosureDenied as exc:
            raise EvidenceStoreError(str(exc)) from exc
        roles = {role for _, role, _, _ in source_rows}
        if not {"sales", "assessment", "geography"}.issubset(roles):
            raise EvidenceStoreError("Synthetic build is missing source role(s)")
        snapshots = sorted({snapshot_id for snapshot_id, _, _, _ in source_rows})
        return {"build_id": build_id, "built_at_utc": built_at,
                "source_kind": kind, "source_snapshot_ids": snapshots}

    def search_synthetic_addresses(self, query: str) -> dict[str, Any]:
        """Return distinct parcel candidates; identical addresses remain ambiguous."""
        self._build()
        key = " ".join(re.findall(r"[a-z0-9]+", query.casefold()))
        rows = self.connection.execute(
            """SELECT c.candidate_id, c.display_address, c.parcel_hint,
                      (SELECT COUNT(*) FROM synthetic_address_candidates other
                       WHERE other.search_key = c.search_key)
               FROM synthetic_address_candidates c
               WHERE instr(c.search_key, ?) > 0
               ORDER BY c.display_address, c.candidate_id LIMIT 9""",
            (key,),
        ).fetchall()
        candidates = [
            {"address_id": aid, "display_address": label,
             "ambiguous_address": count > 1,
             "parcel_hint": hint if count > 1 else None,
             "identity_scope": "parcel_only"}
            for aid, label, hint, count in rows[:8]
        ]
        return {"source_kind": "synthetic_fixture",
                "status": "matches" if candidates else "no_match",
                "candidates": candidates, "truncated": len(rows) > 8}

    def resolve_synthetic_address(self, address_id: str) -> dict[str, Any] | None:
        """Resolve a selected fictional candidate to one parcel, never a building."""
        self._build()
        row = self.connection.execute(
            """SELECT c.candidate_id, c.display_address, c.pin, c.parcel_hint
               FROM synthetic_address_candidates c
               JOIN parcels p ON p.pin = c.pin
               WHERE c.candidate_id = ?""", (address_id,),
        ).fetchone()
        if row is None:
            return None
        return {"source_kind": "synthetic_fixture",
                "identity_status": "synthetic_mapping_only",
                "identity_scope": "parcel_only",
                "building_identity_verified": False,
                "address_id": row[0], "display_address": row[1], "pin": row[2],
                "parcel_hint": row[3]}

    def _assessment(self, pin: str, tax_year: int):
        rows = self.connection.execute(
            """SELECT a.assessor_class, a.building_area_sqft, a.tax_year
               FROM assessment_records a
               JOIN curated_build_sources bs ON bs.snapshot_id = a.snapshot_id
               WHERE bs.build_id = ? AND bs.source_role = 'assessment'
                 AND a.pin = ? AND a.tax_year = ?""",
            (self.build_id, pin, tax_year),
        ).fetchall()
        # The research pipeline accepts only one prior-year building card.
        # 0 or >1 is insufficient/ambiguous, not a licence to select randomly.
        return rows[0] if len(rows) == 1 else None

    def _geography(self, pin: str, tax_year: int):
        rows = self.connection.execute(
            """SELECT g.neighborhood_code, g.latitude, g.longitude
               FROM parcel_geographies g
               JOIN curated_build_sources bs ON bs.snapshot_id = g.snapshot_id
               WHERE bs.build_id = ? AND bs.source_role = 'geography'
                 AND g.pin = ? AND g.tax_year = ?""",
            (self.build_id, pin, tax_year),
        ).fetchall()
        return rows[0] if len(rows) == 1 else None

    def _resolved_subject(self, request: Mapping[str, Any]):
        pin = request["subject"]["pin"]
        if pin is None:
            return None
        parcel = self.connection.execute("SELECT township_code FROM parcels WHERE pin = ?", (pin,)).fetchone()
        if parcel is None:
            return None
        tax_year = int(request["analysis_date"][:4]) - 1
        assessment = self._assessment(pin, tax_year)
        if assessment is None:
            return None
        cls, area, _ = assessment
        if area is None or cls is None:
            return None
        geo = self._geography(pin, tax_year)
        hood, lat, lon = geo if geo is not None else (None, None, None)
        return {"build_id": self.build_id, "pin": pin, "township_code": parcel[0],
                "class": cls, "sqft": area, "characteristics_year": tax_year,
                "nbhd_code": hood, "lat": lat, "lon": lon}

    def _candidates(self, request: Mapping[str, Any]):
        if request["subject"]["pin"] is None:
            return [], {}
        # Query a build's imported transactions only when their actual sales
        # snapshot has been registered with the sales role for this build.
        records = self.connection.execute(
            """SELECT t.transaction_id, t.document_number, t.sale_date,
                      t.price_usd_cents, link.pin, p.township_code,
                      t.snapshot_id
               FROM curated_build_transactions cb
               JOIN sale_transactions t ON t.transaction_id = cb.transaction_id
               JOIN curated_build_sources bs ON bs.build_id = cb.build_id
                      AND bs.snapshot_id = t.snapshot_id AND bs.source_role = 'sales'
               JOIN sale_transaction_parcels link ON link.transaction_id = t.transaction_id
               JOIN parcels p ON p.pin = link.pin
               WHERE cb.build_id = ?""",
            (self.build_id,),
        ).fetchall()
        grouped = defaultdict(list)
        for row in records:
            grouped[row[0]].append(row)
        candidates = []
        transaction_ids = defaultdict(list)
        for transaction_id, linked in grouped.items():
            if len(linked) != 1:  # A multi-parcel sale is not a one-home priced comparable.
                continue
            txn, doc, when, cents, pin, township, snapshot_id = linked[0]
            if not isinstance(when, str) or len(when) != 10 or cents is None or cents <= 0:
                continue
            try:
                year = date.fromisoformat(when).year
            except ValueError:
                continue
            assessment = self._assessment(pin, year - 1)
            if assessment is None:
                continue
            cls, sqft, _ = assessment
            if cls is None or sqft is None or sqft <= 0:
                continue
            geo = self._geography(pin, year - 1)
            hood, lat, lon = geo if geo is not None else (None, None, None)
            row = {"build_id": self.build_id, "pin": pin, "doc_no": doc,
                   "sale_date": when, "sale_price": cents / 100,
                   "sqft": sqft, "class": cls, "township_code": township,
                   "nbhd_code": hood, "lat": lat, "lon": lon,
                   "characteristics_year": year - 1}
            candidates.append(row)
            transaction_ids[(pin, doc, when)].append((txn, snapshot_id, cents))
        return candidates, transaction_ids

    def create(self, payload: Mapping[str, Any], *, today: date | None = None,
               investigation_id: str | None = None, recorded_at: datetime | None = None) -> dict[str, Any]:
        # User-provided content cannot select build ID, sales, source data or demo mode.
        request = validate_request(payload, today=today)
        build = self._build()
        address_id = request["subject"].get("address_id")
        if address_id is not None:
            chosen = self.resolve_synthetic_address(address_id)
            if chosen is None:
                raise ContractError("subject.address_id", "address_not_found")
            submitted_pin = request["subject"]["pin"]
            if submitted_pin is not None and submitted_pin != chosen["pin"]:
                raise ContractError("subject.address_id", "identity_conflict")
            request["subject"]["pin"] = chosen["pin"]
        resolved = self._resolved_subject(request)
        candidates, transaction_ids = self._candidates(request)
        response = build_investigation(request, resolved_subject=resolved,
                                       candidate_sales=candidates, data_build=build,
                                       synthetic_demo=True, today=today)
        # The historical matcher keeps its research price; the v0.3 fixture
        # API exposes only exact decimal strings derived from SQLite cents.
        response["contract_version"] = "p3-draft-v0.3"
        if address_id is not None:
            response["subject"]["identity_status"] = "synthetic_mapping_only"
            response["subject"]["identity_scope"] = "parcel_only"
            response["subject"]["building_identity_verified"] = False
        for comp in response["comparables"]:
            key = (comp["pin"], comp["document"], comp["sale_date"])
            source = transaction_ids.get(key, [])
            if len(source) != 1:
                raise EvidenceStoreError("Selected comparable has ambiguous source transaction")
            _, _, cents = source[0]
            if _saved_cents(comp.get("sale_price")) != cents:
                raise EvidenceStoreError("Selected comparable price differs from exact source cents")
            comp["sale_price_usd"] = _money_text(cents)
            del comp["sale_price"]
        identifier = investigation_id or str(uuid.uuid4())
        if not isinstance(identifier, str) or not identifier or len(identifier) > 120:
            raise EvidenceStoreError("Invalid server-side investigation identifier")
        text = _json(response)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        created = _utc(recorded_at)
        parcel = request["subject"]["pin"]
        if parcel is not None and not self.connection.execute(
            "SELECT 1 FROM parcels WHERE pin = ?", (parcel,)
        ).fetchone():
            parcel = None
        # One atomic transaction. On any ambiguous transaction identity or
        # foreign key failure, no partial investigation or evidence is saved.
        with self.connection:
            self.connection.execute(
                """INSERT INTO investigations
                   (investigation_id, build_id, subject_pin, analysis_date, user_input_json,
                    match_policy_version, evidence_status, created_at_utc)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (identifier, self.build_id, parcel, request["analysis_date"], _json(request),
                 self.POLICY_VERSION, response["status"], created),
            )
            self.connection.execute(
                "INSERT INTO investigation_results VALUES(?,?,?,?)",
                (identifier, text, digest, created),
            )
            for rank, comp in enumerate(response["comparables"], 1):
                key = (comp["pin"], comp["document"], comp["sale_date"])
                ids = transaction_ids.get(key, [])
                if len(ids) != 1:
                    raise EvidenceStoreError("Selected comparable has ambiguous source transaction")
                transaction_id, snapshot_id, original_cents = ids[0]
                if _exact_money_cents(comp.get("sale_price_usd")) != original_cents:
                    raise EvidenceStoreError("Saved comparable price differs from exact source cents")
                self.connection.execute(
                    """INSERT INTO comparable_evidence
                       (investigation_id, build_id, rank, transaction_id, selection_tier,
                        explanation, source_snapshot_id, sale_price_usd_cents)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    (identifier, self.build_id, rank, transaction_id,
                     response["tier"], comp["explanation"], snapshot_id, original_cents),
                )
        return {"investigation_id": identifier, **response}

    def _history_rows(self):
        return self.connection.execute(
            """SELECT investigation_id, created_at_utc, analysis_date
               FROM investigations WHERE build_id = ?
               ORDER BY created_at_utc DESC, investigation_id DESC LIMIT 31""",
            (self.build_id,),
        ).fetchall()

    def shortlist_policy(self, iid):
        return self.connection.execute(
            "SELECT match_policy_version FROM investigations WHERE investigation_id=? AND build_id=?",
            (iid,self.build_id),
        ).fetchone()

    def history(self) -> dict[str, Any]:
        """Bounded local discovery of verified, frozen results; never rematch."""
        self._build()
        rows = self._history_rows()
        items = []
        for iid, created, analysis_date in rows[:30]:
            result = self.reopen(iid)
            if result["analysis_date"] != analysis_date:
                raise EvidenceStoreError("History analysis date differs from saved result")
            subject = result["subject"]
            items.append({
                "investigation_id": iid, "created_at_utc": created,
                "analysis_date": analysis_date, "label": subject.get("label"),
                "pin": subject["pin"], "status": result["status"],
                "selected_count": result["selected_count"],
                "asking_price_usd": subject["asking_price_usd"],
            })
        return {"contract_version": "synthetic-history-v1",
                "source_kind": "synthetic_fixture", "limit": 30,
                "truncated": len(rows) > 30, "investigations": items}

    def reopen(self, investigation_id: str) -> dict[str, Any]:
        row = self.connection.execute(
            """SELECT i.build_id, i.evidence_status, r.response_json, r.result_sha256
               FROM investigations i JOIN investigation_results r
                 ON r.investigation_id = i.investigation_id
               WHERE i.investigation_id = ?""", (investigation_id,),
        ).fetchone()
        if row is None:
            raise EvidenceStoreError("Investigation not found")
        build, status, raw, expected = row
        if build != self.build_id:
            raise EvidenceStoreError("Investigation belongs to another curated build")
        if hashlib.sha256(raw.encode("utf-8")).hexdigest() != expected:
            raise EvidenceStoreError("Stored investigation response was modified")
        result = json.loads(raw)
        if result.get("status") != status or result.get("data_build", {}).get("build_id") != build:
            raise EvidenceStoreError("Stored response conflicts with investigation record")
        subject = result.get("subject", {})
        if subject.get("address_id") is not None:
            # A saved fictional selection must not silently change parcel.
            chosen = self.resolve_synthetic_address(subject["address_id"])
            if (chosen is None or chosen["pin"] != subject.get("pin")
                    or subject.get("identity_scope") != "parcel_only"
                    or subject.get("building_identity_verified") is not False):
                raise EvidenceStoreError("Saved address candidate no longer matches its parcel")
        count = self.connection.execute("SELECT COUNT(*) FROM comparable_evidence WHERE investigation_id = ?",
                                        (investigation_id,)).fetchone()[0]
        if count != len(result.get("comparables", [])) or count != result.get("selected_count"):
            raise EvidenceStoreError("Persisted selected evidence count does not match response")
        evidence = self.connection.execute(
            """SELECT ce.rank, ce.selection_tier, ce.explanation,
                      t.document_number, t.sale_date, link.pin,
                      t.snapshot_id, ce.source_snapshot_id,
                      t.price_usd_cents, ce.sale_price_usd_cents,
                      EXISTS (
                          SELECT 1 FROM curated_build_sources bs
                          WHERE bs.build_id = ce.build_id
                            AND bs.snapshot_id = t.snapshot_id
                            AND bs.source_role = 'sales'
                      )
               FROM comparable_evidence ce
               JOIN sale_transactions t ON t.transaction_id = ce.transaction_id
               JOIN sale_transaction_parcels link ON link.transaction_id = ce.transaction_id
               WHERE ce.investigation_id = ?
               ORDER BY ce.rank, link.pin""", (investigation_id,),
        ).fetchall()
        if len(evidence) != count:
            raise EvidenceStoreError("Persisted comparable identities do not match saved evidence")
        for rank, (row, comp) in enumerate(zip(evidence, result["comparables"]), 1):
            if row[:6] != (rank, result["tier"], comp["explanation"],
                           comp["document"], comp["sale_date"], comp["pin"]):
                raise EvidenceStoreError("Persisted comparable identities do not match saved evidence")
            current_snapshot, saved_snapshot, current_cents, saved_cents, sales_role = row[6:]
            # The original evidence must remain the same *transaction, source
            # snapshot and exact cent amount*, not merely the same PIN/document.
            # A transaction moved even to a different authorised sales snapshot
            # cannot quietly acquire new provenance.
            if (current_snapshot != saved_snapshot or not sales_role
                    or current_cents != saved_cents
                    or "sale_price" in comp
                    or _exact_money_cents(comp.get("sale_price_usd")) != saved_cents):
                raise EvidenceStoreError("Persisted comparable sale price or source snapshot changed")
        # Recheck the current build before returning frozen property evidence.
        # This also denies real/reclassified builds on ID-only reopen.
        self._build()
        return {"investigation_id": investigation_id, **result}
