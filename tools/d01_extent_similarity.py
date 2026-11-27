"""Private aggregate reported-extent sensitivity, not historical comparable validation."""
from collections import Counter
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from tools import d01_transaction_availability as tx

FILTERS = ("earlier_only", "dwelling_25pct", "dwelling_and_erf_25pct")


def observed_coverage(subjects, pool_rows, parcels, bins):
    zero, small, medium, large = bins
    block = {"subject_rows": subjects, "pool_rows": pool_rows,
             "pool_distinct_candidate_parcels": parcels,
             "exclusive_counts": dict(zip(("zero", "one_to_two", "three_to_four", "five_or_more"), bins)),
             "at_least_one": small + medium + large, "at_least_three": medium + large,
             "at_least_five": large, "insufficient_for_three": zero + small,
             "insufficient_for_five": zero + small + medium}
    return {str(days): dict(block) for days in tx.WINDOWS}


def observed_stratum(n, parcels, repeats, years, exact_bins, combined_bins):
    return {"reported_sale_rows": n, "distinct_candidate_parcels": parcels,
            "repeat_candidate_parcels_distinct_reported_dates": repeats,
            "reported_year_counts": dict(zip(("2023", "2024", "2025", "2026"), years)),
            "same_candidate_parcel_day_excluded_rows": 0,
            "availability_eligible_subject_rows": n,
            "availability_eligible_distinct_candidate_parcels": parcels,
            "earlier_exact_pool": observed_coverage(n, 266, 260, exact_bins),
            "earlier_combined_sensitivity_pool": observed_coverage(n, 340, 330, combined_bins)}


AVAILABILITY_BASELINE = {
    "status": "RETROSPECTIVE_REPORTED_DATE_AVAILABILITY_ONLY",
    "source_quality_flags_nonexclusive": {
        "all_reported_rows": 839, "screened_rows": 420, "excluded_from_screened_rows": 419,
        "preliminary_rows": 422, "exact_duplicate_flagged_rows": 2,
        "ambiguous_event_flagged_rows": 2, "formula_like_flagged_rows": 0,
        "positive_reported_consideration_rows": 791, "positive_reported_erf_extent_rows": 839,
        "positive_reported_dwelling_extent_rows": 740, "positive_both_reported_extents_rows": 740,
        "valid_reported_date_rows": 839},
    "strict_unique_screened_same_parcel_day_groups": 0,
    "strict_unique_screened_same_parcel_day_rows": 0,
    "corroborated_same_parcel_day_groups_excluded": 0,
    "strata": {
        "exact": observed_stratum(266, 260, 6, (82, 74, 72, 38), (1, 2, 2, 261), (0, 1, 2, 263)),
        "alias_only": observed_stratum(74, 70, 4, (22, 18, 28, 6), (2, 0, 0, 72), (1, 1, 0, 72)),
        "combined": observed_stratum(340, 330, 10, (104, 92, 100, 44), (3, 2, 2, 333), (1, 2, 2, 335))},
    "corroborated_positive_consideration_and_both_extents_rows": 340,
    "baseline_reproduced": True, "verified_completed_sales": 0,
    "historical_as_of_availability_verified": False,
    "unknown": ["reported date event semantics", "transfer status", "arm's-length eligibility",
                "historical extent observation date", "historical source availability", "legal continuity"],
    "limitations": "Sale-row candidate counts only; no distance, size similarity, price ranking, valuation or verified historical availability. Same-day screening limited to strict unique screened rows; original flags preserved."
}


def positive_extent(value):
    # Fraction of a finite decimal gives exact comparisons, including boundaries.
    if not isinstance(value, str):
        raise ValueError("EXTENT_UNSUPPORTED")
    try:
        d = Decimal(value)
        if not d.is_finite() or d <= 0:
            raise ValueError("EXTENT_UNSUPPORTED")
        return Fraction(d)
    except (InvalidOperation, OverflowError):
        raise ValueError("EXTENT_UNSUPPORTED") from None


def within25(subject, candidate):
    return 3 * subject <= 4 * candidate <= 5 * subject


def latest_maps(subject, pool, extents, days):
    """Filter events before selecting latest qualifying event for each other parcel."""
    oid, day, _ = subject
    a, b = extents[subject]
    maps = [dict() for _ in FILTERS]
    for event in pool:
        other, when, _ = event
        if other == oid or not 0 < (day - when).days <= days:
            continue
        x, y = extents[event]
        checks = (True, within25(a, x), within25(a, x) and within25(b, y))
        for selected, qualifies in zip(maps, checks):
            if qualifies and (other not in selected or when > selected[other]):
                selected[other] = when
    if not maps[2].keys() <= maps[1].keys() <= maps[0].keys():
        raise ValueError("EXTENT_NESTING")
    return maps


def coverage(subjects, pool, extents, days):
    counts = [[], [], []]
    changed_subjects = [0, 0, 0]
    changed_pairs = [0, 0, 0]
    for subject in subjects:
        maps = latest_maps(subject, pool, extents, days)
        for i, selected in enumerate(maps):
            counts[i].append(len(selected))
            changed = sum(when != maps[0][oid] for oid, when in selected.items())
            changed_subjects[i] += changed > 0
            changed_pairs[i] += changed
    output = {}
    for i, name in enumerate(FILTERS):
        ns = counts[i]
        bins = dict.fromkeys(("zero", "one_to_two", "three_to_four", "five_or_more"), 0)
        for n in ns:
            bins["zero" if n == 0 else "one_to_two" if n < 3 else
                 "three_to_four" if n < 5 else "five_or_more"] += 1
        output[name] = {
            "subject_rows": len(ns), "pool_rows": len(pool),
            "pool_distinct_candidate_parcels": len({e[0] for e in pool}),
            "exclusive_counts": bins, "at_least_one": sum(n >= 1 for n in ns),
            "at_least_three": sum(n >= 3 for n in ns), "at_least_five": sum(n >= 5 for n in ns),
            "insufficient_for_three": sum(n < 3 for n in ns),
            "insufficient_for_five": sum(n < 5 for n in ns),
            "subjects_with_older_qualifying_event": changed_subjects[i],
            "subject_candidate_pairs_with_older_qualifying_event": changed_pairs[i],
        }
    return output


def assess_similarity(events, strict_events, extents, availability):
    if availability != AVAILABILITY_BASELINE:
        raise ValueError("EXTENT_AVAILABILITY_BASELINE_MISMATCH")
    days = Counter(strict_events)
    eligible = [e for e in events if days[e[:2]] == 1]
    if len(eligible) != len(set(eligible)) or not set(eligible) <= extents.keys():
        raise ValueError("EXTENT_EVENT_ACCOUNTING")
    parsed = {e: tuple(positive_extent(v) for v in extents[e]) for e in eligible}
    if any(len(v) != 2 for v in parsed.values()):
        raise ValueError("EXTENT_EVENT_STRUCTURE")
    exact = [e for e in eligible if e[2] == "exact"]
    alias = [e for e in eligible if e[2] == "alias_only"]
    strata = {}
    for name, subjects in (("exact", exact), ("alias_only", alias), ("combined", eligible)):
        strata[name] = {}
        for pool_name, pool in (("earlier_exact_pool", exact),
                                ("earlier_combined_sensitivity_pool", eligible)):
            strata[name][pool_name] = {}
            for window in tx.WINDOWS:
                output = coverage(subjects, pool, parsed, window)
                old = availability["strata"][name][pool_name][str(window)]
                if any(output["earlier_only"][k] != v for k, v in old.items()):
                    raise ValueError("EXTENT_COVERAGE_BASELINE_MISMATCH")
                strata[name][pool_name][str(window)] = output
    return {"status": "REPORTED_EXTENT_SIMILARITY_FEASIBILITY_ONLY",
            "baseline_reproduced": True, "tolerance_percent": 25,
            "primary_window_days": 365, "sensitivity_window_days": 730,
            "strata": strata, "verified_completed_sales": 0,
            "historical_as_of_availability_verified": False,
            "limitations": "Reported dwelling and erf extents only; observation dates, units equivalence to living area, legal continuity, transfer and historical availability unverified. No spatial distance, price ranking, valuation or policy adoption. Older qualifying event counts are relative to latest earlier event among retained candidates."}
