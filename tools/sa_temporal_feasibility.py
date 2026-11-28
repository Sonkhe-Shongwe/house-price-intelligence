"""P0 feasibility only: invented chronology examples, no source adapter or application hook.

Dates below describe hypothetical registered-sale evidence, not a City field map.
The probe deliberately has no I/O, pricing, ranking, persistence or runtime switch.
"""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class InventedSale:
    parcel: str
    reported: date
    registered: date | None
    available: date | None
    event_valid: bool
    single_property: bool


@dataclass(frozen=True)
class InventedExtentVersion:
    parcel: str
    effective_from: date
    effective_to: date | None
    observed: date
    available: date | None
    historical_applicability_documented: bool = False


def qualify_fixture(sale, versions, subject_parcel, cutoff, mode):
    """Return a categorical result for a fictional prior event, not comparable eligibility."""
    if mode not in ("retrospective", "as_of"):
        raise ValueError("unknown mode")
    if not isinstance(sale, InventedSale) or not isinstance(subject_parcel, str):
        raise ValueError("invented fixture required")
    versions = tuple(versions)
    if any(not isinstance(v, InventedExtentVersion) for v in versions):
        raise ValueError("invented fixture required")
    if any(not isinstance(key, str) or not key.startswith("fictional-")
           for key in (sale.parcel, subject_parcel, *(v.parcel for v in versions))):
        raise ValueError("invented fixture required")
    if any(type(day) is not date for day in (cutoff, sale.reported)):
        return "unknown_or_invalid_date"
    if any(day is not None and type(day) is not date
           for day in (sale.registered, sale.available)):
        return "unknown_or_invalid_date"
    if sale.parcel == subject_parcel:
        return "subject_property"
    if sale.reported >= cutoff:
        return "not_strictly_earlier"
    if sale.event_valid is not True or sale.single_property is not True:
        return "event_not_qualified"
    # Assumption for this registered-sale fixture only: registration follows
    # the event; source availability of that registered record follows registration.
    if sale.registered is None:
        return "registration_unknown"
    if sale.registered < sale.reported or (
            sale.available is not None and sale.available < sale.registered):
        return "event_chronology_conflict"
    applicable = []
    for v in versions:
        if v.parcel != sale.parcel:
            continue
        if any(type(day) is not date for day in (v.effective_from, v.observed)) or any(
                day is not None and type(day) is not date for day in (v.effective_to, v.available)):
            return "unknown_or_invalid_date"
        if (v.effective_to is not None and v.effective_to <= v.effective_from) or (
                v.available is not None and v.available < v.observed):
            return "attribute_chronology_conflict"
        if v.effective_from <= sale.reported and (
                v.effective_to is None or sale.reported < v.effective_to):
            applicable.append(v)
    if len(applicable) != 1:
        return "attribute_version_missing_or_ambiguous"
    v = applicable[0]
    if v.observed > sale.reported and v.historical_applicability_documented is not True:
        return "historical_attribute_unqualified"
    if mode == "as_of":
        if sale.available is None or v.available is None:
            return "availability_unknown"
        if max(sale.registered, sale.available, v.observed, v.available) > cutoff:
            return "not_available_at_cutoff"
        return "fixture_as_of_qualified"
    return "fixture_retrospective_only"
