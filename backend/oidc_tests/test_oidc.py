import unittest
from time import time
from urllib.parse import urlsplit,parse_qs
from base64 import urlsafe_b64encode
from hashlib import sha256
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from backend.oidc_boundary import OidcBoundary,AuthDenied,random_token

ISS="https://fictional-idp.invalid/"
CLIENT="hpi-fixture"
ORIGIN="https://hpi.invalid"
class IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        cls.other=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    def setUp(self):
        self.now=time()
        self.boundary=OidcBoundary(issuer=ISS,client_id=CLIENT,authorize_endpoint=ISS+"authorize",
            redirect_uri=ORIGIN+"/callback",public_keys={"local":self.key.public_key()},
            owner_map={(ISS,"alice"):"fictional-alice",(ISS,"bob"):"fictional-bob"},clock=lambda:self.now)
        self.binding=random_token()
    def flow(self,**changes):
        query=parse_qs(urlsplit(self.boundary.begin(self.binding)).query)
        state=query["state"][0]
        claims={"iss":ISS,"sub":"alice","aud":CLIENT,"iat":int(time()),"exp":int(time())+300,"nonce":query["nonce"][0]}
        claims.update(changes)
        def exchange(**args):
            self.assertEqual(args["redirect_uri"],ORIGIN+"/callback")
            challenge=urlsafe_b64encode(sha256(args["verifier"].encode()).digest()).decode().rstrip("=")
            self.assertEqual(challenge,query["code_challenge"][0])
            return jwt.encode(claims,self.key,algorithm="RS256",headers={"kid":"local"})
        return state,exchange
    def finish(self,**changes):
        state,exchange=self.flow(**changes)
        return self.boundary.finish(state=state,browser_binding=self.binding,code="fictional-code",exchange=exchange)
    def test_pkce_nonce_session_and_logout(self):
        result=self.finish()
        self.assertIn("Secure; HttpOnly; SameSite=Lax",result["cookie"])
        cookie=result["cookie"].split(";")[0]
        self.assertEqual(self.boundary.authorize(cookie=cookie,method="GET"),"fictional-alice")
        self.assertEqual(self.boundary.authorize(cookie=cookie,method="POST",origin=ORIGIN,csrf=result["csrf"]),"fictional-alice")
        self.assertIn("Max-Age=0",self.boundary.logout(cookie=cookie,origin=ORIGIN,csrf=result["csrf"]))
        with self.assertRaises(AuthDenied):self.boundary.authorize(cookie=cookie,method="GET")
    def test_replay_and_wrong_browser(self):
        state,exchange=self.flow()
        with self.assertRaises(AuthDenied):self.boundary.finish(state=state,browser_binding=random_token(),code="c",exchange=exchange)
        self.boundary.finish(state=state,browser_binding=self.binding,code="c",exchange=exchange)
        with self.assertRaises(AuthDenied):self.boundary.finish(state=state,browser_binding=self.binding,code="c",exchange=exchange)
    def test_claim_rejections(self):
        for fields in ({"iss":"https://other.invalid/"},{"aud":"wrong"},{"aud":[CLIENT,"other"]},{"azp":"wrong"},{"sub":"unknown"},{"nonce":"wrong"},{"exp":int(time())-1},{"iat":int(time())+1000},{"exp":int(time())+5000}):
            with self.subTest(fields=fields),self.assertRaises(AuthDenied):self.finish(**fields)
    def test_signature_algorithm_and_untrusted_keys(self):
        for mode in ("signature","algorithm","kid","jku"):
            state,exchange=self.flow()
            good=exchange(code="c",verifier=self.boundary.pending[next(reversed(self.boundary.pending))].verifier,redirect_uri=ORIGIN+"/callback")
            claims=jwt.decode(good,options={"verify_signature":False})
            if mode=="signature":bad=jwt.encode(claims,self.other,algorithm="RS256",headers={"kid":"local"})
            elif mode=="algorithm":bad=jwt.encode(claims,"x"*32,algorithm="HS256",headers={"kid":"local"})
            elif mode=="kid":bad=jwt.encode(claims,self.key,algorithm="RS256",headers={"kid":"unknown"})
            else:bad=jwt.encode(claims,self.key,algorithm="RS256",headers={"kid":"local","jku":"https://unknown.invalid/"})
            with self.subTest(mode=mode),self.assertRaises(AuthDenied):self.boundary.finish(state=state,browser_binding=self.binding,code="c",exchange=lambda **kw:bad)
    def test_csrf_expiry_duplicate_cookie(self):
        r=self.finish();cookie=r["cookie"].split(";")[0]
        for origin,csrf in ((None,r["csrf"]),("https://other.invalid",r["csrf"]),(ORIGIN,random_token())):
            with self.assertRaises(AuthDenied):self.boundary.authorize(cookie=cookie,method="DELETE",origin=origin,csrf=csrf)
        with self.assertRaises(AuthDenied):self.boundary.authorize(cookie=cookie+"; "+cookie,method="GET")
        self.now+=901
        with self.assertRaises(AuthDenied):self.boundary.authorize(cookie=cookie,method="GET")
    def test_separate_identity_and_server_mapping(self):
        a=self.finish(owner_id="fictional-bob");b=self.finish(sub="bob")
        self.assertEqual(self.boundary.authorize(cookie=a["cookie"].split(";")[0],method="GET"),"fictional-alice")
        self.assertEqual(self.boundary.authorize(cookie=b["cookie"].split(";")[0],method="GET"),"fictional-bob")
    def test_expired_pending_and_failed_exchange(self):
        state,exchange=self.flow();self.now+=301
        with self.assertRaises(AuthDenied):self.boundary.finish(state=state,browser_binding=self.binding,code="c",exchange=exchange)
        state,exchange=self.flow()
        def unavailable(**kwargs):raise RuntimeError("private data")
        with self.assertRaisesRegex(AuthDenied,"Identity exchange unavailable"):self.boundary.finish(state=state,browser_binding=self.binding,code="c",exchange=unavailable)
        with self.assertRaises(AuthDenied):self.boundary.finish(state=state,browser_binding=self.binding,code="c",exchange=exchange)
