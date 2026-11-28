"""Invented metadata and mocked HTTP only; never invoke publisher endpoints."""
import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock

from tools import nyc_metadata_observe as observer
from tools.nyc_qualification import QualificationError


def payload(dataset, **extra):
    a, b = map(int, observer.PINS[dataset].split(":"))
    obj = dict(id=dataset, rowsUpdatedAt=a, viewLastModified=b)
    obj.update(extra)
    return json.dumps(obj).encode()


class MetadataObservationTests(unittest.TestCase):
    def test_exact_four_requests_and_states_only(self):
        calls = []
        def fetch(dataset):
            calls.append(dataset)
            return payload(dataset, licenseId="INVENTED-LICENSE",
                           disclaimer="INVENTED NOTICE", description="INVENTED DESCRIPTION",
                           owner={"name":"INVENTED IDENTITY"},
                           columns=[{"cachedContents":{"top":["INVENTED SAMPLE"]}}])
        result = observer.observe(fetch)
        self.assertEqual(calls, list(observer.PINS))
        self.assertTrue(result["all_exact_projected"])
        self.assertFalse(result["rights_accepted"])
        self.assertFalse(result["property_collection_authorised"])
        self.assertNotIn("INVENTED", json.dumps(result))
        for entry in result["sources"].values():
            self.assertEqual(entry["notice_states"]["license_id"], "present_unreviewed")
            self.assertEqual(entry["notice_states"]["notice_fields"]["disclaimer"], "present_unreviewed")

    def test_revision_drift_never_projects(self):
        result = observer.observe(lambda d: payload(d, rowsUpdatedAt=1))
        self.assertFalse(result["all_exact_projected"])
        for entry in result["sources"].values():
            self.assertEqual(entry["status"], "revision_changed")
            self.assertNotIn("notice_states", entry)

    def test_independent_failures_and_no_error_echo(self):
        calls = []
        def fetch(d):
            calls.append(d)
            if len(calls) == 1:
                raise RuntimeError("INVENTED PRIVATE ERROR")
            if len(calls) == 2:
                return payload(d, id="wrong-id")
            if len(calls) == 3:
                return payload(d, rows=[])
            return payload(d, licenseId=None)
        result = observer.observe(fetch)
        self.assertEqual(calls, list(observer.PINS))
        self.assertEqual([v["status"] for v in result["sources"].values()],
                         ["unavailable", "source_mismatch", "metadata_refused", "exact_revision_projected"])
        self.assertNotIn("INVENTED", json.dumps(result))
        self.assertFalse(result["all_exact_projected"])

    def test_cli_requires_explicit_mode(self):
        with patch.object(observer, "_fetch") as fetch, redirect_stdout(io.StringIO()):
            self.assertEqual(observer.main([]), 2)
            self.assertEqual(observer.main(["--metadata-only", "--extra"]), 2)
            fetch.assert_not_called()

    def test_transport_only_fixed_metadata_path(self):
        dataset = next(iter(observer.PINS))
        raw = payload(dataset)
        with patch.object(observer.http.client, "HTTPSConnection") as factory:
            conn = factory.return_value
            response = conn.getresponse.return_value.__enter__.return_value
            response.status = 200
            headers = {"Content-Type":"application/json", "Content-Length":str(len(raw))}
            response.getheader.side_effect = lambda key, default=None: headers.get(key, default)
            response.read.return_value = raw
            self.assertEqual(observer._fetch(dataset), raw)
            self.assertEqual(factory.call_args.args, (observer.HOST,))
            self.assertEqual(conn.request.call_args.args, ("GET", f"/api/views/{dataset}.json"))
            response.read.assert_called_once_with(len(raw))
            conn.close.assert_called_once()
        with patch.object(observer.http.client, "HTTPSConnection") as factory:
            with self.assertRaises(QualificationError):
                observer._fetch("../resource/" + dataset)
            factory.assert_not_called()

    def test_transport_rejects_unsafe_responses(self):
        dataset = next(iter(observer.PINS))
        for status, headers, raw in (
            (302, {"Content-Type":"application/json"}, b""),
            (200, {"Content-Type":"text/html"}, b""),
            (200, {"Content-Type":"application/json","Content-Encoding":"gzip"}, b""),
            (200, {"Content-Type":"application/json","Content-Length":str(observer.MAX_DOCUMENT_BYTES+1)}, b""),
            (200, {"Content-Type":"application/json","Content-Length":"20","Transfer-Encoding":"chunked"}, b""),
            (200, {"Content-Type":"application/json","Content-Length":"20"}, b"short"),
            (200, {"Content-Type":"application/json"}, b"x"*observer.MAX_DOCUMENT_BYTES),
        ):
            with self.subTest(status=status, headers=headers), patch.object(observer.http.client, "HTTPSConnection") as factory:
                conn = factory.return_value
                response = conn.getresponse.return_value.__enter__.return_value
                response.status = status
                response.getheader.side_effect = lambda key, default=None: headers.get(key, default)
                response.read.return_value = raw
                with self.assertRaises(QualificationError):
                    observer._fetch(dataset)
                conn.request.assert_called_once()
                conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
