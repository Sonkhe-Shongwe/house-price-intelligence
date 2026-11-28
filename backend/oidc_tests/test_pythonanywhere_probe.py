"""No external connections: explicit proxy transport and identity integration."""
from email.message import Message
from io import BytesIO
import json
import ssl
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit
from time import time
from pathlib import Path
from tempfile import TemporaryDirectory

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from backend.oidc_boundary import AuthDenied, random_token
from backend.persistent_oidc import PersistentBoundary
from backend.oidc_pythonanywhere_probe import (
    OfflineProxyExchange, ISSUER, HOST, REDIRECT, CLIENT, SECRET, MAX_RESPONSE,
)


class Response(BytesIO):
    def __init__(self, body, *, status=200, content_type="application/json"):
        super().__init__(body)
        self.status = status
        self.headers = Message()
        self.headers.add_header("Content-Type", content_type)


class ProxyTests(unittest.TestCase):
    def setUp(self):
        self.connection = Mock()
        self.factory = Mock(return_value=self.connection)
        self.exchange = OfflineProxyExchange(proxy_port=8765, connection_factory=self.factory)
        self.verifier = random_token()

    def invoke(self):
        return self.exchange(code="invented-code", verifier=self.verifier,
                             redirect_uri=REDIRECT)

    def response(self, body, **kwargs):
        self.connection.getresponse.return_value = Response(body, **kwargs)

    def test_pinned_connect_and_tls_no_ambient_proxy(self):
        self.response(b'{"id_token":"invented-token"}')
        with patch.dict("os.environ", {"HTTPS_PROXY": "http://unexpected.invalid:80",
                                       "NO_PROXY": "*"}):
            self.assertEqual(self.invoke(), "invented-token")
        args, kwargs = self.factory.call_args
        self.assertEqual(args, ("127.0.0.1", 8765))
        self.assertEqual(kwargs["timeout"], 10)
        self.assertTrue(kwargs["context"].check_hostname)
        self.assertEqual(kwargs["context"].verify_mode, ssl.CERT_REQUIRED)
        self.connection.set_tunnel.assert_called_once_with(
            HOST, 443, headers={"Host": HOST + ":443"})
        args, kwargs = self.connection.request.call_args
        self.assertEqual(args, ("POST", "/oauth/token"))
        self.assertEqual(kwargs["headers"]["Host"], HOST)
        body = parse_qs(kwargs["body"].decode("ascii"))
        self.assertEqual(body["client_secret"], [SECRET])
        self.assertEqual(body["code_verifier"], [self.verifier])
        self.connection.close.assert_called_once()

    def test_redirect_and_invalid_response_refused_without_retry(self):
        for body, opts in (
            (b'{"id_token":"x"}', {"status": 302}),
            (b'{"id_token":"x"}', {"status": 407}),
            (b'{"id_token":"x"}', {"content_type": "text/html"}),
            (b'{"id_token":"x","id_token":"y"}', {}),
            (b'{"error":"private","id_token":"x"}', {}),
            (b'{"id_token":42}', {}),
            (b'{}', {}),
            (b'x' * (MAX_RESPONSE + 1), {}),
        ):
            with self.subTest(opts=opts, length=len(body)):
                self.connection.reset_mock()
                self.response(body, **opts)
                with self.assertRaisesRegex(AuthDenied, "^Identity exchange unavailable$"):
                    self.invoke()
                self.connection.request.assert_called_once()
                self.connection.close.assert_called_once()

    def test_invalid_configuration_and_request_never_connect(self):
        for port in (True, 0, 65536, "8765"):
            with self.assertRaises(ValueError):
                OfflineProxyExchange(proxy_port=port, connection_factory=self.factory)
        with self.assertRaises(AuthDenied):
            self.exchange(code="x", verifier=self.verifier,
                          redirect_uri="https://unexpected.invalid/callback")
        self.factory.assert_not_called()

    def test_tls_or_connect_failure_redacted(self):
        self.connection.request.side_effect = ssl.SSLCertVerificationError("private")
        with self.assertRaisesRegex(AuthDenied, "^Identity exchange unavailable$"):
            self.invoke()
        self.connection.close.assert_called_once()

    def test_signed_token_session_restart_replay_and_logout(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with TemporaryDirectory() as folder:
            config = dict(session_file=Path(folder)/"sessions.sqlite",
                          issuer=ISSUER, client_id=CLIENT,
                          authorize_endpoint=ISSUER+"authorize", redirect_uri=REDIRECT,
                          public_keys={"fixture": key.public_key()},
                          owner_map={(ISSUER, "alice"): "fictional-alice",
                                     (ISSUER, "bob"): "fictional-bob"})
            boundary = PersistentBoundary(**config)
            binding = random_token()
            query = parse_qs(urlsplit(boundary.begin(binding)).query)
            claims = dict(iss=ISSUER, sub="alice", aud=CLIENT, iat=int(time()),
                          exp=int(time())+300, nonce=query["nonce"][0])
            token = jwt.encode(claims, key, algorithm="RS256", headers={"kid": "fixture"})
            self.response(json.dumps({"id_token": token}).encode())
            args = dict(state=query["state"][0], browser_binding=binding,
                        code="invented-code", exchange=self.exchange)
            result = boundary.finish(**args)
            with self.assertRaises(AuthDenied):
                boundary.finish(**args)
            cookie = result["cookie"].split(";")[0]
            restarted = PersistentBoundary(**config)
            self.assertEqual(restarted.authorize(cookie=cookie, method="GET"), "fictional-alice")
            restarted.logout(cookie=cookie, origin="https://hpi.invalid", csrf=result["csrf"])
            with self.assertRaises(AuthDenied):
                boundary.authorize(cookie=cookie, method="GET")
