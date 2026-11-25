"""Authenticated, offline HTTPS-only rehearsal routes, never a live data API.
Called only after the existing offline OIDC adapter checks origin/session/CSRF.
No real-data switch, arbitrary source, deployment launcher or new auth system.
"""
import json
import re
import psycopg
from backend.synthetic_http import (MAX_BODY_BYTES, SECURITY_HEADERS, _response,
    _strict_pairs, _reject_constant, UUID_PART)
from backend.curated_ingestion_candidate import ImportRefused
from backend.investigation_contract import ContractError

PAGE="/private-beta-rehearsal"
PREFIX="/v1/private-beta-rehearsal"
REOPEN=re.compile("^"+PREFIX+"/investigations/"+UUID_PART+"$")


def _body(env):
    content_type=env.get("CONTENT_TYPE","").lower().replace(" ","")
    if content_type not in ("application/json","application/json;charset=utf-8"):
        raise ValueError("Invalid JSON content type")
    size=env.get("CONTENT_LENGTH","")
    if not size.isascii() or not size.isdecimal() or len(size)>5 or not 0<int(size)<=MAX_BODY_BYTES:
        raise ValueError("Invalid JSON body length")
    raw=env["wsgi.input"].read(int(size))
    if len(raw)!=int(size):
        raise ValueError("Incomplete JSON body")
    value=json.loads(raw.decode("utf-8"),object_pairs_hook=_strict_pairs,parse_constant=_reject_constant)
    if not isinstance(value,dict):
        raise ValueError("Object required")
    return value


def route(service,assets,env,start):
    # Defense in depth: never expose the mode from the ordinary fixture adapter.
    if env.get("wsgi.url_scheme")!="https" or env.get("REMOTE_ADDR") not in ("127.0.0.1","::1"):
        return _response(start,403,{"error":"local_fixture_only"})
    path=env.get("PATH_INFO",""); method=env.get("REQUEST_METHOD","")
    if env.get("QUERY_STRING"):
        return _response(start,400,{"error":"query_parameters_not_supported"})
    cookie=env.get("HTTP_COOKIE","")
    auth=dict(cookie=cookie,origin=env.get("HTTP_ORIGIN"),csrf=env.get("HTTP_X_HPI_CSRF"))
    if path=="/" and method=="GET":
        start("303 See Other",[("Location",PAGE),("Content-Length","0"),*SECURITY_HEADERS])
        return [b""]
    if path==PAGE or (path.startswith("/assets/") and path in assets):
        if method!="GET":
            return _response(start,405,{"error":"method_not_allowed"},allow="GET")
        payload,content_type=assets["/" if path==PAGE else path]
        start("200 OK",[("Content-Type",content_type),("Content-Length",str(len(payload))),*SECURITY_HEADERS])
        return [payload]
    match=REOPEN.fullmatch(path)
    if path not in (PREFIX+"/search",PREFIX+"/investigations") and not match:
        return _response(start,404,{"error":"not_found"})
    expected="GET" if match else "POST"
    if method!=expected:
        return _response(start,405,{"error":"method_not_allowed"},allow=expected)
    try:
        payload=None if match else _body(env)
    except (ValueError,KeyError,UnicodeError):
        return _response(start,400,{"error":"invalid_request"})
    try:
        # Both restricted fixture connections are shared by the test harness.
        # Serialize complete calls so transaction-local identity cannot interleave.
        with service.request_lock:
            if match:
                return _response(start,200,service.reopen(match[1],cookie=cookie))
            if path==PREFIX+"/search":
                if set(payload)!={"query","analysis_date"}:
                    return _response(start,400,{"error":"invalid_request"})
                return _response(start,200,service.search(payload["query"],payload["analysis_date"],**auth))
            result=service.create(payload,**auth)
            return _response(start,201,result,location=PREFIX+"/investigations/"+result["investigation_id"])
    except ContractError:
        return _response(start,422,{"error":"invalid_investigation"})
    except ImportRefused:
        return _response(start,404 if match else 422,{"error":"investigation_unavailable"})
    except (psycopg.Error,RuntimeError,KeyError,TypeError):
        return _response(start,503,{"error":"evidence_unavailable"})
