"""Bounded v4 contextual archive transport, not an extraction workflow.

No CLI or application route. Production constructor targets one approved HTTPS
object only. Offline tests inject a loopback connection. The eventual one-shot
workflow must also enforce wall-clock/process, disk and tool/asset budgets.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from email.utils import parsedate_to_datetime
import http.client
import re
import ssl
import time

HOST = "data.source.coop"
PATH = "/protomaps/openstreetmap/v4.pmtiles"
EXPECTED_DATE = date(2026, 3, 31)
# Catalogue reports 125.55 GB to two decimal places. Interpret GB as decimal;
# if live metadata is inconsistent, stop rather than reinterpret the approval.
MIN_SIZE = 125_545_000_000
MAX_SIZE = 125_555_000_000
ARCHIVE_BUDGET = 64 * 1024**2
MAX_RANGE = 8 * 1024**2
MAX_REQUESTS = 1024
MAX_SECONDS = 600
_CHUNK = 64 * 1024


class AcquisitionBlocked(RuntimeError):
    """Safe category only; no arbitrary upstream header/body or URL in logs."""


@dataclass(frozen=True)
class SourceIdentity:
    length: int
    etag: str
    modified: str


def _connect(timeout: float):
    return http.client.HTTPSConnection(
        HOST, 443, timeout=timeout, context=ssl.create_default_context()
    )


def _single(response, name: str, required: bool = True) -> str | None:
    values = response.headers.get_all(name, [])
    if not values and not required:
        return None
    if len(values) != 1:
        raise AcquisitionBlocked("missing_or_duplicate_header")
    return values[0].strip()


def _length(response) -> int:
    value = _single(response, "Content-Length")
    if not re.fullmatch(r"[0-9]{1,15}", value or ""):
        raise AcquisitionBlocked("invalid_content_length")
    if _single(response, "Transfer-Encoding", False) is not None:
        raise AcquisitionBlocked("unexpected_transfer_encoding")
    if _single(response, "Content-Encoding", False) not in (None, "identity"):
        raise AcquisitionBlocked("unexpected_content_encoding")
    return int(value)


def _etag(response) -> str:
    value = _single(response, "ETag")
    # Require one strong, quoted entity-tag; no weak tags or wildcard.
    if not re.fullmatch(r'"[!#-~]{1,200}"', value or ""):
        raise AcquisitionBlocked("invalid_source_identity")
    return value


class BoundedArchive:
    """Sequential, fail-closed transport. Reserve bytes before remote GET.

    Reservations are never refunded, including partial failures. The first
    failure latches the instance closed. No redirects, retries, arbitrary
    destinations, full-object requests or implicit range widening.
    """

    def __init__(self, *, _connection_factory=_connect, _clock=time.monotonic,
                 _byte_limit=ARCHIVE_BUDGET, _range_limit=MAX_RANGE,
                 _request_limit=MAX_REQUESTS, _seconds=MAX_SECONDS):
        if not (0 < _byte_limit <= ARCHIVE_BUDGET
                and 0 < _range_limit <= MAX_RANGE
                and 0 < _request_limit <= MAX_REQUESTS
                and 0 < _seconds <= MAX_SECONDS):
            raise ValueError("limits may only be tightened")
        self._factory = _connection_factory
        self._clock = _clock
        self._deadline = _clock() + _seconds
        self._byte_limit = _byte_limit
        self._range_limit = _range_limit
        self._request_limit = _request_limit
        self.identity: SourceIdentity | None = None
        self.reserved_bytes = 0
        self.received_bytes = 0
        self.range_requests = 0
        self.blocked = False
        self._preflight_attempted = False

    def _remaining(self) -> float:
        left = self._deadline - self._clock()
        if left <= 0:
            raise AcquisitionBlocked("deadline_exhausted")
        return left

    def _open(self, method: str, headers: dict[str, str]):
        conn = self._factory(min(15, self._remaining()))
        try:
            conn.request(method, PATH, headers={
                "Accept-Encoding": "identity",
                "User-Agent": "HousePriceIntelligence-bounded-context-rehearsal/1",
                **headers,
            })
            response = conn.getresponse()
            self._remaining()
            return conn, response
        except Exception:
            conn.close()
            raise

    def preflight(self) -> SourceIdentity:
        if self.blocked or self._preflight_attempted:
            raise AcquisitionBlocked("preflight_already_attempted")
        self._preflight_attempted = True
        conn = response = None
        try:
            conn, response = self._open("HEAD", {})
            if response.status != 200:
                raise AcquisitionBlocked("head_status_rejected")
            size = _length(response)
            if not MIN_SIZE <= size < MAX_SIZE:
                raise AcquisitionBlocked("catalogue_length_mismatch")
            modified = _single(response, "Last-Modified")
            try:
                published_date = parsedate_to_datetime(modified).date()
            except (TypeError, ValueError, OverflowError):
                raise AcquisitionBlocked("catalogue_date_mismatch") from None
            if published_date != EXPECTED_DATE:
                raise AcquisitionBlocked("catalogue_date_mismatch")
            if (_single(response, "Accept-Ranges") or "").lower() != "bytes":
                raise AcquisitionBlocked("range_support_unconfirmed")
            self.identity = SourceIdentity(size, _etag(response), modified)
            return self.identity
        except AcquisitionBlocked:
            self.blocked = True
            raise
        except Exception:
            self.blocked = True
            raise AcquisitionBlocked("head_transport_failed") from None
        finally:
            if response is not None:
                response.close()
            if conn is not None:
                conn.close()

    def read_range(self, start: int, end: int) -> bytes:
        """Inclusive byte positions. Never reads a rejected response body."""
        conn = response = None
        try:
            if self.blocked or self.identity is None:
                raise AcquisitionBlocked("identity_not_available")
            self._remaining()
            if (type(start) is not int or type(end) is not int
                    or not 0 <= start <= end < self.identity.length):
                raise AcquisitionBlocked("invalid_range")
            length = end - start + 1
            if length > self._range_limit:
                raise AcquisitionBlocked("range_limit")
            if self.range_requests >= self._request_limit:
                raise AcquisitionBlocked("request_budget")
            if self.reserved_bytes + length > self._byte_limit:
                raise AcquisitionBlocked("archive_byte_budget")
            self.reserved_bytes += length
            self.range_requests += 1
            conn, response = self._open("GET", {
                "Range": f"bytes={start}-{end}",
                "If-Match": self.identity.etag,
            })
            if response.status != 206:
                raise AcquisitionBlocked("range_status_rejected")
            if _length(response) != length:
                raise AcquisitionBlocked("range_length_mismatch")
            if _etag(response) != self.identity.etag:
                raise AcquisitionBlocked("source_identity_changed")
            if _single(response, "Content-Range") != (
                    f"bytes {start}-{end}/{self.identity.length}"):
                raise AcquisitionBlocked("content_range_mismatch")
            modified = _single(response, "Last-Modified", False)
            if modified is not None and modified != self.identity.modified:
                raise AcquisitionBlocked("source_identity_changed")
            chunks = bytearray()
            while len(chunks) < length:
                # read1 avoids waiting for a full large read. The outer
                # acquisition workflow must enforce a process-wide deadline.
                self._remaining()
                chunk = response.read1(min(_CHUNK, length-len(chunks)))
                self.received_bytes += len(chunk)
                if not chunk:
                    raise AcquisitionBlocked("truncated_range")
                chunks.extend(chunk)
                self._remaining()
            return bytes(chunks)
        except AcquisitionBlocked:
            self.blocked = True
            raise
        except Exception:
            self.blocked = True
            raise AcquisitionBlocked("range_transport_failed") from None
        finally:
            if response is not None:
                response.close()
            if conn is not None:
                conn.close()
