"""Confidential authorization-code exchange candidate; not a live login route.

Only explicitly configured same-origin HTTPS token endpoints. No discovery,
redirects, ambient proxies, refresh token persistence or logging.
"""
import json
import ssl
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, HTTPSHandler, ProxyHandler
from backend.oidc_boundary import AuthDenied, https_url, valid_token

MAX_RESPONSE=65536


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise AuthDenied("Identity exchange unavailable")


def _unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:
            raise ValueError("Duplicate response key")
        result[key]=value
    return result


class ConfidentialCodeExchange:
    """Server-only client_secret_post and S256 PKCE. Never trust response claims here."""
    def __init__(self,*,issuer,token_endpoint,client_id,client_secret,redirect_uri):
        self.issuer=https_url(issuer)
        self.endpoint=https_url(token_endpoint)
        self.redirect=https_url(redirect_uri)
        i,e=urlsplit(self.issuer),urlsplit(self.endpoint)
        if (i.netloc!=e.netloc or i.port not in (None,443)
            or not e.path or e.path=="/" or any(c.isspace() for c in self.endpoint)
            or not isinstance(client_id,str) or not 1<=len(client_id)<=256
            or not isinstance(client_secret,str) or not 24<=len(client_secret)<=2048):
            raise ValueError("Confidential exchange configuration refused")
        self.client_id=client_id
        self._secret=client_secret
        self._opener=build_opener(ProxyHandler({}),HTTPSHandler(context=ssl.create_default_context()),_NoRedirect())

    def __call__(self,*,code,verifier,redirect_uri):
        if (not isinstance(code,str) or not 1<=len(code)<=2048
            or not valid_token(verifier) or redirect_uri!=self.redirect):
            raise AuthDenied("Identity exchange unavailable")
        try:
            body=urlencode({"grant_type":"authorization_code","client_id":self.client_id,
                "client_secret":self._secret,"code":code,"code_verifier":verifier,
                "redirect_uri":self.redirect}).encode("ascii")
            req=Request(self.endpoint,data=body,method="POST",headers={
                "Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"})
            with self._opener.open(req,timeout=10) as response:
                if (response.status!=200 or response.geturl()!=self.endpoint
                    or response.headers.get_content_type()!="application/json"):
                    raise ValueError("Unexpected token response")
                raw=response.read(MAX_RESPONSE+1)
            if len(raw)>MAX_RESPONSE:
                raise ValueError("Token response too large")
            data=json.loads(raw.decode("utf-8"),object_pairs_hook=_unique)
            if not isinstance(data,dict) or "error" in data:
                raise ValueError("Token response refused")
            token=data.get("id_token")
            if not isinstance(token,str) or not 1<=len(token)<=16000:
                raise ValueError("ID token required")
            # Existing OidcBoundary performs signature, issuer, audience,
            # nonce, lifetime and explicit subject-to-owner verification.
            return token
        except Exception:
            raise AuthDenied("Identity exchange unavailable") from None
