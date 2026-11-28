"""Bounded Cook County source-shaped intake. No network or publication.
Operator supplies complete extracts and authentic before/after metadata.
"""
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json

from audit.phase0.audit import (
    SALES_REQUIRED, SALES_OPTIONAL, BUILDINGS_REQUIRED, BUILDINGS_OPTIONAL,
    building_rows_by_key, normalize_pin, sale_reject_reasons, whole_count,
)
from audit.phase1.expand import phase0_class203, enrich_joined

DATASETS = {"sales": "wvhk-k5uv", "assessment": "x54s-btds",
            "geography": "nj4t-kc8j", "address": "3723-97qp"}
REQUIRED = {"sales": SALES_REQUIRED, "assessment": BUILDINGS_REQUIRED,
            "geography": {"pin", "year", "nbhd_code", "lat", "lon"},
            "address": {"pin", "year", "prop_address_full"}}
OPTIONAL = {"sales": SALES_OPTIONAL, "assessment": BUILDINGS_OPTIONAL,
            "geography": set(), "address": set()}
CAPS = {"sales": 5000, "assessment": 40000, "geography": 7500, "address": 7500}
POLICY = "township17-class203-2024-2025-intake-v1"


class IntakeRefused(ValueError):
    """Safe category only; no raw row data."""


def digest(value):
    try:
        return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                 allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError):
        raise IntakeRefused("noncanonical_source_value") from None


def exact_cents(value):
    """Original source string/integer, not the matcher's float."""
    if isinstance(value, (float, bool)) or not isinstance(value, (str, int, Decimal)):
        raise IntakeRefused("invalid_money_representation")
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or not 20_000 <= amount <= 5_000_000:
            raise IntakeRefused("invalid_money")
        # Bound representation before ratio expansion; refuse sub-cent values.
        if len(str(value)) > 100 or amount.as_tuple().exponent < -100:
            raise IntakeRefused("invalid_money")
        numerator, denominator = amount.as_integer_ratio()
        cents, remainder = divmod(numerator * 100, denominator)
        if remainder:
            raise IntakeRefused("invalid_money")
        return cents
    except (InvalidOperation, TypeError, ValueError, OverflowError):
        raise IntakeRefused("invalid_money") from None


def _metadata(before, after):
    if not isinstance(before, dict) or set(before) != set(DATASETS.values()) or before != after:
        raise IntakeRefused("source_revision_or_schema_changed")
    for role, dataset in DATASETS.items():
        meta = before[dataset]
        if not isinstance(meta, dict) or set(meta) != {"epoch", "fields"}:
            raise IntakeRefused("invalid_source_metadata")
        fields = meta["fields"]
        if type(meta["epoch"]) is not int or meta["epoch"] <= 0 or not isinstance(fields, (list, tuple)):
            raise IntakeRefused("invalid_source_metadata")
        if any(not isinstance(field, str) for field in fields) or not REQUIRED[role] <= set(fields):
            raise IntakeRefused("missing_required_source_fields")


def _sale_key(row):
    return normalize_pin(row["pin"]), str(row["doc_no"]), str(row["sale_date"])[:10]


def _key(row):
    return normalize_pin(row.get("pin")), whole_count(row.get("year"))


def prepare_intake(*, rows, metadata_before, metadata_after, extracted_at_utc):
    """Deterministic inactive plan. Caller must verify pagination completeness."""
    _metadata(metadata_before, metadata_after)
    try:
        extracted = datetime.fromisoformat(extracted_at_utc.replace("Z", "+00:00"))
        if extracted.utcoffset() != timezone.utc.utcoffset(None):
            raise ValueError
    except (AttributeError, TypeError, ValueError):
        raise IntakeRefused("invalid_extraction_time") from None
    if not isinstance(rows, dict) or set(rows) != set(DATASETS):
        raise IntakeRefused("unexpected_source_roles")
    manifests = {}
    for role, dataset in DATASETS.items():
        batch = rows[role]
        if not isinstance(batch, list) or len(batch) >= CAPS[role]:
            raise IntakeRefused("source_row_cap_or_shape")
        allowed = REQUIRED[role] | OPTIONAL[role]
        fields = set(metadata_before[dataset]["fields"])
        for row in batch:
            # Socrata omits null-valued selected fields. Metadata proves
            # schema presence; individual nulls follow canonical screening.
            if not isinstance(row, dict) or not set(row) <= allowed & fields:
                raise IntakeRefused("unexpected_source_fields")
            if role in ("sales", "assessment") and whole_count(row.get("township_code")) != 17:
                raise IntakeRefused("unexpected_township")
            if role == "sales" and str(row.get("sale_date",""))[:4] not in ("2024", "2025"):
                raise IntakeRefused("unexpected_sale_year")
            if role != "sales" and (not _key(row)[0] or _key(row)[1] not in (2023, 2024)):
                raise IntakeRefused("unexpected_parcel_year")
        manifests[role] = {"dataset_id": dataset, "source_epoch": metadata_before[dataset]["epoch"],
                           "selected_fields": sorted(set().union(*(set(row) for row in batch))),
                           "row_count": len(batch), "content_sha256": digest(sorted(digest(row) for row in batch)),
                           "extracted_at_utc": extracted.isoformat(), "historical_asof_verified": False,
                           "public_display_approved": False}
    screened = {}
    for row in rows["sales"]:
        if sale_reject_reasons(row):
            continue
        key = _sale_key(row)
        cents = exact_cents(row["sale_price"])
        # Canonical matching requires the township encoding to agree. Do not
        # silently coerce a representation not qualified by the existing study.
        if str(row["township_code"]) != "17":
            raise IntakeRefused("noncanonical_sale_township")
        if key in screened and screened[key] != cents:
            raise IntakeRefused("conflicting_sale_identity")
        screened[key] = cents
    cohort = phase0_class203(rows["sales"], rows["assessment"])
    if not cohort:
        raise IntakeRefused("empty_eligible_cohort")
    keys = {(r["pin"], r["characteristics_year"]) for r in cohort}
    if len(keys) > 500:
        raise IntakeRefused("cohort_key_cap")
    for role in ("geography", "address"):
        if any(_key(r) not in keys for r in rows[role]):
            raise IntakeRefused("unexpected_enrichment_key")
    enhanced, _ = enrich_joined(cohort, rows["geography"], [])
    buildings = building_rows_by_key(rows["assessment"])
    addresses = defaultdict(list)
    for row in rows["address"]:
        addresses[_key(row)].append(row)
    sales, parcels = [], {}
    for row in enhanced:
        key = row["pin"], row["characteristics_year"]
        sale_key = row["pin"], row["doc_no"], row["sale_date"]
        card = buildings[key][0].get("card")
        if card is None or not str(card).strip():
            raise IntakeRefused("missing_assessment_card")
        sales.append({"pin": row["pin"], "sale_date": row["sale_date"],
                      "document_number": row["doc_no"], "sale_price_usd_cents": screened[sale_key],
                      "source_row_id": "derived-" + digest(sale_key), "assessment_year": key[1]})
        candidates = addresses[key]
        label = candidates[0].get("prop_address_full") if len(candidates) == 1 else None
        if label is not None and not isinstance(label,str):
            raise IntakeRefused("invalid_address_type")
        label = label.strip() if isinstance(label, str) else None
        state = "ambiguous" if len(candidates) > 1 else "missing" if not candidates else "one_nonblank" if label else "blank"
        parcels[key] = {"pin": key[0], "tax_year": key[1], "township_code": "17",
                        "card_number": str(card), "assessor_class": row["class"],
                        "building_area_sqft": row["sqft"], "building_identity_verified": False,
                        "neighborhood_code": row["nbhd_code"], "latitude": row["lat"], "longitude": row["lon"],
                        "address_state": state, "display_address": label if state == "one_nonblank" else None}
    plan = {"policy": POLICY, "build_kind": "historical_research", "active": False,
            "public_display_approved": False, "historical_asof_verified": False,
            "source_manifests": manifests, "sales": sorted(sales, key=lambda r: r["source_row_id"]),
            "parcel_years": [parcels[key] for key in sorted(parcels)]}
    plan["build_hash_sha256"] = digest(plan)
    return plan
