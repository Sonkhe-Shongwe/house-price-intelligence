from datetime import date
from email.message import Message
import hashlib
import json
from pathlib import Path
import socket
import tempfile
import time
import unittest
from unittest.mock import patch

from tools import world_bank_pilot as p


def fixture(page, year=None, value=70.25, updated="2025-01-01"):
    return json.dumps([{"page": page, "pages": 2, "per_page": "1", "total": 2,
                        "sourceid": "2", "lastupdated": updated},
        [{"indicator": {"id": p.INDICATOR, "value": p.LABEL},
          "country": {"id": "ZA", "value": "South Africa"}, "countryiso3code": "ZAF",
          "date": year or ("2023" if page == 1 else "2022"), "value": value,
          "unit": "", "obs_status": "", "decimal": 1}]]).encode()


class Response:
    def __init__(self, raw=b"[]", status=200, **headers):
        self.raw, self.status, self.reads = raw, status, []
        self.headers = Message()
        self.headers["Content-Type"] = "application/json"
        for key, value in headers.items():
            self.headers[key.replace("_", "-")] = value
    def read(self, n):
        self.reads.append(n)
        return self.raw[:n]


def fixture_worker(page, deadline, sender):
    sender.send_bytes(b"S" + fixture(page))
    sender.close()


def slow_worker(page, deadline, sender):
    time.sleep(10)


class PilotTests(unittest.TestCase):
    def root(self, temp):
        root = Path(temp)
        for name in ("01_Source_Catalogue", "02_Raw_Data", "07_Reports"):
            (root / name).mkdir()
        return root

    def test_exact_request(self):
        self.assertEqual(p.request_path(2), "/v2/country/ZAF/indicator/SP.URB.TOTL.IN.ZS?source=2&date=2022:2023&format=json&per_page=1&page=2")
        for x in (0, 3, True, "1"):
            with self.assertRaises(p.Refused):
                p.request_path(x)

    def test_response_media_framing_caps(self):
        good = Response(Content_Length="2")
        self.assertEqual(p.bounded_body(good), b"[]")
        self.assertEqual(good.reads, [2])
        for response in (Response(status=302), Response(Content_Encoding="gzip"),
                         Response(Content_Type="text/html"), Response(Content_Length=str(p.CAP+1)),
                         Response(Content_Length="3"), Response(Content_Length="2", Transfer_Encoding="chunked"),
                         Response(raw=b"x"*p.CAP)):
            with self.subTest(response=response), self.assertRaises(p.Refused):
                p.bounded_body(response)
            self.assertTrue(all(n <= p.CAP for n in response.reads))

    def test_dns_destination(self):
        with patch.object(socket, "getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaises(p.Refused):
                p.public_addresses()
        with patch.object(socket, "getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))]):
            self.assertEqual(p.public_addresses()[-1], ("8.8.8.8", 443))

    def test_worker_deadline_and_valid_envelope(self):
        self.assertEqual(p.deadline_fetch(1, worker=fixture_worker, seconds=5), fixture(1))
        start = time.monotonic()
        with self.assertRaisesRegex(p.Refused, "deadline"):
            p.deadline_fetch(1, worker=slow_worker, seconds=0.5)
        self.assertLess(time.monotonic()-start, 4)

    def test_parse_invalid_values_schema_and_pagination(self):
        today = date(2026, 11, 26)
        self.assertEqual(p.parse_page(fixture(1), 1, today)[0]["percent"], "70.25")
        bad = [fixture(2), fixture(1, year="2021"), fixture(1, value=None),
               fixture(1, value=True), fixture(1, value=101), fixture(1, value=float("nan")),
               fixture(1, updated="2027-01-01"), b"{}", b"x"* (p.CAP+1),
               fixture(1).replace(b'"page": 1', b'"page": 1, "page": 1'),
               fixture(1).replace(b'"unit": ""', b'"unit": "", "extra": "unexpected"')]
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(p.Refused):
                p.parse_page(raw, 1, today)

    def test_success_atomic_bundle_and_no_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.root(temp)
            calls = []
            def fetch(page):
                calls.append(page)
                self.assertTrue((root / "02_Raw_Data" / p.ATTEMPT / ("dispatch-%d.json" % page)).is_file())
                return fixture(page, value=70.25 if page == 1 else 69.75)
            result = p.execute(root, fetch)
            attempt = root / "02_Raw_Data" / p.ATTEMPT
            bundle = json.loads((attempt / "validated.json").read_text())
            self.assertEqual(calls, [1, 2])
            self.assertEqual(bundle["percentage_point_change"], "0.50")
            self.assertEqual(bundle["records"][0]["year"], 2022)
            self.assertEqual(result["hashes"][0], hashlib.sha256(fixture(1)).hexdigest())
            self.assertFalse(bundle["registered"])
            self.assertIsNone(bundle["publication_date"])
            self.assertLessEqual(result["bytes"], 2*p.CAP)
            with self.assertRaisesRegex(p.Refused, "consumed"):
                p.execute(root, fetch)
            self.assertEqual(calls, [1, 2])

    def test_first_failure_stops_and_consumes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.root(temp)
            calls = []
            def fetch(page):
                calls.append(page)
                return b"not JSON"
            with self.assertRaises(p.Refused):
                p.execute(root, fetch)
            attempt = root / "02_Raw_Data" / p.ATTEMPT
            self.assertEqual(calls, [1])
            self.assertFalse((attempt / "dispatch-2.json").exists())
            self.assertFalse((attempt / "validated.json").exists())
            with self.assertRaises(p.Refused):
                p.execute(root, fetch)
            self.assertEqual(calls, [1])

    def test_second_page_drift_never_publishes(self):
        for other in (fixture(2, year="2023"), fixture(2, updated="2025-02-01")):
            with tempfile.TemporaryDirectory() as temp:
                root = self.root(temp)
                with self.assertRaises(p.Refused):
                    p.execute(root, lambda page: fixture(1) if page == 1 else other)
                self.assertFalse((root / "02_Raw_Data" / p.ATTEMPT / "validated.json").exists())

    def test_workspace_refusal_before_dispatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.root(temp)
            (root / ".git").mkdir()
            with self.assertRaises(ValueError):
                p.execute(root, lambda _: self.fail("dispatch"))


if __name__ == "__main__":
    unittest.main()
