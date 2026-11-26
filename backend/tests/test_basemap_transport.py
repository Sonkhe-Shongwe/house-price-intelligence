"""Offline guarded-range tests; no public archive or provider contact."""
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.message import Message
from threading import Thread
import unittest

from backend.basemap_transport import (
    BoundedArchive, AcquisitionBlocked, ARCHIVE_BUDGET, PATH,
)

SIZE = 125_550_000_000
ETAG = '"fixture-v4"'
MODIFIED = "Tue, 31 Mar 2026 12:00:00 GMT"


class Response:
    def __init__(self, status=206, body=b"abcd", **headers):
        self.status = status
        self.body = body
        self.headers = Message()
        for key, value in headers.items():
            self.headers[key.replace("_", "-")] = str(value)
        self.reads = 0
        self.closed = False

    def read1(self, count):
        self.reads += 1
        data, self.body = self.body[:count], self.body[count:]
        return data

    def close(self):
        self.closed = True


def head(**overrides):
    headers = dict(Content_Length=SIZE, ETag=ETAG,
                   Last_Modified=MODIFIED, Accept_Ranges="bytes")
    headers.update(overrides)
    return Response(200, b"", **headers)


def partial(**overrides):
    headers = dict(Content_Length=4, ETag=ETAG,
                   Content_Range=f"bytes 0-3/{SIZE}")
    headers.update(overrides)
    return Response(**headers)


class Transport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []
        self.closed = 0

    def __call__(self, timeout):
        return self

    def request(self, method, path, headers):
        self.requests.append((method, path, headers))

    def getresponse(self):
        return self.responses.pop(0)

    def close(self):
        self.closed += 1


class BasemapTransportTests(unittest.TestCase):
    def guard(self, *responses, **limits):
        transport = Transport(*responses)
        guard = BoundedArchive(_connection_factory=transport, **limits)
        return guard, transport

    def test_identity_pinned_and_range_exact(self):
        response = partial()
        guard, transport = self.guard(head(), response)
        self.assertEqual(guard.preflight().etag, ETAG)
        self.assertEqual(guard.read_range(0, 3), b"abcd")
        self.assertEqual(transport.requests[0][:2], ("HEAD", PATH))
        self.assertEqual(transport.requests[1][:2], ("GET", PATH))
        self.assertEqual(transport.requests[1][2]["Range"], "bytes=0-3")
        self.assertEqual(transport.requests[1][2]["If-Match"], ETAG)
        self.assertEqual((guard.reserved_bytes, guard.received_bytes), (4, 4))
        self.assertTrue(response.closed)

    def test_preflight_rejects_wrong_source(self):
        for h in (head(Content_Length=SIZE+1000000000),
                  head(Last_Modified="Wed, 01 Apr 2026 00:00:00 GMT"),
                  head(ETag='W/"weak"'), head(Accept_Ranges="none"),
                  Response(302)):
            with self.subTest(headers=str(h.headers)):
                guard, transport = self.guard(h)
                with self.assertRaises(AcquisitionBlocked):
                    guard.preflight()
                with self.assertRaises(AcquisitionBlocked):
                    guard.read_range(0, 3)
                self.assertEqual(len(transport.requests), 1)
                self.assertEqual(h.reads, 0)

    def test_rejects_full_redirect_unsatisfiable_changed_or_oversize_without_reading(self):
        for response in (Response(200), Response(302), Response(416), Response(412),
                         partial(ETag='"changed"'),
                         partial(Content_Range=f"bytes 1-4/{SIZE}"),
                         partial(Content_Length=5), partial(Transfer_Encoding="chunked"),
                         partial(Content_Encoding="gzip")):
            with self.subTest(status=response.status, headers=str(response.headers)):
                guard, transport = self.guard(head(), response)
                guard.preflight()
                with self.assertRaises(AcquisitionBlocked):
                    guard.read_range(0, 3)
                self.assertEqual(response.reads, 0)
                self.assertEqual(guard.reserved_bytes, 4)
                with self.assertRaises(AcquisitionBlocked):
                    guard.read_range(0, 3)
                self.assertEqual(len(transport.requests), 2)

    def test_duplicate_headers_rejected(self):
        response = partial()
        response.headers["Content-Length"] = "4"
        guard, _ = self.guard(head(), response)
        guard.preflight()
        with self.assertRaises(AcquisitionBlocked):
            guard.read_range(0, 3)
        self.assertEqual(response.reads, 0)

    def test_budget_and_range_request_limits(self):
        for limits, first in ((dict(_byte_limit=7), True),
                              (dict(_request_limit=1), True),
                              (dict(_range_limit=3), False)):
            with self.subTest(limits=limits):
                guard, transport = self.guard(head(), partial(), **limits)
                guard.preflight()
                if first:
                    guard.read_range(0, 3)
                with self.assertRaises(AcquisitionBlocked):
                    guard.read_range(0, 3)
                self.assertEqual(len(transport.requests), 2 if first else 1)

    def test_partial_failure_keeps_reservation(self):
        response = partial()
        response.body = b"ab"
        guard, transport = self.guard(head(), response)
        guard.preflight()
        with self.assertRaisesRegex(AcquisitionBlocked, "truncated_range"):
            guard.read_range(0, 3)
        self.assertEqual((guard.reserved_bytes, guard.received_bytes), (4, 2))
        with self.assertRaises(AcquisitionBlocked):
            guard.read_range(0, 3)
        self.assertEqual(len(transport.requests), 2)

    def test_deadline_prevents_request(self):
        clock = [0]
        guard, transport = self.guard(head(), _clock=lambda: clock[0], _seconds=1)
        guard.preflight()
        clock[0] = 2
        with self.assertRaisesRegex(AcquisitionBlocked, "deadline_exhausted"):
            guard.read_range(0, 3)
        self.assertEqual(len(transport.requests), 1)

    def test_invalid_offsets_and_no_limit_expansion(self):
        with self.assertRaises(ValueError):
            BoundedArchive(_byte_limit=ARCHIVE_BUDGET+1)
        for start, end in ((-1, 2), (0, SIZE), (3, 2), (True, 3)):
            guard, transport = self.guard(head())
            guard.preflight()
            with self.assertRaises(AcquisitionBlocked):
                guard.read_range(start, end)
            self.assertEqual(len(transport.requests), 1)

    def test_real_loopback_http_range(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_HEAD(self):
                requests.append((self.command, self.path))
                self.send_response(200)
                self.send_header("Content-Length", str(SIZE))
                self.send_header("ETag", ETAG)
                self.send_header("Last-Modified", MODIFIED)
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
            def do_GET(self):
                requests.append((self.command, self.path, self.headers["If-Match"],
                                 self.headers["Range"]))
                self.send_response(206)
                self.send_header("Content-Length", "4")
                self.send_header("ETag", ETAG)
                self.send_header("Content-Range", f"bytes 0-3/{SIZE}")
                self.end_headers()
                self.wfile.write(b"abcd")
        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            guard = BoundedArchive(_connection_factory=lambda timeout:
                http.client.HTTPConnection("127.0.0.1", server.server_port,
                                           timeout=timeout))
            guard.preflight()
            self.assertEqual(guard.read_range(0, 3), b"abcd")
            self.assertEqual(requests, [("HEAD", PATH), ("GET", PATH, ETAG, "bytes=0-3")])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
