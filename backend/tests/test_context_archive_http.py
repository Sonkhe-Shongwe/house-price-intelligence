"""Actual WSGI response boundary; immutable invented bytes, not valid PMTiles."""
import hashlib
from io import BytesIO
import unittest
from wsgiref.util import setup_testing_defaults
from backend.context_archive_http import ContextArchive, CONTEXT_PATH, FIXTURE_BYTES
from backend.synthetic_demo import in_memory_demo
from backend.synthetic_http import create_app


class ContextArchiveTests(unittest.TestCase):
    def setUp(self):
        self.db, self.store = in_memory_demo()
        self.addCleanup(self.db.close)
        self.app = create_app(self.store, react_assets={}, context_transport_fixture=True)

    def request(self, method="GET", path=CONTEXT_PATH, **extra):
        env = {}
        setup_testing_defaults(env)
        env.update(REQUEST_METHOD=method, PATH_INFO=path, HTTP_HOST="127.0.0.1:8765",
                   REMOTE_ADDR="127.0.0.1", QUERY_STRING="", **{"wsgi.input": BytesIO()})
        env.update(extra)
        result = {}
        def start(status, headers):
            result.update(status=int(status.split()[0]), headers=dict(headers))
        result["body"] = b"".join(self.app(env, start))
        return result

    def test_opt_in_and_scope(self):
        self.app=create_app(self.store, react_assets={})
        self.assertEqual(self.request(HTTP_RANGE="bytes=0-3")["status"],404)
        with self.assertRaises(ValueError):
            create_app(self.store, context_transport_fixture=True)

    def test_head_and_exact_ranges(self):
        head=self.request("HEAD")
        etag='"'+hashlib.sha256(FIXTURE_BYTES).hexdigest()+'"'
        self.assertEqual(head["status"],200)
        self.assertEqual(head["headers"]["Content-Length"],str(len(FIXTURE_BYTES)))
        self.assertEqual(head["headers"]["ETag"],etag)
        self.assertEqual(head["body"],b"")
        for start,end in ((0,126),(255,300),(len(FIXTURE_BYTES)-1,len(FIXTURE_BYTES)-1)):
            response=self.request(HTTP_RANGE=f"bytes={start}-{end}",HTTP_IF_MATCH=etag)
            self.assertEqual(response["status"],206)
            self.assertEqual(response["body"],FIXTURE_BYTES[start:end+1])
            self.assertEqual(response["headers"]["Content-Range"],f"bytes {start}-{end}/{len(FIXTURE_BYTES)}")
            self.assertEqual(response["headers"]["Content-Length"],str(end-start+1))
            self.assertEqual(response["headers"]["ETag"],etag)
            self.assertEqual(response["headers"]["Cache-Control"],"no-store")
            self.assertEqual(response["headers"]["X-Context-Transport-Fixture"],"true")
            self.assertNotIn("Access-Control-Allow-Origin",response["headers"])

    def test_no_full_body_or_invalid_ranges(self):
        for value in ("","bytes=0-","bytes=-4","bytes=4-3","bytes=0-1,3-4","bytes=0-99999999"):
            r=self.request(HTTP_RANGE=value)
            self.assertEqual((r["status"],r["body"]),(416,b""))
            self.assertEqual(r["headers"]["Content-Range"],f"bytes */{len(FIXTURE_BYTES)}")
        self.assertEqual(self.request()["status"],416)
        self.assertEqual(self.request("HEAD",HTTP_RANGE="bytes=0-3")["status"],400)

    def test_identity_mismatch_never_full_body(self):
        for field in ("HTTP_IF_MATCH","HTTP_IF_RANGE"):
            r=self.request(HTTP_RANGE="bytes=0-3",**{field:'"changed"'})
            self.assertEqual((r["status"],r["body"]),(412,b""))

    def test_method_origin_forwarding_query_and_path_boundary(self):
        for kwargs in (dict(HTTP_ORIGIN="https://evil.invalid"),dict(HTTP_HOST="evil.invalid"),
                       dict(REMOTE_ADDR="192.0.2.1"),dict(HTTP_X_FORWARDED_FOR="192.0.2.1")):
            self.assertEqual(self.request(HTTP_RANGE="bytes=0-3",**kwargs)["status"],403)
        self.assertEqual(self.request(QUERY_STRING="url=other")["status"],400)
        self.assertEqual(self.request(path="/context/other.pmtiles")["status"],404)
        self.assertEqual(self.request("POST")["status"],405)
        self.assertEqual(self.request(CONTENT_LENGTH="5")["status"],400)

    def test_immutable_size_boundary(self):
        with self.assertRaises(ValueError):
            ContextArchive(b"")
        with self.assertRaises(ValueError):
            ContextArchive(bytearray(b"x"))
