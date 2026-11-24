"""Export responses from the ACTUAL local-only WSGI API, not hand-written mock JSON.

Used by the isolated TypeScript evidence-bridge CI. No publisher records,
external HTTP, geography changes or durable database are involved.
"""
from __future__ import annotations

from datetime import date
from io import BytesIO
import json

from wsgiref.util import setup_testing_defaults

from backend.synthetic_demo import example_request, in_memory_demo
from backend.synthetic_http import create_app


def invoke(app, method: str, route: str, payload: dict | None = None):
    raw = b"" if payload is None else json.dumps(payload).encode("utf-8")
    environ = {}
    setup_testing_defaults(environ)
    environ.update({
        "REQUEST_METHOD": method,
        "PATH_INFO": route,
        "QUERY_STRING": "",
        "HTTP_HOST": "127.0.0.1:8765",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.input": BytesIO(raw),
        "CONTENT_TYPE": "application/json",
        "CONTENT_LENGTH": str(len(raw)),
    })
    observed = {}

    def start_response(status, headers):
        observed["code"] = int(status.split()[0])

    body = b"".join(app(environ, start_response))
    result = json.loads(body.decode("utf-8"))
    if observed["code"] not in (200, 201):
        raise AssertionError(f"{method} {route}: {observed['code']} {result}")
    return result


def main():
    conn, store = in_memory_demo()
    try:
        app = create_app(store, today=date(2026, 11, 24))
        supported = invoke(app, "POST", "/v1/investigations", example_request())
        weak_request = example_request()
        weak_request["subject"]["pin"] = "00000000000099"
        weak_request["subject"]["label"] = "Invented no-evidence parcel"
        insufficient = invoke(app, "POST", "/v1/investigations", weak_request)
        collection = invoke(app, "POST", "/v1/shortlists", {"label": "Fixture-only browser bridge"})
        sid = collection["shortlist_id"]
        invoke(app, "POST", f"/v1/shortlists/{sid}/entries",
               {"investigation_id": supported["investigation_id"], "note_text": "Review source"})
        invoke(app, "POST", f"/v1/shortlists/{sid}/entries",
               {"investigation_id": insufficient["investigation_id"], "note_text": "No evidence"})
        reopen = invoke(app, "GET", f"/v1/investigations/{supported['investigation_id']}")
        if supported != reopen:
            raise AssertionError("Frozen investigation did not reopen unchanged")
        shortlist = invoke(app, "GET", f"/v1/shortlists/{sid}")
        print(json.dumps({"supported": supported, "insufficient": insufficient,
                          "shortlist": shortlist}, ensure_ascii=True, allow_nan=False))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
