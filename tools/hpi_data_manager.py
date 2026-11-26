"""Offline HPI data workspace manager. No network, deletion or cloud operations."""
import argparse
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import zipfile

VERSION = "0.1.0"
ARCHIVE = "rppi-2010-2023-v1.zip"
APPROVED_SHA = "62c46ed2a8d22da53d30541bb35843ee30dce8f8b1364a1409d74760fc76646d"
FOLDERS = ("01_Source_Catalogue", "02_Raw_Data", "03_Processed_Data",
           "04_Engineered_Data", "05_Notebooks", "06_Scripts", "07_Reports")
META = "H00 H01 H02 H03 H04 H05 H17 H18 H25 weightP".split()
MONTHS = [f"M{y}{m:02}" for y in range(2010, 2024) for m in range(1, 13)
          if (y, m) <= (2023, 1)]
MEMBER = "rppi-2010-2023-v1/rppi-2010-2023-v1.csv"
MANIFEST = "01_Source_Catalogue/HPI-DATA-002.json"
OUTPUT = "03_Processed_Data/HPI-DATA-002/rppi_monthly.csv"
REPORT = "07_Reports/HPI-DATA-002_quality.json"
RAW = "02_Raw_Data/" + ARCHIVE
MIB = 1024 * 1024

def sha(data):
    return hashlib.sha256(data).hexdigest()

def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")

def check_path(path):
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and
                getattr(part.lstat(), "st_file_attributes", 0) &
                getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024)):
            raise ValueError("Symlink/reparse point refused: " + str(part))

def workspace(root):
    root = Path(root).expanduser()
    if not root.is_absolute():
        if root.anchor:
            raise ValueError("Use a fully qualified path or ordinary relative path.")
        root = Path.cwd() / root
    # Inspect the original traversal before collapsing parent components, so
    # a symlink or junction followed by '..' cannot evade the boundary check.
    check_path(root)
    root = Path(os.path.normpath(root))
    check_path(root)
    if any((p / ".git").exists() or (p / ".git").is_symlink()
           for p in (root, *root.parents)):
        raise ValueError("Use a private workspace outside every Git checkout.")
    return root

def read_bounded(path, limit=10*MIB):
    workspace(path.parent)
    check_path(path)
    if not path.is_file() or path.stat().st_size > limit:
        raise ValueError("Missing or oversized file: " + path.name)
    with path.open("rb") as f:
        data = f.read(limit+1)
    if len(data) > limit:
        raise ValueError("File exceeds limit.")
    return data

def check_target(path, data):
    workspace(path.parent)
    check_path(path)
    if path.exists() and read_bounded(path, 50*MIB) != data:
        raise ValueError("Existing file differs; no overwrite: " + str(path))

def publish(path, data):
    check_target(path, data)
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    check_path(path)
    with path.open("xb") as f:
        f.write(data)

def initialise(root):
    for folder in FOLDERS:
        p = root / folder
        workspace(p)
        check_path(p)
        p.mkdir(parents=True, exist_ok=True)
    path = root / "01_Source_Catalogue/source_catalogue.csv"
    check_path(path)
    if not path.exists():
        publish(path, b"family_id,dataset,status\nD01,Completed sales,unqualified\nD02,Cadastral parcels,rights_pending\nD03,OSM footprints,pilot_closed_no_retained_rows\nD09,RPPI,see dataset manifest\n")
    for folder in FOLDERS:
        if not (root / folder).is_dir():
            raise ValueError("Workspace folder missing.")

def number(value):
    result = Decimal(value.replace(",", "."))
    if not result.is_finite():
        raise ValueError("Non-finite value.")
    return result

def profile(archive, expected=APPROVED_SHA):
    if len(archive) > 10*MIB or sha(archive) != expected:
        raise ValueError("Archive not the approved version or over transfer limit.")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        infos = z.infolist()
        if (len(infos) != 2 or {i.filename for i in infos} !=
                {MEMBER, MEMBER.replace(".csv", ".xlsx")} or
                sum(i.file_size for i in infos) > 50*MIB or
                any(i.flag_bits & 1 or i.is_dir() or
                    stat.S_ISLNK(i.external_attr >> 16) for i in infos)):
            raise ValueError("Unexpected archive members, encryption or size.")
        with z.open(MEMBER) as stream:
            raw = stream.read(50*MIB+1)
        if len(raw) > 50*MIB:
            raise ValueError("Expanded limit exceeded.")
    reader = csv.reader(io.StringIO(raw.decode("utf-8-sig")), delimiter=";")
    if next(reader, None) != META + MONTHS:
        raise ValueError("Unexpected RPPI header.")
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["series_id","geography_name_source","geography_level","month",
                     "index_value","index_base","source_weight_pct","month_on_month_pct","year_on_year_pct"])
    seen = set()
    expected_ids = {f"RPPI{i}00" for i in (*range(10, 20), *range(20, 29))}
    def growth(vals, i, lag):
        return "" if i < lag else f"{(vals[i]/vals[i-lag]-1)*100:.4f}"
    for row in reader:
        if len(row) != len(META)+len(MONTHS) or (len(seen)+1)*len(row) > 100000:
            raise ValueError("Unexpected row width or cell limit.")
        sid = row[3]
        if sid in seen or sid not in expected_ids or not row[5] or row[7] != "Dec 2020=100":
            raise ValueError("Unexpected series, duplicate or index base.")
        seen.add(sid)
        vals = [number(x) for x in row[10:]]
        weight = number(row[9])
        if not 0 <= weight <= 100 or min(vals) <= 0 or vals[MONTHS.index("M202012")] != 100:
            raise ValueError("Invalid index or weight.")
        level = ("national" if sid == "RPPI1000" else "metro_aggregate" if sid == "RPPI2000"
                 else "province" if sid.startswith("RPPI1") else "metro")
        for i, month in enumerate(MONTHS):
            writer.writerow([sid,row[5],level,month[1:5]+"-"+month[5:7]+"-01",
                             str(vals[i]),row[7],str(weight),growth(vals,i,1),growth(vals,i,12)])
    if seen != expected_ids:
        raise ValueError("Missing series.")
    quality = {"series":len(seen),"months":len(MONTHS),"observations":len(seen)*len(MONTHS),
               "missing_index_values":0,"duplicate_series":0,"nonpositive_index_values":0,
               "intentional_initial_mom_blanks":len(seen),"intentional_initial_yoy_blanks":12*len(seen),
               "source_csv_sha256":sha(raw),"xlsx_compared":False,
               "limitations":"Aggregate indices only; no sale prices, no individual properties, no current coverage claim."}
    return out.getvalue().encode("utf-8"), quality

def import_rppi(root, intake, terms_reviewed, expected=APPROVED_SHA, today=None, deadline=None):
    today = today or date.today()
    if not terms_reviewed:
        raise ValueError("Owner must review and confirm applicable terms before import.")
    retention = retention_fields(root,MANIFEST,intake,deadline,today,LEGACY_RPPI)
    raw_path = root / RAW
    candidates = [root / ARCHIVE, raw_path]
    existing = [p for p in candidates if p.exists()]
    if not existing:
        raise ValueError("Place the original approved ZIP in workspace root or 02_Raw_Data.")
    archive = read_bounded(existing[0])
    for p in existing[1:]:
        if read_bounded(p) != archive:
            raise ValueError("Conflicting original archives.")
    result, quality = profile(archive, expected)
    manifest = {"dataset_id":"HPI-DATA-002","manager_version":VERSION,
        "source":"Stats SA, RPPI 2010-2023 v1; UCT DataFirst",
        "doi":"10.25828/VQ6V-2T85","catalogue_licence":"CC BY; version not specified",
        "terms_reviewed_by_owner":True,"first_intake_date":intake.isoformat(),
        **retention,
        "source_sha256":sha(archive),"source_bytes":len(archive),
        "raw_path":RAW,"processed_path":OUTPUT,"processed_sha256":sha(result),
        "quality_report":REPORT,"quality":quality}
    planned = [(root/MANIFEST,json_bytes(manifest)),(raw_path,archive),
               (root/OUTPUT,result),(root/REPORT,json_bytes(quality))]
    for path, data in planned:
        check_target(path,data)
    initialise(root)
    for path, data in planned:
        publish(path,data)
    return manifest

def status(root):
    path = root / MANIFEST
    if not path.exists():
        return {"registered":False}
    manifest = json.loads(read_bounded(path))
    copies = [p for p in (ARCHIVE, RAW, "HPI_DATA_002_processed.zip",
                 "HPI_DATA_002_processed", OUTPUT) if (root/p).exists()]
    return {"registered":True,"dataset_id":"HPI-DATA-002",**retention_status(manifest),"known_local_paths":copies,
            "note":"Check other copies, chat uploads, sync and backups separately; no deletion performed."}

def self_test():
    # Invented rows only; no source data or network.
    text = io.StringIO()
    w = csv.writer(text,delimiter=";")
    w.writerow(META+MONTHS)
    for n in range(10,29):
        w.writerow([n,"D0160","fixture",f"RPPI{n}00","fixture","Invented","Index",
                    "Dec 2020=100","fixture","10"]+["100"]*len(MONTHS))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf,"w") as z:
        z.writestr(MEMBER,text.getvalue())
        z.writestr(MEMBER.replace(".csv",".xlsx"),"not inspected")
    archive = buf.getvalue()
    def rejects(fn):
        try:
            fn()
        except (ValueError, OSError, zipfile.BadZipFile, InvalidOperation):
            return
        raise AssertionError("Expected refusal")
    with tempfile.TemporaryDirectory() as tmp:
        root = workspace(Path(tmp)/"private")
        initialise(root)
        (root/ARCHIVE).write_bytes(archive)
        day = date(2026,1,1)
        rejects(lambda: import_rppi(root,day,False,sha(archive),day))
        rejects(lambda: import_rppi(root,day,True,sha(archive),day+timedelta(days=30),deadline=day+timedelta(days=30)))
        rejects(lambda: import_rppi(root,day,True,"bad",day))
        first = import_rppi(root,day,True,sha(archive),day)
        assert first["quality"]["observations"] == 2983
        spec = ("HPI-DATA-002",MANIFEST,RAW,OUTPUT,REPORT,10*MIB,sha(archive))
        before_audit = [(root/p).read_bytes() for p in (MANIFEST,RAW,OUTPUT,REPORT)]
        assert audit_registered(root,spec,day)["status"] == "integrity checks passed"
        assert before_audit == [(root/p).read_bytes() for p in (MANIFEST,RAW,OUTPUT,REPORT)]
        assert import_rppi(root,day,True,sha(archive),day+timedelta(days=365)) == first
        rejects(lambda: import_rppi(root,day+timedelta(days=1),True,sha(archive),day+timedelta(days=1)))
        assert (root/ARCHIVE).read_bytes() == archive
        (root/OUTPUT).write_text("existing different file")
        rejects(lambda: audit_registered(root,spec,day))
        nested = root/"02_Raw_Data"/"nested"
        nested.mkdir()
        (nested/".git").mkdir()
        rejects(lambda: publish(nested/"private.csv",b"fixture"))
        (nested/"fixture.txt").write_text("fixture")
        rejects(lambda: read_bounded(nested/"fixture.txt"))
        rejects(lambda: import_rppi(root,day,True,sha(archive),day))
        assert (root/OUTPUT).read_text() == "existing different file"
        checkout = Path(tmp)/"checkout"
        checkout.mkdir()
        (checkout/".git").mkdir()
        assert workspace(checkout/".."/"private") == root
        previous_cwd = Path.cwd()
        try:
            os.chdir(checkout)
            assert workspace(Path("..")/"private") == root
            rejects(lambda: workspace(Path("..")/"checkout"/"nested"))
            rejects(lambda: workspace(Path(".")))
        finally:
            os.chdir(previous_cwd)
        # Windows symlink creation may require additional privileges.
        if os.name != "nt":
            alias = Path(tmp)/"alias"
            alias.symlink_to(checkout, target_is_directory=True)
            rejects(lambda: workspace(alias/".."/"private"))
        (root/".git").mkdir()
        rejects(lambda: workspace(root))
    print("PASS: offline import, limits, retention, exact-version, idempotence, no overwrite and Git boundary checks.")


# RPPI's VERSION remains 0.1.0 to preserve byte-identical accepted manifests.
MANAGER_VERSION = "0.2.0"
GEO_FILE = "geoBoundaries-ZAF-ADM2_simplified.geojson"
GEO_SHA = "bb4800b804811ce9cfa5f6bf535466e3f812751249f0e1b7375d5f5753570e7c"
GEO_MANIFEST = "01_Source_Catalogue/HPI-DATA-003.json"
GEO_RAW = "02_Raw_Data/" + GEO_FILE
GEO_OUTPUT = "03_Processed_Data/HPI-DATA-003/district_index.csv"
GEO_REPORT = "07_Reports/HPI-DATA-003_quality.json"
GEO_CRS = {"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}}
GEO_SNAPSHOT = "1c423398df24ddf6e730b116567d2181c9782778d0459c3f3b76ca2f9f12b6bc"
GEO_URL = "https://www.geoboundaries.org/data/snapshots/" + GEO_SNAPSHOT + "/gbOpen/ZAF/ADM2/" + GEO_FILE

def profile_districts(raw, expected=GEO_SHA):
    import math
    try:
        from shapely.geometry import shape
        from shapely.errors import ShapelyError
    except ImportError as exc:
        raise ValueError("District adapter requires Shapely in this Python environment.") from exc
    if len(raw) > 10*MIB or sha(raw) != expected:
        raise ValueError("Unexpected district snapshot or size.")
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection" or data.get("crs") != GEO_CRS:
        raise ValueError("Expected CRS84 FeatureCollection.")
    features = data.get("features")
    if not isinstance(features, list) or len(features) > 100 or len(features) != 52:
        raise ValueError("Expected 52 district features within cap.")
    ids, names, geometries = set(), set(), set()
    pairs = 0
    polygons = multipolygons = missing_iso = 0
    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["shape_id","source_name","source_iso","country","administrative_level",
                "reference_year","geometry_type","coordinate_pairs",
                "min_longitude","min_latitude","max_longitude","max_latitude",
                "official_municipality_code"])
    for f in features:
        if f.get("type") != "Feature":
            raise ValueError("Expected Feature.")
        p, g = f["properties"], f["geometry"]
        if set(p) != {"shapeID","shapeName","shapeISO","shapeGroup","shapeType"}:
            raise ValueError("Unexpected property fields.")
        sid, name, iso = p["shapeID"], p["shapeName"], p["shapeISO"]
        if (not isinstance(sid,str) or not sid.startswith("47623444B") or sid in ids or
                not isinstance(name,str) or not name.strip() or name in names or
                not isinstance(iso,str) or p["shapeGroup"] != "ZAF" or p["shapeType"] != "ADM2"):
            raise ValueError("Invalid or duplicate district identity.")
        ids.add(sid)
        names.add(name)
        missing_iso += not iso.strip()
        kind, coords = g["type"], g["coordinates"]
        if kind == "Polygon":
            parts = [coords]
            polygons += 1
        elif kind == "MultiPolygon":
            parts = coords
            multipolygons += 1
        else:
            raise ValueError("Unsupported district geometry.")
        count = 0
        if not isinstance(parts,list) or not parts:
            raise ValueError("Empty geometry.")
        for part in parts:
            if not isinstance(part,list) or not part:
                raise ValueError("Empty polygon.")
            for ring in part:
                if not isinstance(ring,list) or len(ring) < 4 or ring[0] != ring[-1]:
                    raise ValueError("Unclosed or short ring.")
                for point in ring:
                    if (not isinstance(point,list) or len(point) != 2 or
                            any(type(v) not in (int,float) or not math.isfinite(v) for v in point) or
                            not (-180 <= point[0] <= 180 and -90 <= point[1] <= 90)):
                        raise ValueError("Invalid CRS84 coordinate.")
                    pairs += 1
                    count += 1
                    if pairs > 500000:
                        raise ValueError("Coordinate cap exceeded.")
        try:
            geom = shape(g)
            if geom.is_empty or not geom.is_valid or geom.area <= 0 or geom.wkb in geometries:
                raise ValueError("Empty, invalid or exact duplicate geometry.")
            geometries.add(geom.wkb)
        except ShapelyError as exc:
            raise ValueError("Geometry validation failed.") from exc
        w.writerow([sid,name,iso,"ZAF","ADM2",2020,kind,count,*geom.bounds,""])
    quality = {"features":len(ids),"valid_geometries":len(geometries),"coordinate_pairs":pairs,
               "polygons":polygons,"multipolygons":multipolygons,"missing_shape_iso":missing_iso,
               "duplicate_shape_ids":0,"duplicate_shape_names":0,"empty_geometries":0,
               "exact_duplicate_geometries":0,"official_code_crosswalk_verified":False,
               "topology_across_features_verified":False,"boundary_accuracy_verified":False,
               "limitations":"2020 simplified district geography; not current official codes, parcels or sales."}
    return out.getvalue().encode("utf-8"), quality

def import_districts(root, intake, terms_reviewed, deadline=None, expected=GEO_SHA, today=None):
    today = today or date.today()
    if not terms_reviewed:
        raise ValueError("Owner must confirm applicable source terms before import.")
    retention = retention_fields(root,GEO_MANIFEST,intake,deadline,today,LEGACY_GEO)
    raw_path = root/GEO_RAW
    paths = [p for p in (root/GEO_FILE,raw_path) if p.exists()]
    if not paths:
        raise ValueError("Place the supplied approved GeoJSON in workspace root or 02_Raw_Data.")
    raw = read_bounded(paths[0])
    if any(read_bounded(p) != raw for p in paths[1:]):
        raise ValueError("Conflicting district source copies.")
    result, quality = profile_districts(raw, expected)
    manifest = {"dataset_id":"HPI-DATA-003","manager_version":MANAGER_VERSION,
        "source":"geoBoundaries; OCHA ROSEA; South African Municipal Demarcation Board",
        "source_url":GEO_URL,"snapshot":GEO_SNAPSHOT,"boundary_id":"ZAF-ADM2-47623444",
        "reference_year":2020,"build_date_supplied":"2026-11-02",
        "source_licence":"CC BY 3.0 IGO (publisher metadata)",
        "source_licence_url":"https://creativecommons.org/licenses/by/3.0/igo/",
        "publisher_terms_url":"https://www.geoboundaries.org/",
        "licence_evidence_limit":"Upstream HDX page not independently retrieved; newer build metadata supplied by owner.",
        "attribution":"geoBoundaries (https://www.geoboundaries.org/), OCHA ROSEA, South African Municipal Demarcation Board; Runfola et al. (2020), doi:10.1371/journal.pone.0231866.",
        "changes":"Derived district index CSV; original GeoJSON preserved unmodified; no official code crosswalk.",
        "terms_reviewed_by_owner":True,"first_intake_date":intake.isoformat(),
        **retention,
        "source_sha256":sha(raw),"source_bytes":len(raw),"raw_path":GEO_RAW,
        "processed_path":GEO_OUTPUT,"processed_sha256":sha(result),
        "quality_report":GEO_REPORT,"quality":quality}
    planned = [(root/GEO_MANIFEST,json_bytes(manifest)),(raw_path,raw),
               (root/GEO_OUTPUT,result),(root/GEO_REPORT,json_bytes(quality))]
    for path, content in planned:
        workspace(path.parent)
        check_target(path,content)
    initialise(root)
    # Existing manifest is checked before any copy; publish the manifest last.
    for path, content in planned[1:] + planned[:1]:
        publish(path,content)
    return manifest

def district_status(root):
    path = root/GEO_MANIFEST
    if not path.exists():
        return {"dataset_id":"HPI-DATA-003","registered":False}
    m = json.loads(read_bounded(path))
    return {"registered":True,"dataset_id":"HPI-DATA-003",**retention_status(m),
            "known_local_paths":[p for p in (GEO_FILE,GEO_RAW,GEO_OUTPUT) if (root/p).exists()],
            "note":"Other copies, chat uploads, sync and backups require separate review; no deletion performed."}

def district_cli(root, args):
    existing = root/GEO_MANIFEST
    if existing.exists():
        prior = json.loads(read_bounded(existing))
        intake = args.intake_date or date.fromisoformat(prior["first_intake_date"])
        reviewed = prior["terms_reviewed_by_owner"] is True
        deadline = args.retain_until or stored_deadline(prior)
    else:
        intake = args.intake_date or date.fromisoformat(input("Actual first download date (YYYY-MM-DD): ").strip())
        reviewed = args.terms_reviewed or input("Confirm source terms permit private import and retention (yes/no): ").strip().lower()=="yes"
        deadline = args.retain_until

    m = import_districts(root,intake,reviewed,deadline)
    print(json.dumps({"import":"complete","quality":m["quality"],"status":district_status(root)},indent=2))
    return 0

def district_self_test():
    # Entirely invented geometry, never the supplied file in CI.
    features = []
    for i in range(52):
        x, y = i%10, i//10
        ring = [[x,y],[x+.5,y],[x+.5,y+.5],[x,y+.5],[x,y]]
        features.append({"type":"Feature","properties":{"shapeID":f"47623444Bfixture{i}",
            "shapeName":f"Invented {i}","shapeISO":"","shapeGroup":"ZAF","shapeType":"ADM2"},
            "geometry":{"type":"Polygon","coordinates":[ring]}})
    data = {"type":"FeatureCollection","crs":GEO_CRS,"features":features}
    raw = json_bytes(data)
    def rejects(fn):
        try:
            fn()
        except (ValueError,OSError,KeyError,TypeError):
            return
        raise AssertionError("Expected district refusal.")
    expected = sha(raw)
    _, q = profile_districts(raw,expected)
    assert q["features"] == 52 and q["coordinate_pairs"] == 260
    rejects(lambda: profile_districts(raw,"wrong"))
    bad = json.loads(raw)
    bad["features"][0]["geometry"]["coordinates"][0] = [[0,0],[1,1],[0,1],[1,0],[0,0]]
    b = json_bytes(bad)
    rejects(lambda: profile_districts(b,sha(b)))
    bad = json.loads(raw)
    bad["features"][1]["properties"]["shapeID"] = bad["features"][0]["properties"]["shapeID"]
    b = json_bytes(bad)
    rejects(lambda: profile_districts(b,sha(b)))
    bad = json.loads(raw)
    bad["features"][1]["geometry"] = bad["features"][0]["geometry"]
    b = json_bytes(bad)
    rejects(lambda: profile_districts(b,sha(b)))
    bad = json.loads(raw)
    bad["crs"] = {}
    b = json_bytes(bad)
    rejects(lambda: profile_districts(b,sha(b)))
    with tempfile.TemporaryDirectory() as tmp:
        root = workspace(Path(tmp)/"private")
        initialise(root)
        (root/GEO_FILE).write_bytes(raw)
        day = date(2026,1,1)
        rejects(lambda: import_districts(root,day,False,expected=expected,today=day))
        rejects(lambda: import_districts(root,day,True,day,expected,day))
        rejects(lambda: import_districts(root,day,True,day+timedelta(days=10),expected,day+timedelta(days=10)))
        first = import_districts(root,day,True,day+timedelta(days=10),expected,day)
        spec = ("HPI-DATA-003",GEO_MANIFEST,GEO_RAW,GEO_OUTPUT,GEO_REPORT,10*MIB,expected)
        assert audit_registered(root,spec,day)["status"] == "integrity checks passed"
        rejects(lambda: audit_registered(root,spec,day+timedelta(days=10)))
        paths = [root/p for p in (GEO_RAW,GEO_OUTPUT,GEO_REPORT,GEO_MANIFEST)]
        before = [(p.read_bytes(),p.stat().st_mtime_ns) for p in paths]
        assert import_districts(root,day,True,day+timedelta(days=10),expected,day) == first
        assert before == [(p.read_bytes(),p.stat().st_mtime_ns) for p in paths]
        rejects(lambda: import_districts(root,day,True,day+timedelta(days=11),expected,day))
        (root/GEO_OUTPUT).write_text("conflict")
        rejects(lambda: import_districts(root,day,True,day+timedelta(days=10),expected,day))
        assert (root/GEO_OUTPUT).read_text()=="conflict"
    print("PASS: district identity, geometry, version, retention, idempotence and conflict checks.")



# HPI-DATA-004: one approved publisher partition, no network in the manager.
BUILD_FILE = "part-00088-6362069d-6eea-4a1e-8c47-524b38a5fb20.c000.csv.gz"
BUILD_URL = "https://bfppub.z5.web.core.windows.net/2026-07-24/global-buildings.geojsonl/RegionName=SouthAfrica/quadkey=300301302/" + BUILD_FILE
BUILD_MANIFEST = "01_Source_Catalogue/HPI-DATA-004.json"
BUILD_OUTPUT = "03_Processed_Data/HPI-DATA-004/building_index.csv"
BUILD_REPORT = "07_Reports/HPI-DATA-004_quality.json"
BUILD_RAW = "02_Raw_Data/" + BUILD_FILE
BUILD_MAX_BYTES = 50*MIB
BUILD_MAX_EXPANDED = 500*MIB
BUILD_MAX_RECORDS = 500000
BUILD_MAX_PAIRS = 5000000

def building_profile(raw, max_expanded=BUILD_MAX_EXPANDED,
                     max_records=BUILD_MAX_RECORDS, max_pairs=BUILD_MAX_PAIRS):
    import gzip
    import math
    try:
        from shapely.geometry import shape
        from shapely.geometry.polygon import orient
        from shapely.errors import ShapelyError
        from pyproj import Geod
    except ImportError as exc:
        raise ValueError("Building adapter requires Shapely and pyproj.") from exc
    if not 0 < len(raw) <= BUILD_MAX_BYTES:
        raise ValueError("Compressed building size outside approved bounds.")
    geod = Geod(ellps="WGS84")
    q = dict(records=0,expanded_bytes=0,coordinate_pairs=0,usable=0,
             invalid_geometry=0,exact_duplicate_geometry=0,
             missing_height=0,missing_confidence=0,invalid_height=0,
             invalid_confidence=0,outside_tile_centroid=0)
    seen = set()
    property_keys = set()
    areas = []
    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["source_row","footprint_m2","centroid_lon","centroid_lat",
                "estimated_height_m","detection_confidence"])
    def optional(p, key, maximum=None):
        value = p.get(key)
        if value is None or value == -1:
            q["missing_"+key] += 1
            return ""
        if (type(value) not in (int,float) or not math.isfinite(value) or
                value < 0 or (maximum is not None and value > maximum)):
            q["invalid_"+key] += 1
            return ""
        return str(value)
    def reject_constant(value):
        raise ValueError("Nonfinite JSON constant: " + value)
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        while True:
            # Limit both total expansion and any individual line.
            line = stream.readline(min(4*MIB+1,max_expanded-q["expanded_bytes"]+1))
            if not line:
                break
            q["expanded_bytes"] += len(line)
            q["records"] += 1
            if (q["expanded_bytes"] > max_expanded or len(line)>4*MIB or
                    q["records"] > max_records):
                raise ValueError("Expanded byte, individual line or record cap exceeded.")
            f = json.loads(line, parse_constant=reject_constant)
            if not isinstance(f,dict) or f.get("type") != "Feature":
                raise ValueError("Expected line-delimited GeoJSON Features.")
            p, g = f.get("properties"), f.get("geometry")
            if not isinstance(p,dict) or not isinstance(g,dict):
                raise ValueError("Missing feature properties or geometry object.")
            property_keys.update(p)
            if len(property_keys)>128:
                raise ValueError("Unexpected property schema.")
            kind = g.get("type")
            coords = g.get("coordinates")
            if kind not in ("Polygon","MultiPolygon"):
                raise ValueError("Unexpected geometry type.")
            parts = [coords] if kind == "Polygon" else coords
            structural_valid = True
            if not isinstance(parts,list) or not parts:
                raise ValueError("Unexpected polygon nesting.")
            for part in parts:
                if not isinstance(part,list) or not part:
                    raise ValueError("Unexpected polygon rings.")
                for ring in part:
                    if not isinstance(ring,list):
                        raise ValueError("Unexpected ring structure.")
                    if len(ring)<4 or ring[0]!=ring[-1]:
                        structural_valid = False
                    for point in ring:
                        q["coordinate_pairs"] += 1
                        if q["coordinate_pairs"] > max_pairs:
                            raise ValueError("Coordinate cap exceeded.")
                        if (not isinstance(point,list) or len(point)!=2 or
                                any(type(v) not in (int,float) or not math.isfinite(v) for v in point) or
                                not (-180<=point[0]<=180 and -90<=point[1]<=90)):
                            raise ValueError("Unexpected longitude/latitude coordinate.")
            height = optional(p,"height")
            confidence = optional(p,"confidence",1)
            if not structural_valid:
                q["invalid_geometry"] += 1
                continue
            try:
                geom = shape(g)
                if geom.is_empty or not geom.is_valid or geom.area<=0:
                    q["invalid_geometry"] += 1
                    continue
                digest = hashlib.sha256(geom.wkb).digest()
                if digest in seen:
                    q["exact_duplicate_geometry"] += 1
                    continue
                polygons = [geom] if kind=="Polygon" else geom.geoms
                area = sum(abs(geod.geometry_area_perimeter(orient(poly,sign=1.0))[0])
                           for poly in polygons)
                centroid = geom.centroid
                if not math.isfinite(area) or area<=0:
                    q["invalid_geometry"] += 1
                    continue
            except ShapelyError:
                q["invalid_geometry"] += 1
                continue
            seen.add(digest)
            q["outside_tile_centroid"] += not (30.9375<=centroid.x<=31.640625 and
                                              -25.7998911821<=centroid.y<=-25.1651733687)
            q["usable"] += 1
            areas.append(area)
            w.writerow([q["records"],f"{area:.4f}",f"{centroid.x:.8f}",
                        f"{centroid.y:.8f}",height,confidence])
            if out.tell()>50*MIB:
                raise ValueError("Derived CSV exceeds 50 MiB output safety cap.")
    if not q["records"] or not q["usable"]:
        raise ValueError("No usable building features.")
    from statistics import median
    q.update(source_property_names=sorted(property_keys),
             median_footprint_m2=round(median(areas),4),
             minimum_footprint_m2=round(min(areas),4),
             maximum_footprint_m2=round(max(areas),4),
             summed_footprint_m2=round(math.fsum(areas),4),
             limitations="Imagery-derived footprint detections; not verified houses, floor area, sales, union coverage or ground truth. Centroids are geometric longitude/latitude centroids; exact WKB duplicates only. Optional attribute counts include all source records.")
    return out.getvalue().encode("utf-8"), q

def building_status(root):
    path = root/BUILD_MANIFEST
    if not path.exists():
        return {"dataset_id":"HPI-DATA-004","registered":False}
    m = json.loads(read_bounded(path))
    return {"dataset_id":"HPI-DATA-004","registered":True,**retention_status(m),
            "known_local_paths":[p for p in (BUILD_FILE,BUILD_RAW,BUILD_OUTPUT,BUILD_REPORT,BUILD_MANIFEST)
                                 if (root/p).exists()],
            "note":"Review other copies, chat uploads, sync and backups separately; no deletion performed."}

def import_buildings(root,intake,terms_reviewed,deadline=None,today=None):
    today = today or date.today()
    if not terms_reviewed:
        raise ValueError("Owner must confirm applicable source terms.")
    retention = retention_fields(root,BUILD_MANIFEST,intake,deadline,today,LEGACY_BUILD)
    source = root/BUILD_RAW
    # Require the canonical location, rather than create another raw copy.
    workspace(source.parent)
    raw = read_bounded(source,BUILD_MAX_BYTES)
    digest = sha(raw)
    existing = root/BUILD_MANIFEST
    if existing.exists():
        prior = json.loads(read_bounded(existing))
        if (prior["source_sha256"] != digest or prior["first_intake_date"] != intake.isoformat() or
                prior["do_not_retain_on_or_after"] != retention["do_not_retain_on_or_after"]):
            raise ValueError("Registered source or retention differs; no overwrite or renewal.")
    result, q = building_profile(raw)
    m = {"dataset_id":"HPI-DATA-004","manager_version":"0.3.0",
         "source":"Microsoft Global ML Building Footprints","source_url":BUILD_URL,
         "country":"SouthAfrica","quadkey":"300301302","catalogue_upload_date":"2026-07-24",
         "source_licence":"CDLA Permissive 2.0","source_licence_url":"https://cdla.dev/permissive-2-0/",
         "source_identity_evidence":"Exact catalogue filename and owner-attested download route; first received SHA-256 pinned locally, not an independent publisher checksum.",
         "source_bytes":len(raw),"source_sha256":digest,"raw_path":BUILD_RAW,
         "first_intake_date":intake.isoformat(),"terms_reviewed_by_owner":True,
         **retention,
         "processed_path":BUILD_OUTPUT,"processed_sha256":sha(result),"quality_report":BUILD_REPORT,
         "quality":q}
    planned = [(root/BUILD_OUTPUT,result),(root/BUILD_REPORT,json_bytes(q)),
               (existing,json_bytes(m))]
    for path, content in planned:
        workspace(path.parent)
        check_target(path,content)
    initialise(root)
    for path, content in planned:
        publish(path,content)
    return m

def building_cli(root,args):
    existing = root/BUILD_MANIFEST
    if existing.exists():
        prior = json.loads(read_bounded(existing))
        intake = args.intake_date or date.fromisoformat(prior["first_intake_date"])
        deadline = args.retain_until or stored_deadline(prior)
        reviewed = prior["terms_reviewed_by_owner"] is True
    else:
        if args.intake_date is None or not args.terms_reviewed:
            raise ValueError("First import requires --intake-date and --terms-reviewed; supply --retain-until if source terms require a deadline.")
        intake, deadline, reviewed = args.intake_date,args.retain_until,True
    m = import_buildings(root,intake,reviewed,deadline)
    print(json.dumps({"import":"complete","quality":m["quality"],"status":building_status(root)},indent=2))
    return 0

def building_self_test():
    import gzip
    import copy
    f = {"type":"Feature","properties":{"height":-1,"confidence":0.8},
         "geometry":{"type":"Polygon","coordinates":[[[31,-25.5],[31.0001,-25.5],
             [31.0001,-25.5001],[31,-25.5001],[31,-25.5]]]}}
    def pack(features):
        return gzip.compress(b"".join(json_bytes(x).replace(b"\n",b"")+b"\n" for x in features),mtime=0)
    def rejects(fn):
        try:
            fn()
        except (ValueError,OSError,EOFError,KeyError,TypeError):
            return
        raise AssertionError("Expected building refusal.")
    raw = pack([f,f])
    _, q = building_profile(raw)
    assert q["records"]==2 and q["usable"]==1 and q["exact_duplicate_geometry"]==1
    assert q["missing_height"]==2 and q["missing_confidence"]==0 and q["coordinate_pairs"]==10
    assert 100<q["median_footprint_m2"]<120
    rejects(lambda: building_profile(raw,max_expanded=10))
    rejects(lambda: building_profile(raw,max_records=1))
    rejects(lambda: building_profile(raw,max_pairs=9))
    rejects(lambda: building_profile(raw[:-5]))
    bad = copy.deepcopy(f)
    bad["geometry"]["coordinates"][0][0]=[181,0]
    rejects(lambda: building_profile(pack([bad])))
    with tempfile.TemporaryDirectory() as tmp:
        root=workspace(Path(tmp)/"private")
        initialise(root)
        (root/BUILD_RAW).write_bytes(raw)
        day=date(2026,1,1)
        rejects(lambda: import_buildings(root,day,False,today=day))
        rejects(lambda: import_buildings(root,day,True,day,day))
        rejects(lambda: import_buildings(root,day,True,day+timedelta(days=30),day+timedelta(days=30)))
        m=import_buildings(root,day,True,today=day)
        spec = ("HPI-DATA-004",BUILD_MANIFEST,BUILD_RAW,BUILD_OUTPUT,BUILD_REPORT,BUILD_MAX_BYTES,None)
        assert audit_registered(root,spec,day)["status"] == "integrity checks passed"
        assert m==import_buildings(root,day,True,today=day+timedelta(days=365))
        rejects(lambda: import_buildings(root,day,True,day+timedelta(days=29),day))
        (root/BUILD_OUTPUT).write_text("conflict")
        rejects(lambda: audit_registered(root,spec,day))
        rejects(lambda: import_buildings(root,day,True,today=day))
        assert (root/BUILD_OUTPUT).read_text()=="conflict"
    print("PASS: building streaming caps, geometry, optional attributes, retention and repeat checks.")



OPEN_POLICY = "open-source-terms-v1"
OPEN_RETENTION = "No internal expiry; applicable source terms and law prevail; no automatic deletion."
LEGACY_RPPI = "Maximum 30 days; shorter terms prevail; owner-approved disposal only; no renewal"
LEGACY_GEO = "Maximum 30 days or shorter applicable terms; no automatic deletion or renewal"
LEGACY_BUILD = "Maximum 30 days or shorter terms; no automatic deletion or renewal"

def stored_deadline(manifest):
    value = manifest["do_not_retain_on_or_after"]
    return date.fromisoformat(value) if value is not None else None

def retention_fields(root, path, intake, deadline, today, legacy_text):
    if intake > today:
        raise ValueError("Future intake date.")
    target = root/path
    if target.exists():
        prior = json.loads(read_bounded(target))
        old = stored_deadline(prior)
        if prior["first_intake_date"] != intake.isoformat() or (deadline is not None and deadline != old):
            raise ValueError("Registered intake or source deadline differs; no silent change.")
        if old is not None and today >= old:
            raise ValueError("Retention deadline reached; review applicable terms.")
        fields = {"do_not_retain_on_or_after":prior["do_not_retain_on_or_after"],
                  "retention":prior["retention"]}
        if prior.get("retention_policy") == OPEN_POLICY:
            fields["retention_policy"] = OPEN_POLICY
            if "previous_internal_deadline" in prior:
                fields["previous_internal_deadline"] = prior["previous_internal_deadline"]
        elif prior["retention"] != legacy_text or old is None:
            raise ValueError("Unrecognised retention policy.")
        return fields
    if deadline is not None and (deadline <= intake or today >= deadline):
        raise ValueError("Invalid or expired source deadline.")
    return {"do_not_retain_on_or_after":deadline.isoformat() if deadline else None,
            "retention":OPEN_RETENTION,"retention_policy":OPEN_POLICY}

def retention_status(manifest):
    deadline = stored_deadline(manifest)
    return {"deadline":deadline.isoformat() if deadline else None,
            "retention_due_or_expired":deadline is not None and date.today() >= deadline,
            "retention_policy":manifest.get("retention_policy","legacy"),
            "note_retention":"Applicable source terms and law prevail."}

def remove_internal_deadlines(root, today=None):
    """Explicit owner-authorised metadata migration of the three known imports only."""
    today = today or date.today()
    specs = [(MANIFEST,"HPI-DATA-002",RAW,LEGACY_RPPI,"catalogue_licence","CC BY; version not specified"),
             (GEO_MANIFEST,"HPI-DATA-003",GEO_RAW,LEGACY_GEO,"source_licence","CC BY 3.0 IGO (publisher metadata)"),
             (BUILD_MANIFEST,"HPI-DATA-004",BUILD_RAW,LEGACY_BUILD,"source_licence","CDLA Permissive 2.0")]
    plan, results = [], []
    for name, sid, raw, legacy, licence_field, licence in specs:
        path = root/name
        workspace(path.parent)
        check_path(path)
        if not path.exists():
            results.append({"dataset_id":sid,"result":"not registered"})
            continue
        before = read_bounded(path)
        m = json.loads(before)
        if (m["dataset_id"] != sid or m["raw_path"] != raw or
                m[licence_field] != licence or m["terms_reviewed_by_owner"] is not True):
            raise ValueError("Unexpected manifest identity/terms: "+sid)
        if m.get("retention_policy") == OPEN_POLICY:
            results.append({"dataset_id":sid,"result":"already migrated",**retention_status(m)})
            continue
        # Only the actual 26 Nov registrations with the documented project cap.
        # Never clear any different or shorter deadline by inference.
        if (m["first_intake_date"] != "2026-11-26" or
                m["do_not_retain_on_or_after"] != "2026-12-26" or
                m["retention"] != legacy):
            results.append({"dataset_id":sid,"result":"unchanged: other or source-specific deadline"})
            continue
        if today >= stored_deadline(m):
            raise ValueError("Old deadline already reached; review source terms before migration.")
        m["previous_internal_deadline"] = m["do_not_retain_on_or_after"]
        m["do_not_retain_on_or_after"] = None
        m["retention"] = OPEN_RETENTION
        m["retention_policy"] = OPEN_POLICY
        plan.append((path,before,json_bytes(m)))
        results.append({"dataset_id":sid,"result":"internal deadline removed",**retention_status(m)})
    # All identities checked before writes. Each metadata replacement is atomic.
    for path,before,after in plan:
        check_path(path)
        if read_bounded(path) != before:
            raise ValueError("Manifest changed during migration: "+path.name)
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent,prefix=".retention-",delete=False) as f:
                tmp = Path(f.name)
                f.write(after)
                f.flush()
                os.fsync(f.fileno())
            check_path(path)
            if read_bounded(path) != before:
                raise ValueError("Manifest changed during migration: "+path.name)
            os.replace(tmp,path)
        finally:
            if tmp is not None and tmp.exists():
                tmp.unlink()
    return results

def retention_self_test():
    day = date(2026,11,26)
    with tempfile.TemporaryDirectory() as tmp:
        root = workspace(Path(tmp)/"private")
        initialise(root)
        specs = [(MANIFEST,"HPI-DATA-002",RAW,LEGACY_RPPI,"catalogue_licence","CC BY; version not specified"),
                 (GEO_MANIFEST,"HPI-DATA-003",GEO_RAW,LEGACY_GEO,"source_licence","CC BY 3.0 IGO (publisher metadata)"),
                 (BUILD_MANIFEST,"HPI-DATA-004",BUILD_RAW,LEGACY_BUILD,"source_licence","CDLA Permissive 2.0")]
        for i,(path,sid,raw,legacy,field,licence) in enumerate(specs):
            m = {"dataset_id":sid,"raw_path":raw,field:licence,"terms_reviewed_by_owner":True,
                 "first_intake_date":day.isoformat(),"do_not_retain_on_or_after":"2026-12-26" if i != 1 else "2026-12-01",
                 "retention":legacy,"source_sha256":"fixture","quality":{"fixture":True}}
            publish(root/path,json_bytes(m))
        original = (root/GEO_MANIFEST).read_bytes()
        result = remove_internal_deadlines(root,day)
        assert result[0]["deadline"] is None and result[2]["deadline"] is None
        assert (root/GEO_MANIFEST).read_bytes() == original
        m = json.loads(read_bounded(root/MANIFEST))
        assert m["source_sha256"]=="fixture" and m["previous_internal_deadline"]=="2026-12-26"
        assert retention_fields(root,MANIFEST,day,None,day+timedelta(days=365),LEGACY_RPPI)["do_not_retain_on_or_after"] is None
        before = [(root/p).read_bytes() for p,*_ in specs]
        remove_internal_deadlines(root,day)
        assert before == [(root/p).read_bytes() for p,*_ in specs]
        assert retention_fields(root,"new.json",day,day+timedelta(days=90),day,LEGACY_GEO)["do_not_retain_on_or_after"]=="2027-02-24"
    print("PASS: open retention migration, preservation, repeat and source-specific deadline.")




# HPI-DATA-005: explicitly approved noncommercial Stats SA reference, offline only.
CODE_FILE = "06. Census 2022 Code lists.pdf"
CODE_URL = "https://isibaloweb.statssa.gov.za/metadata/CENSUS/2022/06.%20Census%202022%20Code%20lists.pdf"
CODE_RAW = "02_Raw_Data/" + CODE_FILE
CODE_MANIFEST = "01_Source_Catalogue/HPI-DATA-005.json"
CODE_OUTPUT = "03_Processed_Data/HPI-DATA-005/district_codes.csv"
CODE_REPORT = "07_Reports/HPI-DATA-005_quality.json"
CODE_MAX_BYTES = 5*MIB
CODE_POLICY = "stats-sa-noncommercial-v1"
CODE_RETENTION = "Private noncommercial reference; source terms and law prevail; no automatic deletion."
CODE_PDF_VERSION = "7.2.0"

def code_profile(raw):
    import re
    try:
        from pypdf import PdfReader, __version__
        from pypdf.errors import PdfReadError
    except ImportError as exc:
        raise ValueError("Install the tested dependency: python -m pip install pypdf==" + CODE_PDF_VERSION) from exc
    if __version__ != CODE_PDF_VERSION:
        raise ValueError("Use tested pypdf==" + CODE_PDF_VERSION)
    if len(raw) > CODE_MAX_BYTES or not raw.startswith(b"%PDF-"):
        raise ValueError("Expected bounded original PDF.")
    try:
        pdf = PdfReader(io.BytesIO(raw), strict=True)
        if pdf.is_encrypted or len(pdf.pages) != 10:
            raise ValueError("Expected unencrypted ten-page Census 2022 codebook.")
        def words(page):
            return " ".join(pdf.pages[page].extract_text().split()).casefold()
        cover, rights = words(0), words(1)
        if not all(x in cover for x in ("census 2022 metadata", "code lists", "29 august 2024")):
            raise ValueError("Unexpected cover/version.")
        if not all(x in rights for x in ("statistics south africa", "03-01-47", "independent processing", "prior permission", "sold or offered for sale")):
            raise ValueError("Unexpected publisher/report/terms; review manually.")
        layout = pdf.pages[3].extract_text(extraction_mode="layout")
    except PdfReadError as exc:
        raise ValueError("PDF could not be parsed; no import.") from exc
    if "district and metropolitan municipality names and codes" not in " ".join(layout.split()).casefold():
        raise ValueError("Expected district/metro table on PDF page 4.")
    row = re.compile(r"^(.+?)\s+(DC[1-9]\d?|[A-Z]{3})\s+(.+?)\s+(DC[1-9]\d?|[A-Z]{3})$")
    entries = []
    for line in layout.splitlines():
        match = row.fullmatch(line.strip())
        if match:
            for name, code in ((match[1],match[2]),(match[3],match[4])):
                name = " ".join(name.split())
                level = "district" if code.startswith("DC") else "metro"
                if not name or not name[0].isalpha() or ("metropolitan area" in name.casefold()) != (level=="metro"):
                    raise ValueError("Unexpected name/level in district table.")
                entries.append((code,name,level))
    if (len(entries)!=52 or len({e[0] for e in entries})!=52 or
            len({e[1].casefold() for e in entries})!=52 or
            sum(e[2]=="district" for e in entries)!=44 or sum(e[2]=="metro" for e in entries)!=8):
        raise ValueError("Expected 26 two-column rows, 52 unique names/codes, 44 districts and 8 metros; no partial import.")
    out = io.StringIO(newline="")
    w = csv.writer(out,lineterminator="\n")
    w.writerow(["municipality_code","municipality_name_source","geography_level","geography_reference","source_page"])
    for code,name,level in entries:
        w.writerow([code,name,level,"Census 2022",4])
    q = {"entries":52,"districts":44,"metros":8,"duplicate_codes":0,"duplicate_names":0,
         "pdf_pages":10,"source_page":4,"crosswalk_verified":False,
         "limitations":"Independent Stats SA code reference only; no parcel identity, local-municipality table, geometry or temporal equivalence."}
    return out.getvalue().encode("utf-8"),q

def code_status(root):
    p = root/CODE_MANIFEST
    if not p.exists():
        return {"dataset_id":"HPI-DATA-005","registered":False}
    m = json.loads(read_bounded(p))
    return {"dataset_id":"HPI-DATA-005","registered":True,**retention_status(m),
            "known_local_paths":[x for x in (CODE_RAW,CODE_OUTPUT,CODE_REPORT,CODE_MANIFEST) if (root/x).exists()]}

def import_codes(root,intake,terms_reviewed,confirm,deadline=None,today=None):
    today = today or date.today()
    if not terms_reviewed or intake>today or (deadline is not None and (deadline<=intake or today>=deadline)):
        raise ValueError("Applicable terms, actual intake and retention must be confirmed.")
    raw = read_bounded(root/CODE_RAW,CODE_MAX_BYTES)
    digest = sha(raw)
    existing = root/CODE_MANIFEST
    if existing.exists():
        prior = json.loads(read_bounded(existing))
        old_deadline = stored_deadline(prior)
        if (prior["source_sha256"]!=digest or prior["first_intake_date"]!=intake.isoformat() or
                (deadline is not None and deadline!=old_deadline) or
                (old_deadline is not None and today>=old_deadline) or
                prior.get("retention_policy")!=CODE_POLICY or prior.get("visual_page_reviewed_by_owner") is not True):
            raise ValueError("Registered source, retention or review differs; no overwrite/renewal.")
        deadline = old_deadline
    result,q = code_profile(raw)
    if not existing.exists() and not confirm(result):
        raise ValueError("Visual comparison not confirmed; no reference registered.")
    q["visual_page_reviewed_by_owner"] = True
    m = {"dataset_id":"HPI-DATA-005","manager_version":"0.4.0",
         "source":"Statistics South Africa, Census 2022 Metadata (Code lists), report 03-01-47",
         "source_url":CODE_URL,"publication_date":"2024-08-29","source_licence":"Stats SA 2024 report page 2 terms: attribution and independent processing; no sale without prior permission",
         "attribution":"Statistics South Africa (2024), Census 2022 Metadata, report 03-01-47, p. 4; independent processing by HPI.",
         "source_identity_evidence":"Official URL, validated document identity and page count, owner-attested download and visual comparison; first raw hash pinned locally, no publisher checksum.",
         "source_bytes":len(raw),"source_sha256":digest,"raw_path":CODE_RAW,
         "first_intake_date":intake.isoformat(),"terms_reviewed_by_owner":True,
         "visual_page_reviewed_by_owner":True,"retention_policy":CODE_POLICY,"retention":CODE_RETENTION,
         "do_not_retain_on_or_after":deadline.isoformat() if deadline else None,
         "processed_path":CODE_OUTPUT,"processed_sha256":sha(result),"quality_report":CODE_REPORT,"quality":q}
    planned = [(root/CODE_OUTPUT,result),(root/CODE_REPORT,json_bytes(q)),(existing,json_bytes(m))]
    for path,content in planned:
        check_target(path,content)
    for path,content in planned:
        publish(path,content)
    return m

def code_cli(root,args):
    prior = json.loads(read_bounded(root/CODE_MANIFEST)) if (root/CODE_MANIFEST).exists() else None
    intake = args.intake_date or (date.fromisoformat(prior["first_intake_date"]) if prior else
                                  date.fromisoformat(input("Actual PDF download date (YYYY-MM-DD): ").strip()))
    reviewed = args.terms_reviewed or (prior["terms_reviewed_by_owner"] is True if prior else
                                      input("Read page 2; confirm private noncommercial processing, attribution and source terms (yes/no): ").strip().lower()=="yes")
    def confirm(data):
        print("\nPrivate preview: compare every name/code against PDF page 4, including both columns.")
        print(data.decode("utf-8"))
        return input("All 52 name/code pairs match the visual source page exactly (yes/no): ").strip().lower()=="yes"
    m = import_codes(root,intake,reviewed,confirm,args.retain_until)
    print(json.dumps({"import":"complete","quality":m["quality"],"status":code_status(root)},indent=2))
    return 0

def code_fixture_pdf(duplicate=False, wrong_terms=False):
    # Construct an invented PDF with a plain Helvetica text layout; no source data in CI.
    rows = [f"Invented district {i:<2} DC{i:<2}       Invented district {i+22:<2} DC{i+22:<2}" for i in range(1,23)]
    rows += [f"Invented metro {i} Metropolitan Area A{chr(65+i)}A       Invented metro {i+4} Metropolitan Area B{chr(65+i)}B" for i in range(4)]
    if duplicate:
        rows[-1] = rows[-2]
    pages = [["Census 2022 Metadata (Code lists) 29 August 2024"],
             ["Statistics South Africa 03-01-47", "independent processing; sold or offered for sale without prior permission" if not wrong_terms else "changed terms"],
             ["Contents"],["District and metropolitan municipality names and codes"]+rows]+[["Invented page"] for _ in range(6)]
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               ("<< /Type /Pages /Count 10 /Kids ["+" ".join(f"{4+2*i} 0 R" for i in range(10))+"] >>").encode(),
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    for i,lines in enumerate(pages):
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 792 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {5+2*i} 0 R >>".encode())
        stream = ("BT /F1 9 Tf 30 750 Td 15 TL "+" T* ".join("("+x.replace("(","\\(").replace(")","\\)")+") Tj" for x in lines)+" ET").encode()
        objects.append(b"<< /Length "+str(len(stream)).encode()+b" >>\nstream\n"+stream+b"\nendstream")
    buf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(buf))
        buf.extend(f"{i} 0 obj\n".encode()+obj+b"\nendobj\n")
    xref = len(buf)
    buf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for pos in offsets[1:]:
        buf.extend(f"{pos:010d} 00000 n \n".encode())
    buf.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(buf)

def code_self_test():
    day=date(2026,11,26)
    with tempfile.TemporaryDirectory() as tmp:
        root=workspace(Path(tmp)/"private")
        initialise(root)
        raw=code_fixture_pdf()
        publish(root/CODE_RAW,raw)
        data,q=code_profile(raw)
        assert q["entries"]==52 and q["districts"]==44 and q["metros"]==8
        for bad in (b"not PDF",code_fixture_pdf(duplicate=True),code_fixture_pdf(wrong_terms=True)):
            try:
                code_profile(bad)
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid PDF or table accepted")
        try:
            import_codes(root,day,True,lambda _:False,today=day)
        except ValueError:
            pass
        else:
            raise AssertionError("Unreviewed table accepted")
        assert not (root/CODE_MANIFEST).exists() and not (root/CODE_OUTPUT).exists()
        first=import_codes(root,day,True,lambda x:x==data,today=day)
        assert first==import_codes(root,day,True,lambda _:False,today=day)
        assert audit_registered(root,("HPI-DATA-005",CODE_MANIFEST,CODE_RAW,CODE_OUTPUT,CODE_REPORT,CODE_MAX_BYTES,None),today=day)["status"]=="integrity checks passed"
        assert first["source_sha256"]==sha(raw) and first["quality"]["crosswalk_verified"] is False
    print("PASS: invented ten-page PDF, 52-code validation, refusal, visual gate, repeat and integrity audit.")


# Live inventory is derived from manifests, not the historical starter CSV.
def audit_registered(root, spec, today=None):
    sid, manifest_path, raw_path, output_path, report_path, raw_limit, pinned = spec
    today = today or date.today()
    path = root/manifest_path
    workspace(path.parent)
    check_path(path)
    if not path.exists():
        return {"dataset_id":sid,"status":"not registered"}
    m = json.loads(read_bounded(path))
    if (m["dataset_id"] != sid or m["raw_path"] != raw_path or
            m["processed_path"] != output_path or m["quality_report"] != report_path or
            m["terms_reviewed_by_owner"] is not True):
        raise ValueError("Manifest identity, path or terms attestation differs.")
    intake = date.fromisoformat(m["first_intake_date"])
    deadline = stored_deadline(m)
    if intake > today or (deadline is not None and (deadline <= intake or today >= deadline)):
        raise ValueError("Invalid intake or expired applicable deadline.")
    legacy = {"HPI-DATA-002":LEGACY_RPPI,"HPI-DATA-003":LEGACY_GEO,"HPI-DATA-004":LEGACY_BUILD,"HPI-DATA-005":CODE_RETENTION}[sid]
    if sid == "HPI-DATA-005":
        if (m.get("retention_policy") != CODE_POLICY or m["retention"] != CODE_RETENTION or
                m.get("visual_page_reviewed_by_owner") is not True):
            raise ValueError("Unexpected code reference policy or visual review.")
    elif m.get("retention_policy") == OPEN_POLICY:
        if m["retention"] != OPEN_RETENTION:
            raise ValueError("Unexpected open retention policy wording.")
    elif m["retention"] != legacy or deadline is None:
        raise ValueError("Unexpected legacy retention policy.")
    def measured(relative, cap):
        p = root/relative
        workspace(p.parent)
        check_path(p)
        if not p.is_file():
            raise ValueError("Registered file missing: "+relative)
        digest = hashlib.sha256()
        count = 0
        with p.open("rb") as f:
            while True:
                chunk = f.read(min(MIB,cap-count+1))
                if not chunk:
                    break
                count += len(chunk)
                if count > cap:
                    raise ValueError("Registered file over cap: "+relative)
                digest.update(chunk)
        return count,digest.hexdigest()
    raw_bytes, raw_hash = measured(raw_path,raw_limit)
    output_bytes, output_hash = measured(output_path,50*MIB)
    if (raw_bytes != m["source_bytes"] or raw_hash != m["source_sha256"] or
            (pinned is not None and raw_hash != pinned)):
        raise ValueError("Raw size or checksum mismatch.")
    if output_hash != m["processed_sha256"]:
        raise ValueError("Processed checksum mismatch.")
    if json.loads(read_bounded(root/report_path)) != m["quality"]:
        raise ValueError("Quality report differs from registered metadata.")
    return {"dataset_id":sid,"status":"integrity checks passed",
            "source_bytes":raw_bytes,"processed_bytes":output_bytes,
            "deadline":m["do_not_retain_on_or_after"],"quality":m["quality"]}

def audit_workspace(root):
    specs = [
        ("HPI-DATA-002",MANIFEST,RAW,OUTPUT,REPORT,10*MIB,APPROVED_SHA),
        ("HPI-DATA-003",GEO_MANIFEST,GEO_RAW,GEO_OUTPUT,GEO_REPORT,10*MIB,GEO_SHA),
        ("HPI-DATA-004",BUILD_MANIFEST,BUILD_RAW,BUILD_OUTPUT,BUILD_REPORT,BUILD_MAX_BYTES,None),
        ("HPI-DATA-005",CODE_MANIFEST,CODE_RAW,CODE_OUTPUT,CODE_REPORT,CODE_MAX_BYTES,None),
    ]
    results = []
    for spec in specs:
        try:
            results.append(audit_registered(root,spec))
        except (ValueError,KeyError,TypeError,OSError,AttributeError) as exc:
            results.append({"dataset_id":spec[0],"status":"review required","reason":str(exc)})
    print(json.dumps({"audit":"read-only","datasets":results,
        "limitations":"Checks known registered files only; not ground truth, source authentication, rights, backups, sync or full copy inventory. No files changed."},indent=2))
    return 0 if all(x["status"]=="integrity checks passed" for x in results) else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path.cwd())
    p.add_argument("--dataset",choices=("HPI-DATA-002","HPI-DATA-003","HPI-DATA-004","HPI-DATA-005"),default="HPI-DATA-002")
    p.add_argument("--retain-until",type=date.fromisoformat)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--status",action="store_true")
    p.add_argument("--audit-workspace",action="store_true")
    p.add_argument("--remove-internal-deadlines",action="store_true")
    p.add_argument("--init-only",action="store_true")
    p.add_argument("--intake-date",type=date.fromisoformat)
    p.add_argument("--terms-reviewed",action="store_true")
    args = p.parse_args()
    try:
        if args.self_test:
            self_test()
            district_self_test()
            building_self_test()
            retention_self_test()
            code_self_test()
            return 0
        root = workspace(args.root)
        if args.audit_workspace:
            if args.remove_internal_deadlines or args.init_only or args.status:
                raise ValueError("Workspace audit must be a standalone read-only action.")
            return audit_workspace(root)
        if args.remove_internal_deadlines:
            print(json.dumps(remove_internal_deadlines(root),indent=2))
            return 0
        if args.status:
            print(json.dumps(code_status(root) if args.dataset == "HPI-DATA-005" else building_status(root) if args.dataset == "HPI-DATA-004" else district_status(root) if args.dataset == "HPI-DATA-003" else status(root),indent=2))
            return 0
        initialise(root)
        if args.init_only:
            print("Workspace initialised; existing files preserved.")
            return 0
        if args.dataset == "HPI-DATA-005":
            return code_cli(root,args)
        if args.dataset == "HPI-DATA-004":
            return building_cli(root,args)
        if args.dataset == "HPI-DATA-003":
            return district_cli(root,args)
        existing = root / MANIFEST
        if existing.exists():
            prior = json.loads(read_bounded(existing))
            intake = args.intake_date or date.fromisoformat(prior["first_intake_date"])
            reviewed = prior["terms_reviewed_by_owner"] is True or args.terms_reviewed
        else:
            intake = args.intake_date or date.fromisoformat(input("Actual first download date (YYYY-MM-DD): ").strip())
            reviewed = args.terms_reviewed or input("Confirm applicable terms permit this private import and retention (yes/no): ").strip().lower()=="yes"
        manifest = import_rppi(root,intake,reviewed,deadline=args.retain_until)
        print(json.dumps({"import":"complete","quality":manifest["quality"],"status":status(root)},indent=2))
        return 0
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError, OSError, EOFError, InvalidOperation, zipfile.BadZipFile) as exc:
        print("STOP:",str(exc))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
