"""Network-free transport contract tests; no provider or secret provisioning."""
import json
import unittest
from email.message import Message
from unittest.mock import MagicMock
from urllib.parse import parse_qs
from backend.oidc_boundary import AuthDenied,random_token
from backend.oidc_exchange import ConfidentialCodeExchange,MAX_RESPONSE,_NoRedirect

ISS="https://issuer.invalid/"
TOKEN=ISS+"oauth/token"
REDIRECT="https://127.0.0.1:8766/auth/callback"


class ExchangeTests(unittest.TestCase):
    def setUp(self):
        self.exchange=ConfidentialCodeExchange(issuer=ISS,token_endpoint=TOKEN,
            client_id="fixture",client_secret="fictional-secret-"+"x"*32,redirect_uri=REDIRECT)
        self.opener=MagicMock()
        self.exchange._opener=self.opener
        self.response=self.opener.open.return_value.__enter__.return_value
        self.response.status=200
        self.response.geturl.return_value=TOKEN
        headers=Message()
        headers["Content-Type"]="application/json"
        self.response.headers=headers
        self.response.read.return_value=json.dumps({"id_token":"fictional-id-token",
            "access_token":"discarded","refresh_token":"discarded"}).encode()
        self.verifier=random_token()

    def call(self,**kw):
        return self.exchange(**dict({"code":"fictional-code","verifier":self.verifier,
            "redirect_uri":REDIRECT},**kw))

    def test_pkce_confidential_request_and_only_id_token(self):
        self.assertEqual(self.call(),"fictional-id-token")
        req=self.opener.open.call_args.args[0]
        self.assertEqual(req.full_url,TOKEN)
        self.assertEqual(req.get_method(),"POST")
        self.assertEqual(self.opener.open.call_args.kwargs,{"timeout":10})
        self.assertEqual(parse_qs(req.data.decode()),{"grant_type":["authorization_code"],
            "client_id":["fixture"],"client_secret":["fictional-secret-"+"x"*32],
            "code":["fictional-code"],"code_verifier":[self.verifier],"redirect_uri":[REDIRECT]})
        self.response.read.assert_called_once_with(MAX_RESPONSE+1)

    def test_invalid_input_refused_before_network(self):
        for args in ({"code":""},{"verifier":"bad"},{"redirect_uri":"https://other.invalid/callback"}):
            with self.assertRaises(AuthDenied):self.call(**args)
        self.opener.open.assert_not_called()

    def test_wrong_endpoint_and_redirects_refused(self):
        for endpoint in ("http://issuer.invalid/oauth/token","https://other.invalid/oauth/token",
                         TOKEN+"?leak=1","https://issuer.invalid:444/oauth/token"):
            with self.assertRaises(ValueError):
                ConfidentialCodeExchange(issuer=ISS,token_endpoint=endpoint,
                    client_id="fixture",client_secret="x"*32,redirect_uri=REDIRECT)
        with self.assertRaises(AuthDenied):_NoRedirect().redirect_request(None,None,302,None,None,"https://other.invalid")

    def test_bad_payloads_and_provider_errors_are_redacted(self):
        for body in (b"not json",b'{"id_token":"a","id_token":"b"}',b'{"access_token":"x"}',
            b'{"error":"private-secret"}',b'{"id_token":12}',b"x"*(MAX_RESPONSE+1)):
            self.response.read.return_value=body
            with self.assertRaisesRegex(AuthDenied,"^Identity exchange unavailable$"):self.call()
        self.opener.open.side_effect=OSError("private-secret")
        with self.assertRaisesRegex(AuthDenied,"^Identity exchange unavailable$"):self.call()

    def test_unexpected_status_type_and_final_url(self):
        for field,bad,good in (("status",302,200),):
            setattr(self.response,field,bad)
            with self.assertRaises(AuthDenied):self.call()
            setattr(self.response,field,good)
        self.response.geturl.return_value="https://other.invalid/token"
        with self.assertRaises(AuthDenied):self.call()
        self.response.geturl.return_value=TOKEN
        self.response.headers.replace_header("Content-Type","text/html")
        with self.assertRaises(AuthDenied):self.call()
