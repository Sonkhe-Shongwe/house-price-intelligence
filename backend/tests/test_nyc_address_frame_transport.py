"""Mocked byte responses only; no actual source or network calls."""
import io
import json
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs

from tools import nyc_address_frame as frame
from tools.nyc_address_frame_transport import FrameRehearsal
from tools.nyc_collector import https_response
from tools.nyc_qualification import EXPECTED_TYPES, QualificationError


def metadata(**extra):
    a, b = map(int, frame.REVISION.split(":"))
    result = {"id": frame.DATASET, "rowsUpdatedAt": a, "viewLastModified": b,
              "columns": [{"fieldName": k, "dataTypeName": v,
                           "cachedContents": {"top": ["INVENTED SAMPLE"]}}
                          for k, v in EXPECTED_TYPES[frame.DATASET].items()]}
    result.update(extra)
    return result


def row(n=1, **extra):
    value = {"bbl": f"499001{n:04d}", "borough": "QN", "zipcode": "11361",
             "address": f"99-{n} INVENTED STREET", "bldgclass": "A2",
             "numbldgs": "1", "unitsres": "1", "unitstotal": "1",
             "bldgarea": "1000", "version": frame.VERSION, "areasource": "2"}
    value.update(extra)
    return value


class Response:
    def __init__(self, value, *, headers=None, status=200, raw=None):
        self.raw = json.dumps(value).encode() if raw is None else raw
        self.stream = io.BytesIO(self.raw)
        self.status = status
        self.headers = {"Content-Type":"application/json", "Content-Length":str(len(self.raw))}
        if headers is not None:
            self.headers = headers
        self.chunked = self.headers.get("Transfer-Encoding") == "chunked"
        self.will_close = not self.chunked
        self.read_sizes = []

    def getheader(self, key, default=None):
        return self.headers.get(key, default)

    def read1(self, size):
        self.read_sizes.append(size)
        return self.stream.read(size)

    def isclosed(self):
        return self.stream.tell() == len(self.raw)


class Script:
    def __init__(self, values):
        self.responses = [v if isinstance(v, Response) else Response(v) for v in values]
        self.calls = []

    @contextmanager
    def __call__(self, path, timeout):
        self.calls.append((path, timeout))
        yield self.responses[len(self.calls)-1]


def happy(rows=None):
    rows = [row()] if rows is None else rows
    n = [{"n":str(len(rows))}]
    return [metadata(), n, rows, n, metadata()]


class FrameTransportTests(unittest.TestCase):
    def test_complete_order_fixed_queries_and_redaction(self):
        s = Script(happy([row(), row(2, address=row()["address"], bldgclass="A1")]))
        result = FrameRehearsal(s).run()
        self.assertEqual(result["requests"], 5)
        self.assertEqual(result["bytes_received"], sum(len(r.raw) for r in s.responses))
        self.assertEqual(result["eligible_outcomes"]["ambiguous_address"], 1)
        for (actual, timeout), (path, params) in zip(s.calls, frame.request_plan(2)):
            self.assertEqual(urlsplit(actual).path, path)
            self.assertEqual(parse_qs(urlsplit(actual).query),
                             {} if params is None else {k:[v] for k,v in params.items()})
            self.assertGreater(timeout, 0)
            self.assertLessEqual(timeout, 15)
        self.assertNotIn("INVENTED", json.dumps(result))
        self.assertTrue(result["fixture_only"])
        self.assertFalse(result["property_collection_authorised"])

    def test_live_transport_refused_and_attempt_consumed(self):
        with self.assertRaisesRegex(QualificationError, "live_execution_disabled"):
            FrameRehearsal(https_response)
        for values in (happy(), [metadata(id="wrong")]):
            s = Script(values)
            attempt = FrameRehearsal(s)
            try:
                attempt.run()
            except QualificationError:
                pass
            n = len(s.calls)
            with self.assertRaisesRegex(QualificationError, "frame_attempt_consumed"):
                attempt.run()
            self.assertEqual(len(s.calls), n)

    def test_preflight_refuses_drift_schema_or_cap_before_rows(self):
        for values, calls in (
            ([metadata(rowsUpdatedAt=1)], 1),
            ([metadata(columns=[])], 1),
            ([metadata(rows=[])], 1),
            ([metadata(), [{"n":str(frame.MAX_ROWS+1)}]], 2),
            ([metadata(), [{"n":"0"}]], 2),
            ([metadata(), [{"n":True}]], 2),
        ):
            s = Script(values)
            with self.assertRaisesRegex(QualificationError, "frame_rehearsal_refused"):
                FrameRehearsal(s).run()
            self.assertEqual(len(s.calls), calls)

    def test_incomplete_count_change_and_final_revision_refused(self):
        for values, calls in (
            ([metadata(), [{"n":"2"}], [row()]], 3),
            ([metadata(), [{"n":"1"}], [row()], [{"n":"2"}]], 4),
            (happy()[:4]+[metadata(viewLastModified=1)], 5),
            (happy([row(owner="INVENTED PRIVATE")]), 5),
        ):
            s = Script(values)
            with self.assertRaisesRegex(QualificationError, "^frame_rehearsal_refused$"):
                FrameRehearsal(s).run()
            self.assertEqual(len(s.calls), calls)

    def test_bad_status_framing_and_json(self):
        for response in (
            Response({}, status=302),
            Response({}, headers={"Content-Type":"text/html"}),
            Response({}, headers={"Content-Type":"application/json","Content-Encoding":"gzip"}),
            Response({}, headers={"Content-Type":"application/json","Content-Length":"9",
                                  "Transfer-Encoding":"chunked"}),
            Response({}, headers={"Content-Type":"application/json","Content-Length":"9"}),
            Response({}, raw=b'{"id":1,"id":2}'),
            Response({}, raw=b'{"x":NaN}'),
        ):
            s = Script([response])
            with self.assertRaises(QualificationError):
                FrameRehearsal(s).run()
            self.assertEqual(len(s.calls), 1)

    def test_chunked_payload_and_no_row_close_delimited(self):
        data = happy()
        data[2] = Response(data[2], headers={"Content-Type":"application/json",
                                            "Transfer-Encoding":"chunked"})
        self.assertEqual(FrameRehearsal(Script(data)).run()["requests"], 5)
        data[2] = Response([row()], headers={"Content-Type":"application/json"})
        with self.assertRaises(QualificationError):
            FrameRehearsal(Script(data)).run()

    def test_cumulative_budget_and_no_overread(self):
        data = happy()
        s = Script(data)
        limit = len(s.responses[0].raw)+len(s.responses[1].raw)+1
        with patch.object(frame, "MAX_BYTES", limit):
            with self.assertRaises(QualificationError):
                FrameRehearsal(s).run()
        self.assertEqual(len(s.calls), 3)
        self.assertEqual(s.responses[2].read_sizes, [])

    def test_elapsed_refusal_and_no_exception_echo(self):
        s = Script(happy())
        ticks = iter([0, 0, 180])
        with self.assertRaisesRegex(QualificationError, "^frame_rehearsal_refused$"):
            FrameRehearsal(s, clock=lambda: next(ticks)).run()
        self.assertEqual(len(s.calls), 1)

        def fail(path, timeout):
            raise RuntimeError("INVENTED PRIVATE URL")
        with self.assertRaisesRegex(QualificationError, "^frame_rehearsal_refused$"):
            FrameRehearsal(fail).run()


if __name__ == "__main__":
    unittest.main()
