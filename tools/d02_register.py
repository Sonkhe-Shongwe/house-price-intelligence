"""Private offline registration of the approved Pinelands snapshot."""
from collections import defaultdict
from datetime import date
import json
import math
import os

from tools import hpi_data_manager as dm
from tools import d02_file_profile as fp
from tools.world_bank_pilot import unique, reject_constant

KEYS = ("SG26_CODE","PRTY_NMBR","SL_LAND_PRCL_KEY")
FIELDS = tuple(fp.ALIASES)
INTAKE = date(2026,11,27)
DEADLINE = date(2026,12,27)
SOURCE_URL = "https://odp-cctegis.opendata.arcgis.com/datasets/cctegis::land-parcels/about"
TERMS = "Portal research exemption; exact reuse terms not independently verified"


def safe_geometry(g):
    """Preserve standard geometry content, not foreign members or values."""
    def coords(v):
        if isinstance(v,list):
            return all(coords(x) for x in v)
        return type(v) in (int,float) and math.isfinite(v)
    if g is None:
        return
    if not isinstance(g,dict):
        raise ValueError("GEOMETRY_STRUCTURE")
    if g.get("type")=="GeometryCollection":
        if set(g)!={"type","geometries"} or not isinstance(g["geometries"],list):
            raise ValueError("GEOMETRY_STRUCTURE")
        for child in g["geometries"]:
            safe_geometry(child)
    elif (set(g)!={"type","coordinates"} or
          g["type"] not in ("Point","MultiPoint","LineString","MultiLineString","Polygon","MultiPolygon") or
          not isinstance(g["coordinates"],list) or not coords(g["coordinates"])):
        raise ValueError("GEOMETRY_STRUCTURE")


def geometry_quality(g):
    from shapely.geometry import shape
    if g is None:
        return "missing", None
    if g["type"] not in ("Polygon","MultiPolygon"):
        return "invalid_or_unsupported", None
    try:
        p=shape(g)
        if p.is_empty or not p.is_valid or not all(math.isfinite(x) for x in p.bounds):
            return "invalid_or_unsupported",None
        x0,y0,x1,y1=p.bounds
        if 18<=x0<=x1<=19.5 and -35<=y0<=y1<=-33:
            return "valid_plausible",p
        return "valid_outside_envelope",p
    except Exception:
        return "invalid_or_unsupported",None


def derive(raw):
    q=fp.profile(raw)
    if q["status"]!="PROFILED" or q["ambiguous_canonical_fields"] or not all(q["fields"][k]["resolved"] for k in FIELDS):
        raise ValueError("SCOPE_OR_SCHEMA")
    obj=json.loads(raw.decode("utf-8-sig"),object_pairs_hook=unique,parse_constant=reject_constant)
    rows=obj["features"]
    names={f for row in rows for f in row["properties"]}
    resolved={k:next(f for f in names if f.casefold() in fp.ALIASES[k]) for k in FIELDS}
    props=[{k:r["properties"].get(v) for k,v in resolved.items()} for r in rows]
    groups={k:defaultdict(list) for k in KEYS}
    seen=set()
    for i,p in enumerate(props):
        if (type(p["OBJECTID"]) is not int or p["OBJECTID"] in seen or
            not isinstance(p["SG26_CODE"],str) or len(p["SG26_CODE"])!=26 or
            not p["SG26_CODE"].strip() or not isinstance(p["PRTY_NMBR"],str) or
            not p["PRTY_NMBR"].strip() or type(p["SL_LAND_PRCL_KEY"]) is not int):
            raise ValueError("IDENTITY_TYPE_OR_COMPLETENESS")
        seen.add(p["OBJECTID"])
        for k in KEYS:
            groups[k][p[k]].append(i)
    duplicates={k:{tuple(ix) for ix in groups[k].values() if len(ix)>1} for k in KEYS}
    flagged={i for sets in duplicates.values() for ix in sets for i in ix}
    pairwise={}
    for i,k in enumerate(KEYS):
        for other in KEYS[i+1:]:
            forward=defaultdict(set)
            reverse=defaultdict(set)
            for p in props:
                forward[p[k]].add(p[other])
                reverse[p[other]].add(p[k])
            pairwise[k+"__"+other]={"left_keys_multiple_right":sum(len(v)>1 for v in forward.values()),
                "right_keys_multiple_left":sum(len(v)>1 for v in reverse.values()),
                "identical_duplicate_membership":duplicates[k]==duplicates[other]}
    geometries=[]
    statuses=[]
    shapes=[]
    for row in rows:
        g=row.get("geometry")
        safe_geometry(g)
        status,p=geometry_quality(g)
        geometries.append(g)
        statuses.append(status)
        shapes.append(p)
    assessment={}
    for k in KEYS:
        same_raw=same_topology=conflicts=unassessed=0
        for ix in duplicates[k]:
            same_raw+=all(geometries[i]==geometries[ix[0]] for i in ix)
            if any(shapes[i] is None for i in ix):
                unassessed+=1
            else:
                try:
                    same_topology+=all(shapes[i].equals(shapes[ix[0]]) for i in ix)
                except Exception:
                    unassessed+=1
            conflicts+=any(tuple(props[i][f] for f in ("OFC_SBRB_NAME","LU_LGL_STS_DSCR","ZONING"))!=
                           tuple(props[ix[0]][f] for f in ("OFC_SBRB_NAME","LU_LGL_STS_DSCR","ZONING")) for i in ix)
        assessment[k]={"duplicate_groups":len(duplicates[k]),"exact_geometry_groups":same_raw,
                       "topologically_equal_groups":same_topology,"topology_unassessed_groups":unassessed,
                       "context_attribute_conflict_groups":conflicts}
    output=[]
    for i,p in enumerate(props):
        ambiguous=i in flagged
        valid=statuses[i]=="valid_plausible"
        p=dict(p,quality_flags={"duplicate_identifier":ambiguous,"geometry_status":statuses[i],
                                "unique_key_candidate":not ambiguous,
                                "spatial_candidate":valid and not ambiguous})
        output.append({"type":"Feature","properties":p,"geometry":geometries[i]})
    q.update({"retained_features":len(output),"ambiguous_identity_rows":len(flagged),
              "unique_key_candidates":len(rows)-len(flagged),
              "spatial_candidates":sum(i not in flagged and s=="valid_plausible" for i,s in enumerate(statuses)),
              "cross_key_cardinality":pairwise,"duplicate_assessment":assessment,
              "geometry_flags":{s:statuses.count(s) for s in sorted(set(statuses))},
              "network_requests":0,"property_join":False,"geometry_repair":False,
              "deduplicated":False,"registration_scope":"Private reference; no legal identity, join or app eligibility established."})
    data=dm.json_bytes({"type":"FeatureCollection","features":output})
    if len(data)>50*dm.MIB:
        raise ValueError("DERIVED_SIZE")
    return data,q


def register(root,deadline=None,today=None):
    root=dm.workspace(root)
    today=today or date.today()
    deadline=deadline or DEADLINE
    if not INTAKE<=today<deadline<=DEADLINE:
        raise ValueError("RETENTION_WINDOW")
    for folder in ("01_Source_Catalogue","02_Raw_Data","03_Processed_Data","07_Reports"):
        p=root/folder
        dm.check_path(p)
        if not p.is_dir():
            raise ValueError("WORKSPACE_REQUIRED")
    raw=dm.read_bounded(root/dm.PARCEL_RAW,dm.PARCEL_LIMIT)
    if dm.sha(raw)!=dm.PARCEL_SHA or len(raw)!=fp.OBSERVED_BYTES:
        raise ValueError("SNAPSHOT_MISMATCH")
    data,q=derive(raw)
    if q["features"]!=fp.DISPLAYED_ROWS:
        raise ValueError("COUNT_MISMATCH")
    manifest={"dataset_id":"HPI-DATA-010","manager_version":"0.9.0",
              "source":"City of Cape Town Corporate GIS, Land Parcels, Pinelands filtered export",
              "source_url":SOURCE_URL,"source_original_filename":fp.ORIGINAL,
              "attribution":"City of Cape Town Corporate GIS; HPI field projection and quality flags.",
              "source_identity_evidence":"Owner-observed snapshot SHA-256, not publisher checksum.",
              "source_bytes":len(raw),"source_sha256":dm.sha(raw),"raw_path":dm.PARCEL_RAW,
              "first_intake_date":INTAKE.isoformat(),"private_scope_approved_by_owner":True,
              "terms_status":TERMS,"retention_policy":dm.PARCEL_POLICY,"retention":dm.PARCEL_RETENTION,
              "do_not_retain_on_or_after":deadline.isoformat(),"processed_path":dm.PARCEL_OUTPUT,
              "processed_sha256":dm.sha(data),"quality_report":dm.PARCEL_REPORT,"quality":q}
    plan=[(root/dm.PARCEL_OUTPUT,data),(root/dm.PARCEL_REPORT,dm.json_bytes(q)),
          (root/dm.PARCEL_MANIFEST,dm.json_bytes(manifest))]
    for path,payload in plan:
        dm.check_target(path,payload)
    for path,payload in plan:
        dm.publish(path,payload)
    return dm.audit_registered(root,dm.parcel_spec(),today=today)


def owner_register(root,deadline=None):
    if os.name!="nt" or os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        print("STOP: owner-local Windows only.")
        return 1
    try:
        result=register(root,deadline)
        print(json.dumps({"import":"complete","registered":True,"audit":result,
                          "status":dm.parcel_status(dm.workspace(root))},indent=2))
        return 0
    except Exception:
        print("STOP: snapshot, retention, data structure or local integrity check failed; no overwrite. Review locally.")
        return 1
