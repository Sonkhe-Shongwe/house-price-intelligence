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


def assess(rows, parcel, raw_parcel, addresses, expected=BASELINE):
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
        agreed_spatial += outcome == "agree" and is_spatial
    if any(sum(transitions[k].values()) != baseline["candidate_" + k] for k in STATES):
        raise ValueError("LEGACY_ACCOUNTING")
    if sum(strict.values()) != len(cohort) or sum(addr.values()) != strict["unique"]:
        raise ValueError("COHORT_ACCOUNTING")
    return {"status": "CANDIDATE_CORROBORATION_ONLY", "screened_sale_rows": len(cohort),
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


def run(root, today=None, expected=BASELINE):
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
    result = assess(rows, parse(projection), parse(p_raw), [row[1] for row in reader], expected)
    result["registered_audits"] = {"HPI-DATA-010": "passed", "HPI-DATA-011": "passed"}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if os.name != "nt" or os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        print("STOP: owner-local Windows only.")
        return 1
    try:
        print(json.dumps(run(args.root), indent=2))
        return 0
    except Exception:
        print("STOP: local audit, retention, snapshot, projection or cohort precondition failed; no private values emitted.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
