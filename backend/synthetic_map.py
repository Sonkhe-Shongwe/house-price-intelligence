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


def map_evidence(store, investigation_id: str, *, enabled: bool) -> dict:
    result = store.reopen(investigation_id)
    build = result["data_build"]
    response = {
        "contract_version": "synthetic-map-v1",
        "investigation_id": investigation_id,
        "build_id": build["build_id"],
        "source_kind": "synthetic_fixture",
        "geometry_kind": "virtual_display_point",
        "real_geography_verified": False,
        "distance_supported": False,
        "position_source_id": POSITION_SOURCE,
        "position_source_sha256": POSITION_SHA256,
        "map_available": False,
        "reason": "map_disabled",
        "feature_collection": {"type": "FeatureCollection", "features": []},
    }
    if not enabled:
        return response
    if build["build_id"] != BUILD_ID or build["source_kind"] != "synthetic_fixture":
        raise EvidenceStoreError("Unexpected map evidence build")
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
    if "geo-snap" not in build["source_snapshot_ids"]:
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
