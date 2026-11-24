"""Offline HTTPS-only WSGI session adapter. No issuer network access or launcher.
Only trusted tests may inject a confidential code exchange for a fictional issuer.
"""
import json
import sqlite3
from urllib.parse import urlsplit,parse_qs
from backend.oidc_boundary import AuthDenied,random_token,valid_token
from backend.postgres_runtime import serve_owner
from backend.synthetic_http import ALLOWED_HOST,_response

BINDING="__Host-hpi_login"
def binding_cookie(value,age=300):
    return f"{BINDING}={value}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age={age}"
def browser_binding(cookie):
    if len(cookie)>4096:raise AuthDenied("Login binding rejected")
    vals=[part.strip().split("=",1)[1] for part in cookie.split(";") if part.strip().startswith(BINDING+"=")]
    if len(vals)!=1 or not valid_token(vals[0]):raise AuthDenied("Login binding rejected")
    return vals[0]
def reply(start,code,value,cookies=(),location=None):
    data=json.dumps(value,separators=(",",":")).encode()
    headers=[("Content-Type","application/json"),("Cache-Control","no-store"),("Content-Length",str(len(data))),
        ("X-Content-Type-Options","nosniff"),("Referrer-Policy","no-referrer"),("Content-Security-Policy","default-src 'none'")]
    headers.extend(("Set-Cookie",c) for c in cookies)
    if location:headers.append(("Location",location))
    start(code,headers)
    return [data]
def application(pool,assets,boundary,exchange):
    if not urlsplit(boundary.issuer).hostname.endswith(".invalid") or not ALLOWED_HOST.fullmatch(urlsplit(boundary.origin).netloc):
        raise ValueError("Offline fictional issuer and loopback HTTPS only")
    def app(env,start):
        method=env.get("REQUEST_METHOD","")
        path=env.get("PATH_INFO","")
        host=env.get("HTTP_HOST","")
        origin=env.get("HTTP_ORIGIN")
        cookie=env.get("HTTP_COOKIE","")
        csrf=env.get("HTTP_X_HPI_CSRF")
        if (env.get("wsgi.url_scheme")!="https" or env.get("REMOTE_ADDR") not in ("127.0.0.1","::1")
            or "https://"+host!=boundary.origin or (origin is not None and origin!=boundary.origin)
            or env.get("HTTP_SEC_FETCH_SITE") in ("cross-site","same-site")
            or any(env.get(k) for k in ("HTTP_FORWARDED","HTTP_X_FORWARDED_FOR","HTTP_X_FORWARDED_HOST","HTTP_X_FORWARDED_PROTO","HTTP_X_REAL_IP"))):
            return _response(start,403,{"error":"local_fixture_only"})
        try:
            if path=="/auth/start" and method=="POST":
                if origin!=boundary.origin or env.get("QUERY_STRING"):raise AuthDenied("Login start rejected")
                bind=random_token()
                return reply(start,"200 OK",{"authorize_url":boundary.begin(bind)},(binding_cookie(bind),))
            if path=="/auth/callback" and method=="GET":
                raw=env.get("QUERY_STRING","")
                if len(raw)>4096:raise AuthDenied("Callback rejected")
                args=parse_qs(raw,keep_blank_values=True,strict_parsing=True,max_num_fields=2)
                if set(args)!={"state","code"} or any(len(v)!=1 for v in args.values()):raise AuthDenied("Callback rejected")
                result=boundary.finish(state=args["state"][0],browser_binding=browser_binding(cookie),code=args["code"][0],exchange=exchange)
                return reply(start,"303 See Other",{},(result["cookie"],binding_cookie("",0)),location="/")
            if path=="/auth/session" and method=="GET":
                if env.get("QUERY_STRING"):raise AuthDenied("Session rejected")
                return reply(start,"200 OK",{"csrf":boundary.csrf_for_session(cookie)})
            if path=="/auth/logout" and method=="POST":
                if env.get("QUERY_STRING"):raise AuthDenied("Session rejected")
                return reply(start,"200 OK",{"logged_out":True},(boundary.logout(cookie=cookie,origin=origin,csrf=csrf),))
            if path.startswith("/auth/"):return _response(start,405,{"error":"method_not_allowed"})
            owner=boundary.authorize(cookie=cookie,method=method,origin=origin,csrf=csrf)
            return serve_owner(pool,assets,env,start,owner)
        except (AuthDenied,ValueError):return _response(start,401,{"error":"fictional_authentication_required"})
        except (sqlite3.Error,OSError):return _response(start,503,{"error":"session_unavailable"})
    return app
