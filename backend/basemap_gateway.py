"""Private loopback range gateway for the approved regional extraction.

No public app route or generic proxy. No executable installation or live
invocation here. The caller must supply a preflighted transport and own the
process/disk/time limits. All requests are serialised by HTTPServer.
"""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import re
from threading import Thread
from backend.basemap_transport import AcquisitionBlocked, BoundedArchive, MAX_RANGE

LOCAL_PATH = "/approved-context.pmtiles"
BBOX = "-87.76,42.00,-87.64,42.09"
OUTPUT = "evanston-context.pmtiles"


class _Server(HTTPServer):
    allow_reuse_address = False

    def __init__(self, guard):
        self.guard = guard
        super().__init__(("127.0.0.1", 0), _Handler)

    def get_request(self):
        sock, addr = super().get_request()
        sock.settimeout(10)
        return sock, addr

    def handle_error(self, request, client_address):
        # Do not print arbitrary input, upstream metadata or tracebacks.
        self.guard.blocked = True


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *args):
        pass

    def _reply(self, status, *, length=0, headers=None, body=None):
        self.send_response(status)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.close_connection = True
        if body is not None:
            self.wfile.write(body)

    def _identity(self):
        guard = self.server.guard
        if guard.blocked or guard.identity is None:
            self._reply(503)
            return None
        if self.path != LOCAL_PATH:
            self._reply(404)
            return None
        # Reject absolute request targets, unexpected Host, request bodies and
        # ambiguous headers. No forwarded authentication/cookies/URL parameters.
        hosts = self.headers.get_all("Host", [])
        if (hosts != [f"127.0.0.1:{self.server.server_port}"]
                or self.headers.get_all("Transfer-Encoding")
                or self.headers.get_all("Content-Length") not in (None, ["0"])):
            self._reply(400)
            return None
        return guard.identity

    def do_HEAD(self):
        identity = self._identity()
        if identity is None:
            return
        if self.headers.get_all("Range"):
            self._reply(400)
            return
        self._reply(200, length=identity.length, headers={
            "ETag": identity.etag, "Last-Modified": identity.modified,
            "Accept-Ranges": "bytes", "Content-Type": "application/octet-stream",
        })

    def do_GET(self):
        identity = self._identity()
        if identity is None:
            return
        tags = self.headers.get_all("If-Match", [])
        if tags and tags != [identity.etag]:
            self._reply(412)
            return
        ranges = self.headers.get_all("Range", [])
        match = re.fullmatch(r"bytes=([0-9]{1,15})-([0-9]{1,15})", ranges[0]) if len(ranges) == 1 else None
        if not match:
            self._reply(416, headers={"Content-Range": f"bytes */{identity.length}"})
            return
        start, end = map(int, match.groups())
        if not 0 <= start <= end < identity.length or end-start+1 > MAX_RANGE:
            self._reply(416, headers={"Content-Range": f"bytes */{identity.length}"})
            return
        try:
            data = self.server.guard.read_range(start, end)
        except AcquisitionBlocked:
            self._reply(503)
            return
        # Never emit a partial result if the upstream transport failed.
        self._reply(206, length=len(data), headers={
            "Content-Range": f"bytes {start}-{end}/{identity.length}",
            "ETag": identity.etag, "Last-Modified": identity.modified,
            "Accept-Ranges": "bytes", "Content-Type": "application/octet-stream",
        }, body=data)


@contextmanager
def loopback_gateway(guard: BoundedArchive):
    if guard.blocked or guard.identity is None:
        raise AcquisitionBlocked("identity_not_available")
    server = _Server(guard)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}{LOCAL_PATH}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def extraction_command(executable: Path, source: str, workdir: Path) -> list[str]:
    """Fixed CLI argument vector, not an executable runner or integrity check."""
    if not executable.is_absolute() or not workdir.is_absolute():
        raise ValueError("absolute qualified paths required")
    if not re.fullmatch(r"http://127\.0\.0\.1:[0-9]{1,5}/approved-context\.pmtiles", source):
        raise ValueError("only the loopback gateway is permitted")
    return [str(executable), "extract", source, str(workdir / OUTPUT),
            "--bbox=" + BBOX, "--minzoom=0", "--maxzoom=15",
            "--download-threads=1", "--overfetch=0"]
