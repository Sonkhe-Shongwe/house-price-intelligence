"""Same-origin, bounded read-only archive transport for local qualification.

This route is currently enabled ONLY with code-generated non-map fixture bytes.
It is not a PMTiles parser, geographic validation or a provider proxy.
"""
from dataclasses import dataclass, field
import hashlib
import re

from backend.basemap_limits import OUTPUT_LIMIT
from backend.basemap_transport import MAX_RANGE

CONTEXT_PATH = "/context/qualification-v1.pmtiles"
FIXTURE_BYTES = bytes(range(256)) * 64


@dataclass(frozen=True)
class ContextArchive:
    payload: bytes
    digest: str = field(init=False)
    def __post_init__(self):
        if type(self.payload) is not bytes or not 0 < len(self.payload) <= OUTPUT_LIMIT:
            raise ValueError("invalid_context_archive_size")
        object.__setattr__(self, "digest", hashlib.sha256(self.payload).hexdigest())

    @property
    def etag(self):
        return '"' + self.digest + '"'

    def serve(self, env, start_response, security_headers):
        length = len(self.payload)
        method = env.get("REQUEST_METHOD")
        # No shared caches or cross-origin requests; caller checks loopback,
        # Origin, forwarding, query and exact path before invoking.
        common = [*security_headers,
                  ("Content-Type", "application/octet-stream"),
                  ("ETag", self.etag), ("Accept-Ranges", "bytes"),
                  ("X-Context-Transport-Fixture", "true")]
        def reply(status, body=b"", *, size=None, headers=()):
            start_response(status, [*common,
                ("Content-Length", str(len(body) if size is None else size)), *headers])
            return [body]
        if method not in ("GET", "HEAD"):
            return reply("405 Method Not Allowed", headers=(("Allow", "GET, HEAD"),))
        if env.get("CONTENT_LENGTH") not in (None, "", "0") or env.get("HTTP_TRANSFER_ENCODING"):
            return reply("400 Bad Request")
        if env.get("HTTP_IF_MATCH") not in (None, self.etag):
            return reply("412 Precondition Failed")
        if env.get("HTTP_IF_RANGE") not in (None, self.etag):
            return reply("412 Precondition Failed") # never fall back to full object
        if method == "HEAD":
            if env.get("HTTP_RANGE") is not None:
                return reply("400 Bad Request")
            return reply("200 OK", size=length)
        match = re.fullmatch(r"bytes=([0-9]{1,12})-([0-9]{1,12})",
                             env.get("HTTP_RANGE", ""))
        invalid = (("Content-Range", f"bytes */{length}"),)
        if not match:
            return reply("416 Range Not Satisfiable", headers=invalid)
        start, end = map(int, match.groups())
        if not 0 <= start <= end < length or end-start+1 > MAX_RANGE:
            return reply("416 Range Not Satisfiable", headers=invalid)
        return reply("206 Partial Content", self.payload[start:end+1],
                     headers=(("Content-Range", f"bytes {start}-{end}/{length}"),))


def transport_fixture():
    return ContextArchive(FIXTURE_BYTES)
