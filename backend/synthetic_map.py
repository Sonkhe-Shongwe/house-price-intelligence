"""Versioned virtual display geography, separate from the original matcher.
No real locations, distances or source publication rights. Read-only.
"""
import hashlib
import json
from types import MappingProxyType

from backend.durable_fixture import _fixture_signature
from backend.synthetic_demo import BUILD_ID, in_memory_demo
from backend.synthetic_investigation_store import EvidenceStoreError

POSITION_SOURCE = "synthetic-display-geography-v1"
POSITIONS = MappingProxyType({
    "00000000000001": (0.0000, 0.0000),
    "00000000000002": (-0.0060, 0.0040),
    "00000000000003": (0.0050, 0.0055),
    "00000000000004": (0.0030, -0.0060),
    "00000000000005": (-0.0055, -0.0050),
    "00000000000006": (0.0070, -0.0030),
})
POSITION_SHA256 = hashlib.sha256(json.dumps(
    {"source": POSITION_SOURCE, "build": BUILD_ID, "positions": dict(POSITIONS)},
    sort_keys=True, separators=(",", ":"),
).encode("ascii")).hexdigest()


REVISION_BUILDS = ("candidate-e758c7da195b3ac129a70614","candidate-b693166e4803634e513f41d2")
REVISION_GEOGRAPHY = dict(zip(REVISION_BUILDS,("fixture-geography-832ca8c3512516370966cd8a","fixture-geography-da7701adc4635ca152577027")))
REVISION_SOURCE = "synthetic-display-geography-v2"
REVISION_SHA256 = hashlib.sha256(json.dumps({"source":REVISION_SOURCE,"builds":REVISION_BUILDS,"positions":dict(POSITIONS)},sort_keys=True,separators=(",",":")).encode("ascii")).hexdigest()

RICH_BUILD="candidate-12d7698f01e5de3078c4d754"
RICH_GEO="fixture-geography-58f4a593d52bae1cc2ae897a"
RICH_SOURCE="synthetic-display-geography-v3"
RICH_SHA256=hashlib.sha256(json.dumps({"source":RICH_SOURCE,"build":RICH_BUILD,"positions":dict(POSITIONS)},sort_keys=True,separators=(",",":")).encode("ascii")).hexdigest()

def map_evidence(store, investigation_id: str, *, enabled: bool) -> dict:
    if POSITION_SHA256 != "c692c4933f7e967c9bd89a5278126ffcbbda3fcbc5c37f4c0f1c6f2824d5f7b9":
        raise EvidenceStoreError("Display source changed without a new version")
    result = store.reopen(investigation_id)
    build = result["data_build"]
    revision = build["build_id"] in REVISION_BUILDS
    rich = build["build_id"] == RICH_BUILD
    if rich and RICH_SHA256 != "f3c44ac291dc4bdf008f9ec0685ea60f5392cb81fc9a071d766e442c7385c2b5":
        raise EvidenceStoreError("Rich display source changed")
    if revision and REVISION_SHA256 != "411cd6d2403b0b520e52d67f8c1ea99daa1f7fbdf8f61a1bffdb17ecbc9735f8":
        raise EvidenceStoreError("Revised display source changed")
    response = {
        "contract_version": "synthetic-map-v1",
        "investigation_id": investigation_id,
        "build_id": build["build_id"],
        "source_kind": "synthetic_fixture",
        "geometry_kind": "virtual_display_point",
        "real_geography_verified": False,
        "distance_supported": False,
        "position_source_id": RICH_SOURCE if rich else REVISION_SOURCE if revision else POSITION_SOURCE,
        "position_source_sha256": RICH_SHA256 if rich else REVISION_SHA256 if revision else POSITION_SHA256,
        "map_available": False,
        "reason": "map_disabled",
        "feature_collection": {"type": "FeatureCollection", "features": []},
    }
    # A reviewed source-shaped replay has no reviewed display positions.
    # Do not attach another build's position-source identity or permit unknown builds.
    from backend.curated_ingestion_candidate import _plan
    replay = build["build_id"] in {_plan(revision)[2] for revision in ("v4","v5","v6")}
    if replay:
        if build["source_kind"] != "synthetic_fixture":
            raise EvidenceStoreError("Unexpected replay map evidence source")
        if hasattr(store, "verify_map_fixture"):
            store.verify_map_fixture()
        response.update(position_source_id=None, position_source_sha256=None,
                        reason="geometry_unavailable" if enabled else "map_disabled")
        return response
    if not enabled:
        return response
    if (build["build_id"] != BUILD_ID and not revision and not rich) or build["source_kind"] != "synthetic_fixture":
        raise EvidenceStoreError("Unexpected map evidence build")
    # PostgreSQL candidate checks the same immutable source rows with its
    # native schema/history validation; SQLite retains the original signature.
    if hasattr(store, "verify_map_fixture"):
        store.verify_map_fixture()
    else:
        expected, _ = in_memory_demo()
        try:
            if _fixture_signature(store.connection) != _fixture_signature(expected):
                raise EvidenceStoreError("Map fixture source differs from trusted seed")
        finally:
            expected.close()
    stored = store.connection.execute(
        "SELECT subject_pin, analysis_date FROM investigations WHERE investigation_id = ?",
        (investigation_id,),
    ).fetchone()
    subject = result["subject"]["pin"]
    if stored is None or stored[1] != result["analysis_date"]:
        raise EvidenceStoreError("Map investigation identity mismatch")
    if not result["comparables"] or result["status"] not in (
            "supported_neighbourhood", "exploratory_spatial"):
        response["reason"] = "insufficient_or_unsupported_evidence"
        return response
    if stored[0] != subject:
        raise EvidenceStoreError("Map subject identity mismatch")
    members = [(0, subject)] + [(rank, item["pin"])
        for rank, item in enumerate(result["comparables"], 1)]
    if any(pin not in POSITIONS for _, pin in members):
        response["reason"] = "geometry_unavailable"
        return response
    if len({pin for _, pin in members}) != len(members):
        raise EvidenceStoreError("Map contains duplicate parcel identities")
    expected_geo = RICH_GEO if rich else REVISION_GEOGRAPHY[build["build_id"]] if revision else "geo-snap"
    if expected_geo not in build["source_snapshot_ids"]:
        raise EvidenceStoreError("Missing frozen geography snapshot")
    # geo-snap is original matching provenance, NOT the virtual positions.
    response["feature_collection"]["features"] = [
        {"type": "Feature", "id": f"rank-{rank}",
         "geometry": {"type": "Point", "coordinates": list(POSITIONS[pin])},
         "properties": {"rank": rank, "pin": pin,
                        "kind": "subject" if rank == 0 else "comparable"}}
        for rank, pin in members
    ]
    response.update(map_available=True, reason=None)
    return response
