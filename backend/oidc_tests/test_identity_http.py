"""WSGI qualification of provider callback without network, DB or deployment."""
import json
import tempfile
import unittest
from pathlib import Path
from email.message import Message
from time import time
from urllib.parse import urlsplit,parse_qs,urlencode
from unittest.mock import MagicMock
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from jwt.algorithms import RSAAlgorithm
from backend.oidc_provider_config import prepare_auth0,CALLBACK
from backend.oidc_identity_http import identity_only_application,ORIGIN

ISS="https://example-fixture.us.auth0.com/"


class IdentityHttpTests(unittest.TestCase):
    def setUp(self):
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        self.key=key
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.boundary,self.exchange=prepare_auth0(issuer=ISS,client_id="fixture",client_secret="x"*48,
            redirect_uri=CALLBACK,jwks={"keys":[dict(json.loads(RSAAlgorithm.to_jwk(key.public_key())),
                kid="pinned",use="sig",alg="RS256")]},owner_by_subject={"auth0|alice":"owner-a"},
            session_file=Path(tmp.name)/"identity.sqlite")
        self.opener=MagicMock()
        self.exchange._opener=self.opener
        self.diagnostics=[]
        self.app=identity_only_application(self.boundary,self.exchange,diagnostic=self.diagnostics.append)

    def request(self,path="/",method="GET",**overrides):
        env=dict(REQUEST_METHOD=method,PATH_INFO=path,QUERY_STRING="",REMOTE_ADDR="127.0.0.1",
                 HTTP_HOST="127.0.0.1:8766")
        env["wsgi.url_scheme"]="https"
        env.update(overrides)
        result=[]
        body=b"".join(self.app(env,lambda status,headers:result.extend((status,headers))))
        return result[0],result[1],body

    def begin(self):
        status,headers,_=self.request("/auth/start","POST",HTTP_ORIGIN=ORIGIN)
        self.assertEqual(status,"303 See Other")
        q=parse_qs(urlsplit(dict(headers)["Location"]).query)
        cookie=dict(headers)["Set-Cookie"].split(";",1)[0]
        now=int(time())
        token=jwt.encode(dict(iss=ISS,sub="auth0|alice",aud="fixture",
            nonce=q["nonce"][0],iat=now,exp=now+300),self.key,algorithm="RS256",headers={"kid":"pinned"})
        response=self.opener.open.return_value.__enter__.return_value
        response.status=200
        response.geturl.return_value=ISS+"oauth/token"
        response.headers=Message()
        response.headers["Content-Type"]="application/json"
        response.read.return_value=json.dumps({"id_token":token}).encode()
        return dict(QUERY_STRING=urlencode({"code":"fictional-code","state":q["state"][0],"iss":ISS}),
            HTTP_COOKIE=cookie,HTTP_SEC_FETCH_SITE="cross-site",
            HTTP_SEC_FETCH_MODE="navigate",HTTP_SEC_FETCH_DEST="document")

    def test_cross_site_callback_and_logout(self):
        params=self.begin()
        status,headers,_=self.request("/auth/callback",**params)
        self.assertEqual(status,"303 See Other")
        cookies=[v for k,v in headers if k=="Set-Cookie"]
        cookie=cookies[0].split(";",1)[0]
        self.assertIn("Identity verified",self.request(HTTP_COOKIE=cookie,HTTP_SEC_FETCH_SITE="cross-site",
            HTTP_SEC_FETCH_MODE="navigate",HTTP_SEC_FETCH_DEST="document")[2].decode())
        status,_,body=self.request("/auth/session",HTTP_COOKIE=cookie)
        self.assertEqual(status,"200 OK")
        csrf=json.loads(body)["csrf"]
        self.assertEqual(self.request("/auth/logout","POST",HTTP_COOKIE=cookie,
            HTTP_ORIGIN=ORIGIN,HTTP_X_HPI_CSRF=csrf)[0],"200 OK")
        self.assertEqual(self.request("/auth/session",HTTP_COOKIE=cookie)[0],"401 Unauthorized")
        self.assertEqual(self.request("/auth/callback",**params)[0],"401 Unauthorized")
        self.opener.open.assert_called_once()

    def test_callback_binding_and_navigation_required(self):
        params=self.begin()
        self.assertEqual(self.request("/auth/callback",**dict(params,HTTP_SEC_FETCH_DEST="iframe"))[0],"403 Forbidden")
        self.assertEqual(self.request("/auth/callback",**dict(params,HTTP_COOKIE=""))[0],"401 Unauthorized")
        self.opener.open.assert_not_called()

    def test_no_data_routes_and_local_transport_only(self):
        for path in ("/api/investigations","/private-beta-rehearsal","/api/shortlists"):
            self.assertEqual(self.request(path)[0],"404 Not Found")
        for extra in ({"REMOTE_ADDR":"192.0.2.1"},{"HTTP_HOST":"other.invalid"},
                      {"wsgi.url_scheme":"http"},{"HTTP_X_FORWARDED_FOR":"127.0.0.1"},
                      {"HTTP_SEC_FETCH_SITE":"cross-site"}):
            self.assertEqual(self.request(**extra)[0],"403 Forbidden")
        self.assertEqual(self.request("/auth/start","POST")[0],"401 Unauthorized")
        self.opener.open.assert_not_called()

    def test_landing_referrer_policy_preserves_origin_validation(self):
        status,headers,_=self.request()
        self.assertEqual(status,"200 OK")
        self.assertEqual(dict(headers)["Referrer-Policy"],"same-origin")
        for origin in ("null","https://other.invalid"):
            status,headers,_=self.request("/auth/start","POST",HTTP_ORIGIN=origin)
            self.assertEqual(status,"403 Forbidden")
            self.assertEqual(dict(headers)["Referrer-Policy"],"no-referrer")
        status,headers,_=self.request("/auth/start","POST",HTTP_ORIGIN=ORIGIN,
            HTTP_SEC_FETCH_SITE="same-origin")
        self.assertEqual(status,"303 See Other")
        self.assertEqual(dict(headers)["Referrer-Policy"],"no-referrer")
        self.opener.open.assert_not_called()

    def test_callback_diagnostics_are_fixed_and_browser_error_generic(self):
        params=self.begin()
        for cookie in ("","__Host-hpi_login=invalid",params["HTTP_COOKIE"]+"; "+params["HTTP_COOKIE"],"x"*4097):
            status,_,body=self.request("/auth/callback",**dict(params,HTTP_COOKIE=cookie))
            self.assertEqual(status,"401 Unauthorized")
            self.assertEqual(json.loads(body),{"error":"identity_rejected"})
        self.assertEqual(self.diagnostics,["browser_binding"]*4)
        self.opener.open.assert_not_called()
        self.opener.open.side_effect=OSError("private-fixture-secret")
        status,_,body=self.request("/auth/callback",**params)
        self.assertEqual(status,"401 Unauthorized")
        self.assertEqual(json.loads(body),{"error":"identity_rejected"})
        self.assertEqual(self.diagnostics,["browser_binding"]*4+["token_exchange"])
        self.assertEqual(self.request("/auth/callback",**params)[0],"401 Unauthorized")
        self.assertEqual(self.diagnostics[-1],"callback_state_binding")

    def test_signed_unapproved_subject_diagnostic(self):
        params=self.begin()
        response=self.opener.open.return_value.__enter__.return_value
        original=json.loads(response.read.return_value)["id_token"]
        claims=jwt.decode(original,self.key.public_key(),algorithms=["RS256"],audience="fixture")
        claims["sub"]="auth0|unapproved"
        token=jwt.encode(claims,self.key,algorithm="RS256",headers={"kid":"pinned"})
        response.read.return_value=json.dumps({"id_token":token}).encode()
        status,_,body=self.request("/auth/callback",**params)
        self.assertEqual(status,"401 Unauthorized")
        self.assertEqual(json.loads(body),{"error":"identity_rejected"})
        self.assertEqual(self.diagnostics,["subject_allowlist"])

    def test_callback_issuer_and_parameter_validation_before_exchange(self):
        params=self.begin()
        query=params["QUERY_STRING"]
        values={k:v[0] for k,v in parse_qs(query).items()}
        for bad,category in (
            (urlencode(dict(values,iss="https://other.invalid/")),"callback_issuer"),
            (urlencode(dict(values,iss=ISS.rstrip("/"))),"callback_issuer"),
            (urlencode({k:v for k,v in values.items() if k!="iss"}),"callback_parameters"),
            (urlencode(dict(values,iss="")),"callback_parameters"),
            (urlencode(dict(values,code="")),"callback_parameters"),
            (query+"&iss="+ISS,"callback_parameters"),
            (query+"&unexpected=x","callback_parameters"),
            ("malformed&"+query,"callback_parameters"),
        ):
            with self.subTest(category=category):
                status,_,body=self.request("/auth/callback",**dict(params,QUERY_STRING=bad))
                self.assertEqual(status,"401 Unauthorized")
                self.assertEqual(json.loads(body),{"error":"identity_rejected"})
                self.assertEqual(self.diagnostics[-1],category)
                self.opener.open.assert_not_called()
        self.assertEqual(self.request("/auth/callback",**params)[0],"303 See Other")
        self.opener.open.assert_called_once()
