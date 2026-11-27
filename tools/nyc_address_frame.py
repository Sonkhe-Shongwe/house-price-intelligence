"""Offline PLUTO-only full recorded-address frame qualification design.

No network, file writes, CLI, approval, or real-data dispatch. All returned
statistics describe an invented rehearsal. The future approved collector must
independently enforce transport, schema, timing, revision and protection gates.
"""
from collections import Counter
from decimal import Decimal
import re

from tools.nyc_qualification import SUBJECT_FIELDS, QualificationError, require
from tools.nyc_collector import numeric_key, area_method

DATASET = "64uk-42ks"
REVISION = "1795476446:1795465895"
VERSION = "26v3"
WHERE = "borough = 'QN' AND zipcode = 11361"
MAX_ROWS = 10_000
MAX_REQUESTS = 5
MAX_BYTES = 10 * 1024 * 1024
MAX_SECONDS = 180


def count_parameters():
    return {"$select": "count(*) as n", "$where": WHERE, "$limit": "1"}


def row_parameters(count):
    require(type(count) is int and 0 < count <= MAX_ROWS, "frame_count_limit")
    # One complete page, no offset/tie instability, no eligibility predicate.
    return {"$select": ",".join(SUBJECT_FIELDS), "$where": WHERE,
            "$order": "bbl ASC", "$limit": str(count)}


def request_plan(count):
    """Fixed logical requests only. No HTTP implementation or activation."""
    rows = row_parameters(count)
    return ((f"/api/views/{DATASET}.json", None),
            (f"/resource/{DATASET}.json", count_parameters()),
            (f"/resource/{DATASET}.json", rows),
            (f"/resource/{DATASET}.json", count_parameters()),
            (f"/api/views/{DATASET}.json", None))


def _integer(value):
    if type(value) not in (int, str, Decimal):
        return None
    text = str(value)
    if len(text) > 32 or not re.fullmatch(r"[0-9]{1,15}(?:\.0+)?", text):
        return None
    return int(text.split(".")[0])


def _address(value):
    if value is None:
        return None
    require(type(value) is str and len(value) <= 200
            and all(c.isprintable() for c in value), "invalid_address_shape")
    label = " ".join(value.upper().split())
    return label or None


def _usable(label):
    # Queens hyphens are significant. No fuzzy matching, alias/range expansion,
    # or street-name-only entry. A number and a nonempty street name required.
    return bool(label and re.fullmatch(r"[0-9]+(?:-[0-9]+)?[A-Z]? .*[A-Z].*", label))


def _eligible(row):
    return (row.get("bldgclass") == "A2"
            and all(_integer(row.get(k)) == 1 for k in ("numbldgs", "unitsres", "unitstotal"))
            and (_integer(row.get("bldgarea")) or 0) > 0
            and area_method(row.get("areasource")) == "2")


def qualify_fixture_frame(rows, *, count_before, count_after, revision_before,
                          revision_after):
    """Count full frame before eligibility, returning no address or key.

    Caller-supplied counts/revisions model independent transport observations;
    they do not prove actual publisher access or actual frame completeness.
    """
    require(revision_before == revision_after == REVISION, "frame_revision_changed")
    row_parameters(count_before)
    require(type(count_after) is int and count_after == count_before, "frame_count_changed")
    require(type(rows) in (tuple, list) and len(rows) == count_before, "frame_incomplete")

    labels, keys = Counter(), Counter()
    candidates = []
    missing_address = unusable_address = invalid_key = 0
    for row in rows:
        require(type(row) is dict and set(row) <= set(SUBJECT_FIELDS), "unexpected_source_field")
        require(row.get("borough") == "QN" and _integer(row.get("zipcode")) == 11361,
                "frame_scope_conflict")
        require(row.get("version") == VERSION, "frame_version_conflict")
        # No nested payloads or unexpected structured objects in scalar fields.
        require(all(type(v) in (str, int, Decimal, type(None)) for v in row.values()),
                "invalid_source_scalar")
        label = _address(row.get("address"))
        try:
            key = numeric_key(row.get("bbl"))
        except QualificationError:
            key = None
        if label is None:
            missing_address += 1
        else:
            labels[label] += 1
            if not _usable(label):
                unusable_address += 1
        if key is None:
            invalid_key += 1
        else:
            keys[key] += 1
        if _eligible(row):
            candidates.append((label, key))

    outcomes = Counter()
    for label, key in candidates:
        if not _usable(label) or key is None:
            outcomes["invalid_identity"] += 1
        elif labels[label] != 1:
            outcomes["ambiguous_address"] += 1
        elif keys[key] != 1:
            outcomes["duplicate_bbl"] += 1
        else:
            outcomes["unique_eligible"] += 1

    return {
        "contract": "nyc-address-frame-rehearsal-v1",
        "fixture_only": True,
        "dataset": DATASET,
        "expected_revision": REVISION,
        "frame_rows": count_before,
        "eligible_shape_rows": len(candidates),
        "noneligible_shape_rows": count_before-len(candidates),
        "missing_address_rows": missing_address,
        "unusable_address_rows": unusable_address,
        "invalid_bbl_rows": invalid_key,
        "duplicate_address_groups": sum(n > 1 for n in labels.values()),
        "duplicate_bbl_groups": sum(n > 1 for n in keys.values()),
        "eligible_outcomes": {k: outcomes[k] for k in (
            "invalid_identity", "ambiguous_address", "duplicate_bbl", "unique_eligible")},
        "actual_entry_verified": False,
        "aliases_verified": False,
        "property_collection_authorised": False,
    }
