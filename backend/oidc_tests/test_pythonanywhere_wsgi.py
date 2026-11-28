"""Integrated WSGI calls using invented identities, no provider or network."""
from datetime import date, timedelta
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time
import unittest
from urllib.parse import parse_qs, urlsplit
from wsgiref.util import setup_testing_defaults

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from backend.oidc_boundary import random_token
from backend.persistent_oidc import PersistentBoundary
from backend.oidc_pythonanywhere_wsgi import (
    application, _workspace_lock, OWNERS, HOST, ORIGIN, REDIRECT, ISSUER, CLIENT, SEALS, BUILT,
)
from backend.nyc_lifecycle_guard import AuthoritySnapshot, SourceAuthority, OPERATIONS
from backend.synthetic_demo import example_request, in_memory_demo


class WorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.now = BUILT + timedelta(days=1)
        self.revoke = False
        self.config = dict(session_file=self.root/"sessions.sqlite", issuer=ISSUER,
                           client_id=CLIENT, authorize_endpoint=ISSUER+"authorize",
                           redirect_uri=REDIRECT, public_keys={"fixture": self.key.public_key()},
                           owner_map=OWNERS)
        self.boundary = PersistentBoundary(**self.config)
        self.app = self.make_app(self.boundary)
        self.alice = self.login("alice")
        self.bob = self.login("bob")

    def authority(self, owner, now):
        return AuthoritySnapshot(owner, tuple(SourceAuthority(
            seal, seal.original_deadline, "revoked" if self.revoke else "reviewed",
            "clear", "verified", OPERATIONS) for seal in SEALS), now)

    def make_app(self, boundary):
        return application(self.root, boundary, authority=self.authority, clock=lambda:self.now)

    def login(self, subject):
        binding = random_token()
        query = parse_qs(urlsplit(self.boundary.begin(binding)).query)
        token = jwt.encode(dict(iss=ISSUER, sub=subject, aud=CLIENT, iat=int(time()),
                           exp=int(time())+300, nonce=query["nonce"][0]),
                           self.key, algorithm="RS256", headers={"kid":"fixture"})
        result = self.boundary.finish(state=query["state"][0], browser_binding=binding,
                                      code="fixture-code", exchange=lambda **kw:token)
        return result["cookie"].split(";")[0], result["csrf"]

    def call(self, method, path, user, data=None, *, app=None, **changes):
        raw = b"" if data is None else json.dumps(data).encode()
        env = {}
        setup_testing_defaults(env)
        env.update({"REQUEST_METHOD":method, "PATH_INFO":path, "QUERY_STRING":"",
                    "wsgi.url_scheme":"https", "HTTP_HOST":HOST, "REMOTE_ADDR":"127.0.0.1",
                    "HTTP_ORIGIN":ORIGIN, "HTTP_COOKIE":user[0], "HTTP_X_HPI_CSRF":user[1],
                    "CONTENT_TYPE":"application/json", "CONTENT_LENGTH":str(len(raw)),
                    "wsgi.input":BytesIO(raw)})
        env.update(changes)
        headers = []
        def start(status, pairs):
            headers.extend([int(status.split()[0]), dict(pairs)])
        body = b"".join((app or self.app)(env, start))
        self.assertEqual(len(headers), 2)
        self.assertEqual(headers[1]["Cache-Control"], "no-store")
        return headers[0], json.loads(body)

    def save(self, n=1, user=None):
        req = example_request()
        req["subject"]["pin"] = f"{n:014d}"
        req["subject"]["asking_price_usd"] = "500000.01"
        code, saved = self.call("POST", "/v1/investigations", user or self.alice, req)
        self.assertEqual(code, 201)
        return saved

    def test_exact_response_parity_and_restart(self):
        saved = self.save()
        req = example_request()
        req["subject"]["asking_price_usd"] = "500000.01"
        conn, store = in_memory_demo()
        try:
            expected = store.create(req, today=date(2026,11,28),
                                    investigation_id=saved["investigation_id"])
        finally:
            conn.close()
        self.assertEqual(saved, expected)
        self.assertEqual(saved["subject"]["asking_price_usd"], "500000.01")
        self.assertEqual([c["sale_price_usd"] for c in saved["comparables"]], ["525000.00"]*3)
        restarted = self.make_app(PersistentBoundary(**self.config))
        path = "/v1/investigations/" + saved["investigation_id"]
        self.assertEqual(self.call("GET", path, self.alice, app=restarted), (200, saved))
        self.assertEqual(self.call("GET", path, self.bob, app=restarted)[0], 404)

    def test_shortlist_three_notes_cross_owner_and_restart(self):
        code, shortlist = self.call("POST", "/v1/shortlists", self.alice, {"label":"Fixture comparison"})
        self.assertEqual(code, 201)
        path = "/v1/shortlists/" + shortlist["shortlist_id"]
        items = [self.save(i) for i in (1,2,3,4)]
        for item in items[:3]:
            code, result = self.call("POST", path+"/entries", self.alice,
                                     {"investigation_id":item["investigation_id"], "note_text":"Fixture note"})
            self.assertEqual(code, 201)
        self.assertEqual(len(result["entries"]), 3)
        self.assertEqual(self.call("POST", path+"/entries", self.alice,
                         {"investigation_id":items[3]["investigation_id"]})[0],409)
        self.assertEqual(self.call("GET", path, self.bob)[0],404)
        self.assertEqual(self.call("PATCH", path+"/entries/"+items[0]["investigation_id"],
                                   self.bob, {"note_text":"Forbidden"})[0],404)
        restarted = self.make_app(PersistentBoundary(**self.config))
        self.assertEqual(self.call("GET", path, self.alice, app=restarted),(200,result))
        self.assertEqual(result["entries"][0]["note_text"],"Fixture note")
        self.assertEqual(self.call("GET","/v1/shortlists",self.bob)[1]["shortlists"],[])

    def test_auth_origin_csrf_forwarding_and_logout(self):
        for change in ({"HTTP_COOKIE":""}, {"HTTP_X_HPI_CSRF":""},
                       {"HTTP_ORIGIN":"https://wrong.invalid"},
                       {"HTTP_X_FORWARDED_HOST":HOST}, {"HTTP_X_HPI_OWNER":"fixture-bob"},
                       {"REMOTE_ADDR":"192.0.2.1"}, {"wsgi.url_scheme":"http"}):
            with self.subTest(change=change):
                self.assertEqual(self.call("POST","/v1/investigations",self.alice,
                                           example_request(),**change)[0],403)
        self.assertFalse((self.root/"fixture-alice"/"workspace.sqlite").exists())
        self.assertEqual(self.call("POST","/auth/logout",self.alice)[0],200)
        self.assertEqual(self.call("GET","/v1/investigations/history",self.alice)[0],403)

    def test_revocation_expiry_and_unimplemented_routes_fail_closed(self):
        item = self.save()
        path = "/v1/investigations/"+item["investigation_id"]
        self.revoke = True
        self.assertEqual(self.call("GET",path,self.alice)[0],403)
        self.assertEqual(self.call("POST","/v1/investigations",self.alice,example_request())[0],403)
        self.assertEqual(self.call("GET","/v1/shortlists",self.alice)[0],403)
        self.revoke = False
        self.now = SEALS[0].original_deadline
        self.assertEqual(self.call("GET",path,self.alice)[0],403)
        for route in ("/export","/restore"):
            self.assertEqual(self.call("POST",route,self.alice,{})[0],404)

    def test_contended_request_does_not_open_or_mutate_workspace(self):
        with _workspace_lock(self.root, "fixture-alice"):
            self.assertEqual(self.call("POST","/v1/investigations",self.alice,example_request())[0],503)
            self.assertFalse((self.root/"fixture-alice"/"workspace.sqlite").exists())
            self.save(user=self.bob)
        self.save()

    def test_symlink_owner_folder_refused(self):
        folder = self.root/"fixture-alice"
        other = self.root/"fixture-bob"
        other.mkdir(mode=0o700)
        folder.symlink_to(other, target_is_directory=True)
        self.assertEqual(self.call("POST","/v1/investigations",self.alice,example_request())[0],503)
        self.assertFalse((other/"workspace.sqlite").exists())
