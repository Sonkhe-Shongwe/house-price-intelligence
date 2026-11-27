"""PLUTO-only bounded response orchestration, invented transport rehearsal.

No live transport constructor, command-line entrypoint, or authority marker.
The caller supplies an invented response context manager. A separate approved
local launcher must enforce a hard deadline, host protection and persistent
one-attempt consumption before any actual requests. Never run real rows in CI.
"""
import json
import time
from decimal import Decimal
from urllib.parse import urlencode

from tools import nyc_address_frame as frame
from tools.nyc_collector import https_response, strict_pairs, invalid_constant, uint
from tools.nyc_qualification import EXPECTED_TYPES, QualificationError, require


class FrameRehearsal:
    def __init__(self, transport, clock=time.monotonic):
        require(callable(transport) and transport is not https_response,
                "live_execution_disabled")
        self._transport = transport
        self._clock = clock
        self._used = False
        self._requests = 0
        self._bytes = 0
        self._start = None

    def _elapsed(self):
        elapsed = self._clock() - self._start
        require(0 <= elapsed < frame.MAX_SECONDS, "frame_time_limit")
        return elapsed

    def _request(self, path, params=None):
        remaining = frame.MAX_BYTES - self._bytes
        require(self._requests < frame.MAX_REQUESTS, "frame_request_limit")
        require(remaining > 0, "frame_byte_limit")
        self._requests += 1
        url = path if params is None else path + "?" + urlencode(params)
        content = bytearray()
        with self._transport(url, min(15, frame.MAX_SECONDS-self._elapsed())) as response:
            require(response.status == 200, "frame_http_status")
            require(response.getheader("Content-Type", "").split(";")[0].strip().lower()
                    == "application/json", "frame_content_type")
            require(response.getheader("Content-Encoding", "identity").lower()
                    == "identity", "frame_content_encoding")
            length = response.getheader("Content-Length")
            transfer = response.getheader("Transfer-Encoding")
            if transfer is not None:
                require(length is None and transfer.strip().lower() == "chunked"
                        and getattr(response, "chunked", False), "frame_framing")
            if length is not None:
                expected = uint(length)
                require(0 < expected <= remaining, "frame_byte_limit")
                while len(content) < expected:
                    self._elapsed()
                    chunk = response.read1(min(65536, expected-len(content)))
                    require(type(chunk) is bytes and 0 < len(chunk) <= expected-len(content),
                            "frame_incomplete_response")
                    content.extend(chunk)
                    self._bytes += len(chunk)
            else:
                require(transfer is not None or (params is None
                        and getattr(response, "will_close", False)), "frame_framing")
                while True:
                    self._elapsed()
                    room = frame.MAX_BYTES-self._bytes
                    require(room > 0, "frame_byte_limit")
                    chunk = response.read1(min(65536, room))
                    require(type(chunk) is bytes and len(chunk) <= room, "frame_incomplete_response")
                    if not chunk:
                        require(response.isclosed() and bool(content), "frame_incomplete_response")
                        break
                    content.extend(chunk)
                    self._bytes += len(chunk)
        self._elapsed()
        result = json.loads(content, object_pairs_hook=strict_pairs,
                            parse_float=Decimal, parse_constant=invalid_constant)
        self._elapsed()
        return result

    def _metadata(self):
        raw = self._request(f"/api/views/{frame.DATASET}.json")
        require(type(raw) is dict and raw.get("id") == frame.DATASET
                and not ({"rows", "data", "results", "records"} & raw.keys())
                and type(raw.get("columns")) is list, "frame_metadata_shape")
        columns = raw["columns"]
        require(all(type(c) is dict and type(c.get("fieldName")) is str
                    and type(c.get("dataTypeName")) is str for c in columns),
                "frame_metadata_shape")
        types = {c["fieldName"]: c["dataTypeName"] for c in columns}
        require(len(types) == len(columns) and all(types.get(k) == v
                for k, v in EXPECTED_TYPES[frame.DATASET].items()), "frame_metadata_types")
        tokens = [raw.get(k) for k in ("rowsUpdatedAt", "viewLastModified")]
        require(all(type(t) is int and 0 < t <= 2**53-1 for t in tokens),
                "frame_metadata_revision")
        revision = ":".join(map(str, tokens))
        require(revision == frame.REVISION, "frame_revision_changed")
        return revision

    def _count(self):
        raw = self._request(f"/resource/{frame.DATASET}.json", frame.count_parameters())
        require(type(raw) is list and len(raw) == 1 and type(raw[0]) is dict
                and set(raw[0]) == {"n"}, "frame_count_shape")
        n = uint(raw[0]["n"])
        frame.row_parameters(n)
        return n

    def run(self):
        require(not self._used, "frame_attempt_consumed")
        self._used = True
        try:
            self._start = self._clock()
            before = self._metadata()
            count = self._count()
            path, params = frame.request_plan(count)[2]
            rows = self._request(path, params)
            require(type(rows) is list and len(rows) == count, "frame_incomplete")
            after_count = self._count()
            require(after_count == count, "frame_count_changed")
            after = self._metadata()
            result = frame.qualify_fixture_frame(
                rows, count_before=count, count_after=after_count,
                revision_before=before, revision_after=after)
            result.update(requests=self._requests, bytes_received=self._bytes,
                          elapsed_seconds=round(self._elapsed(), 3),
                          attempt_consumed=True)
            return result
        except Exception:
            # Never pass transport/decoder exceptions or arbitrary source values
            # to stdout, logs or a caller. Failure has no partial result.
            raise QualificationError("frame_rehearsal_refused") from None
