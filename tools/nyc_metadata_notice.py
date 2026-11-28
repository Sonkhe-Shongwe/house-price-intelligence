"""Offline NYC publisher-notice projection, not a collector or permission check.

Input is four previously obtained metadata JSON documents, not property rows.
No I/O, CLI, network client, credentials, activation or persistence. Candidate
notice text is for private human review, not buyer display or public logs.
"""
import json
import re
from urllib.parse import urlsplit

from tools.nyc_qualification import FIELDS, QualificationError, require

SOURCE_IDS = tuple(FIELDS)
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
MAX_NOTICE_CHARS = 2048
MAX_LINK_CHARS = 512
MAX_CUSTOM_GROUPS = 32
MAX_CUSTOM_FIELDS = 64
_MISSING = object()
_TEXT_KEYS = ("termsOfUse", "usageRestrictions", "disclaimer", "attributionRequirements")
_LINK_KEYS = ("termsOfUseUrl", "licenseUrl", "attributionLink")
_CUSTOM_KEYS = {
    "License": "text", "License URL": "link", "Terms of Use": "text",
    "Terms of Use URL": "link", "Usage Restrictions": "text",
    "Disclaimer": "text", "Attribution Requirements": "text",
}
_CUSTOM_GROUPS = ("Dataset Information", "Additional Resources", "Licensing")


def metadata_path(dataset):
    require(type(dataset) is str and dataset in SOURCE_IDS, "unsupported_source")
    return f"/api/views/{dataset}.json"


def _pairs(items):
    obj = {}
    for key, value in items:
        require(key not in obj, "duplicate_metadata_key")
        obj[key] = value
    return obj


def _constant(_):
    raise QualificationError("invalid_metadata_json")


def _decode(payload):
    require(type(payload) is bytes and 0 < len(payload) <= MAX_DOCUMENT_BYTES,
            "metadata_byte_limit")
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=_constant)
    except QualificationError:
        raise
    except (ValueError, RecursionError):
        raise QualificationError("invalid_metadata_json") from None
    require(type(value) is dict, "invalid_metadata_shape")
    # Refuse mixed row envelopes; ordinary unused metadata fields are ignored.
    require(not ({"rows", "data", "results", "records"} & value.keys()),
            "unexpected_record_envelope")
    return value


def _revision(raw):
    parts = [raw.get(k) for k in ("rowsUpdatedAt", "viewLastModified")]
    require(all(type(x) is int and 0 < x <= 2**53-1 for x in parts),
            "invalid_metadata_revision")
    return ":".join(map(str, parts))


def _text(value):
    require(type(value) is str and len(value) <= MAX_NOTICE_CHARS,
            "invalid_notice_text")
    # Plain text only. Refuse obvious contact tokens and control/bidi markup.
    # This is minimisation, not a guarantee of personal-data detection.
    require(all(c.isprintable() or c in "\n\t\r" for c in value)
            and not any(c in value for c in "<>@")
            and not re.search(r"\d{3}[\s.-]+\d{3}[\s.-]+\d{4}", value),
            "unsafe_notice_text")
    return value.strip()


def _link(value):
    require(type(value) is str and 0 < len(value) <= MAX_LINK_CHARS
            and all(33 <= ord(c) <= 126 for c in value)
            and not any(c in value for c in "\\%<>"), "invalid_notice_link")
    try:
        parts = urlsplit(value)
        host = parts.hostname or ""
        port = parts.port
    except ValueError:
        raise QualificationError("invalid_notice_link") from None
    # Only publisher/licensing references; never follow them here.
    allowed = (host in {"nyc.gov", "cityofnewyork.us", "creativecommons.org",
                        "opendatacommons.org", "cityofnewyork.github.io"}
               or host.endswith(".nyc.gov") or host.endswith(".cityofnewyork.us")
               or host == "www.creativecommons.org")
    require(parts.scheme == "https" and allowed and port is None
            and parts.netloc.lower() == host and not parts.query,
            "unreviewed_notice_link")
    return value


def _field(container, key, kind="text"):
    value = container.get(key, _MISSING)
    if value is _MISSING:
        return {"state": "not_present"}
    if value is None or (type(value) is str and not value.strip()):
        return {"state": "explicit_empty"}
    if kind == "link":
        safe = _link(value)
    elif kind == "token":
        require(type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", value),
                "invalid_license_id")
        safe = value
    else:
        safe = _text(value)
    return {"state": "present_unreviewed", "value": safe}


def _context(container, key):
    value = container.get(key, _MISSING)
    if value is _MISSING:
        return "not_present"
    require(value is None or type(value) is str, "invalid_context_shape")
    return "explicit_empty" if value is None or not value.strip() else "present_unreviewed"


def _custom(raw):
    meta = raw.get("metadata", _MISSING)
    if meta is _MISSING:
        return {"state": "not_present", "notices": {}, "other_fields_unreviewed": False}
    require(type(meta) is dict, "invalid_metadata_shape")
    groups = meta.get("custom_fields", _MISSING)
    if groups is _MISSING:
        return {"state": "not_present", "notices": {}, "other_fields_unreviewed": False}
    require(type(groups) is dict and len(groups) <= MAX_CUSTOM_GROUPS, "invalid_custom_fields")
    notices = {}
    other = False
    for group, fields in groups.items():
        require(type(fields) is dict and len(fields) <= MAX_CUSTOM_FIELDS, "invalid_custom_fields")
        for key in fields:
            if group not in _CUSTOM_GROUPS or key not in _CUSTOM_KEYS:
                other = True
                continue
            require(key not in notices, "ambiguous_custom_notice")
            notices[key] = _field(fields, key, _CUSTOM_KEYS[key])
    return {"state": "present_unreviewed" if groups else "explicit_empty",
            "notices": notices, "other_fields_unreviewed": other}


def project_notice(dataset, payload, expected_revision):
    """Bind one bounded document to an independently supplied revision token."""
    path = metadata_path(dataset)
    require(type(expected_revision) is str and re.fullmatch(r"[1-9]\d{0,15}:[1-9]\d{0,15}", expected_revision),
            "invalid_expected_revision")
    raw = _decode(payload)
    require(raw.get("id") == dataset, "metadata_source_mismatch")
    revision = _revision(raw)
    require(revision == expected_revision, "metadata_revision_mismatch")
    license_obj = raw.get("license", _MISSING)
    if license_obj is _MISSING:
        license_detail = {"state": "not_present"}
    elif license_obj is None or license_obj == {}:
        license_detail = {"state": "explicit_empty"}
    else:
        require(type(license_obj) is dict
                and set(license_obj) <= {"name", "termsLink", "logoUrl"},
                "unexpected_license_field")
        license_detail = {"state": "present_unreviewed",
                          "name": _field(license_obj, "name"),
                          "termsLink": _field(license_obj, "termsLink", "link")}
    return {
        "dataset": dataset, "metadata_path": path, "revision": revision,
        "license_id": _field(raw, "licenseId", "token"),
        "license_detail": license_detail,
        "notice_fields": {key: _field(raw, key) for key in _TEXT_KEYS},
        "reference_links": {key: _field(raw, key, "link") for key in _LINK_KEYS},
        "custom_fields": _custom(raw),
        "description_state": _context(raw, "description"),
        "attribution_state": _context(raw, "attribution"),
        "manual_review_required": True, "rights_accepted": False,
    }


def project_notice_batch(documents, expected_revisions):
    """All four IDs must be present; never return a partial successful batch."""
    require(type(documents) is dict and type(expected_revisions) is dict
            and set(documents) == set(SOURCE_IDS)
            and set(expected_revisions) == set(SOURCE_IDS), "incomplete_notice_batch")
    sources = {dataset: project_notice(dataset, documents[dataset], expected_revisions[dataset])
               for dataset in SOURCE_IDS}
    return {"contract": "nyc-metadata-notice-v1", "sources": sources,
            "manual_review_required": True, "rights_accepted": False,
            "property_collection_authorised": False}
