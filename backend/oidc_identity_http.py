"""Identity-only local qualification HTTP boundary. No property routes or launcher.

External top-level GET callback and non-sensitive landing page are the only
cross-site navigation exceptions; state, nonce,
browser binding and PKCE remain mandatory. No actual provider request in tests.
"""
from urllib.parse import parse_qs
import json
from backend.oidc_boundary import AuthDenied,random_token,valid_token
from backend.oidc_provider_config import CALLBACK,ISSUER
from backend.oidc_exchange import ConfidentialCodeExchange
from backend.persistent_oidc import PersistentBoundary

ORIGIN="https://127.0.0.1:8766"
BINDING="__Host-hpi_login"


def _binding(cookie):
    if not isinstance(cookie,str) or len(cookie)>4096:
        raise AuthDenied("Login rejected")
    values=[part.strip().split("=",1)[1] for part in cookie.split(";")
            if part.strip().startswith(BINDING+"=")]
    if len(values)!=1 or not valid_token(values[0]):
        raise AuthDenied("Login rejected")
    return values[0]


def _reply(start,status,value=None,*,cookies=(),location=None,html=None,form_issuer=None):
    if html is None:
        body=json.dumps(value or {},separators=(",",":")).encode()
        content_type="application/json"
    else:
        body=html.encode()
        content_type="text/html; charset=utf-8"
    headers=[("Content-Type",content_type),("Content-Length",str(len(body))),
        ("Cache-Control","no-store"),("Referrer-Policy","no-referrer"),
        ("X-Content-Type-Options","nosniff"),
        ("Content-Security-Policy","default-src 'none'; form-action 'self'"+(" "+form_issuer.rstrip("/") if form_issuer else "")+"; frame-ancestors 'none'; base-uri 'none'")]
    if location:headers.append(("Location",location))
    headers.extend(("Set-Cookie",cookie) for cookie in cookies)
    start(status,headers)
    return [body]


def identity_only_application(boundary,exchange):
    if (not isinstance(boundary,PersistentBoundary) or not isinstance(exchange,ConfidentialCodeExchange)
        or not ISSUER.fullmatch(boundary.issuer) or boundary.redirect!=CALLBACK
        or boundary.origin!=ORIGIN or exchange.issuer!=boundary.issuer
        or exchange.client_id!=boundary.client_id or exchange.redirect!=CALLBACK
        or exchange.endpoint!=boundary.issuer+"oauth/token"):
        raise ValueError("Identity qualification configuration refused")

    def app(env,start):
        method,path=env.get("REQUEST_METHOD"),env.get("PATH_INFO")
        origin=env.get("HTTP_ORIGIN")
        site=env.get("HTTP_SEC_FETCH_SITE")
        query=env.get("QUERY_STRING","")
        cookie=env.get("HTTP_COOKIE","")
        callback=method=="GET" and path=="/auth/callback"
        navigation=callback or (method=="GET" and path=="/" and not query)
        if (env.get("wsgi.url_scheme")!="https" or env.get("REMOTE_ADDR")!="127.0.0.1"
            or env.get("HTTP_HOST")!="127.0.0.1:8766"
            or (origin is not None and origin!=ORIGIN)
            or (site in ("cross-site","same-site") and not navigation)
            or (navigation and site in ("cross-site","same-site") and
                (env.get("HTTP_SEC_FETCH_MODE")!="navigate" or env.get("HTTP_SEC_FETCH_DEST")!="document"))
            or any(env.get(k) for k in ("HTTP_FORWARDED","HTTP_X_FORWARDED_FOR",
                "HTTP_X_FORWARDED_HOST","HTTP_X_FORWARDED_PROTO","HTTP_X_REAL_IP"))):
            return _reply(start,"403 Forbidden",{"error":"local_identity_only"})
        try:
            if method=="GET" and path=="/" and not query:
                try:
                    boundary.authorize(cookie=cookie,method="GET")
                    body="<h1>Identity verified</h1><p>Local identity qualification only. No property data.</p>"
                except AuthDenied:
                    body='<h1>HPI identity qualification</h1><form method="post" action="/auth/start"><button>Sign in</button></form>'
                return _reply(start,"200 OK",html="<!doctype html><html><meta charset=utf-8><title>HPI identity qualification</title>"+body+"</html>",form_issuer=boundary.issuer)
            if method=="POST" and path=="/auth/start" and not query:
                if origin!=ORIGIN:raise AuthDenied("Login rejected")
                bind=random_token()
                url=boundary.begin(bind)
                return _reply(start,"303 See Other",location=url,cookies=(
                    f"{BINDING}={bind}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=300",))
            if callback:
                if len(query)>4096:raise AuthDenied("Callback rejected")
                args=parse_qs(query,keep_blank_values=True,strict_parsing=True,max_num_fields=2)
                if set(args)!={"state","code"} or any(len(v)!=1 for v in args.values()):
                    raise AuthDenied("Callback rejected")
                result=boundary.finish(state=args["state"][0],browser_binding=_binding(cookie),
                    code=args["code"][0],exchange=exchange)
                return _reply(start,"303 See Other",location="/",cookies=(result["cookie"],
                    f"{BINDING}=; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=0"))
            if method=="GET" and path=="/auth/session" and not query:
                return _reply(start,"200 OK",{"authenticated":True,"csrf":boundary.csrf_for_session(cookie)})
            if method=="POST" and path=="/auth/logout" and not query:
                cleared=boundary.logout(cookie=cookie,origin=origin,csrf=env.get("HTTP_X_HPI_CSRF"))
                return _reply(start,"200 OK",{"logged_out":True},cookies=(cleared,))
            return _reply(start,"404 Not Found",{"error":"identity_route_only"})
        except (AuthDenied,ValueError):
            return _reply(start,"401 Unauthorized",{"error":"identity_rejected"})
        except Exception:
            return _reply(start,"503 Service Unavailable",{"error":"identity_unavailable"})
    return app
