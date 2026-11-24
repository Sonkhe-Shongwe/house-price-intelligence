"""Isolated loopback proof: Vite dist + strictly gated HPI fixture WSGI.

Not part of backend/ or the approved frontend. Does not relax the app's
local-host, forwarded-header, same-origin, source-kind or privacy restrictions.
Only a compiled, finite set of JS/CSS assets may be read. All source evidence
is generated and served by the actual HPI SQLite/WSGI fixture application.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.synthetic_demo import example_request, in_memory_demo  # noqa: E402
from backend.synthetic_http import (  # noqa: E402
    ALLOWED_HOST, ID_ROUTE, SHORTLIST_ROUTE, ADDRESS_ROUTE,
    SHORTLIST_MEMBERS_ROUTE, SHORTLIST_ENTRY_ROUTE,
    SECURITY_HEADERS, create_app,
)
from backend.synthetic_shortlists import SyntheticShortlistService  # noqa: E402

DIST = Path(__file__).resolve().parents[1] / "dist"
ASSET_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,62}-[A-Za-z0-9_-]{6,}\.(?:js|css)$")
MIME_TYPES = {".html": "text/html; charset=utf-8",
              ".js": "text/javascript; charset=utf-8",
              ".css": "text/css; charset=utf-8"}
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; "
       "connect-src 'self'; img-src 'self'; worker-src 'self'; "
       "base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'")
STRICT_HEADERS = [
    (key, CSP if key == "Content-Security-Policy" else value)
    for key, value in SECURITY_HEADERS
] + [("X-Proof-Mode", "read-only")]


def _allowed_request(environ) -> bool:
    host = environ.get("HTTP_HOST", "")
    origin = environ.get("HTTP_ORIGIN")
    if (environ.get("REMOTE_ADDR") not in ("127.0.0.1", "::1")
            or not ALLOWED_HOST.fullmatch(host)
            or (origin is not None and origin.lower() != "http://" + host.lower())
            or environ.get("HTTP_SEC_FETCH_SITE") in ("same-site", "cross-site")):
        return False
    return not any(environ.get(header) for header in (
        "HTTP_X_FORWARDED_FOR", "HTTP_X_FORWARDED_HOST",
        "HTTP_X_FORWARDED_PROTO", "HTTP_X_REAL_IP", "HTTP_FORWARDED",
    ))


def _send(start_response, code: int, body: bytes, content_type: str, *, mode: str = "read-only"):
    statuses = {200: "200 OK", 400: "400 Bad Request", 403: "403 Forbidden",
                404: "404 Not Found", 405: "405 Method Not Allowed",
                503: "503 Service Unavailable"}
    start_response(statuses[code], [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        *((key, mode if key == "X-Proof-Mode" else value) for key, value in STRICT_HEADERS),
    ])
    return [body]


def _json(start_response, code: int, value, *, mode: str = "read-only"):
    return _send(
        start_response, code,
        json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("utf-8"),
        "application/json; charset=utf-8", mode=mode,
    )


def approved_assets(directory: Path) -> dict[str, tuple[bytes, str]]:
    """Read an exact allowlist at startup, never resolve request paths to disk."""
    directory = directory.resolve(strict=True)
    index = directory / "index.html"
    if index.is_symlink() or not index.is_file():
        raise RuntimeError("Missing trusted Vite index.html")
    assets = {"/": (index.read_bytes(), MIME_TYPES[".html"]),
              "/source-review": (index.read_bytes(), MIME_TYPES[".html"])}
    generated = directory / "assets"
    if not generated.is_dir() or generated.is_symlink():
        raise RuntimeError("Missing trusted Vite assets directory")
    for entry in generated.iterdir():
        if entry.is_symlink() or not entry.is_file() or not ASSET_NAME.fullmatch(entry.name):
            raise RuntimeError("Unrecognised asset in isolated Vite build: " + entry.name)
        assets["/assets/" + entry.name] = (entry.read_bytes(), MIME_TYPES[entry.suffix])
    if not any(p.startswith("/assets/SourceReview-") and p.endswith(".js") for p in assets):
        raise RuntimeError("Connected review chunk is absent from production Vite build")
    return assets


def seeded_readonly_preview(directory: Path = DIST, *, enable_buyer_workflow: bool = False,
                            enable_shortlist_workflow: bool = False):
    if enable_shortlist_workflow and not enable_buyer_workflow:
        raise ValueError('Shortlist write proof requires the separate buyer-workflow flag')
    db, store = in_memory_demo()
    try:
        verified = store.create(example_request(), today=date(2026, 11, 24))
        missing_req = example_request()
        missing_req["subject"]["pin"] = "00000000000099"
        missing_req["subject"]["label"] = "Invented no-evidence parcel"
        insufficient = store.create(missing_req, today=date(2026, 11, 24))
        shortlist = SyntheticShortlistService(store)
        sid = shortlist.create({"label": "Fictional buyer review"})["shortlist_id"]
        shortlist.add(sid, {"investigation_id": verified["investigation_id"],
                            "note_text": "Check the original recorded evidence"})
        shortlist.add(sid, {"investigation_id": insufficient["investigation_id"],
                            "note_text": "No eligible sales, do not infer a price"})
        cases = {
            "source_kind": "synthetic_fixture",
            "cases": [
                {"key": "supported", "label": verified["subject"]["label"],
                 "investigation_id": verified["investigation_id"]},
                {"key": "insufficient", "label": insufficient["subject"]["label"],
                 "investigation_id": insufficient["investigation_id"]},
            ],
            "shortlist_id": sid,
        }
        assets = approved_assets(directory)
        backend_app = create_app(store, today=date(2026, 11, 24))
    except Exception:
        db.close()
        raise

    def app(environ, start_response):
        mode = ("fixture-shortlist-writes" if enable_shortlist_workflow else
                "fixture-investigation-writes" if enable_buyer_workflow else "read-only")
        if not _allowed_request(environ):
            return _json(start_response, 403, {"error": "local_fixture_only"}, mode=mode)
        if environ.get("QUERY_STRING"):
            return _json(start_response, 400, {"error": "query_parameters_not_supported"}, mode=mode)
        path = environ.get("PATH_INFO", "")
        method = environ.get("REQUEST_METHOD", "")
        if (enable_buyer_workflow and method == "POST"
                and path in ("/v1/addresses/search", "/v1/investigations")):
            # Preserve every original JSON validation, source check and error code.
            return backend_app(environ, start_response)
        if (enable_shortlist_workflow and
                ((method == "POST" and (path == "/v1/shortlists" or
                     SHORTLIST_MEMBERS_ROUTE.fullmatch(path))) or
                 (method == "PATCH" and SHORTLIST_ENTRY_ROUTE.fullmatch(path)))):
            # Shortlist service enforces max 3, unique parcels and frozen source evidence.
            # No DELETE routes or production persistence are exposed in this experiment.
            return backend_app(environ, start_response)
        if method != "GET":
            return _json(start_response, 405, {"error": "read_only_fixture_preview"}, mode=mode)
        if path in assets or (enable_buyer_workflow and path == "/buyer-workflow"):
            body, mime = assets[path if path in assets else "/"]
            return _send(start_response, 200, body, mime, mode=mode)
        if path == "/_study/cases":
            return _json(start_response, 200, cases, mode=mode)
        if path == "/_study/capabilities":
            return _json(start_response, 200, {"source_kind": "synthetic_fixture",
                "buyer_writes": enable_buyer_workflow,
                "shortlist_writes": enable_shortlist_workflow}, mode=mode)
        if (path == "/health" or ID_ROUTE.fullmatch(path) or SHORTLIST_ROUTE.fullmatch(path)
                or (enable_buyer_workflow and ADDRESS_ROUTE.fullmatch(path))):
            return backend_app(environ, start_response)
        return _json(start_response, 404, {"error": "not_found"}, mode=mode)

    return app, db


def main() -> None:
    parser = argparse.ArgumentParser(description="Isolated read-only React <-> Python fixture review")
    parser.add_argument("--port", type=int, default=8797)
    parser.add_argument("--enable-buyer-workflow", action="store_true",
                        help="Opt in to fictional address-search and investigation-create POSTs")
    parser.add_argument("--enable-shortlist-workflow", action="store_true",
                        help="Separately opt in to fictional shortlist create/add/note writes")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Use an unprivileged local port")
    if args.enable_shortlist_workflow and not args.enable_buyer_workflow:
        parser.error("--enable-shortlist-workflow requires --enable-buyer-workflow")
    app, db = seeded_readonly_preview(enable_buyer_workflow=args.enable_buyer_workflow,
                                      enable_shortlist_workflow=args.enable_shortlist_workflow)
    try:
        with make_server("127.0.0.1", args.port, app) as server:
            route = "/buyer-workflow" if args.enable_buyer_workflow else "/source-review"
            print(f"Fictional local HPI preview: http://127.0.0.1:{args.port}{route}", flush=True)
            server.serve_forever()
    finally:
        db.close()


if __name__ == "__main__":
    main()
