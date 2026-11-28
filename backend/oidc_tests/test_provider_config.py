"""Provider-shaped signed tokens through the real exchange adapter, no network."""
import json
import tempfile
import unittest
from pathlib import Path
from email.message import Message
from time import time
from urllib.parse import urlsplit,parse_qs
from unittest.mock import MagicMock
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from jwt.algorithms import RSAAlgorithm
from backend.oidc_boundary import AuthDenied,random_token
from backend.oidc_provider_config import prepare_auth0,CALLBACK

ISS="https://example-fixture.us.auth0.com/"
CLIENT="fixture-client"


class ProviderConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        cls.jwk=dict(json.loads(RSAAlgorithm.to_jwk(cls.key.public_key())),kid="pinned",use="sig",alg="RS256")

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config=dict(issuer=ISS,client_id=CLIENT,client_secret="x"*48,redirect_uri=CALLBACK,
            jwks={"keys":[self.jwk]},owner_by_subject={"auth0|alice":"owner-a","auth0|bob":"owner-b"},
            session_file=Path(self.tmp.name)/"provider.sqlite")

    def flow(self,boundary,exchange,**changes):
        bind=random_token()
        q=parse_qs(urlsplit(boundary.begin(bind)).query)
        now=int(time())
        claims=dict(iss=ISS,sub="auth0|alice",aud=CLIENT,nonce=q["nonce"][0],iat=now,exp=now+300)
        claims.update(changes)
        token=jwt.encode(claims,self.key,algorithm="RS256",headers={"kid":"pinned"})
        opener=MagicMock()
        exchange._opener=opener
        response=opener.open.return_value.__enter__.return_value
        response.status=200
        response.geturl.return_value=ISS+"oauth/token"
        response.headers=Message()
        response.headers["Content-Type"]="application/json"
        response.read.return_value=json.dumps({"id_token":token}).encode()
        result=boundary.finish(state=q["state"][0],browser_binding=bind,code="fictional-code",exchange=exchange)
        opener.open.assert_called_once()
        return result

    def test_signed_exchange_session_reconstruction_and_logout(self):
        boundary,exchange=prepare_auth0(**self.config)
        a=self.flow(boundary,exchange,email="ignored@example.invalid",owner_id="owner-b")
        b=self.flow(boundary,exchange,sub="auth0|bob")
        resumed,_=prepare_auth0(**self.config)
        self.assertEqual(resumed.authorize(cookie=a["cookie"],method="GET"),"owner-a")
        self.assertEqual(resumed.authorize(cookie=b["cookie"],method="GET"),"owner-b")
        resumed.logout(cookie=a["cookie"],origin=resumed.origin,csrf=a["csrf"])
        with self.assertRaises(AuthDenied):boundary.authorize(cookie=a["cookie"],method="GET")

    def test_unknown_subject_wrong_issuer_and_excessive_lifetime(self):
        boundary,exchange=prepare_auth0(**self.config)
        for changes in ({"sub":"auth0|unknown"},{"iss":"https://other.us.auth0.com/"},
                        {"exp":int(time())+36000}):
            with self.subTest(changes=changes),self.assertRaises(AuthDenied):
                self.flow(boundary,exchange,**changes)

    def test_reject_ambiguous_or_untrusted_configuration(self):
        for bad in ({"issuer":"https://example.auth0.com.evil.invalid/"},
                    {"redirect_uri":"https://other.invalid/auth/callback"},
                    {"owner_by_subject":{"auth0|alice":"same","auth0|bob":"same"}},
                    {"owner_by_subject":{"auth0|alice":"fixture-owner-a"}},
                    {"jwks":{"keys":[self.jwk,self.jwk]}},
                    {"jwks":{"keys":[dict(self.jwk,d="private")] }},
                    {"jwks":{"keys":[dict(self.jwk,alg="HS256")]}}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                prepare_auth0(**dict(self.config,**bad))
        self.assertFalse(self.config["session_file"].exists())
