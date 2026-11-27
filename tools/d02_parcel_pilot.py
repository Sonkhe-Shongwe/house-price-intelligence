"""D02-P1 approved Cape Town parcel feasibility; aggregate-only, one attempt."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import re
import time
from urllib.parse import urlencode

from tools.hpi_data_manager import check_path, workspace
from tools.world_bank_pilot import (PinnedHTTPS, Refused, bounded_body,
    deadline_fetch, exclusive_json, remaining, unique, reject_constant)

HOST = "citymaps.capetown.gov.za"
LAYER = "/agsext/rest/services/Theme_Based/ODP_SPLIT_4/FeatureServer/0/query"
FIELDS = ("OBJECTID", "SG26_CODE", "PRTY_NMBR", "OFC_SBRB_NAME", "LU_LGL_STS_DSCR", "ZONING")
ENVELOPE = (18.46, -33.97, 18.48, -33.95)
PARAMS = {"where":"1=1", "geometry":"18.46,-33.97,18.48,-33.95",
    "geometryType":"esriGeometryEnvelope", "inSR":"4326",
    "spatialRel":"esriSpatialRelIntersects", "outFields":",".join(FIELDS),
    "returnGeometry":"true", "outSR":"4326", "orderByFields":"OBJECTID ASC",
    "resultRecordCount":"100", "f":"geojson"}
REQUEST = LAYER + "?" + urlencode(PARAMS)
CAP = 5 * 1024**2
SECONDS = 60
MAX_ROWS = 100
MAX_PAIRS = 100000
ATTEMPT = "D02-P1-cape-town-parcels-once"
MEDIA = ("application/json", "application/geo+json")
REASONS = {"BODY", "SCHEMA", "FIELDS", "GEOMETRY", "CAP", "EMPTY", "DEADLINE", "TRANSPORT"}


class ParcelRefused(Refused):
    def __init__(self, code):
        self.code = code if code in REASONS else "SCHEMA"
        super().__init__(self.code)


class ParcelHTTPS(PinnedHTTPS):
    HOSTNAME = HOST


def network_worker(page, deadline, sender):
    try:
        if type(page) is not int or page != 1:
            raise ParcelRefused("TRANSPORT")
        conn = ParcelHTTPS(deadline)
        try:
            remaining(deadline)
            conn.request("GET", REQUEST, headers={"Accept": ", ".join(MEDIA),
                "Accept-Encoding": "identity", "Connection": "close",
                "User-Agent": "HPI-bounded-research/1.0"})
            remaining(deadline)
            raw = bounded_body(conn.getresponse(), MEDIA, cap=CAP)
            remaining(deadline)
        finally:
            conn.close()
        sender.send_bytes(b"S" + raw)
    except Exception:
        sender.send_bytes(b"ETRANSPORT")
    finally:
        sender.close()


def fetch_once(seconds):
    return deadline_fetch(1, worker=network_worker, seconds=seconds, cap=CAP)


def profile(raw, deadline):
    from shapely.geometry import shape
    if not isinstance(raw, bytes) or not 0 < len(raw) <= CAP:
        raise ParcelRefused("BODY")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                         parse_constant=reject_constant)
    except (UnicodeError, ValueError, RecursionError):
        raise ParcelRefused("SCHEMA") from None
    allowed = {"type", "features", "exceededTransferLimit", "crs"}
    if (not isinstance(obj, dict) or set(obj) - allowed or
            obj.get("type") != "FeatureCollection" or not isinstance(obj.get("features"), list)):
        raise ParcelRefused("SCHEMA")
    if "exceededTransferLimit" in obj and type(obj["exceededTransferLimit"]) is not bool:
        raise ParcelRefused("SCHEMA")
    if "crs" in obj and obj["crs"] not in (
            {"type":"name","properties":{"name":"EPSG:4326"}},
            {"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},
            {"type":"name","properties":{"name":"urn:ogc:def:crs:EPSG::4326"}}):
        raise ParcelRefused("GEOMETRY")
    rows = obj["features"]
    if not rows:
        raise ParcelRefused("EMPTY")
    if len(rows) > MAX_ROWS:
        raise ParcelRefused("CAP")
    missing = dict.fromkeys(FIELDS, 0)
    keys = {k:Counter() for k in FIELDS[:3]}
    pairs = valid = invalid = plausible = 0
    for feature in rows:
        remaining(deadline)
        if (not isinstance(feature, dict) or set(feature) - {"type","id","properties","geometry"}
                or feature.get("type") != "Feature" or "geometry" not in feature
                or not isinstance(feature.get("properties"), dict)):
            raise ParcelRefused("SCHEMA")
        props = feature["properties"]
        if set(props) - set(FIELDS):
            raise ParcelRefused("FIELDS")
        if "id" in feature and (type(feature["id"]) is not int or feature["id"] != props.get("OBJECTID")):
            raise ParcelRefused("FIELDS")
        for field in FIELDS:
            value = props.get(field)
            if value is None or (isinstance(value,str) and not value.strip()):
                missing[field] += 1
                continue
            if field == "OBJECTID":
                if type(value) is not int or value < 0:
                    raise ParcelRefused("FIELDS")
            elif (not isinstance(value,str) or len(value)>256 or
                    any(ord(ch)<32 for ch in value) or
                    re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",value)):
                raise ParcelRefused("FIELDS")
            if field in keys:
                keys[field][value] += 1
        geom = feature["geometry"]
        if geom is None:
            invalid += 1
            continue
        if (not isinstance(geom,dict) or set(geom)!={"type","coordinates"}
                or geom["type"] not in ("Polygon","MultiPolygon")):
            raise ParcelRefused("GEOMETRY")
        polygons = [geom["coordinates"]] if geom["type"]=="Polygon" else geom["coordinates"]
        if not isinstance(polygons,list) or not polygons:
            raise ParcelRefused("GEOMETRY")
        for polygon in polygons:
            if not isinstance(polygon,list) or not polygon:
                raise ParcelRefused("GEOMETRY")
            for ring in polygon:
                if not isinstance(ring,list) or len(ring)<4:
                    raise ParcelRefused("GEOMETRY")
                for xy in ring:
                    pairs += 1
                    if pairs > MAX_PAIRS:
                        raise ParcelRefused("CAP")
                    if (not isinstance(xy,list) or len(xy)!=2 or
                        any(type(v) not in (int,float) or not math.isfinite(v) for v in xy)
                        or not -180<=xy[0]<=180 or not -90<=xy[1]<=90):
                        raise ParcelRefused("GEOMETRY")
                if ring[0]!=ring[-1]:
                    raise ParcelRefused("GEOMETRY")
                remaining(deadline)
        try:
            polygon = shape(geom)
            if polygon.is_empty or not polygon.is_valid:
                invalid += 1
                continue
            valid += 1
            x0,y0,x1,y1 = polygon.bounds
            if x0<=ENVELOPE[2] and x1>=ENVELOPE[0] and y0<=ENVELOPE[3] and y1>=ENVELOPE[1]:
                plausible += 1
        except Exception:
            raise ParcelRefused("GEOMETRY") from None
    remaining(deadline)
    return {"features":len(rows), "missing_fields":missing,
            "duplicate_key_groups":{k:sum(n>1 for n in counts.values()) for k,counts in keys.items()},
            "valid_polygons":valid,"invalid_or_missing_polygons":invalid,
            "valid_polygon_bounds_intersect_request":plausible,"coordinate_pairs":pairs,
            "source_transfer_limit_flag":obj.get("exceededTransferLimit"),
            "sample_cap_reached":len(rows)==MAX_ROWS}


def execute(root, fetch=fetch_once):
    # Import before consuming an attempt; existing district adapter uses Shapely.
    from shapely.geometry import shape
    root = workspace(root)
    reports = root/"07_Reports"
    for target in (root/"01_Source_Catalogue",root/"02_Raw_Data",reports):
        check_path(target)
        if not target.is_dir():
            raise Refused("existing private workspace required")
    attempt = reports/ATTEMPT
    check_path(attempt)
    try:
        attempt.mkdir(mode=0o700)
    except FileExistsError:
        raise Refused("D02-P1 attempt already consumed; do not replay") from None
    start = datetime.now(timezone.utc).isoformat()
    metadata = {"approval":"2026-11-27 D02-P1", "source":"City of Cape Town",
                "endpoint":"https://"+HOST+REQUEST, "started_utc":start,
                "max_requests":1,"max_body_bytes":CAP,"deadline_seconds":SECONDS,
                "max_features":MAX_ROWS,"max_coordinate_pairs":MAX_PAIRS,
                "registered":False,"raw_retained":False}
    exclusive_json(attempt/"attempt.json",metadata)
    deadline = time.monotonic()+SECONDS
    raw = None
    result = dict(metadata, status="STOP", requests_dispatched_max=1)
    try:
        raw = fetch(remaining(deadline))
        metrics = profile(raw,deadline)
        result.update(metrics,status="PASS")
    except Exception as exc:
        result["reason"] = exc.code if isinstance(exc,ParcelRefused) else (
            "DEADLINE" if time.monotonic()>=deadline else "TRANSPORT")
    if isinstance(raw,bytes) and 0<len(raw)<=CAP:
        result.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    raw = None
    result["limitation"] = "Capped sample, not representative; parcel not dwelling; bounds plausibility not identity or legal area; no joins or valuation."
    exclusive_json(attempt/"result.json",result)
    return result


def owner_execute(root):
    if os.name!="nt" or os.environ.get("GITHUB_ACTIONS") or os.environ.get("CI"):
        raise Refused("D02-P1 requires owner-local Windows outside CI")
    try:
        result = execute(root)
    except Exception:
        print("STOP: preflight or attempt ledger refused; do not replay any consumed attempt.")
        return 1
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result["status"]=="PASS" else 1
