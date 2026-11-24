"""Fixture-only WSGI investigation API, with deliberate local-only access.

No third-party dependencies, no public network listener and no real data path.
This module is a testable HTTP boundary, not a production API or a consumer
address-search decision. The caller must provide a trusted synthetic store.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import json
import re
import sqlite3
from typing import Any

from backend.investigation_contract import ContractError
from backend.synthetic_investigation_store import EvidenceStoreError, SyntheticInvestigationStore
from backend.synthetic_shortlists import ShortlistError, SyntheticShortlistService
from backend.synthetic_map import map_evidence
from backend.buyer_evidence_preview import buyer_evidence_preview

MAX_BODY_BYTES = 16 * 1024
# Exactly three assets are served: no directory traversal, assets from a fixed tree.
# The entire UI is a disposable, synthetic-only development preview.
FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
STATIC_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/assets/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/assets/app.js": ("app.js", "text/javascript; charset=utf-8"),
}
SECURITY_HEADERS = [
    ("Cache-Control", "no-store"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "no-referrer"),
    ("Cross-Origin-Resource-Policy", "same-origin"),
    ("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; "
      "connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; "
      "frame-ancestors 'none'; object-src 'none'"),
    ("X-Synthetic-Only", "true"),
]


def _static_response(start_response, asset):
    filename, content_type = asset
    try:
        payload = (FRONTEND / filename).read_bytes()
    except OSError:
        return _response(start_response, 503, {"error": "demo_asset_unavailable"})
    start_response("200 OK", [("Content-Type", content_type),
                              ("Content-Length", str(len(payload))), *SECURITY_HEADERS])
    return [payload]

ID_ROUTE = re.compile(r"^/v1/investigations/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$")
ADDRESS_ROUTE = re.compile(r"^/v1/addresses/([a-z0-9-]{1,40})$")
UUID_PART = r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
MAP_ROUTE = re.compile(r"^/v1/investigations/" + UUID_PART + r"/map$")
PREVIEW_ROUTE = re.compile(r"^/v1/investigations/" + UUID_PART + r"/evidence-preview$")
SHORTLIST_ROUTE = re.compile(r"^/v1/shortlists/" + UUID_PART + r"$")
SHORTLIST_MEMBERS_ROUTE = re.compile(r"^/v1/shortlists/" + UUID_PART + r"/entries$")
SHORTLIST_ENTRY_ROUTE = re.compile(r"^/v1/shortlists/" + UUID_PART + r"/entries/" + UUID_PART + r"$")
ADDRESS_SEARCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,\-']{1,79}$")
ALLOWED_HOST = re.compile(r"^(?:127\.0\.0\.1|localhost|\[::1\])(?::[0-9]{1,5})?$", re.IGNORECASE)


def _strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("invalid_json_number")


def _response(start_response, code: int, value: Any, *, location: str | None = None,
              allow: str | None = None):
    payload = json.dumps(value, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    status = {200: "200 OK", 201: "201 Created", 400: "400 Bad Request",
              403: "403 Forbidden", 404: "404 Not Found", 405: "405 Method Not Allowed",
              411: "411 Length Required", 413: "413 Content Too Large",
              415: "415 Unsupported Media Type", 409: "409 Conflict",
              422: "422 Unprocessable Content",
              503: "503 Service Unavailable", 500: "500 Internal Server Error"}[code]
    headers = [("Content-Type", "application/json; charset=utf-8"),
               ("Content-Length", str(len(payload))), *SECURITY_HEADERS]
    if location is not None:
        headers.append(("Location", location))
    if allow is not None:
        headers.append(("Allow", allow))
    start_response(status, headers)
    return [payload]


def create_app(store: SyntheticInvestigationStore, *, today: date | None = None,
               react_assets: dict[str, tuple[bytes, str]] | None = None, synthetic_map: bool = False):
    """Build a WSGI app against the **server-injected** synthetic evidence store.

    Host/remote checks are belt-and-braces protections, not an authentication
    mechanism: do not mount behind proxies or bind on public interfaces.
    """
    if not isinstance(store, SyntheticInvestigationStore):
        raise TypeError("Only the fixture-backed investigation store may be served")
    shortlists = SyntheticShortlistService(store)
    if synthetic_map and react_assets is None:
        raise ValueError("Synthetic map requires the React frontend")
    react_headers = [(key, value + "; worker-src 'self'" if synthetic_map and key == "Content-Security-Policy" else value)
                     for key, value in SECURITY_HEADERS]

    def app(environ, start_response):
        method = environ.get("REQUEST_METHOD", "")
        path = environ.get("PATH_INFO", "")
        host = environ.get("HTTP_HOST", "")
        remote = environ.get("REMOTE_ADDR")
        origin = environ.get("HTTP_ORIGIN")
        # A browser's same-origin JSON POST sends Origin. Keep those requests
        # working while rejecting unrelated web pages and DNS-rebinding hosts.
        if (remote not in ("127.0.0.1", "::1") or not ALLOWED_HOST.fullmatch(host)
                or (origin is not None and origin.lower() != environ.get("wsgi.url_scheme","http") + "://" + host.lower())
                or environ.get("HTTP_SEC_FETCH_SITE") in ("cross-site", "same-site")
                or environ.get("HTTP_X_FORWARDED_FOR")
                or environ.get("HTTP_X_FORWARDED_HOST") or environ.get("HTTP_X_FORWARDED_PROTO")
                or environ.get("HTTP_X_REAL_IP") or environ.get("HTTP_FORWARDED")):
            return _response(start_response, 403, {"error": "local_fixture_only"})

        if environ.get("QUERY_STRING"):
            return _response(start_response, 400, {"error": "query_parameters_not_supported"})

        if react_assets is not None and path in react_assets:
            if method != "GET":
                return _response(start_response, 405, {"error": "method_not_allowed"}, allow="GET")
            payload, content_type = react_assets[path]
            start_response("200 OK", [("Content-Type", content_type),
                                      ("Content-Length", str(len(payload))), *react_headers])
            return [payload]

        if react_assets is None and path in STATIC_ASSETS:
            if method != "GET":
                return _response(start_response, 405, {"error": "method_not_allowed"}, allow="GET")
            return _static_response(start_response, STATIC_ASSETS[path])

        if path == "/health":
            if method != "GET":
                return _response(start_response, 405, {"error": "method_not_allowed"}, allow="GET")
            return _response(start_response, 200, {"status": "ok", "mode": "synthetic_fixture_only"})

        if path == "/v1/investigations/history":
            if method != "GET":
                return _response(start_response, 405, {"error": "method_not_allowed"}, allow="GET")
            try:
                return _response(start_response, 200, store.history())
            except (EvidenceStoreError, sqlite3.Error, ValueError, TypeError, KeyError):
                return _response(start_response, 503, {"error": "evidence_unavailable"})

        shortlist_match = SHORTLIST_ROUTE.fullmatch(path)
        members_match = SHORTLIST_MEMBERS_ROUTE.fullmatch(path)
        entry_match = SHORTLIST_ENTRY_ROUTE.fullmatch(path)

        if (path == "/v1/shortlists" and method == "GET"
                or shortlist_match and method == "GET"
                or entry_match and method == "DELETE"):
            try:
                if path == "/v1/shortlists":
                    result = shortlists.list()
                elif shortlist_match:
                    result = shortlists.get(shortlist_match.group(1))
                else:
                    result = shortlists.remove(entry_match.group(1), entry_match.group(2))
                return _response(start_response, 200, result)
            except ShortlistError as exc:
                return _response(start_response, exc.status, {"error": exc.code})
            except (EvidenceStoreError, sqlite3.Error):
                return _response(start_response, 503, {"error": "evidence_unavailable"})

        if shortlist_match or (entry_match and method != "PATCH"):
            return _response(start_response, 405, {"error": "method_not_allowed"},
                             allow="GET" if shortlist_match else "PATCH, DELETE")
        if members_match and method != "POST":
            return _response(start_response, 405, {"error": "method_not_allowed"}, allow="POST")
        if path == "/v1/shortlists" and method not in ("GET", "POST"):
            return _response(start_response, 405, {"error": "method_not_allowed"}, allow="GET, POST")

        shortlist_write = (path == "/v1/shortlists" or members_match is not None
                           or entry_match is not None)
        if path in ("/v1/investigations", "/v1/addresses/search") or shortlist_write:
            if not shortlist_write and method != "POST":
                return _response(start_response, 405, {"error": "method_not_allowed"}, allow="POST")
            if environ.get("HTTP_TRANSFER_ENCODING"):
                return _response(start_response, 400, {"error": "unsupported_transfer_encoding"})
            content_type = environ.get("CONTENT_TYPE", "").lower().replace(" ", "")
            if content_type not in ("application/json", "application/json;charset=utf-8"):
                return _response(start_response, 415, {"error": "json_content_type_required"})
            content_length = environ.get("CONTENT_LENGTH", "")
            if not content_length or not re.fullmatch(r"[0-9]+", str(content_length)):
                return _response(start_response, 411, {"error": "content_length_required"})
            if len(str(content_length)) > 6:
                return _response(start_response, 413, {"error": "request_too_large"})
            size = int(content_length)
            if size > MAX_BODY_BYTES:
                return _response(start_response, 413, {"error": "request_too_large"})
            try:
                body = environ["wsgi.input"].read(size)
                if len(body) != size:
                    return _response(start_response, 400, {"error": "incomplete_body"})
                decoded = body.decode("utf-8", "strict")
                # Avoid unpaired surrogate escapes propagating into SQLite.
                decoded.encode("utf-8", "strict")
                payload = json.loads(decoded, object_pairs_hook=_strict_pairs,
                                     parse_constant=_reject_constant)
                json.dumps(payload, ensure_ascii=False).encode("utf-8", "strict")
            except (KeyError, ValueError, UnicodeError, json.JSONDecodeError, RecursionError):
                return _response(start_response, 400, {"error": "invalid_json"})
            if shortlist_write:
                try:
                    if path == "/v1/shortlists":
                        result = shortlists.create(payload)
                        return _response(start_response, 201, result,
                                         location="/v1/shortlists/" + result["shortlist_id"])
                    if members_match:
                        result = shortlists.add(members_match.group(1), payload)
                        return _response(start_response, 201, result)
                    result = shortlists.set_note(entry_match.group(1), entry_match.group(2), payload)
                    return _response(start_response, 200, result)
                except ShortlistError as exc:
                    return _response(start_response, exc.status, {"error": exc.code})
                except (EvidenceStoreError, sqlite3.Error):
                    return _response(start_response, 503, {"error": "evidence_unavailable"})
                except Exception:
                    return _response(start_response, 500, {"error": "internal_error"})
            if path == "/v1/addresses/search":
                if (not isinstance(payload, dict) or set(payload) != {"query"}
                        or not isinstance(payload.get("query"), str)):
                    return _response(start_response, 422,
                                     {"error": "invalid_request", "field": "query",
                                      "code": "query_required"})
                query = payload["query"].strip()
                if not ADDRESS_SEARCH_PATTERN.fullmatch(query):
                    return _response(start_response, 422,
                                     {"error": "invalid_request", "field": "query",
                                      "code": "invalid_search_query"})
                try:
                    return _response(start_response, 200, store.search_synthetic_addresses(query))
                except (EvidenceStoreError, sqlite3.Error):
                    return _response(start_response, 503, {"error": "evidence_unavailable"})
            try:
                result = store.create(payload, today=today)
            except ContractError as exc:
                return _response(start_response, 422,
                                 {"error": "invalid_request", "field": exc.field, "code": exc.code})
            except (EvidenceStoreError, sqlite3.Error):
                return _response(start_response, 503, {"error": "evidence_unavailable"})
            except Exception:
                # Do not leak publisher records, SQL, file paths or stack traces.
                return _response(start_response, 500, {"error": "internal_error"})
            return _response(start_response, 201, result,
                             location=f"/v1/investigations/{result['investigation_id']}")

        address_match = ADDRESS_ROUTE.fullmatch(path)
        if address_match:
            if method != "GET":
                return _response(start_response, 405,
                                 {"error": "method_not_allowed"}, allow="GET")
            try:
                found = store.resolve_synthetic_address(address_match.group(1))
            except (EvidenceStoreError, sqlite3.Error):
                return _response(start_response, 503, {"error": "evidence_unavailable"})
            if found is None:
                return _response(start_response, 404, {"error": "address_not_found"})
            return _response(start_response, 200, found)

        preview_match = PREVIEW_ROUTE.fullmatch(path)
        if preview_match:
            if method != "GET":
                return _response(start_response, 405, {"error": "method_not_allowed"}, allow="GET")
            try:
                return _response(start_response, 200, buyer_evidence_preview(store, preview_match.group(1)))
            except EvidenceStoreError as exc:
                if str(exc) == "Investigation not found":
                    return _response(start_response, 404, {"error": "investigation_not_found"})
                return _response(start_response, 503, {"error": "evidence_unavailable"})
            except (sqlite3.Error, ValueError, TypeError, KeyError):
                return _response(start_response, 503, {"error": "evidence_unavailable"})

        map_match = MAP_ROUTE.fullmatch(path)
        if map_match:
            if method != "GET":
                return _response(start_response, 405, {"error": "method_not_allowed"}, allow="GET")
            try:
                return _response(start_response, 200, map_evidence(
                    store, map_match.group(1), enabled=synthetic_map))
            except EvidenceStoreError as exc:
                if str(exc) == "Investigation not found":
                    return _response(start_response, 404, {"error": "investigation_not_found"})
                return _response(start_response, 503, {"error": "evidence_unavailable"})
            except (sqlite3.Error, ValueError, TypeError, KeyError):
                return _response(start_response, 503, {"error": "evidence_unavailable"})

        match = ID_ROUTE.fullmatch(path)
        if match:
            if method != "GET":
                return _response(start_response, 405, {"error": "method_not_allowed"}, allow="GET")
            try:
                result = store.reopen(match.group(1))
            except EvidenceStoreError as exc:
                if str(exc) == "Investigation not found":
                    return _response(start_response, 404, {"error": "investigation_not_found"})
                return _response(start_response, 503, {"error": "evidence_unavailable"})
            except sqlite3.Error:
                return _response(start_response, 503, {"error": "evidence_unavailable"})
            except Exception:
                return _response(start_response, 500, {"error": "internal_error"})
            return _response(start_response, 200, result)
        return _response(start_response, 404, {"error": "not_found"})

    return app
