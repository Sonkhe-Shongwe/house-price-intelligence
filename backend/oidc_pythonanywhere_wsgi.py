"""Offline authenticated WSGI workspace rehearsal; no hosted launcher.

Canonical legacy invented fixtures only, not persistent NYC property data.
NYC lifecycle policy is exercised against independent synthetic authority.
"""
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import fcntl
import os
from pathlib import Path
import stat

from backend.durable_fixture import open_file_demo
from backend.nyc_lifecycle_guard import Evidence, IntakeSeal, SOURCE_IDS, evaluate
from backend.oidc_boundary import AuthDenied
from backend.oidc_pythonanywhere_probe import ISSUER, CLIENT
from backend.persistent_oidc import PersistentBoundary
from backend.synthetic_http import (
    create_app, _response, ID_ROUTE, SHORTLIST_ROUTE, SHORTLIST_MEMBERS_ROUTE,
    SHORTLIST_ENTRY_ROUTE, ADDRESS_ROUTE,
)

HOST = "127.0.0.1:8766"
ORIGIN = "https://" + HOST
REDIRECT = ORIGIN + "/auth/callback"
OWNERS = {(ISSUER, "alice"): "fixture-alice", (ISSUER, "bob"): "fixture-bob"}
INTAKE = datetime(2026, 11, 24, tzinfo=timezone.utc)
BUILT = INTAKE + timedelta(days=1)
SEALS = tuple(IntakeSeal(source, "fixture-workspace-v1",
                         "fixture-workspace-" + str(i), "fixture-workspace-policy",
                         INTAKE, INTAKE + timedelta(days=30))
              for i, source in enumerate(sorted(SOURCE_IDS)))
FORWARDED = ("HTTP_FORWARDED", "HTTP_X_FORWARDED_FOR", "HTTP_X_FORWARDED_HOST",
             "HTTP_X_FORWARDED_PROTO", "HTTP_X_REAL_IP", "HTTP_X_HPI_OWNER")


def _private_dir(path):
    details = path.lstat()
    if (path.resolve() != path or not stat.S_ISDIR(details.st_mode)
            or details.st_uid != os.getuid() or details.st_mode & 0o077):
        raise ValueError("Private workspace directory required")


@contextmanager
def _workspace_lock(root, owner):
    # Fixed paths, never request-selected; same-UID administrator is trusted.
    if owner not in OWNERS.values():
        raise ValueError("Fixture owner required")
    _private_dir(root)
    folder = root / owner
    folder.mkdir(mode=0o700, exist_ok=True)
    _private_dir(folder)
    lock = folder / "request.lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        details = os.fstat(fd)
        current = lock.lstat()
        if (not stat.S_ISREG(details.st_mode) or details.st_uid != os.getuid()
                or details.st_mode & 0o077 or details.st_nlink != 1
                or (details.st_dev, details.st_ino) != (current.st_dev, current.st_ino)):
            raise ValueError("Unsafe workspace lock")
        # Serialize complete read/validate/write operations, not just writes.
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield folder
    finally:
        os.close(fd)


def _operations(path, method):
    if path == "/v1/investigations" and method == "POST":
        return ("read", "save")
    if method == "GET" and (path == "/v1/investigations/history" or ID_ROUTE.fullmatch(path)):
        return ("read", "reopen")
    if ((path == "/v1/addresses/search" and method == "POST")
            or (method == "GET" and ADDRESS_ROUTE.fullmatch(path))):
        return ("read",)
    if method == "GET" and (path == "/v1/shortlists" or SHORTLIST_ROUTE.fullmatch(path)):
        return ("read", "compare")
    if ((path == "/v1/shortlists" and method == "POST")
            or (method == "POST" and SHORTLIST_MEMBERS_ROUTE.fullmatch(path))
            or (method in ("PATCH", "DELETE") and SHORTLIST_ENTRY_ROUTE.fullmatch(path))):
        return ("read", "compare", "save")
    return ()


def application(root, boundary, *, authority, clock):
    """Test-invoked WSGI callable; no server, external account or deployment."""
    if os.name != "posix":
        raise ValueError("POSIX offline candidate required")
    root = Path(root).absolute()
    _private_dir(root)
    if (type(boundary) is not PersistentBoundary or boundary.issuer != ISSUER
            or boundary.client_id != CLIENT or boundary.redirect != REDIRECT
            or boundary.origin != ORIGIN or boundary.owners != OWNERS
            or boundary.path.parent != root or boundary.path.name != "sessions.sqlite"
            or not callable(authority) or not callable(clock)):
        raise ValueError("Explicit fixture identity and independent authority required")

    def app(env, start):
        method = env.get("REQUEST_METHOD", "")
        path = env.get("PATH_INFO", "")
        origin = env.get("HTTP_ORIGIN")
        cookie = env.get("HTTP_COOKIE", "")
        csrf = env.get("HTTP_X_HPI_CSRF")
        if (env.get("wsgi.url_scheme") != "https" or env.get("HTTP_HOST") != HOST
                or env.get("REMOTE_ADDR") != "127.0.0.1" or origin not in (None, ORIGIN)
                or env.get("HTTP_SEC_FETCH_SITE") in ("same-site", "cross-site")
                or env.get("QUERY_STRING") or any(env.get(k) for k in FORWARDED)):
            return _response(start, 403, {"error": "local_fixture_only"})
        try:
            owner = boundary.authorize(cookie=cookie, method=method, origin=origin, csrf=csrf)
            with _workspace_lock(root, owner) as folder:
                if owner != boundary.authorize(cookie=cookie, method=method, origin=origin, csrf=csrf):
                    raise AuthDenied("Session rejected")
                if path == "/auth/logout" and method == "POST":
                    cleared = boundary.logout(cookie=cookie, origin=origin, csrf=csrf)
                    def logout_start(status, headers):
                        return start(status, [*headers, ("Set-Cookie", cleared)])
                    return _response(logout_start, 200, {"logged_out": True})
                operations = _operations(path, method)
                if not operations:
                    return _response(start, 404, {"error": "offline_route_only"})
                now = clock()
                snapshot = authority(owner, now)
                evidence = Evidence(owner, SEALS, BUILT)
                if not all(evaluate(evidence, snapshot, owner=owner, operation=op,
                                    now=now).allowed is True for op in operations):
                    return _response(start, 403, {"error": "fixture_evidence_unavailable"})
                conn, store = open_file_demo(folder / "workspace.sqlite", private_file=True)
                try:
                    # Canonical handlers return an eager response; no header rewriting.
                    return create_app(store, today=date(2026, 11, 28))(env, start)
                finally:
                    conn.close()
        except AuthDenied:
            return _response(start, 403, {"error": "identity_rejected"})
        except Exception:
            return _response(start, 503, {"error": "fixture_workspace_unavailable"})
    return app
