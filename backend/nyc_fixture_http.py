"""Fixed invented NYC request adapter; no network source, storage or live entry."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import re

from backend.nyc_buyer_fixture import FixtureAddress, FixtureSnapshot, investigate_fixture
from tools.nyc_qualification import FIELDS, Sale, Master, Legal, bbl, require
from backend.nyc_lifecycle_guard import IntakeSeal, SourceAuthority, Evidence, AuthoritySnapshot, evaluate

NYC_PATH = "/v2/fictional/nyc/investigate"
CONTRACT = "nyc-buyer-fixture-v1"


# Fixed simulated timeline for the disposable public demo, not wall-clock
# authority. No request, environment flag or restored record can set it.
_OWNER = "fixture-nyc-http-owner"
_INTAKE = datetime(2026, 11, 24, tzinfo=timezone.utc)
_BUILD = datetime(2026, 11, 27, tzinfo=timezone.utc)
_REHEARSAL_NOW = datetime(2026, 11, 28, tzinfo=timezone.utc)
_REVISION = "fixture-http-one"
_VERSION = "fixture-nyc-http-one"
_POLICY = "fixture-nyc-http-policy-v1"
_SOURCES = ("usep-8jbt", "64uk-42ks", "bnx9-e6tj", "8h5j-fqxa")
_ORIGINALS = tuple(IntakeSeal(source, _REVISION, f"fixture-http-intake-{source}",
                             _POLICY, _INTAKE, _INTAKE+timedelta(days=30))
                   for source in _SOURCES)


class LifecycleUnavailable(RuntimeError):
    """Categorical refusal, never a property or authority payload."""


def _authority(now):
    """Separate fixed invented authority, not derived from the fixture plan."""
    return AuthoritySnapshot(_OWNER, tuple(
        SourceAuthority(seal, seal.original_deadline, "reviewed", "clear",
                        "verified", frozenset({"read"})) for seal in _ORIGINALS), now)


def _require_read(plan):
    # Bind the source plan to the original frozen manifest before matching.
    if (type(plan) is not FixtureSnapshot or plan.source_kind != "synthetic_fixture"
            or plan.version != _VERSION or type(plan.revisions) is not tuple
            or len(plan.revisions) != len(_ORIGINALS)
            or not all(type(pair) is tuple and len(pair) == 2
                       and all(type(v) is str for v in pair) for pair in plan.revisions)
            or set(plan.revisions) != {(s.source, s.revision) for s in _ORIGINALS}):
        raise LifecycleUnavailable("fixture_evidence_unavailable")
    now = _REHEARSAL_NOW
    decision = evaluate(Evidence(_OWNER, _ORIGINALS, _BUILD),
                        _authority(now), owner=_OWNER, operation="read", now=now)
    if decision.allowed is not True:
        raise LifecycleUnavailable("fixture_evidence_unavailable")


def fixture():
    # Deliberately artificial labels, amounts, dates and keys, not publisher rows.
    cutoff = date(2026, 11, 27)
    published = date(2026, 11, 23)
    version = "fixture-nyc-http-one"
    plan = FixtureSnapshot(cutoff, date(2025, 11, 1), date(2026, 10, 31),
        published, version, tuple((d, "fixture-http-one") for d in FIELDS),
        frame_complete=True, source_complete=True, source_versions_stable=True,
        available=True)

    def property_row(n, address, area, kind="A2"):
        return FixtureAddress(bbl(4, 99001, n), address, "QN", 11361, kind,
                              1, 1, 1, area, "2", version)

    addresses = (
        property_row(1, "Fictional NYC Home A", 1000),
        property_row(2, "Fictional NYC Home B", 2000),
        property_row(3, "Fictional NYC Home C", 1050),
        property_row(4, "Fictional NYC Ambiguous", 1000),
        property_row(5, "Fictional NYC Ambiguous", 1000, "A1"),
        property_row(6, "Fictional NYC Unsupported", 1000, "A1"),
    )
    sales = tuple(Sale(bbl(4, 99002, i), cutoff-timedelta(days=30+i),
        41000000 + i*100001, area, True, False, area, published, version, "2")
        for i, area in enumerate((950, 1000, 1100, 1250, 1500), 1))
    masters = tuple(Master(f"INVENTEDHTTP{i}", "DEED", s.day, s.day, s.cents,
                           Decimal("100")) for i, s in enumerate(sales, 1))
    legals = tuple(Legal(m.doc, s.key, True, True, True) for m, s in zip(masters, sales))
    return plan, addresses, sales, masters, legals


def investigate(payload):
    require(type(payload) is dict and set(payload) == {
        "contract_version", "address", "asking_price_usd"}, "invalid_request")
    require(payload["contract_version"] == CONTRACT, "invalid_contract")
    address = payload["address"]
    # No arbitrary real-address lookup or personal information in this preview.
    require(isinstance(address, str) and len(address) <= 80
            and re.fullmatch(r"Fictional NYC [A-Za-z0-9 ]{1,60}", address.strip(), re.I)
            is not None, "invalid_fixture_address")
    price = payload["asking_price_usd"]
    if price is not None:
        require(isinstance(price, str) and re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,2})?", price)
                is not None, "invalid_asking_price")
        whole, _, fraction = price.partition(".")
        price = int(whole)*100 + int(fraction.ljust(2, "0"))
    require(price is None or 0 < price <= 99999999999999, "invalid_asking_price")
    plan, *rows = fixture()
    _require_read(plan)
    return investigate_fixture(address, price, plan, *rows)
