"""Offline explicit CONNECT proxy compatibility probe.

Not a provider adapter. Only a reserved invented issuer and a loopback proxy
are supported; no live endpoint, environment configuration, credential
loading, discovery or deployment entry point. Connection factory must be
injected by the offline test harness.
"""
import http.client
import json
import ssl
from urllib.parse import urlencode

from backend.oidc_boundary import AuthDenied, valid_token
from backend.oidc_exchange import MAX_RESPONSE, _unique

ISSUER = "https://fictional-idp.invalid/"
HOST = "fictional-idp.invalid"
REDIRECT = "https://hpi.invalid/callback"
CLIENT = "hpi-fixture"
SECRET = "invented-only-credential-not-a-secret"


class OfflineProxyExchange:
    """Model a pinned HTTPS tunnel without changing the ordinary exchange."""

    def __init__(self, *, proxy_port, connection_factory):
        if (type(proxy_port) is not int or not 1 <= proxy_port <= 65535
                or not callable(connection_factory)):
            raise ValueError("Explicit loopback proxy probe required")
        self.port = proxy_port
        self._factory = connection_factory

    def __call__(self, *, code, verifier, redirect_uri):
        if (not isinstance(code, str) or not 1 <= len(code) <= 2048
                or not valid_token(verifier) or redirect_uri != REDIRECT):
            raise AuthDenied("Identity exchange unavailable")
        conn = None
        try:
            body = urlencode({
                "grant_type": "authorization_code", "client_id": CLIENT,
                "client_secret": SECRET, "code": code,
                "code_verifier": verifier, "redirect_uri": REDIRECT,
            }).encode("ascii")
            context = ssl.create_default_context()
            if not context.check_hostname or context.verify_mode != ssl.CERT_REQUIRED:
                raise ValueError("TLS verification required")
            # HTTPSConnection connects to the explicit local proxy, issues
            # CONNECT to the pinned host and verifies TLS for the tunnel host.
            # No ambient proxy, redirects, caller-selected authority or retry.
            conn = self._factory("127.0.0.1", self.port, timeout=10, context=context)
            conn.set_tunnel(HOST, 443, headers={"Host": HOST + ":443"})
            conn.request("POST", "/oauth/token", body=body, headers={
                "Host": HOST, "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json", "Accept-Encoding": "identity",
                "Connection": "close",
            })
            with conn.getresponse() as response:
                content_type = response.headers.get_all("Content-Type", [])
                encoding = response.headers.get_all("Content-Encoding", [])
                if (response.status != 200 or len(content_type) != 1
                        or response.headers.get_content_type() != "application/json"
                        or encoding not in ([], ["identity"])):
                    raise ValueError("Unexpected token response")
                raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ValueError("Token response too large")
            data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
            if not isinstance(data, dict) or "error" in data:
                raise ValueError("Token response refused")
            token = data.get("id_token")
            if not isinstance(token, str) or not 1 <= len(token) <= 16000:
                raise ValueError("ID token required")
            # OidcBoundary still owns signature, nonce, audience, issuer,
            # subject and lifetime verification; never trust claims here.
            return token
        except Exception:
            raise AuthDenied("Identity exchange unavailable") from None
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
