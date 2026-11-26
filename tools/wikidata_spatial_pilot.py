"""One authorised AE0 spatial query; owner Windows workspace only."""
import argparse
import base64
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import re
from urllib.parse import urlencode
import unicodedata

from tools.hpi_data_manager import check_path, workspace
from tools.world_bank_pilot import (CAP, SECONDS, PinnedHTTPS, Refused,
    bounded_body, deadline_fetch, exclusive_json, remaining, unique, reject_constant)

HOST = "query-next.wikidata.org"
ATTEMPT = "AE0-wikidata-schools-once"
QUERY = "PREFIX wd: <http://www.wikidata.org/entity/>\nPREFIX wdt: <http://www.wikidata.org/prop/direct/>\nPREFIX p: <http://www.wikidata.org/prop/>\nPREFIX psv: <http://www.wikidata.org/prop/statement/value/>\nPREFIX wikibase: <http://wikiba.se/ontology#>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\nSELECT DISTINCT ?facility ?name ?lat ?lon WHERE {\n  ?facility wdt:P31 wd:Q3914; wdt:P17 wd:Q258; p:P625 ?statement; rdfs:label ?name .\n  ?statement a wikibase:BestRank; psv:P625 ?coordinate .\n  ?coordinate wikibase:geoGlobe wd:Q2; wikibase:geoLatitude ?lat; wikibase:geoLongitude ?lon .\n  FILTER(LANG(?name) = \"en\" && ?lat >= -26.4 && ?lat <= -25.9 && ?lon >= 27.7 && ?lon <= 28.3)\n}\nORDER BY ?facility ?name ?lat ?lon\nLIMIT 25"
REQUEST = "/sparql?" + urlencode({"query": QUERY, "format": "json"})
MEDIA = ("application/sparql-results+json", "application/json")
AGENT = "HPI-bounded-research/1.0 (https://github.com/Sonkhe-Shongwe/house-price-intelligence)"
VARS = {"facility", "name", "lat", "lon"}
REFERENCE = (-26.2, 28.0)
XSD = "http://www.w3.org/2001/XMLSchema#"


class SpatialHTTPS(PinnedHTTPS):
    HOSTNAME = HOST


def network_worker(page, deadline, sender):
    try:
        if type(page) is not int or page != 1:
            raise Refused("unapproved spatial request")
        conn = SpatialHTTPS(deadline)
        try:
            remaining(deadline)
            conn.request("GET", REQUEST, headers={"Accept": MEDIA[0], "Accept-Encoding": "identity",
                         "Connection": "close", "User-Agent": AGENT})
            remaining(deadline)
            raw = bounded_body(conn.getresponse(), MEDIA)
            remaining(deadline)
        finally:
            conn.close()
        sender.send_bytes(b"S" + raw)
    except Refused as exc:
        sender.send_bytes(b"E" + str(exc).encode("ascii"))
    except Exception:
        sender.send_bytes(b"Enetwork or TLS failure")
    finally:
        sender.close()


def fetch_once():
    # Reuse the tested killable worker envelope, not the World Bank request.
    return deadline_fetch(1, worker=network_worker, seconds=SECONDS)


def binding(obj, keys, kinds):
    if not isinstance(obj, dict) or set(obj) != keys or obj.get("type") not in kinds:
        raise Refused("unexpected RDF binding")
    if not isinstance(obj.get("value"), str):
        raise Refused("invalid RDF value")
    return obj["value"]


def coordinate(obj, lower, upper):
    value = binding(obj, {"type", "datatype", "value"}, ("literal", "typed-literal"))
    if obj["datatype"] not in (XSD+"decimal", XSD+"double", XSD+"float"):
        raise Refused("unexpected coordinate datatype")
    if len(value) > 48 or not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]{1,3})?", value):
        raise Refused("invalid coordinate lexical form")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise Refused("invalid coordinate") from exc
    if (not number.is_finite() or not Decimal(lower) <= number <= Decimal(upper)
            or abs(number.as_tuple().exponent) > 32):
        raise Refused("coordinate outside approved rectangle")
    return number


def parse(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= CAP:
        raise Refused("response byte cap")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                         parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Refused("invalid SPARQL JSON") from exc
    if not isinstance(obj, dict) or set(obj) != {"head", "results"}:
        raise Refused("unexpected response schema")
    head, results = obj["head"], obj["results"]
    if (not isinstance(head, dict) or set(head) != {"vars"} or
            not isinstance(head["vars"], list) or len(head["vars"]) != 4 or
            not all(isinstance(v, str) for v in head["vars"]) or set(head["vars"]) != VARS):
        raise Refused("unexpected projection")
    if not isinstance(results, dict) or set(results) != {"bindings"}:
        raise Refused("unexpected results schema")
    bindings = results["bindings"]
    if not isinstance(bindings, list) or not 1 <= len(bindings) <= 25:
        raise Refused("empty or oversized spatial sample; unsupported")
    rows, seen = [], set()
    for row in bindings:
        if not isinstance(row, dict) or set(row) != VARS:
            raise Refused("unexpected row fields")
        uri = binding(row["facility"], {"type", "value"}, ("uri",))
        match = re.fullmatch(r"http://www\.wikidata\.org/entity/(Q[1-9][0-9]{0,15})", uri)
        if not match or match[1] in seen:
            raise Refused("invalid or repeated facility identifier")
        qid = match[1]
        seen.add(qid)
        label = binding(row["name"], {"type", "value", "xml:lang"}, ("literal",))
        if (row["name"]["xml:lang"] != "en" or not label.strip() or len(label) > 200
                or any(unicodedata.category(c).startswith("C") for c in label)):
            raise Refused("invalid institutional label")
        lat = coordinate(row["lat"], "-26.4", "-25.9")
        lon = coordinate(row["lon"], "27.7", "28.3")
        rows.append({"qid": qid, "name": label, "lat": format(lat, "f"), "lon": format(lon, "f")})
    return rows


def distances(rows):
    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    lat0, lon0 = REFERENCE
    output = []
    for row in rows:
        _, _, metres = geod.inv(lon0, lat0, float(row["lon"]), float(row["lat"]))
        if not math.isfinite(metres) or not 0 <= metres <= 100000:
            raise Refused("invalid geodesic distance")
        output.append({**row, "distance_m": round(metres, 2)})
    return sorted(output, key=lambda r: (r["distance_m"], r["qid"]))


def execute(root, fetch=fetch_once):
    # Fail before consuming authority if required existing dependency is absent.
    from pyproj import Geod
    Geod(ellps="WGS84")
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
        raise Refused("spatial attempt already consumed; never remove or replay") from exc
    started = datetime.now(timezone.utc)
    exclusive_json(attempt/"attempt.json", {"approval": "2026-11-26 exact AE0 spatial pilot",
        "started_utc": started.isoformat(), "max_requests": 1, "max_body_bytes": CAP})
    exclusive_json(attempt/"dispatch-1.json", {"host": HOST, "path": REQUEST})
    raw = fetch()
    rows = distances(parse(raw))
    digest = hashlib.sha256(raw).hexdigest()
    bundle = {"source": "Wikidata contributors", "licence": "CC0", "endpoint": "https://"+HOST+"/sparql",
        "query": QUERY, "acquired_utc": started.isoformat(), "source_vintage": None,
        "geography": {"lat": [-26.4, -25.9], "lon": [27.7, 28.3], "crs": "EPSG:4326"},
        "reference": {"lat": REFERENCE[0], "lon": REFERENCE[1], "not_property": True},
        "method": "PyProj Geod WGS84 ellipsoidal geodesic, metres",
        "limitation": "Direct class, English-labelled community-mapped sample; not complete, verified active schools, road distances or nearest actual school",
        "at_cap": len(rows) == 25, "requests": 1, "bytes": len(raw), "sha256": digest,
        "body_base64": base64.b64encode(raw).decode("ascii"), "records": rows, "registered": False}
    stage, final = attempt/"validated.staging.json", attempt/"validated.json"
    exclusive_json(stage, bundle)
    check_path(final)
    os.link(stage, final)
    return {"status": "PASS", "requests": 1, "records": len(rows), "bytes": len(raw),
        "sha256": digest, "at_cap": bundle["at_cap"], "distances_computed": len(rows),
        "result": "validated.json", "registered": False}


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
    except ImportError:
        print("STOP: existing PyProj dependency unavailable; no request dispatched.")
        return 1
    except (ValueError, OSError) as exc:
        print("STOP:", str(exc) if isinstance(exc, Refused) else type(exc).__name__)
        print("Do not rerun. Preserve attempt markers; share only STOP reason.")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
