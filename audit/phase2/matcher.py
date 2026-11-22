"""Explainable, deterministic comparable-sale selection for a bounded historical pilot.

This is a pure research engine. Matching never consults sale prices; the
caller may evaluate prices only after a result is finalized.

The data's sale dates are NOT proof of their historical publication times.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import asin, cos, isfinite, radians, sin, sqrt


@dataclass(frozen=True)
class MatchPolicy:
    class_code: str = "203"
    history_days: int = 365
    size_tolerance: float = 0.25
    radius_km: float = 2.0
    min_comps: int = 3
    max_comps: int = 5

    def __post_init__(self):
        if self.history_days < 1 or not 0 < self.size_tolerance <= 1:
            raise ValueError("Invalid date window or building-area tolerance")
        if not 0 < self.radius_km <= 10:
            raise ValueError("Radius must be between 0 and 10 km")
        if not 1 <= self.min_comps <= self.max_comps <= 20:
            raise ValueError("Invalid comparison count limits")


def analysis_date(subject):
    """Buyer investigations use analysis_date; retrospective sales use sale_date."""
    value = subject.get("analysis_date") or subject.get("sale_date")
    if not value:
        raise ValueError("Subject requires analysis_date or historical sale_date")
    return date.fromisoformat(str(value)[:10])


def _location(row):
    try:
        lat, lon = float(row.get("lat")), float(row.get("lon"))
    except (TypeError, ValueError, OverflowError):
        return None
    if not all(map(isfinite, (lat, lon))) or not (40 <= lat <= 43 and -89 <= lon <= -86):
        return None
    return (lat, lon)


def _distance_km(a, b):
    loc_a, loc_b = _location(a), _location(b)
    if loc_a is None or loc_b is None:
        return None
    lat1, lon1, lat2, lon2 = (radians(v) for v in (*loc_a, *loc_b))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 6371.0088 * 2 * asin(min(1.0, sqrt(h)))


def _eligible(subject, sale, as_of, policy):
    """Guarded sale filters; return (size difference, age days), or None."""
    if sale.get("class") != policy.class_code or sale.get("township_code") != subject.get("township_code"):
        return None
    if not sale.get("pin") or sale.get("pin") == subject.get("pin"):
        return None
    if subject.get("doc_no") and subject["doc_no"] == sale.get("doc_no"):
        return None
    try:
        when = date.fromisoformat(str(sale["sale_date"])[:10])
        subj_area, area = float(subject["sqft"]), float(sale["sqft"])
        if not all(map(isfinite, (subj_area, area))) or min(subj_area, area) <= 0:
            return None
    except (ValueError, KeyError, TypeError, OverflowError):
        return None
    if not as_of - timedelta(days=policy.history_days) <= when < as_of:
        return None
    difference = abs(area / subj_area - 1)
    if difference > policy.size_tolerance:
        return None
    return difference, (as_of - when).days


def _base_candidates(subject, population, policy):
    as_of = analysis_date(subject)
    if subject.get("class") != policy.class_code or not subject.get("township_code"):
        return [], as_of, "unsupported_property_scope"
    try:
        area = float(subject["sqft"])
    except (TypeError, ValueError, KeyError, OverflowError):
        area = 0
    if not isfinite(area) or area <= 0:
        return [], as_of, "invalid_subject_area"

    by_pin = {}
    for sale in population:
        hit = _eligible(subject, sale, as_of, policy)
        if hit is None:
            continue
        # A house contributes a maximum of one comparable sale. Keep its
        # most recent eligible transaction, independently of sale price.
        pin = str(sale["pin"])
        current = by_pin.get(pin)
        key = (str(sale["sale_date"])[:10], str(sale.get("doc_no", "")))
        if current is None or key > current[2]:
            by_pin[pin] = (sale, hit, key)
    return [(record, attrs) for record, attrs, _ in by_pin.values()], as_of, None


def match_property(subject, population, *, policy=MatchPolicy()):
    """Neighbourhood first, then bounded 2km spatial expansion, else abstain.

    Selected comparables retain traceability and matching explanations locally.
    They are NOT safe to upload as public CI artifacts.
    """
    candidates, as_of, initial_error = _base_candidates(subject, population, policy)
    hood = str(subject.get("nbhd_code") or "").strip()
    local = [(row, info) for row, info in candidates if hood and str(row.get("nbhd_code") or "").strip() == hood]
    nearby = []
    for row, info in candidates:
        dist = _distance_km(subject, row)
        if dist is not None and dist <= policy.radius_km:
            nearby.append((row, info, dist))

    if initial_error:
        tier, chosen, why = "none", [], initial_error
    elif len(local) >= policy.min_comps:
        tier, why = "same_neighborhood", "at_least_three_local_sales"
        chosen = sorted([(row, info, _distance_km(subject, row)) for row, info in local],
                        key=lambda item: (item[1][0], item[1][1], str(item[0]["pin"])))[:policy.max_comps]
    elif len(nearby) >= policy.min_comps:
        tier, why = "spatial_fallback", "insufficient_neighborhood_sales_within_2km"
        # A distance-based fallback uses distance first, then area and recency.
        chosen = sorted(nearby, key=lambda item: (item[2], item[1][0], item[1][1], str(item[0]["pin"])))[:policy.max_comps]
    else:
        tier, chosen = "none", []
        if _location(subject) is None and len(local) < policy.min_comps:
            why = "missing_subject_coordinates"
        elif not candidates:
            why = "no_eligible_prior_sales"
        else:
            why = "insufficient_local_and_nearby_sales"

    comps = []
    for row, (diff, age), distance in chosen:
        same_hood = bool(hood and str(row.get("nbhd_code") or "").strip() == hood)
        comps.append({
            "pin": row["pin"], "document": row.get("doc_no"),
            "sale_date": str(row["sale_date"])[:10], "sale_price": row["sale_price"],
            "size_difference_pct": round(diff * 100, 2), "age_days": age,
            "distance_km": None if distance is None else round(distance, 3),
            "same_neighborhood": same_hood,
            "explanation": ("same assessor neighborhood" if tier == "same_neighborhood"
                            else "within bounded 2 km of subject") +
                           f"; floor area differs by {diff * 100:.1f}%; sale {age} days earlier",
            "source_type": "recorded_sale", "characteristics_year": row.get("characteristics_year"),
        })

    return {
        "status": "supported" if comps else "insufficient_data", "tier": tier, "reason": why,
        "analysis_date": as_of.isoformat(), "scope_class": policy.class_code,
        "eligible_unique_properties": len(candidates), "local_candidate_count": len(local),
        "nearby_candidate_count": len(nearby), "selected_count": len(comps),
        "radius_km": policy.radius_km, "minimum_comparables": policy.min_comps,
        "comparables": comps,
        "data_warning": "Historic records may be backfilled; sale date is not proof of publication date.",
    }
