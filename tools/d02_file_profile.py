"""D02-F1 local-only aggregate exploration, no download, join, or registration."""
from collections import Counter
from datetime import date
import hashlib
import json
import math
import os
import re

from tools.hpi_data_manager import read_bounded, workspace
from tools.world_bank_pilot import unique, reject_constant

FILENAME = "CapeTown_LandParcels_Pinelands_2026.geojson"
ORIGINAL = "Property_-2034817884066750538.geojson"
CAP = 25 * 1024**2
MAX_ROWS = 10000
DISPLAYED_ROWS = 3442
OBSERVED_BYTES = 2780852
INTAKE = date(2026,11,27)
REVIEW_BY = date(2026,12,27)
ALIASES = {
    "OBJECTID": ("objectid", "object id", "fid"),
    "SG26_CODE": ("sg26_code", "sg26 code"),
    "PRTY_NMBR": ("prty_nmbr", "property number", "property_number"),
    "SL_LAND_PRCL_KEY": ("sl_land_prcl_key", "isis / lis key", "isis/lis key"),
    "OFC_SBRB_NAME": ("ofc_sbrb_name", "official suburb name"),
    "LU_LGL_STS_DSCR": ("lu_lgl_sts_dscr", "legal status sg", "legal status"),
    "ZONING": ("zoning",),
}
# Do not return unknown field names or values. Screen for explicit personal
# attributes; this is a heuristic, not a guarantee of absence of personal data.
PERSONAL = re.compile(r"(?:^|_)(?:owner|owners|surname|person|tenant|occupant|email|e_mail|phone|mobile|contact|id_number|identity_number|taxpayer|first_name|last_name|full_name|cellphone)(?:_|$)",re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")


class ProfileStop(ValueError):
    pass


def scalar_type(value):
    if value is None: return "null"
    if type(value) is bool: return "boolean"
    if type(value) is int: return "integer"
    if type(value) is float: return "number"
    if isinstance(value,str): return "string"
    return "nested"


def missing(value):
    return value is None or (isinstance(value,str) and not value.strip())


def profile(raw):
    from shapely.geometry import shape
    if not isinstance(raw,bytes) or not 0<len(raw)<=CAP:
        raise ProfileStop("BYTE_LIMIT")
    try:
        obj=json.loads(raw.decode("utf-8-sig"),object_pairs_hook=unique,parse_constant=reject_constant)
    except (ValueError,UnicodeError,RecursionError):
        raise ProfileStop("INVALID_JSON") from None
    if not isinstance(obj,dict) or obj.get("type")!="FeatureCollection" or not isinstance(obj.get("features"),list):
        raise ProfileStop("NOT_FEATURE_COLLECTION")
    rows=obj["features"]
    if not 0<len(rows)<=MAX_ROWS:
        raise ProfileStop("FEATURE_LIMIT")
    fields=set()
    for feature in rows:
        if not isinstance(feature,dict) or feature.get("type")!="Feature" or not isinstance(feature.get("properties"),dict):
            raise ProfileStop("FEATURE_STRUCTURE")
        props=feature["properties"]
        fields.update(props)
        for k,v in props.items():
            normalized=re.sub(r"[^a-z0-9]+","_",re.sub(r"([a-z])([A-Z])",r"\1_\2",k).lower()).strip("_")
            if PERSONAL.search(normalized) or scalar_type(v)=="nested" or (isinstance(v,str) and EMAIL.search(v)):
                raise ProfileStop("POSSIBLE_PERSONAL_OR_NESTED_DATA")
    lower={}
    for field in fields:
        lower.setdefault(field.casefold(),[]).append(field)
    resolved={}
    ambiguous=0
    for canonical,aliases in ALIASES.items():
        matches=[f for alias in aliases for f in lower.get(alias,[])]
        if len(matches)==1:
            resolved[canonical]=matches[0]
        elif len(matches)>1:
            ambiguous+=1
    suburb=resolved.get("OFC_SBRB_NAME")
    if not suburb:
        raise ProfileStop("SUBURB_FIELD_UNRESOLVED")
    in_scope=sum(isinstance(f["properties"].get(suburb),str) and f["properties"][suburb].strip().casefold()=="pinelands" for f in rows)
    if in_scope!=len(rows):
        return {"status":"STOP","reason":"SUBURB_SCOPE","features":len(rows),"pinelands_matches":in_scope}
    report={}
    for canonical in ALIASES:
        field=resolved.get(canonical)
        values=[f["properties"].get(field) for f in rows] if field else [None]*len(rows)
        present=[v for v in values if not missing(v)]
        types=Counter(scalar_type(v) for v in values)
        entry={"resolved":field is not None,"missing":len(rows)-len(present),"types":dict(types),
               "maximum_string_length":max((len(v) for v in present if isinstance(v,str)),default=0)}
        if canonical in ("OBJECTID","SG26_CODE","PRTY_NMBR","SL_LAND_PRCL_KEY"):
            # Preserve type and original string, including leading zeros.
            counts=Counter((scalar_type(v),v) for v in present)
            entry.update(distinct_present=len(counts),duplicate_groups=sum(n>1 for n in counts.values()),
                         rows_in_duplicate_groups=sum(n for n in counts.values() if n>1))
            if canonical=="SG26_CODE":
                entry["strings_length_26"]=sum(isinstance(v,str) and len(v)==26 for v in present)
        report[canonical]=entry
    valid=invalid=absent=plausible=0
    for feature in rows:
        geom=feature.get("geometry")
        if geom is None:
            absent+=1
            continue
        if not isinstance(geom,dict) or geom.get("type") not in ("Polygon","MultiPolygon"):
            invalid+=1
            continue
        try:
            poly=shape(geom)
            if poly.is_empty or not poly.is_valid:
                invalid+=1
                continue
            bounds=poly.bounds
            if not all(math.isfinite(v) for v in bounds):
                invalid+=1
                continue
            valid+=1
            x0,y0,x1,y1=bounds
            # Broad envelope only; not verified boundary membership or CRS.
            if 18<=x0<=x1<=19.5 and -35<=y0<=y1<=-33:
                plausible+=1
        except Exception:
            invalid+=1
    return {"status":"PROFILED","features":len(rows),"pinelands_matches":in_scope,
            "matches_portal_display_count":len(rows)==DISPLAYED_ROWS,
            "property_field_count":len(fields),"unprofiled_field_count":len(fields)-len(resolved),
            "ambiguous_canonical_fields":ambiguous,"fields":report,
            "geometry":{"valid_polygons":valid,"invalid_or_unsupported":invalid,"missing":absent,
                        "valid_bounds_plausible_cape_town":plausible},
            "limitation":"Exploratory profile only; no ground truth, legal area, title, dwelling, temporal or join qualification."}


def owner_profile(root):
    if os.name!="nt" or os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        print("STOP: owner-local Windows only.")
        return 1
    if not INTAKE<=date.today()<REVIEW_BY:
        print("STOP: retention window needs review; no automatic deletion.")
        return 1
    try:
        raw=read_bounded(workspace(root)/"02_Raw_Data"/FILENAME,CAP)
        result=profile(raw)
        result.update(file=FILENAME,original_filename=ORIGINAL,bytes=len(raw),
                      matches_attachment_size=len(raw)==OBSERVED_BYTES,
                      sha256=hashlib.sha256(raw).hexdigest(),source="City of Cape Town Land Parcels",
                      intake_date=INTAKE.isoformat(),review_by=REVIEW_BY.isoformat(),
                      registered=False,network_requests=0,files_modified=False)
    except ProfileStop as exc:
        print(json.dumps({"status":"STOP","reason":str(exc),"registered":False}))
        return 1
    except Exception:
        print("STOP: local read or profiling failed; no record values emitted.")
        return 1
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result["status"]=="PROFILED" else 1
