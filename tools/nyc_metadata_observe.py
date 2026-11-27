"""Owner-local public metadata observation, strictly separate from collection.

Four fixed HTTPS GETs maximum; no resource endpoint, credentials, redirects,
files or raw output. Use an external hard deadline (WSL timeout). No invocation
in CI. The returned notice states are evidence for review, not rights approval.
"""
import http.client
import json
import re
import ssl
import sys
from datetime import datetime, timezone

from tools.nyc_metadata_notice import (
    MAX_DOCUMENT_BYTES, SOURCE_IDS, metadata_path, project_notice, _decode, _revision,
)
from tools.nyc_qualification import QualificationError

HOST = "data.cityofnewyork.us"
# Owner-observed pins preserved in SOURCE_REGISTER.md, 27 November 2026.
PINS = {
    "usep-8jbt": "1795635328:1795635300",
    "64uk-42ks": "1795476446:1795465895",
    "bnx9-e6tj": "1794332294:1740778366",
    "8h5j-fqxa": "1794332093:1740778244",
}
TIMEOUT_SECONDS = 12


def _fetch(dataset):
    path = metadata_path(dataset)
    conn = http.client.HTTPSConnection(HOST, timeout=TIMEOUT_SECONDS,
                                       context=ssl.create_default_context())
    try:
        conn.request("GET", path, headers={"Accept": "application/json",
                     "Accept-Encoding": "identity", "Connection": "close"})
        with conn.getresponse() as response:
            if response.status != 200:
                raise QualificationError("http_status_unavailable")
            content_type = response.getheader("Content-Type", "")
            if content_type.split(";")[0].strip().lower() != "application/json":
                raise QualificationError("metadata_content_type")
            if response.getheader("Content-Encoding", "identity").lower() != "identity":
                raise QualificationError("metadata_encoding")
            length = response.getheader("Content-Length")
            transfer = response.getheader("Transfer-Encoding")
            if transfer is not None and (length is not None or transfer.strip().lower() != "chunked"):
                raise QualificationError("metadata_framing")
            if length is not None:
                if not re.fullmatch(r"[0-9]{1,8}", length):
                    raise QualificationError("metadata_framing")
                expected = int(length)
                if not 0 < expected <= MAX_DOCUMENT_BYTES:
                    raise QualificationError("metadata_byte_limit")
                payload = response.read(expected)
                if len(payload) != expected:
                    raise QualificationError("metadata_incomplete")
            else:
                # Unknown-length documents at the limit are refused; no extra
                # byte is read to distinguish exact size from oversize.
                payload = response.read(MAX_DOCUMENT_BYTES)
                if not 0 < len(payload) < MAX_DOCUMENT_BYTES:
                    raise QualificationError("metadata_byte_limit")
            return payload
    finally:
        conn.close()


def _states(item):
    """Do not return values, even when the notice projector accepts them."""
    detail = item["license_detail"]
    custom = item["custom_fields"]
    return {
        "license_id": item["license_id"]["state"],
        "license_detail": detail["state"],
        "license_name": detail.get("name", {}).get("state", "not_present"),
        "license_terms_link": detail.get("termsLink", {}).get("state", "not_present"),
        "notice_fields": {k: v["state"] for k, v in item["notice_fields"].items()},
        "reference_links": {k: v["state"] for k, v in item["reference_links"].items()},
        "custom_fields": custom["state"],
        "custom_notices": {k: v["state"] for k, v in custom["notices"].items()},
        "other_custom_fields_unreviewed": custom["other_fields_unreviewed"],
        "description": item["description_state"],
        "attribution": item["attribution_state"],
    }


def observe(fetch):
    """Injected transport permits independent invented tests. No retry."""
    if set(PINS) != set(SOURCE_IDS):
        raise RuntimeError("source_inventory_mismatch")
    sources = {}
    for dataset, expected in PINS.items():
        entry = {"expected_revision": expected, "status": "unavailable"}
        sources[dataset] = entry
        try:
            payload = fetch(dataset)
            raw = _decode(payload)
            if raw.get("id") != dataset:
                entry["status"] = "source_mismatch"
                continue
            observed = _revision(raw)
            entry["observed_revision"] = observed
            if observed != expected:
                entry["status"] = "revision_changed"
                continue
            item = project_notice(dataset, payload, expected)
            entry["notice_states"] = _states(item)
            entry["status"] = "exact_revision_projected"
        except QualificationError:
            # Error messages and upstream payloads are not safe output.
            entry["status"] = "metadata_refused"
        except Exception:
            entry["status"] = "unavailable"
    return {
        "contract": "nyc-metadata-observation-v1",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
        "all_exact_projected": all(v["status"] == "exact_revision_projected" for v in sources.values()),
        "manual_review_required": True,
        "rights_accepted": False,
        "property_collection_authorised": False,
    }


def main(argv=None):
    if (sys.argv[1:] if argv is None else argv) != ["--metadata-only"]:
        print("Refused: explicit --metadata-only required.")
        return 2
    result = observe(_fetch)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_exact_projected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
