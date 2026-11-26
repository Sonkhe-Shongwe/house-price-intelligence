"""One approved AE0 World Bank mechanism pilot. Windows private workspace only.

No arbitrary URL, credential, retry, redirect, registration or application upload.
Synthetic tests exercise the same parsing, transport envelope and attempt ledger.
"""
import argparse
import base64
from datetime import date, datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import http.client
import ipaddress
import json
import multiprocessing as mp
import os
from pathlib import Path
import queue
import socket
import ssl
import threading
import time

from tools.hpi_data_manager import check_path, workspace

HOST = "api.worldbank.org"
INDICATOR = "SP.URB.TOTL.IN.ZS"
LABEL = "Urban population (% of total population)"
PATH = "/v2/country/ZAF/indicator/" + INDICATOR
CAP = 64 * 1024
SECONDS = 20
ATTEMPT = "AE0-world-bank-2022-2023-once"


class Refused(ValueError):
    pass


def request_path(page):
    if type(page) is not int or page not in (1, 2):
        raise Refused("unapproved page")
    return PATH + "?source=2&date=2022:2023&format=json&per_page=1&page=" + str(page)


def remaining(deadline):
    left = deadline - time.monotonic()
    if left <= 0:
        raise Refused("request deadline exceeded")
    return left


def public_addresses():
    entries = socket.getaddrinfo(HOST, 443, type=socket.SOCK_STREAM,
                                 proto=socket.IPPROTO_TCP)
    if not entries:
        raise Refused("DNS returned no addresses")
    for family, kind, proto, _, address in entries:
        ip = ipaddress.ip_address(address[0])
        if (family not in (socket.AF_INET, socket.AF_INET6) or
                not ip.is_global or ip.is_multicast or
                getattr(ip, "ipv4_mapped", None) is not None or address[1] != 443):
            raise Refused("DNS destination refused")
    return entries[0]


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, deadline):
        self.deadline = deadline
        self.context = ssl.create_default_context()
        super().__init__(HOST, port=443, timeout=remaining(deadline), context=self.context)

    def connect(self):
        family, kind, proto, _, address = public_addresses()
        raw = socket.socket(family, kind, proto)
        try:
            raw.settimeout(remaining(self.deadline))
            raw.connect(address)  # no second resolution, proxy or alternate address retry
            raw.settimeout(remaining(self.deadline))
            self.sock = self.context.wrap_socket(raw, server_hostname=HOST)
            self.sock.settimeout(remaining(self.deadline))
        except BaseException:
            raw.close()
            raise


def bounded_body(response):
    if response.status != 200:
        raise Refused("HTTP status refused; no redirect or retry")
    def single(name, default=None):
        values = response.headers.get_all(name, [])
        if len(values) > 1:
            raise Refused("duplicate response header")
        return values[0] if values else default
    content = single("Content-Type", "").split(";", 1)[0].strip().lower()
    encoding = single("Content-Encoding", "identity").strip().lower()
    transfer = single("Transfer-Encoding", "").strip().lower()
    length = single("Content-Length")
    if content != "application/json" or encoding != "identity":
        raise Refused("response media or encoding refused")
    if transfer not in ("", "chunked") or (transfer and length is not None):
        raise Refused("ambiguous response framing")
    if length is not None:
        if not length.isascii() or not length.isdigit() or len(length) > 10:
            raise Refused("invalid response length")
        count = int(length)
        if not 0 < count <= CAP:
            raise Refused("response byte cap")
        raw = response.read(count)
        if len(raw) != count:
            raise Refused("incomplete response")
    else:
        raw = response.read(CAP)
        if len(raw) >= CAP:
            raise Refused("unbounded response reached cap")
    if not raw:
        raise Refused("empty response")
    return raw


def network_worker(page, deadline, sender):
    """Child is killable even if DNS or a slow response ignores socket timeouts."""
    try:
        path = request_path(page)
        conn = PinnedHTTPS(deadline)
        try:
            remaining(deadline)
            conn.request("GET", path, headers={"Accept": "application/json",
                         "Accept-Encoding": "identity", "Connection": "close",
                         "User-Agent": "HPI-bounded-research/1.0"})
            remaining(deadline)
            raw = bounded_body(conn.getresponse())
            remaining(deadline)
        finally:
            conn.close()
        sender.send_bytes(b"S" + raw)
    except Refused as exc:
        sender.send_bytes(b"E" + str(exc).encode("ascii"))
    except Exception:
        # Never print source response, socket details, or exception arguments.
        sender.send_bytes(b"Enetwork or TLS failure")
    finally:
        sender.close()


def deadline_fetch(page, worker=network_worker, seconds=SECONDS):
    request_path(page)
    deadline = time.monotonic() + seconds
    context = mp.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    proc = context.Process(target=worker, args=(page, deadline, sender), daemon=True)
    messages = queue.Queue(maxsize=1)
    def read():
        try:
            messages.put(receiver.recv_bytes(CAP + 1))
        except (OSError, EOFError):
            messages.put(None)
    started = False
    try:
        proc.start()
        started = True
        sender.close()
        thread = threading.Thread(target=read, daemon=True)
        thread.start()
        try:
            msg = messages.get(timeout=remaining(deadline))
        except queue.Empty as exc:
            raise Refused("request deadline exceeded") from exc
        proc.join(timeout=remaining(deadline))
        if proc.is_alive():
            raise Refused("request deadline exceeded")
        remaining(deadline)
        if not msg or proc.exitcode != 0:
            raise Refused("request worker failed")
        if msg[:1] == b"E":
            raise Refused("transport refused: " + msg[1:].decode("ascii", errors="replace"))
        if msg[:1] != b"S" or not 1 < len(msg) <= CAP + 1:
            raise Refused("invalid worker envelope")
        return msg[1:]
    finally:
        sender.close()
        if started:
            if proc.is_alive():
                proc.kill()
            proc.join(timeout=1)
            if proc.is_alive():
                raise Refused("worker termination unverified; stop")
            proc.close()
        receiver.close()


def unique(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise Refused("duplicate JSON field")
        result[k] = v
    return result


def reject_constant(_):
    raise Refused("nonfinite JSON number")


def parse_page(raw, page, today):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= CAP:
        raise Refused("response byte cap")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                         parse_float=Decimal, parse_constant=reject_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise Refused("invalid JSON response") from exc
    if not isinstance(obj, list) or len(obj) != 2:
        raise Refused("unexpected outer schema")
    meta, rows = obj
    keys = {"page", "pages", "per_page", "total", "sourceid", "lastupdated"}
    if not isinstance(meta, dict) or set(meta) - keys or not keys - {"lastupdated"} <= set(meta):
        raise Refused("unexpected metadata fields")
    if (type(meta["page"]) is not int or meta["page"] != page or
            type(meta["pages"]) is not int or meta["pages"] != 2 or
            type(meta["total"]) is not int or meta["total"] != 2 or
            type(meta["per_page"]) not in (int, str) or meta["per_page"] not in (1, "1") or
            type(meta["sourceid"]) not in (int, str) or meta["sourceid"] not in (2, "2")):
        raise Refused("pagination or source drift")
    updated = meta.get("lastupdated")
    if "lastupdated" in meta:
        try:
            if (not isinstance(updated, str) or len(updated) != 10 or
                    date.fromisoformat(updated).isoformat() != updated or date.fromisoformat(updated) > today):
                raise ValueError
        except ValueError as exc:
            raise Refused("invalid source update date") from exc
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise Refused("expected one observation")
    row = rows[0]
    if set(row) != {"indicator", "country", "countryiso3code", "date", "value",
                    "unit", "obs_status", "decimal"}:
        raise Refused("unexpected observation fields")
    if (row["indicator"] != {"id": INDICATOR, "value": LABEL} or
            row["country"] != {"id": "ZA", "value": "South Africa"} or
            row["countryiso3code"] != "ZAF" or row["date"] not in ("2022", "2023") or
            row["unit"] != "" or row["obs_status"] != "" or
            type(row["decimal"]) is not int or not 0 <= row["decimal"] <= 15):
        raise Refused("observation outside exact scope")
    value = row["value"]
    if type(value) not in (int, Decimal):
        raise Refused("missing or invalid observation; unsupported")
    value = Decimal(value)
    if (not value.is_finite() or not 0 <= value <= 100 or
            len(value.as_tuple().digits) > 32 or abs(value.as_tuple().exponent) > 32):
        raise Refused("invalid percentage")
    return {"year": int(row["date"]), "percent": format(value, "f"),
            "source_decimal": row["decimal"]}, updated


def exclusive_json(path, value):
    check_path(path)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def execute(root, fetch=deadline_fetch):
    root = workspace(root)
    rawdir = root / "02_Raw_Data"
    for target in (root / "01_Source_Catalogue", rawdir, root / "07_Reports"):
        check_path(target)
        if not target.is_dir():
            raise Refused("existing private workspace required")
    attempt = rawdir / ATTEMPT
    check_path(attempt)
    try:
        attempt.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise Refused("attempt already consumed; never remove or replay") from exc
    acquired = datetime.now(timezone.utc)
    exclusive_json(attempt / "attempt.json", {"approval": "2026-11-26 exact AE0 pilot",
                   "started_utc": acquired.isoformat(), "max_requests": 2, "max_body_bytes": 2 * CAP})
    records, evidence = [], []
    updated = None
    for page in (1, 2):
        # The marker is durable before entering any network code.
        exclusive_json(attempt / ("dispatch-%d.json" % page), {"page": page, "path": request_path(page)})
        raw = fetch(page)
        row, stamp = parse_page(raw, page, acquired.date())
        if page == 2 and (stamp != updated or row["year"] == records[0]["year"]):
            raise Refused("source version drift or duplicate year")
        updated = stamp
        records.append(row)
        evidence.append({"page": page, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                         "body_base64": base64.b64encode(raw).decode("ascii")})
    if {r["year"] for r in records} != {2022, 2023}:
        raise Refused("year coverage")
    records.sort(key=lambda r: r["year"])
    with localcontext() as ctx:
        ctx.prec = 80
        change = Decimal(records[1]["percent"]) - Decimal(records[0]["percent"])
    bundle = {"source": "World Bank WDI; UN World Urbanization Prospects",
              "indicator": INDICATOR, "licence": "CC BY 4.0; applicable World Bank terms",
              "geography": "ZAF national", "unit": "percent", "acquired_utc": acquired.isoformat(),
              "source_last_updated": updated, "publication_date": None,
              "records": records, "percentage_point_change": format(change, "f"),
              "requests": 2, "response_body_bytes": sum(e["bytes"] for e in evidence),
              "source_responses": evidence, "registered": False}
    # No accepted output visible until both pages validate; hard link is
    # atomic and no-overwrite on the same filesystem. A crash may leave staging.
    staged, final = attempt / "validated.staging.json", attempt / "validated.json"
    exclusive_json(staged, bundle)
    check_path(final)
    os.link(staged, final)
    # Preserve staging as an additional link (same bytes); no auto deletion.
    return {"status": "PASS", "requests": 2, "records": 2, "bytes": bundle["response_body_bytes"],
            "source_last_updated": updated, "hashes": [e["sha256"] for e in evidence],
            "result": "validated.json", "registered": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        parser.error("explicit --execute required")
    if os.name != "nt":
        parser.error("approved execution environment is owner Windows only")
    checkout = Path(__file__).absolute().parents[1]
    check_path(checkout)
    root = checkout.parent / "HPI-Data-Workspace"
    try:
        result = execute(root)
    except (ValueError, OSError) as exc:
        print("STOP:", str(exc) if isinstance(exc, Refused) else type(exc).__name__)
        print("Do not rerun. Preserve attempt markers; share only STOP reason.")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
