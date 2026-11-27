"""NYC exact-entry and evidence projection for invented fixtures ONLY.

No network, database, runtime route, actual source constructor or release grant.
The completed research collector stays aggregate-only. A trusted future reader
must establish source completeness, rights and protected storage independently.
"""
from dataclasses import dataclass
from datetime import date, timedelta
import re

from tools.nyc_qualification import (
    AREA_METHOD, CURRENT_SNAPSHOT, FIELDS, MAX_KEYS, Subject,
    day_value, positive_int, require, valid_key, _screen_sales, _select_comparables,
)


@dataclass(frozen=True)
class FixtureAddress:
    key: str
    address: str
    borough: str
    zipcode: int
    building_class: str
    buildings: int
    residential_units: int
    total_units: int
    area: int
    area_source: str
    version: str


@dataclass(frozen=True)
class FixtureSnapshot:
    cutoff: date
    covered_from: date
    covered_through: date
    publication: date
    version: str
    revisions: tuple
    source_kind: str = "synthetic_fixture"
    frame_complete: bool = False
    source_complete: bool = False
    source_versions_stable: bool = False
    available: bool = False


def _normalise(address):
    require(isinstance(address, str) and 0 < len(address) <= 200
            and not any(ord(c) < 32 or ord(c) == 127 for c in address),
            "invalid_address")
    result = " ".join(address.upper().split())
    require(bool(result), "invalid_address")
    return result


def _money(cents):
    return f"{cents // 100}.{cents % 100:02d}"


def _eligible(row, plan):
    return (row.borough == "QN" and type(row.zipcode) is int and row.zipcode == 11361
            and row.building_class == "A2" and all(type(x) is int and x == 1 for x in
                (row.buildings, row.residential_units, row.total_units))
            and positive_int(row.area) and row.area_source == AREA_METHOD
            and row.version == plan.version)


def investigate_fixture(address, asking_cents, plan, addresses, sales, masters, legals):
    """Resolve one independently indexed subject; output a strict display allowlist.

    The address universe must include competing/unsupported rows, not only
    eligible sales or preselected matches. Exact case/space normalisation only.
    All fixture labels and revisions are explicitly invented; no persistence.
    """
    require(type(plan) is FixtureSnapshot and plan.source_kind == "synthetic_fixture"
            and isinstance(plan.version, str)
            and re.fullmatch(r"fixture-nyc-[a-z0-9-]{1,40}", plan.version),
            "fixture_only")
    require(type(plan.revisions) is tuple and len(plan.revisions) == len(FIELDS)
            and all(type(pair) is tuple and len(pair) == 2
                    and isinstance(pair[0], str) and isinstance(pair[1], str)
                    and re.fullmatch(r"fixture-[a-z0-9-]{1,40}", pair[1])
                    for pair in plan.revisions)
            and {pair[0] for pair in plan.revisions} == set(FIELDS), "fixture_revisions")
    require(all(day_value(x) for x in (plan.cutoff, plan.covered_from,
                plan.covered_through, plan.publication))
            and plan.covered_from <= plan.covered_through < plan.cutoff
            and plan.publication <= plan.cutoff, "invalid_coverage")
    require(asking_cents is None or (positive_int(asking_cents)
            and asking_cents <= 99999999999999), "invalid_asking_price")
    label = _normalise(address)
    result = {
        "contract_version": "nyc-buyer-fixture-v1",
        "source_kind": "synthetic_fixture", "market": "queens_11361_a2",
        "currency": "USD", "asking_price_usd": None if asking_cents is None else _money(asking_cents),
        "asking_price_source": "buyer_reported",
        "status": "evidence_unavailable", "subject": None, "comparables": [],
        "selected_count": 0, "comparison_mode": CURRENT_SNAPSHOT,
        "provenance": {"analysis_date": plan.cutoff.isoformat(),
                       "snapshot_publication_date": plan.publication.isoformat(),
                       "snapshot_version": plan.version,
                       "area_source": AREA_METHOD,
                       "sales_covered_from": plan.covered_from.isoformat(),
                       "sales_covered_through": plan.covered_through.isoformat(),
                       "lookback_fully_covered": plan.covered_from <= plan.cutoff-timedelta(days=365)
                           and plan.covered_through == plan.cutoff-timedelta(days=1),
                       "source_revisions": dict(plan.revisions),
                       "publisher_attributed": False,
                       "sale_time_area_verified": False,
                       "historical_asof_verified": False,
                       "public_display_approved": False},
        "valuation": None, "price_per_sqft_supported": False,
        "representative_coverage_verified": False,
    }
    if not (plan.available is True and plan.frame_complete is True
            and plan.source_complete is True and plan.source_versions_stable is True):
        return result
    addresses, sales, masters, legals = map(tuple, (addresses, sales, masters, legals))
    require(len(addresses) <= MAX_KEYS and all(type(row) is FixtureAddress
            and valid_key(row.key) and _normalise(row.address).startswith("FICTIONAL ")
            for row in addresses), "invalid_fixture_frame")
    matches = [row for row in addresses if _normalise(row.address) == label]
    if not matches:
        result["status"] = "out_of_coverage"
        return result
    if len(matches) != 1 or sum(r.key == matches[0].key for r in addresses) != 1:
        result["status"] = "ambiguous_address"
        return result
    row = matches[0]
    if not _eligible(row, plan):
        result["status"] = "out_of_coverage"
        return result
    subject = Subject(row.key, row.area, plan.publication, plan.version, True, True, AREA_METHOD)
    qualified, _ = _screen_sales([r.key for r in addresses], sales, masters, legals,
        cutoff=plan.cutoff, covered_from=plan.covered_from, covered_through=plan.covered_through,
        mode=CURRENT_SNAPSHOT, snapshot=plan.publication, version=plan.version)
    selected = _select_comparables(subject, qualified, CURRENT_SNAPSHOT)
    result["subject"] = {"address": row.address, "borough": "Queens", "zipcode": "11361",
                         "building_class": "A2", "snapshot_gross_area_sqft": row.area}
    if len(selected) < 3:
        result["status"] = "insufficient_data"
        return result
    result["status"] = "supported"
    result["selected_count"] = len(selected)
    result["comparables"] = [
        {"rank": i, "sale_date": sale.day.isoformat(), "sale_price_usd": _money(sale.cents),
         "age_days": (plan.cutoff-sale.day).days, "building_class": "A2",
         "dof_neighbourhood": "BAYSIDE", "snapshot_gross_area_sqft": sale.snapshot_area,
         "absolute_area_difference_sqft": abs(sale.snapshot_area-row.area),
         "selection_rule": "earlier_whole_deed_same_snapshot_area_within_25_percent"}
        for i, sale in enumerate(selected, 1)
    ]
    return result
