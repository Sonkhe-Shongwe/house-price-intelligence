"""Versioned SA fictional investigation, isolated from existing US routes.

No real source input, storage, HTTP route or deployment. The fixed invented
metre grid tests spatial policy, not actual WGS84 geography or accuracy.
"""
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
import re

from tools.sa_temporal_feasibility import (
    InventedSale, InventedExtentVersion, qualify_fixture,
)

VERSION = "hpi-investigation-v2-fictional"
MARKET = "ZA"
NAMESPACE = "za-fictional-erf"
CLASS = "fictional-freehold-single-dwelling"
LOCALITY = "fictional-pinelands-study"
BUILD = "za-fictional-build-v1"
POLICY = "za-fictional-pinelands-v1"
MINIMUM = 3
PREFERRED = 5
RADIUS_M = 2000


class ContractError(ValueError):
    pass


def parse_day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ContractError("invalid_date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ContractError("invalid_date") from None


def parse_money(value):
    """Exact decimal ZAR to integer cents; no binary floats or conversion."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,10}(?:\.[0-9]{1,2})?", value):
        raise ContractError("invalid_zar_amount")
    whole, _, cents = value.partition(".")
    amount = int(whole) * 100 + int(cents.ljust(2, "0"))
    if not 0 < amount <= 100_000_000_000:
        raise ContractError("zar_amount_out_of_fixture_range")
    return amount


def money(cents):
    if type(cents) is not int or not 0 < cents <= 100_000_000_000:
        raise ContractError("invalid_fixture_cents")
    return {"currency": "ZAR", "minor_units": cents,
            "decimal": f"{cents // 100}.{cents % 100:02d}"}


def area(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,7}(?:\.[0-9]{1,6})?", value):
        raise ContractError("invalid_m2_extent")
    a = Fraction(value)
    if not 0 < a <= 1_000_000:
        raise ContractError("invalid_m2_extent")
    return a


def key(value):
    if not isinstance(value, dict) or set(value) != {"namespace", "value"}:
        raise ContractError("invalid_property_key")
    token = value["value"]
    if value["namespace"] != NAMESPACE or not isinstance(token, str) or not re.fullmatch(r"fictional-erf-[0-9]{6}", token):
        raise ContractError("unsupported_property_namespace_or_token")
    return token


def wire_key(token):
    return {"namespace": NAMESPACE, "value": token}


@dataclass(frozen=True)
class Property:
    token: str
    identity: str
    property_class: str
    locality: str
    point: tuple[int, int] | None
    versions: tuple


@dataclass(frozen=True)
class Extents:
    chronology: InventedExtentVersion
    dwelling: str
    land: str


@dataclass(frozen=True)
class Event:
    event_id: str
    chronology: InventedSale
    cents: int


def _property(n, x, y, dwelling="200", land="800", identity="exact", property_class=CLASS):
    token = f"fictional-erf-{n:06d}"
    v = InventedExtentVersion(token, date(2022, 1, 1), None,
                              date(2022, 1, 1), date(2022, 1, 2))
    return Property(token, identity, property_class, LOCALITY, (x, y),
                    (Extents(v, dwelling, land),))


def _event(n, day, suffix="a", available=True, valid=True):
    token = f"fictional-erf-{n:06d}"
    return Event(f"fictional-event-{n:06d}-{suffix}",
                 InventedSale(token, day, day + timedelta(days=10),
                              day + timedelta(days=20) if available else None,
                              valid, True), 220_000_001 + n * 1_000_000)


def fixture():
    """Entirely invented, not generated from source records or real coordinates."""
    props = (_property(1, 0, 0), _property(2, 400, 0, "190", "780"),
             _property(3, 800, 0, "210", "810"),
             _property(4, 1200, 0, "220", "900"),
             _property(5, 1600, 0, "200", "820"),
             _property(6, 2000, 0, "250", "1000"),
             _property(7, 2001, 0), _property(8, 100, 0, "251"),
             _property(9, 100, 200, identity="alias_candidate"),
             _property(10, 100, 300, identity="ambiguous"),
             _property(11, 50, 100, "200", "599"),
             _property(12, 300, 300), _property(13, 400, 400),
             _property(14, 500, 500), _property(15, 600, 600,
                                                property_class="fictional-other"))
    events = (_event(2, date(2025, 2, 1)), _event(2, date(2025, 4, 1), "b"),
              _event(3, date(2025, 3, 1)), _event(4, date(2025, 4, 1)),
              _event(5, date(2024, 8, 1)), _event(6, date(2024, 9, 1)),
              _event(7, date(2025, 3, 1)), _event(8, date(2025, 3, 1)),
              _event(9, date(2025, 3, 1)), _event(10, date(2025, 3, 1)),
              _event(11, date(2025, 3, 1)), _event(12, date(2025, 3, 1), available=False),
              _event(13, date(2025, 7, 1)), _event(14, date(2025, 3, 1), valid=False),
              _event(15, date(2025, 3, 1)), _event(1, date(2025, 3, 1)))
    return props, events


def validate_request(payload, today):
    if not isinstance(payload, dict) or set(payload) != {
            "contract_version", "market", "currency", "area_unit",
            "subject_key", "analysis_date", "mode", "asking_price"}:
        raise ContractError("invalid_request_fields")
    if (payload["contract_version"], payload["market"], payload["currency"], payload["area_unit"]) != (
            VERSION, MARKET, "ZAR", "m2"):
        raise ContractError("unsupported_contract_market_currency_or_unit")
    if payload["mode"] not in ("retrospective", "as_of"):
        raise ContractError("unsupported_mode")
    cutoff = parse_day(payload["analysis_date"])
    if cutoff > today:
        raise ContractError("future_analysis_date")
    return key(payload["subject_key"]), cutoff, payload["mode"], (
        None if payload["asking_price"] is None else parse_money(payload["asking_price"]))


def extent_version(prop, day, cutoff, mode):
    # Subject uses analysis date; candidate uses reported sale date.
    applicable = []
    for item in prop.versions:
        v = item.chronology
        if v.parcel != prop.token or type(v.effective_from) is not date or type(v.observed) is not date:
            return None
        if v.effective_to is not None and (type(v.effective_to) is not date or v.effective_to <= v.effective_from):
            return None
        if v.available is not None and (type(v.available) is not date or v.available < v.observed):
            return None
        if v.effective_from <= day and (v.effective_to is None or day < v.effective_to):
            applicable.append(item)
    if len(applicable) != 1:
        return None
    item = applicable[0]
    v = item.chronology
    if v.observed > day and v.historical_applicability_documented is not True:
        return None
    if mode == "as_of" and (v.available is None or max(v.available, v.observed) > cutoff):
        return None
    try:
        return item, area(item.dwelling), area(item.land)
    except ContractError:
        return None


def _evaluate(payload, properties, events, *, today):
    """Internal fixture test seam. Public entry always uses fixed fixture()."""
    token, cutoff, mode, asking = validate_request(payload, today)
    if any(not isinstance(p, Property) or key(wire_key(p.token)) != p.token for p in properties):
        raise ContractError("invalid_fixture_property")
    if any(not isinstance(e, Event) or not re.fullmatch(r"fictional-event-[0-9]{6}-[a-z]+", e.event_id)
           for e in events):
        raise ContractError("invalid_fixture_event")
    by_key = {p.token: p for p in properties}
    if len(by_key) != len(properties) or len({e.event_id for e in events}) != len(events):
        raise ContractError("duplicate_fixture_identity")
    if any(e.chronology.parcel not in by_key for e in events):
        raise ContractError("orphan_fixture_event")
    for e in events:
        money(e.cents)
    response = {"contract_version": VERSION, "market": MARKET, "currency": "ZAR",
                "area_unit": "m2", "data_build": BUILD, "source_kind": "synthetic_fixture",
                "policy_version": POLICY, "analysis_date": cutoff.isoformat(),
                "mode": mode, "historical_as_of_verified": False,
                "fictional_as_of_qualified": False, "real_data_approved": False,
                "subject": {"property_key": wire_key(token),
                            "asking_price": None if asking is None else money(asking),
                            "asking_price_source": "user_reported"},
                "status": "insufficient_data", "reason": None,
                "window_days": None, "radius_metres": RADIUS_M,
                "minimum_comparables": MINIMUM, "preferred_comparables": PREFERRED,
                "extent_tolerance_percent": 25,
                "eligible_unique_by_window": {"365": 0, "730": 0},
                "selected_count": 0, "comparables": [], "valuation": None,
                "warnings": ["Fictional data only. No real property or transaction verified.",
                             "Distances use an invented metre grid, not real WGS84 coordinates."]}
    subject = by_key.get(token)
    if subject is None or subject.identity != "exact":
        response["reason"] = "subject_identity_unresolved"
        return response
    if subject.property_class != CLASS or subject.locality != LOCALITY:
        response.update(status="out_of_coverage", reason="unsupported_fixture_class_or_locality")
        return response
    v = extent_version(subject, cutoff, cutoff, mode)
    if v is None or subject.point is None:
        response["reason"] = "subject_attributes_or_location_unqualified"
        return response
    subject_version, a, b = v
    response["subject"].update(property_class=CLASS, locality=LOCALITY,
                               dwelling_extent=subject_version.dwelling, land_extent=subject_version.land,
                               identity_scope="fictional_parcel_only", building_identity_verified=False)
    same_day = Counter((e.chronology.parcel, e.chronology.reported) for e in events)
    candidates = []
    for event in events:
        sale = event.chronology
        prop = by_key[sale.parcel]
        if (prop.identity != "exact" or prop.property_class != CLASS or prop.locality != LOCALITY
                or prop.point is None or same_day[(sale.parcel, sale.reported)] != 1):
            continue
        result = qualify_fixture(sale, [item.chronology for item in prop.versions], token, cutoff, mode)
        if result not in ("fixture_as_of_qualified", "fixture_retrospective_only"):
            continue
        age = (cutoff - sale.reported).days
        if not 0 < age <= 730:
            continue
        extent = extent_version(prop, sale.reported, cutoff, mode)
        if extent is None:
            continue
        item, x, y = extent
        if not (3*a <= 4*x <= 5*a and 3*b <= 4*y <= 5*b):
            continue
        d2 = sum((p-q)**2 for p,q in zip(subject.point, prop.point))
        if not 0 < d2 <= RADIUS_M**2:
            continue
        candidates.append((event, item, age, d2, abs(x/a-1), abs(y/b-1)))
    pools = {}
    for days in (365, 730):
        latest = {}
        for row in candidates:
            event, _, age, *_ = row
            if age > days:
                continue
            parcel = event.chronology.parcel
            previous = latest.get(parcel)
            if previous is None or event.chronology.reported > previous[0].chronology.reported:
                latest[parcel] = row
        pools[days] = list(latest.values())
        response["eligible_unique_by_window"][str(days)] = len(latest)
    window = 365 if len(pools[365]) >= MINIMUM else 730 if len(pools[730]) >= MINIMUM else None
    if window is None:
        response["reason"] = "fewer_than_three_qualified_fixture_parcels"
        return response
    # Price-free deterministic order: dual extent deviation, distance, recency, key.
    selected = sorted(pools[window], key=lambda row: (row[4], row[5], row[3], row[2],
                                                      row[0].chronology.parcel))[:PREFERRED]
    comps = []
    for event, item, age, d2, _, _ in selected:
        sale = event.chronology
        comps.append({"property_key": wire_key(sale.parcel), "event_id": event.event_id,
                      "reported_sale_date": sale.reported.isoformat(),
                      "registration_date": sale.registered.isoformat(),
                      "availability_date": sale.available.isoformat() if sale.available else None,
                      "sale_consideration": money(event.cents),
                      "source_type": "invented_registered_sale",
                      "dwelling_extent": item.dwelling, "land_extent": item.land,
                      "attribute_observed_date": item.chronology.observed.isoformat(),
                      "attribute_effective_from": item.chronology.effective_from.isoformat(),
                      "attribute_available_date": item.chronology.available.isoformat() if item.chronology.available else None,
                      "age_days": age, "distance_squared_metres": d2})
    response.update(status="fictional_supported", reason="primary_window" if window==365 else "extended_window",
                    window_days=window, selected_count=len(comps), comparables=comps,
                    fictional_as_of_qualified=mode=="as_of")
    return response


def investigate(payload, *, today=None):
    """Only fixed invented fixture data. No caller-supplied source/build/permissions."""
    return _evaluate(payload, *fixture(), today=today or date.today())
