"""P3 candidate: property investigation contract against the Phase 2 research matcher.

Pure, stdlib-only, no network or persistence. Real publisher-level sale details
are never released by this adapter; only explicitly synthetic fixtures can
render individual comparable records. NOT a production API or approved design.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from math import isfinite
import re
from typing import Any, Mapping, Sequence

from audit.phase2.matcher import MatchPolicy, match_property

SCOPE_TOWNSHIP = "17"
SCOPE_CLASS = "203"
STATUS = frozenset({"supported_neighbourhood", "exploratory_spatial", "insufficient_data", "out_of_coverage"})
PIN_PATTERN = re.compile(r"^[0-9]{14}$")
BUILD_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{1,100}$")


class ContractError(ValueError):
    def __init__(self, field: str, code: str):
        self.field = field
        self.code = code
        super().__init__(f"{field}: {code}")


def _string(value: Any, field: str, *, max_len: int = 120) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_len:
        raise ContractError(field, "invalid_string")
    return value.strip()


def _price(value: Any, field: str) -> str | None:
    """Money is decimal text, never a binary float or a guessed appraisal."""
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", value):
        raise ContractError(field, "invalid_decimal_amount")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ContractError(field, "invalid_decimal_amount") from exc
    if amount <= 0 or amount > Decimal("1000000000"):
        raise ContractError(field, "amount_out_of_range")
    return f"{amount:.2f}"


def _area(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ContractError(field, "invalid_area")
    area = float(value)
    if not isfinite(area) or area <= 0 or area > 100000:
        raise ContractError(field, "invalid_area")
    return area


def validate_request(payload: Mapping[str, Any], *, today: date | None = None) -> dict[str, Any]:
    """Validate user-reported fields; do not trust location codes from a browser.

    A parcel may be unknown, in which case the inquiry can still be saved, but
    we cannot assert it is a verified property or serve comparable-level data.
    """
    if not isinstance(payload, dict):
        raise ContractError("request", "object_required")
    permitted = {"subject", "analysis_date", "township_code", "class_code"}
    if set(payload) - permitted:
        raise ContractError("request", "unknown_fields")
    subj = payload.get("subject")
    if not isinstance(subj, dict):
        raise ContractError("subject", "object_required")
    allowed = {"pin", "address_id", "building_area_sqft", "asking_price_usd", "label"}
    if set(subj) - allowed:
        # No user-supplied neighbourhood/lat/lon. Those must be resolved from a vetted source.
        raise ContractError("subject", "unknown_fields")
    township = _string(payload.get("township_code"), "township_code", max_len=8)
    class_code = _string(payload.get("class_code"), "class_code", max_len=8)
    raw_when = _string(payload.get("analysis_date"), "analysis_date", max_len=10)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_when):
        raise ContractError("analysis_date", "invalid_iso_date")
    try:
        when = date.fromisoformat(raw_when)
    except ValueError as exc:
        raise ContractError("analysis_date", "invalid_iso_date") from exc
    if when > (today or date.today()):
        raise ContractError("analysis_date", "future_analysis_date")
    pin = subj.get("pin")
    if pin is not None and (not isinstance(pin, str) or not PIN_PATTERN.fullmatch(pin)):
        raise ContractError("subject.pin", "invalid_pin")
    address_id = subj.get("address_id")
    if address_id is not None and (not isinstance(address_id, str)
                                  or not re.fullmatch(r"[a-z0-9-]{1,40}", address_id)):
        raise ContractError("subject.address_id", "invalid_address_id")
    area = _area(subj.get("building_area_sqft"), "subject.building_area_sqft")
    label = subj.get("label")
    if label is not None:
        label = _string(label, "subject.label")
    subject = {
        "pin": pin, "building_area_sqft": area,
        "asking_price_usd": _price(subj.get("asking_price_usd"), "subject.asking_price_usd"),
        "label": label,
    }
    if address_id is not None:
        subject["address_id"] = address_id
    return {
        "township_code": township,
        "class_code": class_code,
        "analysis_date": when.isoformat(),
        "subject": subject,
    }


def _validate_build(data_build: Mapping[str, Any], *, today: date | None = None) -> dict[str, Any]:
    """Validate a server-selected curated evidence build (not a raw source snapshot).

    A build may combine transaction, improvement and geographic snapshots. The
    caller must fetch this from trusted application storage, not HTTP input.
    """
    if not isinstance(data_build, dict):
        raise ContractError("data_build", "object_required")
    identifier = _string(data_build.get("build_id"), "data_build.build_id", max_len=100)
    if not BUILD_PATTERN.fullmatch(identifier):
        raise ContractError("data_build.build_id", "invalid_build_id")
    timestamp = _string(data_build.get("built_at_utc"), "data_build.built_at_utc", max_len=40)
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("offset required")
    except ValueError as exc:
        raise ContractError("data_build.built_at_utc", "offset_timestamp_required") from exc
    if parsed.date() > (today or date.today()):
        raise ContractError("data_build.built_at_utc", "future_build")
    source_kind = _string(data_build.get("source_kind"), "data_build.source_kind", max_len=24)
    if source_kind not in {"historical_research", "synthetic_fixture"}:
        raise ContractError("data_build.source_kind", "unsupported_source_kind")
    source_ids = data_build.get("source_snapshot_ids")
    if not isinstance(source_ids, list) or not source_ids or len(source_ids) > 10:
        raise ContractError("data_build.source_snapshot_ids", "invalid_source_list")
    if (any(not isinstance(x, str) or not BUILD_PATTERN.fullmatch(x) for x in source_ids)
            or len(source_ids) != len(set(source_ids))):
        raise ContractError("data_build.source_snapshot_ids", "invalid_source_list")
    return {"build_id": identifier, "built_at_utc": timestamp,
            "source_kind": source_kind, "source_snapshot_ids": list(source_ids),
            "historical_as_of_verified": False,
            "public_property_display_approved": False}


def _require_build_membership(row: Mapping[str, Any], build_id: str, field: str) -> None:
    if not isinstance(row, dict) or row.get("build_id") != build_id:
        raise ContractError(field, "missing_or_mismatched_build")


def _validate_candidates(sales: Sequence[Mapping[str, Any]], build_id: str) -> None:
    for index, row in enumerate(sales):
        field = f"candidate_sales[{index}]"
        _require_build_membership(row, build_id, field)
        # The source preprocessing is still provisional; reject features known
        # to belong to a later tax year than the recorded transaction.
        try:
            raw_date = row["sale_date"]
            if not isinstance(raw_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_date):
                raise ValueError("invalid ISO sale date")
            year = date.fromisoformat(raw_date).year
            characteristics_year = row.get("characteristics_year")
            if (characteristics_year is not None
                    and (type(characteristics_year) is not int or characteristics_year >= year)):
                raise ValueError("future or invalid tax-year characteristics")
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError(field, "invalid_sale_or_characteristics_year") from exc


def build_investigation(
    request: Mapping[str, Any], *, resolved_subject: Mapping[str, Any] | None,
    candidate_sales: Sequence[Mapping[str, Any]], data_build: Mapping[str, Any],
    synthetic_demo: bool = False, today: date | None = None,
) -> dict[str, Any]:
    """Produce a safe P3 response using the existing matcher unchanged.

    Matching only occurs with a *server-resolved* subject record. The response
    contains individual sale details solely for explicit SYNTHETIC fixtures.
    """
    validated = validate_request(request, today=today)
    provenance = _validate_build(data_build, today=today)
    if not isinstance(candidate_sales, (list, tuple)):
        raise ContractError("candidate_sales", "sequence_required")
    _validate_candidates(candidate_sales, provenance["build_id"])
    if not isinstance(synthetic_demo, bool):
        raise ContractError("synthetic_demo", "boolean_required")
    if synthetic_demo and provenance["source_kind"] != "synthetic_fixture":
        raise ContractError("synthetic_demo", "restricted_to_synthetic_fixture")
    response = {
        "contract_version": "p3-draft-v0.2", "status": "insufficient_data", "reason": None,
        "tier": "none", "analysis_date": validated["analysis_date"],
        "subject": {**validated["subject"], "asking_price_source": "user_reported"},
        "selected_count": 0, "comparables": [], "evidence_details_redacted": not synthetic_demo,
        "data_build": provenance, "valuation": None,
        "warnings": ["Historical source records may have been revised or backfilled; recorded sale date is not publication date."],
    }
    if validated["township_code"] != SCOPE_TOWNSHIP or validated["class_code"] != SCOPE_CLASS:
        response.update(status="out_of_coverage", reason="unsupported_market_or_class")
        return response
    if validated["subject"]["pin"] is None:
        response["reason"] = "parcel_identity_not_resolved"
        return response
    if not isinstance(resolved_subject, dict):
        response["reason"] = "parcel_not_found_in_curated_build"
        return response
    _require_build_membership(resolved_subject, provenance["build_id"], "resolved_subject")
    pin = validated["subject"]["pin"]
    if resolved_subject.get("pin") != pin:
        raise ContractError("resolved_subject.pin", "identity_conflict")
    if resolved_subject.get("class") != SCOPE_CLASS or resolved_subject.get("township_code") != SCOPE_TOWNSHIP:
        response.update(status="out_of_coverage", reason="resolved_property_out_of_scope")
        return response
    # The source-resolved location is required for trusted matching. User inputs
    # are only a report of their enquiry; unverified coordinates are forbidden.
    verified = dict(resolved_subject)
    verified["analysis_date"] = validated["analysis_date"]
    verified["sqft"] = _area(verified.get("sqft"), "resolved_subject.sqft")
    record_year = verified.get("characteristics_year")
    if record_year is not None and (not isinstance(record_year, int) or isinstance(record_year, bool)
                                   or record_year >= int(validated["analysis_date"][:4])):
        raise ContractError("resolved_subject.characteristics_year", "invalid_or_future_record_year")
    if abs(verified["sqft"] / validated["subject"]["building_area_sqft"] - 1) > 0.1:
        response["warnings"].append("User-entered floor area differs from the source record by more than 10%.")
    result = match_property(verified, candidate_sales, policy=MatchPolicy())
    response["selected_count"] = result["selected_count"]
    response["tier"] = result["tier"]
    response["reason"] = result["reason"]
    if result["status"] == "supported" and result["tier"] == "same_neighborhood":
        response["status"] = "supported_neighbourhood"
    elif result["status"] == "supported" and result["tier"] == "spatial_fallback":
        response["status"] = "exploratory_spatial"
        response["warnings"].append("Spatial fallback is exploratory only; its median price has not met validation criteria.")
    else:
        response["status"] = "insufficient_data"
    if synthetic_demo:
        # Explicit fixture-only use. No approved pathway to expose real records yet.
        response["comparables"] = result["comparables"]
    return response
