"""Private offline aggregate-only Pinelands identity corroboration."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import io
import json
import os
from pathlib import Path
import re

from tools import d01_register as sales
from tools import d01_file_profile as sf
from tools import d02_register as parcels
from tools import d02_file_profile as pf
from tools import hpi_data_manager as dm
from tools.world_bank_pilot import unique, reject_constant

REGION = "C0160046"
BASELINE = (420, 409, 1, 10)
STATES = ("unique", "ambiguous", "unmatched")
ADDRESS_STATES = ("agree", "mismatch", "missing", "ambiguous", "unsupported")
FIELDS = ("ADR_NO", "ADR_NO_SFX", "STR_NAME", "LU_STR_NAME_TYPE", "OFC_SBRB_NAME")


MISMATCH_REASONS = ("house_number_only", "street_name_tokens_only", "street_type_token_only",
                    "multiple_components", "unknown_component_boundary")
UNSUPPORTED_REASONS = ("sale_structure_only", "parcel_structure_only", "both_structures", "unknown")
DIAGNOSTIC_BASELINE = {
    "screened_sale_rows": 420, "parcel_features": 3442,
    "legacy": {"unique": 409, "ambiguous": 1, "unmatched": 10},
    "strict": {"unique": 409, "ambiguous": 1, "unmatched": 10},
    "legacy_to_strict": {k: {j: n if k == j else 0 for j in STATES}
                         for k, n in zip(STATES, (409, 1, 10))},
    "parcel_region_quality": {"malformed": 87, "wrong_region": 8,
                              "nonzero_portion_or_suffix": 13, "eligible": 3334},
    "legacy_method_conflicts": 0, "strict_exact_reference_conflicts": 0,
    "strict_unique_spatial_candidates": 409, "address_schema": "available",
    "address_assessed_denominator": 409,
    "address_outcomes": {"agree": 266, "mismatch": 138, "missing": 0, "ambiguous": 0, "unsupported": 5},
    "region_and_address_corroborated": 266, "region_and_address_spatial_candidates": 266,
}


def mismatch_reason(left, right, parcel_type):
    """Lexical component diagnosis only, never a new identity or alias rule."""
    if not left or not right or not parcel_type or len(parcel_type.split()) != 1:
        return "unknown_component_boundary"
    l, r = left.split(), right.split()
    if (len(l) < 4 or len(r) < 4 or l[-1] != r[-1] or
            l[-1] != "pinelands" or r[-2] != parcel_type):
        return "unknown_component_boundary"
    # Sales address is unstructured: last pre-suburb token is a type
    # hypothesis, not an independently verified street type.
    differences = (l[0] != r[0], l[1:-2] != r[1:-2], l[-2] != r[-2])
    if sum(differences) > 1:
        return "multiple_components"
    if sum(differences) == 1:
        return MISMATCH_REASONS[differences.index(True)]
    return "unknown_component_boundary"


def unsupported_reason(left, right):
    if left == right == "unsupported":
        return "both_structures"
    if left == "unsupported" and right == "comparable":
        return "sale_structure_only"
    if right == "unsupported" and left == "comparable":
        return "parcel_structure_only"
    return "unknown"


def parse(raw):
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique,
                      parse_constant=reject_constant)


def norm(value):
    return " ".join(value.casefold().split()) if isinstance(value, str) else ""


def simple_address(value):
    if not isinstance(value, str) or not value.strip():
        return "missing", None
    text = norm(value)
    if not re.fullmatch(r"[1-9][0-9]* [a-z]+(?: [a-z]+)+ pinelands", text):
        return "unsupported", None
    return "comparable", text


def address_schema(features):
    names = {k for f in features for k in f["properties"]}
    fields = {}
    for key in (*FIELDS, "ADR_NO_PRF"):
        hits = [n for n in names if n.casefold() == key.casefold()]
        if len(hits) > 1:
            return "ambiguous", {}
        if hits:
            fields[key] = hits[0]
    if not all(k in fields for k in FIELDS):
        return "missing", {}
    return "available", fields


def parcel_address(p, schema, fields):
    if schema != "available":
        return schema, None
    if any(v not in p for v in fields.values()):
        return "missing", None
    number = p[fields["ADR_NO"]]
    street, kind, suburb = (p[fields[k]] for k in FIELDS[2:])
    if number is None or not all(norm(v) for v in (street, kind, suburb)):
        return "missing", None
    for k in ("ADR_NO_PRF", "ADR_NO_SFX"):
        if k in fields:
            v = p[fields[k]]
            if v is not None and (not isinstance(v, str) or v.strip()):
                return "unsupported", None
    if type(number) is not int or number <= 0 or norm(suburb) != "pinelands":
        return "unsupported", None
    if not all(re.fullmatch(r"[a-z]+(?: [a-z]+)*", norm(v)) for v in (street, kind)):
        return "unsupported", None
    return simple_address(f"{number} {street} {kind} {suburb}")


def assess(rows, parcel, raw_parcel, addresses, expected=BASELINE, diagnose=False):
    cohort = [row for row in rows if row["quality_flags"]["screened_candidate"]]
    baseline = sales.match(rows, parcel)["screened_cohort"]
    if expected is not None and tuple(baseline[k] for k in
            ("rows", "candidate_unique", "candidate_ambiguous", "candidate_unmatched")) != expected:
        raise ValueError("LEGACY_BASELINE_MISMATCH")
    raw_features = raw_parcel["features"]
    if len(raw_features) != len(parcel["features"]) or len(addresses) != len(rows):
        raise ValueError("SOURCE_ALIGNMENT")
    oid_names = {k for f in raw_features for k in f["properties"]
                 if k.casefold() in pf.ALIASES["OBJECTID"]}
    if len(oid_names) != 1:
        raise ValueError("SOURCE_ALIGNMENT")
    oid_field = next(iter(oid_names))
    schema, fields = address_schema(raw_features)
    old_erf, strict_erf = defaultdict(set), defaultdict(set)
    exact = {k: defaultdict(set) for k in sales.KEYS}
    flags, raw_address, address_index = {}, {}, defaultdict(set)
    parcel_types = {}
    region = Counter(dict.fromkeys(("malformed", "wrong_region", "nonzero_portion_or_suffix", "eligible"), 0))
    for feature, raw_feature in zip(parcel["features"], raw_features):
        p, rp = feature["properties"], raw_feature["properties"]
        oid = p["OBJECTID"]
        if type(rp.get(oid_field)) is not int or rp[oid_field] != oid or oid in flags:
            raise ValueError("SOURCE_ALIGNMENT")
        flags[oid] = p["quality_flags"]
        for key in sales.KEYS:
            exact[key][str(p[key])].add(oid)
        sg = sales.SG26.fullmatch(p["SG26_CODE"])
        if sg and sg.group(2) == sg.group(3) == "00000":
            old_erf[int(sg.group(1))].add(oid)
        if not sg:
            region["malformed"] += 1
        elif not p["SG26_CODE"].startswith(REGION):
            region["wrong_region"] += 1
        elif sg.group(2) != "00000" or sg.group(3) != "00000":
            region["nonzero_portion_or_suffix"] += 1
        else:
            region["eligible"] += 1
            strict_erf[int(sg.group(1))].add(oid)
        state, key = parcel_address(rp, schema, fields)
        raw_address[oid] = state, key
        if diagnose and state == "comparable":
            parcel_types[oid] = norm(rp[fields["LU_STR_NAME_TYPE"]])
        if key is not None:
            address_index[key].add(oid)

    def classify(hits):
        if not hits:
            return "unmatched"
        if len(hits) != 1 or not flags[next(iter(hits))]["unique_key_candidate"]:
            return "ambiguous"
        return "unique"

    sale_addresses, sale_address_erfs = {}, defaultdict(set)
    for row in cohort:
        ordinal = row["source_row_ordinal"]
        if not 1 <= ordinal <= len(addresses):
            raise ValueError("SOURCE_ALIGNMENT")
        state, key = simple_address(addresses[ordinal - 1])
        sale_addresses[ordinal] = state, key
        e = sales.ERF.fullmatch(row["registered_description"].strip())
        if key is not None and e:
            sale_address_erfs[key].add(int(e.group(1)))

    transitions = {k: dict.fromkeys(STATES, 0) for k in STATES}
    strict = Counter(dict.fromkeys(STATES, 0))
    addr = Counter(dict.fromkeys(ADDRESS_STATES, 0))
    mismatch_counts = Counter(dict.fromkeys(MISMATCH_REASONS, 0))
    unsupported_counts = Counter(dict.fromkeys(UNSUPPORTED_REASONS, 0))
    spatial = agreed_spatial = exact_conflicts = legacy_conflicts = 0
    for row in cohort:
        e = sales.ERF.fullmatch(row["registered_description"].strip())
        erf = int(e.group(1)) if e and row["quality_flags"]["pinelands_address_suffix"] else None
        hits = set().union(*(exact[k].get(row["valuation_reference"], set()) for k in sales.KEYS))
        old, new = old_erf.get(erf, set()), strict_erf.get(erf, set())
        old_conflict = bool(hits and old and hits != old)
        old_state = "ambiguous" if old_conflict else classify(hits | old)
        legacy_conflicts += old_conflict
        conflict = bool(hits and hits != new)
        exact_conflicts += conflict
        # An exact reference alone never overrides region or duplicate checks.
        new_state = "ambiguous" if conflict and new else classify(new)
        transitions[old_state][new_state] += 1
        strict[new_state] += 1
        if new_state != "unique":
            continue
        oid = next(iter(new))
        is_spatial = flags[oid]["spatial_candidate"] is True
        spatial += is_spatial
        left, lk = sale_addresses[row["source_row_ordinal"]]
        right, rk = raw_address[oid]
        if "ambiguous" in (left, right):
            outcome = "ambiguous"
        elif "missing" in (left, right):
            outcome = "missing"
        elif left != "comparable" or right != "comparable":
            outcome = "unsupported"
        elif len(address_index[rk]) != 1 or len(sale_address_erfs[lk]) != 1:
            outcome = "ambiguous"
        elif lk != rk:
            outcome = "mismatch"
        else:
            outcome = "agree"
        addr[outcome] += 1
        if diagnose and outcome == "mismatch":
            mismatch_counts[mismatch_reason(lk, rk, parcel_types.get(oid))] += 1
        elif diagnose and outcome == "unsupported":
            unsupported_counts[unsupported_reason(left, right)] += 1
        agreed_spatial += outcome == "agree" and is_spatial
    if any(sum(transitions[k].values()) != baseline["candidate_" + k] for k in STATES):
        raise ValueError("LEGACY_ACCOUNTING")
    if sum(strict.values()) != len(cohort) or sum(addr.values()) != strict["unique"]:
        raise ValueError("COHORT_ACCOUNTING")
    result = {"status": "CANDIDATE_CORROBORATION_ONLY", "screened_sale_rows": len(cohort),
            "parcel_features": len(flags), "legacy": {k: baseline["candidate_" + k] for k in STATES},
            "legacy_to_strict": transitions, "strict_region": REGION,
            "parcel_region_quality": dict(region), "strict": dict(strict),
            "legacy_method_conflicts": legacy_conflicts, "strict_exact_reference_conflicts": exact_conflicts,
            "strict_unique_spatial_candidates": spatial, "address_schema": schema,
            "address_assessed_denominator": strict["unique"], "address_outcomes": dict(addr),
            "region_and_address_corroborated": addr["agree"],
            "region_and_address_spatial_candidates": agreed_spatial,
            "verified_identity_matches": 0, "persistent_join": False,
            "network_requests": 0, "files_modified": False,
            "limitation": "Current snapshot candidates only; no legal identity, temporal continuity, sale eligibility or buyer-use qualification."}

    if diagnose:
        if any(result[k] != v for k, v in DIAGNOSTIC_BASELINE.items()):
            raise ValueError("ADDRESS_DIAGNOSTIC_BASELINE_MISMATCH")
        if (sum(mismatch_counts.values()) != addr["mismatch"] or
                sum(unsupported_counts.values()) != addr["unsupported"]):
            raise ValueError("ADDRESS_DIAGNOSTIC_ACCOUNTING")
        result["mismatch_diagnosis"] = {
            "status": "AGGREGATE_LEXICAL_DIAGNOSIS_ONLY",
            "mismatch_denominator": addr["mismatch"],
            "mismatch_reasons": dict(mismatch_counts),
            "unsupported_denominator": addr["unsupported"],
            "unsupported_reasons": dict(unsupported_counts),
            "baseline_reproduced": True,
            "new_matches": 0,
            "limitations": "Lexical differences, not causes; sales terminal token is a type hypothesis. No aliases, fuzzy matching, historical address inference or identity promotion."}
    return result


def run(root, today=None, expected=BASELINE, diagnose=False):
    root = dm.workspace(root)
    today = today or date.today()
    if not sf.INTAKE <= today < sf.REVIEW:
        raise ValueError("RETENTION_WINDOW")
    for spec in (dm.parcel_spec(), dm.sale_spec()):
        if dm.audit_registered(root, spec, today=today)["status"] != "integrity checks passed":
            raise ValueError("AUDIT_REQUIRED")
    p_raw = dm.read_bounded(root / dm.PARCEL_RAW, dm.PARCEL_LIMIT)
    s_raw = dm.read_bounded(root / dm.SALE_RAW, sf.CAP)
    if (dm.sha(p_raw) != dm.PARCEL_SHA or len(p_raw) != pf.OBSERVED_BYTES or
            dm.sha(s_raw) != dm.SALE_SHA or len(s_raw) != sf.OBSERVED_BYTES):
        raise ValueError("SNAPSHOT_MISMATCH")
    projection, pq = parcels.derive(p_raw)
    rows, _ = sales.derive(s_raw)
    if pq["retained_features"] != pf.DISPLAYED_ROWS:
        raise ValueError("PARCEL_COUNT")
    if (projection != dm.read_bounded(root / dm.PARCEL_OUTPUT, 50 * dm.MIB) or
            dm.json_bytes({"dataset_id": "HPI-DATA-011", "reported_sales": rows}) !=
            dm.read_bounded(root / dm.SALE_OUTPUT, 50 * dm.MIB)):
        raise ValueError("PROJECTION_MISMATCH")
    reader = csv.reader(io.StringIO(s_raw.decode("utf-8-sig"), newline=""), strict=True)
    if tuple(next(reader)) != sf.HEADERS:
        raise ValueError("HEADER_MISMATCH")
    result = assess(rows, parse(projection), parse(p_raw), [row[1] for row in reader], expected, diagnose=diagnose)
    result["registered_audits"] = {"HPI-DATA-010": "passed", "HPI-DATA-011": "passed"}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--diagnose-mismatches", action="store_true", help="Approved bounded aggregate lexical diagnosis only")
    args = parser.parse_args()
    if os.name != "nt" or os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        print("STOP: owner-local Windows only.")
        return 1
    try:
        print(json.dumps(run(args.root, diagnose=args.diagnose_mismatches), indent=2))
        return 0
    except Exception:
        print("STOP: local audit, retention, snapshot, projection or cohort precondition failed; no private values emitted.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
