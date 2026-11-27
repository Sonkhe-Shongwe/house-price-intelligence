"""Aggregate retrospective reported-date availability; no prices or address values."""
from collections import Counter, defaultdict
from datetime import date

WINDOWS = (365, 730)
STRATA = ("exact", "alias_only")


def earlier_count(subject, pool, days):
    """Distinct other candidate parcels; latest strictly earlier event per parcel."""
    oid, day, _ = subject
    latest = {}
    for other, when, _ in pool:
        if other != oid and 0 < (day - when).days <= days:
            if other not in latest or when > latest[other]:
                latest[other] = when
    return len(latest)


def coverage(subjects, pool):
    result = {}
    for days in WINDOWS:
        counts = [earlier_count(subject, pool, days) for subject in subjects]
        bins = {"zero": 0, "one_to_two": 0, "three_to_four": 0, "five_or_more": 0}
        for n in counts:
            bins["zero" if n == 0 else "one_to_two" if n < 3 else
                 "three_to_four" if n < 5 else "five_or_more"] += 1
        result[str(days)] = {
            "subject_rows": len(counts), "pool_rows": len(pool),
            "pool_distinct_candidate_parcels": len({e[0] for e in pool}),
            "exclusive_counts": bins,
            "at_least_one": sum(n >= 1 for n in counts),
            "at_least_three": sum(n >= 3 for n in counts),
            "at_least_five": sum(n >= 5 for n in counts),
            "insufficient_for_three": sum(n < 3 for n in counts),
            "insufficient_for_five": sum(n < 5 for n in counts),
        }
    return result


def summarize(events, eligible):
    dates = defaultdict(set)
    for oid, day, _ in events:
        dates[oid].add(day)
    years = Counter(str(day.year) for _, day, _ in events)
    return {
        "reported_sale_rows": len(events),
        "distinct_candidate_parcels": len(dates),
        "repeat_candidate_parcels_distinct_reported_dates": sum(len(v) > 1 for v in dates.values()),
        "reported_year_counts": dict(sorted(years.items())),
        "same_candidate_parcel_day_excluded_rows": len(events) - len(eligible),
        "availability_eligible_subject_rows": len(eligible),
        "availability_eligible_distinct_candidate_parcels": len({e[0] for e in eligible}),
    }


def assess_availability(events, strict_events, rows):
    """Events are in-memory (candidate parcel, reported date, stratum) tuples only."""
    if any(s not in STRATA or type(d) is not date for _, d, s in events):
        raise ValueError("TRANSACTION_EVENT_STRUCTURE")
    all_days = Counter(strict_events)
    retained = Counter((oid, day) for oid, day, _ in events)
    if any(n > all_days[key] for key, n in retained.items()):
        raise ValueError("TRANSACTION_EVENT_ACCOUNTING")
    # Exclude every row in a repeated candidate parcel/day, even if another
    # strict screened row failed address corroboration or belonged to another stratum.
    eligible = [e for e in events if all_days[e[:2]] == 1]
    exact = [e for e in eligible if e[2] == "exact"]
    alias = [e for e in eligible if e[2] == "alias_only"]
    strata = {}
    for name in (*STRATA, "combined"):
        base = events if name == "combined" else [e for e in events if e[2] == name]
        subjects = eligible if name == "combined" else exact if name == "exact" else alias
        strata[name] = summarize(base, subjects)
        strata[name]["earlier_exact_pool"] = coverage(subjects, exact)
        strata[name]["earlier_combined_sensitivity_pool"] = coverage(subjects, eligible)
    flags = [r["quality_flags"] for r in rows]
    quality = {
        "all_reported_rows": len(flags),
        "screened_rows": sum(f["screened_candidate"] for f in flags),
        "excluded_from_screened_rows": sum(not f["screened_candidate"] for f in flags),
        "preliminary_rows": sum(f["preliminary_candidate"] for f in flags),
        "exact_duplicate_flagged_rows": sum(f["exact_duplicate"] for f in flags),
        "ambiguous_event_flagged_rows": sum(f["ambiguous_event"] for f in flags),
        "formula_like_flagged_rows": sum(f["formula_like_text"] for f in flags),
        "positive_reported_consideration_rows": sum(f["price_status"] == "positive" for f in flags),
        "positive_reported_erf_extent_rows": sum(f["erf_extent_status"] == "positive" for f in flags),
        "positive_reported_dwelling_extent_rows": sum(f["dwelling_extent_status"] == "positive" for f in flags),
        "positive_both_reported_extents_rows": sum(f["erf_extent_status"] == f["dwelling_extent_status"] == "positive" for f in flags),
        "valid_reported_date_rows": sum(f["date_status"] == "valid" for f in flags),
    }
    return {
        "status": "RETROSPECTIVE_REPORTED_DATE_AVAILABILITY_ONLY",
        "source_quality_flags_nonexclusive": quality,
        "strict_unique_screened_same_parcel_day_groups": sum(n > 1 for n in all_days.values()),
        "strict_unique_screened_same_parcel_day_rows": sum(n for n in all_days.values() if n > 1),
        "corroborated_same_parcel_day_groups_excluded": sum(all_days[k] > 1 for k in retained),
        "strata": strata,
        "corroborated_positive_consideration_and_both_extents_rows": len(events),
        "baseline_reproduced": True,
        "verified_completed_sales": 0,
        "historical_as_of_availability_verified": False,
        "unknown": ["reported date event semantics", "transfer status", "arm's-length eligibility",
                    "historical extent observation date", "historical source availability", "legal continuity"],
        "limitations": "Sale-row candidate counts only; no distance, size similarity, price ranking, valuation or verified historical availability. Same-day screening limited to strict unique screened rows; original flags preserved."
    }
