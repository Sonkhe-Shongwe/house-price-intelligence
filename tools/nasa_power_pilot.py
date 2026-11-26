"""Approved one-request NASA POWER CSV pilot. No live network on import."""
import argparse
import base64
import csv
from datetime import date, datetime, timezone
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import hashlib
import io
import json
import os
from pathlib import Path
import re

from tools.hpi_data_manager import check_path, workspace
from tools.world_bank_pilot import (CAP, SECONDS, PinnedHTTPS, Refused,
    bounded_body, deadline_fetch, exclusive_json, remaining)

HOST = "power.larc.nasa.gov"
PARAM = "ALLSKY_SFC_SW_DWN"
REQUEST = ("/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN&community=RE"
           "&longitude=28.0&latitude=-26.2&start=20240101&end=20240107"
           "&format=CSV&time-standard=UTC")
MEDIA = ("text/csv", "application/csv")
ATTEMPT = "AE0-nasa-power-csv-once"
HEADER = ["YEAR", "MO", "DY", PARAM]
BEGIN, END = "-BEGIN HEADER-", "-END HEADER-"
DATES = "Dates (month/day/year): 01/01/2024 through 01/07/2024 in UTC"
MISSING_PREFIX = "the value for missing source data that cannot be computed or is outside of the sources availability range:"
UNIT = r"(?:kW-hr/m\^2/day|kWh/m\^2/day|kWh/m2/day|kWh/m²/day)"
LOCATION = re.compile(r"Location:\s*latitude\s+(-?\d{1,3}(?:\.\d{1,10})?)\s+longitude\s+(-?\d{1,3}(?:\.\d{1,10})?)", re.I | re.ASCII)
PARAM_LINE = re.compile(r"ALLSKY_SFC_SW_DWN\s+CERES SYN1deg\s+All Sky Surface Shortwave Downward Irradiance\s*\(" + UNIT + r"\)\s*;?", re.I)
CODES = frozenset(("BODY_LIMIT", "UTF8", "PREAMBLE", "SOURCE", "DATE_UTC", "LOCATION",
                   "MISSING_METADATA", "UNIT", "METADATA", "COLUMNS", "CSV", "ROW_COUNT",
                   "DATE", "DUPLICATE", "MISSING_VALUE", "VALUE", "TRANSPORT"))


class CsvRefused(Refused):
    def __init__(self, code):
        self.code = code if code in CODES else "METADATA"
        super().__init__(self.code)


class NasaHTTPS(PinnedHTTPS):
    HOSTNAME = HOST


def network_worker(page, deadline, sender):
    try:
        if type(page) is not int or page != 1:
            raise Refused("unapproved NASA request")
        conn = NasaHTTPS(deadline)
        try:
            remaining(deadline)
            conn.request("GET", REQUEST, headers={"Accept": "text/csv, application/csv",
                         "Accept-Encoding": "identity", "Connection": "close",
                         "User-Agent": "HPI-bounded-research/1.0"})
            remaining(deadline)
            raw = bounded_body(conn.getresponse(), MEDIA)
            remaining(deadline)
        finally:
            conn.close()
        sender.send_bytes(b"S" + raw)
    except Exception:
        sender.send_bytes(b"ETRANSPORT")
    finally:
        sender.close()


def fetch_once():
    return deadline_fetch(1, worker=network_worker, seconds=SECONDS)


def safe_diagnostic(raw, reason):
    """Fixed flags only. Never retain unknown keys, metadata, rows or body."""
    result = {"status": "STOP", "reason": reason if reason in CODES else "TRANSPORT",
              "bytes": None, "sha256": None, "flags": {
                  "utf8": False, "begin_header": False, "end_header": False,
                  "expected_columns": False, "expected_utc_dates": False,
                  "known_parameter_unit": False}}
    if not isinstance(raw, bytes) or len(raw) > CAP:
        return result
    result["bytes"] = len(raw)
    result["sha256"] = hashlib.sha256(raw).hexdigest()
    try:
        lines = [line.strip() for line in raw.decode("utf-8-sig").splitlines()]
    except UnicodeError:
        return result
    result["flags"].update({"utf8": True, "begin_header": BEGIN in lines, "end_header": END in lines,
                  "expected_columns": ",".join(HEADER) in lines,
                  "expected_utc_dates": DATES in lines,
                  "known_parameter_unit": any(PARAM_LINE.fullmatch(line) for line in lines)})
    return result


def parse(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= CAP:
        raise CsvRefused("BODY_LIMIT")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise CsvRefused("UTF8") from exc
    if any(ord(ch) < 32 and ch not in "\r\n\t" for ch in text):
        raise CsvRefused("CSV")
    lines = [s.strip() for s in text.splitlines()]
    if not lines or lines[0] != BEGIN or lines.count(BEGIN) != 1 or lines.count(END) != 1:
        raise CsvRefused("PREAMBLE")
    end = lines.index(END)
    if not 5 <= end <= 24 or any(len(s) > 500 for s in lines):
        raise CsvRefused("PREAMBLE")
    meta = [s for s in lines[1:end] if s]
    if not meta or meta[0] not in ("NASA/POWER Source Native Resolution Daily Data",
                                   "NASA/POWER CERES/MERRA2 Native Resolution Daily Data"):
        raise CsvRefused("SOURCE")
    if meta.count(DATES) != 1:
        raise CsvRefused("DATE_UTC")
    locations = [LOCATION.fullmatch(s) for s in meta if s.lower().startswith("location:")]
    if len(locations) != 1 or locations[0] is None:
        raise CsvRefused("LOCATION")
    lat, lon = map(Decimal, locations[0].groups())
    # Source-reported coordinates are not a verified grid centre.
    if abs(lat - Decimal("-26.2")) > Decimal("0.5") or abs(lon - Decimal("28.0")) > Decimal("0.5"):
        raise CsvRefused("LOCATION")
    missing = [s for s in meta if s.lower().startswith(MISSING_PREFIX)]
    if len(missing) != 1 or not re.fullmatch(r"-999(?:\.0+)?", missing[0].split(":")[-1].strip()):
        raise CsvRefused("MISSING_METADATA")
    param = [s for s in meta if s.startswith(PARAM)]
    if len(param) != 1 or not PARAM_LINE.fullmatch(param[0]):
        raise CsvRefused("UNIT")
    allowed = {meta[0], DATES, missing[0], param[0]}
    for s in meta:
        if s in allowed or LOCATION.fullmatch(s) or s.lower() in ("parameter(s):", "parameters:"):
            continue
        if re.fullmatch(r"Elevation from MERRA-2: Average for 0\.5 x 0\.625 degree lat/lon region = -?\d+(?:\.\d+)? meters", s, re.I):
            continue
        raise CsvRefused("METADATA")
    try:
        table = list(csv.reader(io.StringIO("\n".join(lines[end+1:])), strict=True))
    except csv.Error as exc:
        raise CsvRefused("CSV") from exc
    if not table or table[0] != HEADER:
        raise CsvRefused("COLUMNS")
    if len(table) != 8:
        raise CsvRefused("ROW_COUNT")
    rows, seen = [], set()
    for row in table[1:]:
        if len(row) != 4:
            raise CsvRefused("COLUMNS")
        if not re.fullmatch(r"2024", row[0]) or not re.fullmatch(r"0?1", row[1]) or not re.fullmatch(r"0?[1-7]", row[2]):
            raise CsvRefused("DATE")
        day = date(2024, 1, int(row[2])).isoformat()
        if day in seen:
            raise CsvRefused("DUPLICATE")
        seen.add(day)
        if re.fullmatch(r"-999(?:\.0+)?", row[3]):
            raise CsvRefused("MISSING_VALUE")
        if not re.fullmatch(r"\d{1,2}(?:\.\d{1,12})?", row[3], re.ASCII):
            raise CsvRefused("VALUE")
        value = Decimal(row[3])
        if not 0 <= value <= 33:
            raise CsvRefused("VALUE")
        rows.append({"date": day, "irradiation_kwh_m2_day": format(value, "f")})
    rows.sort(key=lambda r: r["date"])
    with localcontext() as ctx:
        ctx.prec = 40
        total = sum(Decimal(r["irradiation_kwh_m2_day"]) for r in rows)
        mean = (total / 7).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    return {"records": rows, "mean_kwh_m2_day": format(mean, "f"),
            "reported_location": {"lat": str(lat), "lon": str(lon), "grid_centre_verified": False},
            "metadata": meta, "time_standard": "UTC", "unit": "kWh/m²/day"}


def execute(root, fetch=fetch_once):
    root = workspace(root)
    for target in (root/"01_Source_Catalogue", root/"02_Raw_Data", root/"07_Reports"):
        check_path(target)
        if not target.is_dir():
            raise Refused("existing private workspace required")
    attempt = root/"02_Raw_Data"/ATTEMPT
    check_path(attempt)
    try:
        attempt.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise Refused("NASA attempt already consumed; never remove or replay") from exc
    started = datetime.now(timezone.utc)
    exclusive_json(attempt/"attempt.json", {"approval": "2026-11-27 exact NASA CSV pilot",
        "started_utc": started.isoformat(), "max_requests": 1, "max_body_bytes": CAP})
    exclusive_json(attempt/"dispatch-1.json", {"host": HOST, "path": REQUEST})
    raw = None
    try:
        raw = fetch()
        parsed = parse(raw)
    except (Refused, OSError) as exc:
        diagnostic = safe_diagnostic(raw, exc.code if isinstance(exc, CsvRefused) else "TRANSPORT")
        exclusive_json(attempt/"refusal.json", diagnostic)
        return diagnostic
    digest = hashlib.sha256(raw).hexdigest()
    bundle = {**parsed, "source": "NASA Langley Research Center POWER",
              "licence": "CC BY 4.0 catalogue listing", "endpoint": "https://"+HOST+REQUEST,
              "acquired_utc": started.isoformat(), "source_vintage": None,
              "requested_location": {"lat": "-26.2", "lon": "28.0", "not_property": True},
              "limitation": "Seven historical UTC days, coarse native solar grid; not rooftop, energy yield or long-term potential",
              "requests": 1, "bytes": len(raw), "sha256": digest,
              "body_base64": base64.b64encode(raw).decode("ascii"), "registered": False}
    stage, final = attempt/"validated.staging.json", attempt/"validated.json"
    exclusive_json(stage, bundle)
    check_path(final)
    os.link(stage, final)
    return {"status": "PASS", "requests": 1, "records": 7, "bytes": len(raw),
            "sha256": digest, "mean_computed": True, "result": "validated.json", "registered": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute or os.name != "nt":
        parser.error("explicit --execute on owner Windows required")
    checkout = Path(__file__).absolute().parents[1]
    try:
        check_path(checkout)
        result = execute(checkout.parent/"HPI-Data-Workspace")
    except (ValueError, OSError) as exc:
        print("STOP:", str(exc) if isinstance(exc, Refused) else type(exc).__name__)
        print("Do not rerun. Preserve attempt markers.")
        return 1
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS":
        print("Do not rerun. Preserve attempt markers; share only this diagnostic.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
