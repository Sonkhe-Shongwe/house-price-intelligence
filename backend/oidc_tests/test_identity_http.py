"""WSGI qualification of provider callback without network, DB or deployment."""
import json
from io import BytesIO
import re
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

    def test_native_logout_preserves_csp_and_revokes_session(self):
        status,headers,_=self.request("/auth/callback",**self.begin())
        self.assertEqual(status,"303 See Other")
        cookie=next(v for k,v in headers if k=="Set-Cookie").split(";",1)[0]
        status,headers,body=self.request(HTTP_COOKIE=cookie)
        self.assertEqual(status,"200 OK")
        csp=dict(headers)["Content-Security-Policy"]
        self.assertIn("default-src 'none'",csp)
        self.assertNotIn("connect-src",csp)
        self.assertIn("form-action 'self'",csp)
        self.assertEqual(dict(headers)["Cache-Control"],"no-store")
        self.assertIn(b'<form method="post" action="/auth/logout">',body)
        self.assertIn(b'</svg>Sign out</button>',body)
        csrf=re.search(rb'name="csrf" value="([A-Za-z0-9_-]{43})"',body).group(1)
        raw=b"csrf="+csrf
        def submit(payload=raw,**overrides):
            env=dict(HTTP_COOKIE=cookie,HTTP_ORIGIN=ORIGIN,
                CONTENT_TYPE="application/x-www-form-urlencoded",CONTENT_LENGTH=str(len(payload)))
            env["wsgi.input"]=BytesIO(payload)
            env.update(overrides)
            return self.request("/auth/logout","POST",**env)
        for payload,overrides,expected in (
            (raw,{"HTTP_ORIGIN":"https://other.invalid"},"403 Forbidden"),
            (raw,{"HTTP_ORIGIN":None},"401 Unauthorized"),
            (raw,{"HTTP_SEC_FETCH_SITE":"cross-site"},"403 Forbidden"),
            (raw,{"HTTP_X_HPI_CSRF":csrf.decode()},"401 Unauthorized"),
            (b"csrf="+b"x"*43,{},"401 Unauthorized"),
            (raw+b"&csrf="+csrf,{},"401 Unauthorized"),
            (raw[:-1],{"CONTENT_LENGTH":"48"},"401 Unauthorized"),
            (raw,{"CONTENT_LENGTH":"99999999"},"401 Unauthorized"),
        ):
            with self.subTest(expected=expected,overrides=overrides):
                self.assertEqual(submit(payload,**overrides)[0],expected)
                self.assertEqual(self.request("/auth/session",HTTP_COOKIE=cookie)[0],"200 OK")
        status,headers,_=submit()
        self.assertEqual(status,"303 See Other")
        self.assertEqual(dict(headers)["Location"],"/")
        self.assertIn("Max-Age=0",dict(headers)["Set-Cookie"])
        self.assertEqual(self.request("/auth/session",HTTP_COOKIE=cookie)[0],"401 Unauthorized")
        self.assertIn(b"Sign in",self.request(HTTP_COOKIE=cookie)[2])
        self.assertEqual(submit()[0],"401 Unauthorized")

    def test_landing_styles_are_hash_pinned_and_identity_only(self):
        from base64 import b64encode
        from hashlib import sha256
        status,headers,body=self.request()
        self.assertEqual(status,"200 OK")
        css=re.search(rb"<style>(.*?)</style>",body,re.S).group(1)
        csp=dict(headers)["Content-Security-Policy"]
        expected="'sha256-"+b64encode(sha256(css).digest()).decode()+"'"
        self.assertIn("style-src "+expected,csp)
        self.assertNotIn("unsafe-inline",csp)
        self.assertNotIn("script-src",csp)
        self.assertNotIn("connect-src",csp)
        self.assertNotIn(b"<script",body)
        self.assertNotIn(b"Open buyer workspace",body)
        self.assertIn(b'<form method="post" action="/auth/start">',body)
        self.assertIn(b'aria-hidden="true" focusable="false"',body)
        self.assertIn(b'</svg>Sign in</button>',body)
        self.assertNotIn(b'<img',body)
        self.assertIn(b'HPI identity qualification',body)
        _,headers,_=self.request("/auth/session")
        self.assertNotIn("style-src",dict(headers)["Content-Security-Policy"])
        self.opener.open.assert_not_called()

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

    def test_token_timing_diagnostics_keep_strict_limit(self):
        cases=(
            (-10,591,"token_duration_excessive duration_seconds=601"),
            (-700,-100,"token_expired"),
            (120,720,"token_not_yet_valid"),
            (0,31536001,"token_duration_excessive"),
            (-10,590,None),
        )
        for issued,expires,category in cases:
            with self.subTest(category=category):
                params=self.begin()
                response=self.opener.open.return_value.__enter__.return_value
                original=json.loads(response.read.return_value)["id_token"]
                claims=jwt.decode(original,self.key.public_key(),algorithms=["RS256"],audience="fixture")
                now=int(time())
                claims.update(iat=now+issued,exp=now+expires)
                response.read.return_value=json.dumps({"id_token":jwt.encode(
                    claims,self.key,algorithm="RS256",headers={"kid":"pinned"})}).encode()
                status,_,body=self.request("/auth/callback",**params)
                if category is None:
                    self.assertEqual(status,"303 See Other")
                else:
                    self.assertEqual(status,"401 Unauthorized")
                    self.assertEqual(json.loads(body),{"error":"identity_rejected"})
                    self.assertEqual(self.diagnostics[-1],category)
