"""Exercise the actual loopback gateway without any external network."""
import http.client
from pathlib import Path
from urllib.parse import urlsplit
import unittest

from backend.basemap_gateway import loopback_gateway, extraction_command, LOCAL_PATH, BBOX
from backend.basemap_transport import AcquisitionBlocked, SourceIdentity


class Fixture:
    def __init__(self):
        self.identity = SourceIdentity(32, '"fixture"', "Tue, 31 Mar 2026 12:00:00 GMT")
        self.blocked = False
        self.calls = []

    def read_range(self, start, end):
        self.calls.append((start, end))
        if len(self.calls) > 1:
            self.blocked = True
            raise AcquisitionBlocked("archive_byte_budget")
        return bytes(range(start, end+1))


class GatewayTests(unittest.TestCase):
    def request(self, url, method, path=LOCAL_PATH, headers=None):
        p = urlsplit(url)
        conn = http.client.HTTPConnection(p.hostname, p.port, timeout=5)
        try:
            conn.request(method, path, headers=headers or {})
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def test_head_and_exact_conditional_range(self):
        guard = Fixture()
        with loopback_gateway(guard) as url:
            code, headers, body = self.request(url, "HEAD")
            self.assertEqual((code, headers["Content-Length"], body), (200, "32", b""))
            self.assertEqual(guard.calls, [])
            code, headers, body = self.request(url, "GET", headers={"Range": "bytes=3-6", "If-Match": '"fixture"'})
            self.assertEqual((code, headers["Content-Range"], body), (206, "bytes 3-6/32", bytes(range(3, 7))))
            self.assertEqual(guard.calls, [(3, 6)])

    def test_no_full_get_multi_range_suffix_or_unbounded_range(self):
        guard = Fixture()
        with loopback_gateway(guard) as url:
            for headers in ({}, {"Range": "bytes=0-2,4-6"}, {"Range": "bytes=-4"},
                            {"Range": "bytes=0-"}, {"Range": "bytes=4-3"},
                            {"Range": "bytes=0-32"}):
                with self.subTest(headers=headers):
                    code, _, body = self.request(url, "GET", headers=headers)
                    self.assertEqual((code, body), (416, b""))
            self.assertEqual(guard.calls, [])

    def test_no_other_paths_hosts_or_identity_changes(self):
        guard = Fixture()
        with loopback_gateway(guard) as url:
            for path in ("/", "/../approved-context.pmtiles", LOCAL_PATH+"?url=https://example.invalid",
                         "http://example.invalid"+LOCAL_PATH):
                self.assertEqual(self.request(url, "GET", path, {"Range":"bytes=0-1"})[0], 404)
            self.assertEqual(self.request(url, "GET", headers={"Range":"bytes=0-1","Host":"example.invalid"})[0], 400)
            self.assertEqual(self.request(url, "GET", headers={"Range":"bytes=0-1","If-Match":'"changed"'})[0], 412)
            self.assertEqual(guard.calls, [])

    def test_upstream_failure_latches_and_no_partial_output(self):
        guard = Fixture()
        with loopback_gateway(guard) as url:
            self.assertEqual(self.request(url, "GET", headers={"Range":"bytes=0-1"})[0], 206)
            self.assertEqual(self.request(url, "GET", headers={"Range":"bytes=2-3"})[::2], (503,b""))
            self.assertEqual(self.request(url, "HEAD")[0], 503)
            self.assertEqual(self.request(url, "GET", headers={"Range":"bytes=0-1"})[0], 503)
            self.assertEqual(guard.calls, [(0,1),(2,3)])
        with self.assertRaises(AcquisitionBlocked):
            with loopback_gateway(guard):
                self.fail("blocked guard served")

    def test_fixed_extractor_command(self):
        args = extraction_command(Path("/tmp/approved/pmtiles"), "http://127.0.0.1:12345"+LOCAL_PATH, Path("/tmp/approved"))
        self.assertEqual(args, ["/tmp/approved/pmtiles","extract",
            "http://127.0.0.1:12345"+LOCAL_PATH,"/tmp/approved/evanston-context.pmtiles",
            "--bbox="+BBOX,"--minzoom=0","--maxzoom=15","--download-threads=1","--overfetch=0"])
        for url in ("https://data.source.coop/protomaps/openstreetmap/v4.pmtiles",
                    "http://127.0.0.1:12345"+LOCAL_PATH+"?x=1",
                    "http://localhost:12345"+LOCAL_PATH):
            with self.assertRaises(ValueError):
                extraction_command(Path("/tmp/approved/pmtiles"),url,Path("/tmp/approved"))
