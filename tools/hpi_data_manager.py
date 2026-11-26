"""HPI data workspace manager. Offline by default; explicit bounded Treasury intake only. No deletion or cloud operations."""
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
    return fixture_pdf(pages)

def fixture_pdf(pages):
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               (f"<< /Type /Pages /Count {len(pages)} /Kids ["+" ".join(f"{4+2*i} 0 R" for i in range(len(pages)))+"] >>").encode(),
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
    legacy = {"HPI-DATA-002":LEGACY_RPPI,"HPI-DATA-003":LEGACY_GEO,"HPI-DATA-004":LEGACY_BUILD,"HPI-DATA-005":CODE_RETENTION,"HPI-DATA-006":MARKET_RETENTION,"HPI-DATA-007":TREASURY_RETENTION,"HPI-DATA-008":CENSUS_RETENTION}[sid]
    if sid == "HPI-DATA-008":
        if (m.get("retention_policy") != CENSUS_POLICY or m["retention"] != CENSUS_RETENTION or
                m.get("visual_page_reviewed_by_owner") is not True):
            raise ValueError("Unexpected Census retention policy or visual review.")
    elif sid == "HPI-DATA-007":
        if m.get("retention_policy")!=TREASURY_POLICY or m["retention"]!=TREASURY_RETENTION:
            raise ValueError("Unexpected Treasury retention policy.")
    elif sid == "HPI-DATA-006":
        if (m.get("retention_policy") != MARKET_POLICY or m["retention"] != MARKET_RETENTION or
                m.get("visual_page_reviewed_by_owner") is not True):
            raise ValueError("Unexpected market reference policy or visual review.")
    elif sid == "HPI-DATA-005":
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
        ("HPI-DATA-006",MARKET_MANIFEST,MARKET_RAW,MARKET_OUTPUT,MARKET_REPORT,MARKET_MAX,None),
        treasury_spec(),
        census_spec(),
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



# P0-GEO-CROSSWALK: read-only candidates, not a confirmed mapping.
GEO_INDEX_HEADER = ["shape_id","source_name","source_iso","country","administrative_level",
                    "reference_year","geometry_type","coordinate_pairs","min_longitude",
                    "min_latitude","max_longitude","max_latitude","official_municipality_code"]
CODE_INDEX_HEADER = ["municipality_code","municipality_name_source","geography_level",
                     "geography_reference","source_page"]

def crosswalk_rows(data, header):
    reader = csv.reader(io.StringIO(data.decode("utf-8"), newline=""), strict=True)
    if next(reader, None) != header:
        raise ValueError("Unexpected registered reference header.")
    rows = []
    for row in reader:
        if len(row) != len(header) or len(rows) >= 52:
            raise ValueError("Unexpected reference row width or count.")
        rows.append(dict(zip(header,row)))
    if len(rows) != 52:
        raise ValueError("Expected exactly 52 reference rows.")
    return rows

def crosswalk_candidates(geo_data, code_data):
    import re
    geo = crosswalk_rows(geo_data,GEO_INDEX_HEADER)
    codes = crosswalk_rows(code_data,CODE_INDEX_HEADER)
    def normal(name):
        # No punctuation removal, suffix removal, translation or alias expansion.
        return " ".join(name.split()).casefold()
    for row in geo:
        if (not row["shape_id"].startswith("47623444B") or not normal(row["source_name"]) or
                row["country"]!="ZAF" or row["administrative_level"]!="ADM2" or
                row["reference_year"]!="2020" or row["official_municipality_code"]):
            raise ValueError("Unexpected ADM2 identity, vintage, or pre-existing official code.")
    for row in codes:
        key = row["municipality_code"]
        level = row["geography_level"]
        valid_code = (re.fullmatch(r"DC[1-9]\d?",key) if level=="district" else
                      re.fullmatch(r"[A-Z]{3}",key) if level=="metro" else None)
        if (not valid_code or not normal(row["municipality_name_source"]) or
                row["geography_reference"]!="Census 2022" or row["source_page"]!="4"):
            raise ValueError("Unexpected official code, level, vintage or provenance.")
    for rows,key,name in ((geo,"shape_id","source_name"),(codes,"municipality_code","municipality_name_source")):
        if len({x[key] for x in rows})!=52 or len({x[name] for x in rows})!=52:
            raise ValueError("Duplicate source identifier or original name; no comparison.")
    if sum(x["geography_level"]=="district" for x in codes)!=44 or sum(x["geography_level"]=="metro" for x in codes)!=8:
        raise ValueError("Unexpected district/metro counts.")
    def grouped(rows,name):
        groups = {}
        for row in rows:
            groups.setdefault(normal(row[name]),[]).append(row)
        return groups
    g,c = grouped(geo,"source_name"),grouped(codes,"municipality_name_source")
    matches,ambiguities,missing_geo,missing_code=[],[],[],[]
    matched_geo,matched_code,ambiguous_geo,ambiguous_code=set(),set(),set(),set()
    for key in sorted(set(g)|set(c)):
        left,right=g.get(key,[]),c.get(key,[])
        def geo_ref(row):
            return {"shape_id":row["shape_id"],"source_name":row["source_name"],"reference_year":2020,"source_level":"ADM2"}
        def code_ref(row):
            return {"municipality_code":row["municipality_code"],"source_name":row["municipality_name_source"],"reference":"Census 2022","source_level":row["geography_level"]}
        if len(left)>1 or len(right)>1:
            ambiguities.append({"normalised_name":key,"geometry_candidates":[geo_ref(x) for x in left],"code_candidates":[code_ref(x) for x in right],"reason":"normalised-name collision; abstain"})
            ambiguous_geo.update(x["shape_id"] for x in left)
            ambiguous_code.update(x["municipality_code"] for x in right)
        elif left and right:
            x,y=left[0],right[0]
            matches.append({"geometry":geo_ref(x),"official_reference":code_ref(y),"status":"exact_name_candidate_only"})
            matched_geo.add(x["shape_id"])
            matched_code.add(y["municipality_code"])
        elif left:
            missing_geo.append(geo_ref(left[0]))
        else:
            missing_code.append(code_ref(right[0]))
    if len(matches)+len(ambiguous_geo)+len(missing_geo)!=52 or len(matches)+len(ambiguous_code)+len(missing_code)!=52:
        raise ValueError("Candidate accounting mismatch.")
    return {"summary":{"geometry_rows":52,"official_code_rows":52,"exact_name_candidates":len(matches),
                       "ambiguous_name_groups":len(ambiguities),"ambiguous_geometry_rows":len(ambiguous_geo),
                       "ambiguous_code_rows":len(ambiguous_code),"unmatched_geometry_rows":len(missing_geo),
                       "unmatched_code_rows":len(missing_code),
                       "district_candidates":sum(x["official_reference"]["source_level"]=="district" for x in matches),
                       "metro_candidates":sum(x["official_reference"]["source_level"]=="metro" for x in matches),
                       "crosswalk_verified":False,"boundary_equivalence_verified":False,
                       "independent_district_metro_classification_verified":False},
            "exact_name_candidates":matches,"ambiguous_groups":ambiguities,
            "unmatched_geometry":missing_geo,"unmatched_official_codes":missing_code}

def crosswalk_report(root,today=None,geo_pin=GEO_SHA):
    root=workspace(root)
    specs=[("HPI-DATA-003",GEO_MANIFEST,GEO_RAW,GEO_OUTPUT,GEO_REPORT,10*MIB,geo_pin),
           ("HPI-DATA-005",CODE_MANIFEST,CODE_RAW,CODE_OUTPUT,CODE_REPORT,CODE_MAX_BYTES,None)]
    payloads,provenance=[],[]
    for spec in specs:
        sid,mp,rp,op,qp,cap,pin=spec
        before=read_bounded(root/mp)
        m=json.loads(before)
        audit=audit_registered(root,spec,today)
        if audit["status"]!="integrity checks passed":
            raise ValueError(sid+" registration missing or incomplete.")
        if sid=="HPI-DATA-003":
            valid=(m.get("reference_year")==2020 and m.get("snapshot")==GEO_SNAPSHOT and
                   m.get("source_url")==GEO_URL and m.get("source_licence")=="CC BY 3.0 IGO (publisher metadata)" and
                   m["quality"].get("features")==52 and m["quality"].get("official_code_crosswalk_verified") is False)
        else:
            valid=(m.get("source_url")==CODE_URL and m.get("publication_date")=="2024-08-29" and
                   m.get("retention_policy")==CODE_POLICY and m["quality"].get("entries")==52 and
                   m["quality"].get("visual_page_reviewed_by_owner") is True and m["quality"].get("crosswalk_verified") is False)
        if not valid or not m.get("attribution"):
            raise ValueError(sid+" source identity, terms or qualification differs.")
        data=read_bounded(root/op,1*MIB)
        if sha(data)!=m["processed_sha256"] or read_bounded(root/mp)!=before:
            raise ValueError(sid+" changed during validation; stop.")
        payloads.append(data)
        provenance.append({"dataset_id":sid,"source":m["source"],"source_url":m["source_url"],
                           "source_sha256":m["source_sha256"],"processed_sha256":m["processed_sha256"],
                           "source_licence":m["source_licence"],"attribution":m["attribution"],
                           "reference":"2020 geography" if sid=="HPI-DATA-003" else "Census 2022",
                           "deadline":m["do_not_retain_on_or_after"],"integrity":"passed"})
    result=crosswalk_candidates(*payloads)
    return {"experiment":"P0-GEO-CROSSWALK","mode":"private read-only terminal report","provenance":provenance,
            **result,"limitations":["Candidate matching uses casefold and whitespace only; no aliases or fuzzy matching.",
            "ADM2 is the shared district/metro tier; HPI-DATA-003 has no independent district-versus-metro type field.",
            "Matching labels do not establish stable identity, temporal equivalence, topology or boundary accuracy.",
            "Stats SA noncommercial/source terms and both source attributions apply; no public redistribution.",
            "No files changed, no network, no geometry operations, no material join or accepted crosswalk."]}

def crosswalk_self_test():
    day=date(2026,11,26)
    def make(header,rows):
        out=io.StringIO(newline="")
        w=csv.writer(out,lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
        return out.getvalue().encode()
    geo,code=[],[]
    for i in range(52):
        level="district" if i<44 else "metro"
        key=f"DC{i+1}" if i<44 else "X"+chr(65+i-44)+"X"
        name=f"Invented district {i}" if i<44 else f"Invented metro {i}"
        geo.append([f"47623444B{i}",name,"","ZAF","ADM2","2020","Polygon","5","0","0","1","1",""])
        code.append([key,name.upper(),level,"Census 2022","4"])
    gb,cb=make(GEO_INDEX_HEADER,geo),make(CODE_INDEX_HEADER,code)
    assert crosswalk_candidates(gb,cb)["summary"]["exact_name_candidates"]==52
    code[0][1]="Different punctuation-name"
    assert crosswalk_candidates(gb,make(CODE_INDEX_HEADER,code))["summary"]["unmatched_geometry_rows"]==1
    code[0][1]=code[1][1].lower()
    q=crosswalk_candidates(gb,make(CODE_INDEX_HEADER,code))["summary"]
    assert q["ambiguous_name_groups"]==1 and q["ambiguous_code_rows"]==2 and q["exact_name_candidates"]==50 and q["unmatched_geometry_rows"]==1
    code[0][1]=code[1][1]
    for bad in (make(CODE_INDEX_HEADER,code),make(CODE_INDEX_HEADER,code[:-1])):
        try:
            crosswalk_candidates(gb,bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid table accepted")
    with tempfile.TemporaryDirectory() as tmp:
        root=workspace(Path(tmp)/"private")
        raw=b"invented geography"
        for sid,mp,rp,op,qp,data,raw_data,extra in (
            ("HPI-DATA-003",GEO_MANIFEST,GEO_RAW,GEO_OUTPUT,GEO_REPORT,gb,raw,
             {"reference_year":2020,"snapshot":GEO_SNAPSHOT,"source_url":GEO_URL,"source_licence":"CC BY 3.0 IGO (publisher metadata)",
              "retention_policy":OPEN_POLICY,"retention":OPEN_RETENTION,"quality":{"features":52,"official_code_crosswalk_verified":False}}),
            ("HPI-DATA-005",CODE_MANIFEST,CODE_RAW,CODE_OUTPUT,CODE_REPORT,cb,b"invented PDF",
             {"publication_date":"2024-08-29","source_url":CODE_URL,"source_licence":"Invented terms",
              "retention_policy":CODE_POLICY,"retention":CODE_RETENTION,"visual_page_reviewed_by_owner":True,
              "quality":{"entries":52,"visual_page_reviewed_by_owner":True,"crosswalk_verified":False}})):
            m={"dataset_id":sid,"source":"Invented fixture","attribution":"Invented fixture","raw_path":rp,
               "processed_path":op,"quality_report":qp,"terms_reviewed_by_owner":True,
               "first_intake_date":day.isoformat(),"do_not_retain_on_or_after":None,"source_bytes":len(raw_data),
               "source_sha256":sha(raw_data),"processed_sha256":sha(data),**extra}
            for p,b in ((rp,raw_data),(op,data),(qp,json_bytes(m["quality"])),(mp,json_bytes(m))):
                publish(root/p,b)
        before={p.relative_to(root):p.read_bytes() for p in root.rglob("*") if p.is_file()}
        report=crosswalk_report(root,day,sha(raw))
        assert report["summary"]["exact_name_candidates"]==52 and report["summary"]["crosswalk_verified"] is False
        assert before=={p.relative_to(root):p.read_bytes() for p in root.rglob("*") if p.is_file()}
        (root/CODE_OUTPUT).write_bytes(cb+b"\n")
        try:
            crosswalk_report(root,day,sha(raw))
        except ValueError:
            pass
        else:
            raise AssertionError("Tampered reference accepted")
    print("PASS: read-only crosswalk, exact candidates, ambiguity, missing/duplicate rows, checksum refusal and unchanged files.")




# Public documentary name variants, approved for candidate comparison only.
# These are independently published municipal names/codes, not private shape IDs.
RENAME_EVIDENCE = "https://census.statssa.gov.za/assets/documents/2022/Census_2022_Municipal_factsheet-Web.pdf"
METRO_EVIDENCE = "https://www.statssa.gov.za/publications/Report-03-01-83/Report-03-01-832022.pdf"
ALIAS_RULES = (
    ("Cacadu","DC10","Sarah Baartman","district","documented_rename",RENAME_EVIDENCE),
    ("Eden","DC4","Garden Route","district","documented_rename",RENAME_EVIDENCE),
    ("Sisonke","DC43","Harry Gwala","district","documented_rename",RENAME_EVIDENCE),
    ("Uthungulu","DC28","King Cetshwayo","district","documented_rename",RENAME_EVIDENCE),
    ("Buffalo City","BUF","Buffalo City Metropolitan Area","metro","metro_name_variant",METRO_EVIDENCE),
    ("City of Cape Town","CPT","City of Cape Town Metropolitan Area","metro","metro_name_variant",METRO_EVIDENCE),
    ("City of Johannesburg","JHB","City of Johannesburg Metropolitan Area","metro","metro_name_variant",METRO_EVIDENCE),
    ("City of Tshwane","TSH","City of Tshwane Metropolitan Area","metro","metro_name_variant",METRO_EVIDENCE),
    ("Ekurhuleni","EKU","City of Ekurhuleni Metropolitan Area","metro","metro_name_variant",METRO_EVIDENCE),
    ("eThekwini","ETH","eThekwini Metropolitan Area","metro","metro_name_variant",METRO_EVIDENCE),
    ("Mangaung","MAN","Mangaung Metropolitan Area","metro","metro_name_variant",METRO_EVIDENCE),
    ("Nelson Mandela Bay","NMA","Nelson Mandela Bay Metropolitan Area","metro","metro_name_variant",METRO_EVIDENCE),
)

def alias_candidates(baseline, rules=ALIAS_RULES):
    q=baseline["summary"]
    expected={"geometry_rows":52,"official_code_rows":52,"exact_name_candidates":40,
              "ambiguous_name_groups":0,"ambiguous_geometry_rows":0,"ambiguous_code_rows":0,
              "unmatched_geometry_rows":12,"unmatched_code_rows":12,
              "district_candidates":40,"metro_candidates":0}
    if any(q.get(k)!=v for k,v in expected.items()):
        raise ValueError("Exact-name baseline changed; review before applying aliases.")
    if any(q.get(k) is not False for k in ("crosswalk_verified","boundary_equivalence_verified",
                                           "independent_district_metro_classification_verified")):
        raise ValueError("Unexpected accepted crosswalk or geography status.")
    if (len(rules)!=12 or len({x[0] for x in rules})!=12 or len({x[1] for x in rules})!=12 or
            len({x[2] for x in rules})!=12 or
            sum(x[3]=="district" and x[4]=="documented_rename" for x in rules)!=4 or
            sum(x[3]=="metro" and x[4]=="metro_name_variant" for x in rules)!=8):
        raise ValueError("Invalid bounded alias allowlist.")
    left,right=baseline["unmatched_geometry"],baseline["unmatched_official_codes"]
    exact=baseline["exact_name_candidates"]
    if len(left)!=12 or len(right)!=12 or len(exact)!=40 or baseline["ambiguous_groups"]:
        raise ValueError("Exact baseline accounting differs.")
    g={x["source_name"]:x for x in left}
    c={x["municipality_code"]:x for x in right}
    exact_g={x["geometry"]["shape_id"] for x in exact}
    exact_c={x["official_reference"]["municipality_code"] for x in exact}
    if (len(g)!=12 or len(c)!=12 or len(exact_g)!=40 or len(exact_c)!=40 or
            len({x["shape_id"] for x in left})!=12 or
            exact_g.intersection(x["shape_id"] for x in left) or exact_c.intersection(c)):
        raise ValueError("Duplicate or previously matched identity; no alias comparison.")
    matched_g,matched_c=set(),set()
    aliases,abstentions=[],[]
    for old,code,new,level,kind,evidence in rules:
        x,y=g.get(old),c.get(code)
        # Exact original source labels required. No fuzzy guessing, even for Buffalo City.
        if x is None or y is None or y["source_name"]!=new or y["source_level"]!=level:
            abstentions.append({"expected_geometry_name":old,"expected_code":code,
                                "expected_reference_name":new,"reason":"exact approved local labels/code/level not all present"})
            continue
        if x["shape_id"] in matched_g or code in matched_c:
            raise ValueError("Alias collision; no comparison.")
        aliases.append({"geometry":x,"official_reference":y,"status":"documentary_alias_candidate_only",
                        "alias_kind":kind,"evidence_url":evidence})
        matched_g.add(x["shape_id"])
        matched_c.add(code)
    ug=[x for x in left if x["shape_id"] not in matched_g]
    uc=[x for x in right if x["municipality_code"] not in matched_c]
    if 40+len(aliases)+len(ug)!=52 or 40+len(aliases)+len(uc)!=52:
        raise ValueError("Alias accounting mismatch.")
    return {"experiment":"P0-GEO-ALIAS","mode":"private read-only terminal report",
            "provenance":baseline["provenance"],"exact_baseline_summary":dict(q),
            "summary":{"geometry_rows":52,"official_code_rows":52,"exact_name_candidates":40,
                       "documentary_alias_candidates":len(aliases),"total_candidates":40+len(aliases),
                       "historical_rename_candidates":sum(x["alias_kind"]=="documented_rename" for x in aliases),
                       "metro_variant_candidates":sum(x["alias_kind"]=="metro_name_variant" for x in aliases),
                       "unmatched_geometry_rows":len(ug),"unmatched_code_rows":len(uc),
                       "abstained_alias_rules":len(abstentions),"ambiguous_name_groups":0,
                       "district_candidates":40+sum(x["official_reference"]["source_level"]=="district" for x in aliases),
                       "metro_candidates":sum(x["official_reference"]["source_level"]=="metro" for x in aliases),
                       "crosswalk_verified":False,"boundary_equivalence_verified":False,
                       "independent_district_metro_classification_verified":False},
            "exact_name_candidates":exact,"documentary_alias_candidates":aliases,
            "abstained_rules":abstentions,"unmatched_geometry":ug,"unmatched_official_codes":uc,
            "limitations":["Only the approved exact documentary name variants are considered; no fuzzy matching.",
                           "The 2020 geometry and Census 2022 reference have different vintages; historical boundary changes remain unverified.",
                           "ADM2 is a shared tier, not independent district/metro classification.",
                           "Both source terms and attribution, including Stats SA noncommercial restrictions, remain binding.",
                           "No files changed, no network, no geometry operations, no accepted mapping or material join."]}

def alias_self_test():
    import copy
    # Invented rows and rules, never actual private source rows.
    def g(i,name):
        return {"shape_id":f"fixture-{i}","source_name":name,"reference_year":2020,"source_level":"ADM2"}
    def c(i,name,level):
        return {"municipality_code":f"fixture-code-{i}","source_name":name,"reference":"Census 2022","source_level":level}
    rules=tuple((f"Old {i}",f"fixture-code-{i}",f"New {i}","district" if i<4 else "metro",
                 "documented_rename" if i<4 else "metro_name_variant","https://example.invalid") for i in range(12))
    q={"geometry_rows":52,"official_code_rows":52,"exact_name_candidates":40,
       "ambiguous_name_groups":0,"ambiguous_geometry_rows":0,"ambiguous_code_rows":0,
       "unmatched_geometry_rows":12,"unmatched_code_rows":12,"district_candidates":40,"metro_candidates":0,
       "crosswalk_verified":False,"boundary_equivalence_verified":False,"independent_district_metro_classification_verified":False}
    baseline={"summary":q,"provenance":[],"ambiguous_groups":[],
              "exact_name_candidates":[{"geometry":g(i,f"Exact {i}"),"official_reference":c(i,f"Exact {i}","district")} for i in range(12,52)],
              "unmatched_geometry":[g(i,f"Old {i}") for i in range(12)],
              "unmatched_official_codes":[c(i,f"New {i}","district" if i<4 else "metro") for i in range(12)]}
    before=copy.deepcopy(baseline)
    report=alias_candidates(baseline,rules)
    assert report["summary"]["total_candidates"]==52 and report["summary"]["historical_rename_candidates"]==4
    assert report["summary"]["metro_variant_candidates"]==8 and report["summary"]["crosswalk_verified"] is False
    assert report["exact_baseline_summary"]==q and baseline==before
    changed=copy.deepcopy(baseline)
    changed["unmatched_geometry"][0]["source_name"]="Unexpected old name"
    changed["unmatched_official_codes"][1]["source_name"]="Unexpected new name"
    result=alias_candidates(changed,rules)["summary"]
    assert result["total_candidates"]==50 and result["abstained_alias_rules"]==2 and result["unmatched_code_rows"]==2
    changed=copy.deepcopy(baseline)
    changed["unmatched_official_codes"][4]["source_level"]="district"
    assert alias_candidates(changed,rules)["summary"]["total_candidates"]==51
    for kind in ("baseline","duplicate","overlap","rules"):
        bad=copy.deepcopy(baseline)
        use_rules=rules
        if kind=="baseline":
            bad["summary"]["exact_name_candidates"]=41
        elif kind=="duplicate":
            bad["unmatched_geometry"][1]["shape_id"]=bad["unmatched_geometry"][0]["shape_id"]
        elif kind=="overlap":
            bad["unmatched_geometry"][0]["shape_id"]=bad["exact_name_candidates"][0]["geometry"]["shape_id"]
        else:
            use_rules=rules[:-1]+(rules[0],)
        try:
            alias_candidates(bad,use_rules)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid alias scope accepted")
    print("PASS: bounded alias candidates, immutable baseline, exact labels, abstention, collision and baseline refusal.")




# HPI-DATA-006: one fixed publication; not a continuation of 002.
MARKET_URL = "https://www.statssa.gov.za/publications/P0160/P0160June2026.pdf"
MARKET_RAW = "02_Raw_Data/P0160June2026.pdf"
MARKET_MANIFEST = "01_Source_Catalogue/HPI-DATA-006.json"
MARKET_OUTPUT = "03_Processed_Data/HPI-DATA-006/metro_index.csv"
MARKET_REPORT = "07_Reports/HPI-DATA-006_quality.json"
MARKET_MAX = 5*MIB
MARKET_POLICY = "stats-sa-p0160-private-v1"
MARKET_RETENTION = "Private noncommercial publication reference; source terms and law prevail; no automatic deletion."
MARKET_NAMES = ("City of Cape Town","City of Johannesburg")
MARKET_MONTHS = ("2025-06","2026-05","2026-06")

def market_growth_compatible(old,new,published):
    # One decimal shown: compare intervals, not a point estimate.
    half=Decimal("0.05")
    if old<=half or new<=half:
        return False
    lo=100*((new-half)/(old+half)-1)
    hi=100*((new+half)/(old-half)-1)
    return lo<=published+half and hi>=published-half

def market_table(layout):
    import re
    flat=" ".join(layout.split()).casefold()
    if not all(x in flat for x in ("table 4","rppi for all metropolitan areas","dec 2020","jun 2025","may 2026","jun 2026","subject to revision")):
        raise ValueError("Expected Table 4, three observation periods, base and revision note on PDF page 6.")
    if not re.search(r"dec 2020\s*=\s*100",flat):
        raise ValueError("Unexpected index base.")
    # Only read Table 4, not similarly named figure labels.
    table=re.split(r"Figure\s+4\b",layout, maxsplit=1,flags=re.I)[0]
    rows=[]
    for name in MARKET_NAMES:
        pattern=r"^\s*"+r"\s+".join(map(re.escape,name.split()))+r"\s+(\d+[,.]\d{2})\s+(\d+[,.]\d)\s+(\d+[,.]\d)\s+(\d+[,.]\d)\s+([+-]?\d+[,.]\d)\s+([+-]?\d+[,.]\d)\s*$"
        hits=re.findall(pattern,table,re.M|re.I)
        if len(hits)!=1:
            raise ValueError("Expected one complete Table 4 row for "+name+"; no partial import.")
        weight,old,prev,now,mom,yoy=(Decimal(x.replace(",",".")) for x in hits[0])
        if not 0<weight<=100 or min(old,prev,now)<=0 or not market_growth_compatible(prev,now,mom) or not market_growth_compatible(old,now,yoy):
            raise ValueError("Invalid weight/index or inconsistent published growth for "+name)
        for month,idx in zip(MARKET_MONTHS,(old,prev,now)):
            rows.append([name,"metro",month,str(idx),"2020-12=100",str(weight),
                         str(mom) if month=="2026-06" else "",str(yoy) if month=="2026-06" else "",
                         "2026-06","2026-11-05",5,6,"4","latest 12 months revisable"])
    out=io.StringIO(newline="")
    w=csv.writer(out,lineterminator="\n")
    w.writerow(["metro_name_source","geography_level","observation_month","index_value","index_base",
                "published_weight_percent","published_mom_percent","published_yoy_percent","release_month",
                "publication_date","printed_page","pdf_page","source_table","revision_caveat"])
    w.writerows(rows)
    q={"metro_rows":2,"index_observations":6,"unique_metro_months":6,"published_change_percentages":4,
       "published_weights":2,"growth_rounding_checks_passed":4,"index_base":"2020-12=100",
       "observation_months":list(MARKET_MONTHS),"publication_date":"2026-11-05","printed_page":5,"pdf_page":6,
       "continuous_time_series":False,"merged_with_002":False,"individual_sales":False}
    return out.getvalue().encode("utf-8"),q

def market_cover(text):
    import re
    cover=" ".join(text.split()).casefold()
    # The actual publisher logo is not extracted as text. Check the printed
    # official domain, release identifier, title/month and embargo date instead.
    if not (re.search(r"\bwww\.statssa\.gov\.za\b",cover) and
            re.search(r"\bstatistical release\s+p0160\s+residential property price index\s+june 2026\b",cover) and
            re.search(r"\bembargoed until:\s+5 november 2026\b",cover)):
        raise ValueError("Unexpected publication or release date; expected official P0160 June 2026 cover and embargo date.")

def market_profile(raw):
    import re
    try:
        from pypdf import PdfReader, __version__
        from pypdf.errors import PdfReadError
    except ImportError as exc:
        raise ValueError("Install the existing tested dependency: pypdf=="+CODE_PDF_VERSION) from exc
    if __version__!=CODE_PDF_VERSION or len(raw)>MARKET_MAX or not raw.startswith(b"%PDF-"):
        raise ValueError("Expected bounded original PDF and tested pypdf version.")
    try:
        pdf=PdfReader(io.BytesIO(raw),strict=True)
        if pdf.is_encrypted or len(pdf.pages)!=12:
            raise ValueError("Unexpected release page count or encryption; expected twelve pages.")
        market_cover(pdf.pages[0].extract_text())
        rights=" ".join(pdf.pages[11].extract_text().split()).casefold()
        if not all(x in rights for x in ("copyright on this publication","acknowledge stats sa","own processing")):
            raise ValueError("Unexpected printed page 11 source terms; review before import.")
        data,q=market_table(pdf.pages[5].extract_text(extraction_mode="layout"))
    except PdfReadError as exc:
        raise ValueError("PDF parsing failed; no registration.") from exc
    q["pdf_pages"]=len(pdf.pages)
    return data,q

def market_status(root):
    path=root/MARKET_MANIFEST
    if not path.exists():
        return {"dataset_id":"HPI-DATA-006","registered":False}
    m=json.loads(read_bounded(path))
    return {"dataset_id":"HPI-DATA-006","registered":True,**retention_status(m),
            "known_local_paths":[x for x in (MARKET_RAW,MARKET_OUTPUT,MARKET_REPORT,MARKET_MANIFEST) if (root/x).exists()]}

def import_market(root,intake,terms_reviewed,confirm,deadline=None,today=None):
    today=today or date.today()
    if not terms_reviewed or not date(2026,11,5)<=intake<=today or (deadline is not None and (deadline<=intake or today>=deadline)):
        raise ValueError("Confirm applicable terms and actual valid intake/retention dates.")
    raw=read_bounded(root/MARKET_RAW,MARKET_MAX)
    digest=sha(raw)
    existing=root/MARKET_MANIFEST
    if existing.exists():
        prior=json.loads(read_bounded(existing))
        old_deadline=stored_deadline(prior)
        if (prior["source_sha256"]!=digest or prior["first_intake_date"]!=intake.isoformat() or
                (deadline is not None and deadline!=old_deadline) or
                (old_deadline is not None and today>=old_deadline) or
                prior.get("retention_policy")!=MARKET_POLICY or prior.get("visual_page_reviewed_by_owner") is not True):
            raise ValueError("Registered source or retention differs; no overwrite/renewal.")
        deadline=old_deadline
    data,q=market_profile(raw)
    if not existing.exists() and not confirm(data):
        raise ValueError("Visual verification not confirmed; no registration.")
    q["visual_page_reviewed_by_owner"]=True
    m={"dataset_id":"HPI-DATA-006","manager_version":"0.5.0","source":"Statistics South Africa, P0160 June 2026",
       "source_url":MARKET_URL,"publication_date":"2026-11-05",
       "source_licence":"Stats SA publication printed page 11: attribution and identification of independent processing; private noncommercial project scope",
       "attribution":"Statistics South Africa, Residential Property Price Index, June 2026, P0160, 5 November 2026, Table 4; independently processed by HPI.",
       "source_identity_evidence":"Official URL owner attestation, checked publication and visually reviewed table; local hash not publisher checksum.",
       "source_bytes":len(raw),"source_sha256":digest,"raw_path":MARKET_RAW,"first_intake_date":intake.isoformat(),
       "terms_reviewed_by_owner":True,"visual_page_reviewed_by_owner":True,
       "retention_policy":MARKET_POLICY,"retention":MARKET_RETENTION,
       "do_not_retain_on_or_after":deadline.isoformat() if deadline else None,
       "processed_path":MARKET_OUTPUT,"processed_sha256":sha(data),"quality_report":MARKET_REPORT,"quality":q}
    planned=[(root/MARKET_OUTPUT,data),(root/MARKET_REPORT,json_bytes(q)),(existing,json_bytes(m))]
    for path,content in planned:
        check_target(path,content)
    for path,content in planned:
        publish(path,content)
    return m

def market_cli(root,args):
    prior=json.loads(read_bounded(root/MARKET_MANIFEST)) if (root/MARKET_MANIFEST).exists() else None
    intake=args.intake_date or (date.fromisoformat(prior["first_intake_date"]) if prior else date.fromisoformat(input("Actual PDF download date (YYYY-MM-DD): ").strip()))
    reviewed=args.terms_reviewed or (prior["terms_reviewed_by_owner"] is True if prior else
                                    input("Confirm printed page 11 terms, attribution and private processing (yes/no): ").strip().lower()=="yes")
    def confirm(data):
        print("\nPrivate preview: compare both Table 4 rows on PDF page 6 (printed page 5), cover and terms.")
        print(data.decode("utf-8"))
        return input("All six index observations, both weights and four changes visually match the official table (yes/no): ").strip().lower()=="yes"
    m=import_market(root,intake,reviewed,confirm,args.retain_until)
    print(json.dumps({"import":"complete","quality":m["quality"],"status":market_status(root)},indent=2))
    return 0

def market_self_test():
    # Actual public metro labels, invented numeric observations only.
    rows=["Table 4 - RPPI for all metropolitan areas",
          "Weight Index (Dec 2020=100) Jun 2025 May 2026 Jun 2026",
          "City of Cape Town   30,00   100,0   109,0   110,0   0,9   10,0",
          "City of Johannesburg   20,00   90,0   99,0   100,0   1,0   11,1",
          "The latest 12 months are subject to revision","Figure 4"]
    # Reproduce the observed cover structure, omitting contact details.
    cover_lines=["www.statssa.gov.za", "STATISTICAL RELEASE", "P0160", "",
                 "Residential Property Price Index", "", "June 2026",
                 "Embargoed until:", "5 November 2026", "09:00",
                 "FORTHCOMING ISSUE: EXPECTED RELEASE DATE:", "July 2026 3 December 2026"]
    cover_text=" \n ".join(cover_lines)
    market_cover(cover_text)
    for bad in (cover_text.replace("www.statssa.gov.za","example.invalid"),
                cover_text.replace("P0160","P0161"),
                cover_text.replace("June 2026","May 2026"),
                cover_text.replace("5 November 2026","4 November 2026")+" 5 November 2026"):
        try:
            market_cover(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Incorrect publication identity accepted")
    pages=[cover_lines]+[["Invented page"] for _ in range(11)]
    pages[5]=rows
    pages[11]=["Stats SA has copyright on this publication; acknowledge Stats SA; own processing."]
    raw=fixture_pdf(pages)
    data,q=market_profile(raw)
    assert q["index_observations"]==6 and q["growth_rounding_checks_passed"]==4
    assert market_growth_compatible(Decimal("100.0"),Decimal("110.0"),Decimal("9.9"))
    for bad in (rows[:2]+rows[3:],rows[:3]+[rows[2]]+rows[3:], [x.replace("10,0","90,0") for x in rows]):
        try:
            market_table("\n".join(bad))
        except ValueError:
            pass
        else:
            raise AssertionError("Unexpected market table accepted")
    day=date(2026,11,26)
    with tempfile.TemporaryDirectory() as tmp:
        root=workspace(Path(tmp)/"private")
        initialise(root)
        publish(root/MARKET_RAW,raw)
        publish(root/RAW,b"untouched historical fixture")
        try:
            import_market(root,day,True,lambda _:False,today=day)
        except ValueError:
            pass
        else:
            raise AssertionError("Unreviewed table registered")
        assert not (root/MARKET_MANIFEST).exists() and not (root/MARKET_OUTPUT).exists()
        first=import_market(root,day,True,lambda d:d==data,today=day)
        assert first==import_market(root,day,True,lambda _:False,today=day)
        assert (root/RAW).read_bytes()==b"untouched historical fixture"
        spec=("HPI-DATA-006",MARKET_MANIFEST,MARKET_RAW,MARKET_OUTPUT,MARKET_REPORT,MARKET_MAX,None)
        assert audit_registered(root,spec,today=day)["status"]=="integrity checks passed"
        (root/MARKET_OUTPUT).write_bytes(data+b"\n")
        try:
            audit_registered(root,spec,today=day)
        except ValueError:
            pass
        else:
            raise AssertionError("Changed output accepted")
    print("PASS: invented market PDF, two metros, six observations, rounding intervals, refusal, repeat, historical isolation and integrity.")




# HPI-DATA-007: one approved three-request experiment, never a live application feed.
TREASURY_HOST = "municipaldata.treasury.gov.za"
TREASURY_BASE = "/api/cubes/audit_opinions"
TREASURY_TERMS = "https://municipalmoney.gov.za/terms"
TREASURY_CAP = 256*1024
TREASURY_RAW = "02_Raw_Data/HPI-DATA-007_responses.zip"
TREASURY_MANIFEST = "01_Source_Catalogue/HPI-DATA-007.json"
TREASURY_OUTPUT = "03_Processed_Data/HPI-DATA-007/audit_opinions.json"
TREASURY_REPORT = "07_Reports/HPI-DATA-007_quality.json"
TREASURY_ATTEMPT = "07_Reports/HPI-DATA-007_attempt.json"
TREASURY_RECOVERY = "07_Reports/HPI-DATA-007_recovery_attempt.json"
TREASURY_POLICY = "treasury-private-audit-opinions-v1"
TREASURY_RETENTION = "Private bounded qualification only; source terms and law prevail; no automatic deletion."
TREASURY_NAMES = {"CPT":"City of Cape Town","JHB":"City of Johannesburg"}
TREASURY_FIELDS = {"financial_year_end.year","demarcation.code","demarcation.label",
                   "opinion.code","opinion.label","opinion.report_url"}
TREASURY_PATHS = {"model":TREASURY_BASE+"/model",
                  **{code:TREASURY_BASE+"/facts?cut=financial_year_end.year%3A2024%7Cdemarcation.code%3A%22"+code+"%22&pagesize=5"
                     for code in TREASURY_NAMES}}

def treasury_get(path, connection_factory=None):
    import http.client
    import ssl
    if path not in TREASURY_PATHS.values():
        raise ValueError("Request outside approved Treasury scope.")
    factory=connection_factory or http.client.HTTPSConnection
    conn=factory(TREASURY_HOST,timeout=20,context=ssl.create_default_context())
    try:
        # http.client does not follow redirects or retry requests. No proxy, auth,
        # cookies, report links, compression, or arbitrary host/path accepted.
        conn.request("GET",path,headers={"Accept":"application/json","Accept-Encoding":"identity","User-Agent":"HPI-bounded-research/1.0","Connection":"close"})
        response=conn.getresponse()
        if response.status!=200:
            raise ValueError("Treasury HTTP status "+str(response.status)+"; no retry.")
        if (response.getheader("Content-Type","").split(";")[0].strip().lower()!="application/json" or
                response.getheader("Content-Encoding","identity").lower()!="identity"):
            raise ValueError("Unexpected Treasury response media type or encoding.")
        length=response.getheader("Content-Length")
        if length is not None:
            n=int(length)
            if not 0<n<=TREASURY_CAP:
                raise ValueError("Treasury response outside approved byte cap.")
            body=response.read(n)
            if len(body)!=n:
                raise ValueError("Incomplete Treasury response.")
        else:
            body=response.read(TREASURY_CAP)
            if len(body)>=TREASURY_CAP:
                raise ValueError("Unbounded response reached cap; completeness unverified.")
        if not body:
            raise ValueError("Empty Treasury response.")
        return body
    finally:
        conn.close()

def treasury_json(raw):
    import re
    if not isinstance(raw,bytes) or not 0<len(raw)<=TREASURY_CAP:
        raise ValueError("Treasury response outside approved cap.")
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:
                raise ValueError("Duplicate JSON key in Treasury response.")
            result[k]=v
        return result
    def bad_constant(_):
        raise ValueError("Non-finite JSON value.")
    obj=json.loads(raw.decode("utf-8"),object_pairs_hook=unique,parse_constant=bad_constant)
    def screen(value):
        if isinstance(value,dict):
            for k,v in value.items():
                if re.search(r"(?:^|[._])(?:email|phone|mobile|contact|person|officials|id_number|address|first_name|last_name)(?:$|[._])",k,re.I):
                    raise ValueError("Unexpected personal-information field; response not retained.")
                screen(v)
        elif isinstance(value,list):
            for v in value:
                screen(v)
        elif isinstance(value,str) and re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",value):
            raise ValueError("Possible personal information in response; response not retained.")
    screen(obj)
    if not isinstance(obj,dict) or obj.get("status")!="ok":
        raise ValueError("Treasury response is not a successful JSON object.")
    return obj

def treasury_model(raw):
    import re
    obj=treasury_json(raw)
    model=obj["model"]
    if not isinstance(model,dict) or model.get("name","audit_opinions")!="audit_opinions":
        raise ValueError("Unexpected cube identity.")
    dimensions=model["dimensions"]
    if set(dimensions)!={"financial_year_end","demarcation","opinion"}:
        raise ValueError("Unexpected audit-opinion dimensions.")
    attrs={a["ref"] for d in dimensions.values() for a in d["attributes"].values()}
    if attrs!=TREASURY_FIELDS:
        raise ValueError("Unexpected audit-opinion model fields.")
    updated=model.get("last_updated")
    # Publisher source also emits YYYY-MM-DDTHH:MM for recorded imports.
    # Preserve the exact source precision; never infer a publication date.
    if not isinstance(updated,str) or not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])(?:-\d{2}(?:T\d{2}:\d{2})?)?",updated):
        raise ValueError("Missing or unsupported source update metadata.")
    if len(updated)==16:
        from datetime import datetime
        datetime.fromisoformat(updated)
    else:
        date.fromisoformat(updated+"-01" if len(updated)==7 else updated)
    if updated[:4]<"2024":
        raise ValueError("Model update predates selected year.")
    # last_updated is the source update/reference period, not publication date.
    published=model.get("publication_date")
    if published is not None:
        if not isinstance(published,str) or len(published)!=10:
            raise ValueError("Unexpected explicit publication date.")
        date.fromisoformat(published)
    return {"source_last_updated":updated,"publication_date":published}

def treasury_facts(raw,code):
    import re
    from urllib.parse import urlsplit
    obj=treasury_json(raw)
    fields=obj["fields"]
    rows=obj["data"]
    total=obj["total_fact_count"]
    if (not isinstance(fields,list) or len(fields)!=len(TREASURY_FIELDS) or set(fields)!=TREASURY_FIELDS or
            type(obj["page"]) is not int or obj["page"]!=1 or type(obj["page_size"]) is not int or
            not 1<=obj["page_size"]<=5 or type(total) is not int or total not in (0,1) or
            not isinstance(rows,list) or len(rows)!=total):
        raise ValueError("Unexpected facts schema, duplicate outcome or incomplete page; no pagination.")
    if not rows:
        return {"municipality_code":code,"financial_year_end":2024,"status":"unavailable"}
    row=rows[0]
    if (not isinstance(row,dict) or set(row)!=TREASURY_FIELDS or row["demarcation.code"]!=code or
            type(row["financial_year_end.year"]) is not int or row["financial_year_end.year"]!=2024 or
            row["demarcation.label"]!=TREASURY_NAMES[code]):
        raise ValueError("Treasury fact outside exact approved municipality/year scope.")
    opinion=row["opinion.code"]
    label=row["opinion.label"]
    url=row["opinion.report_url"]
    if not isinstance(opinion,str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}",opinion):
        raise ValueError("Unexpected opinion code.")
    known={"unqualified - no findings","unqualified - emphasis of matter items",
           "qualified","qualified opinion","adverse","adverse opinion",
           "disclaimer","disclaimer of opinion","unqualified - findings",
           "unqualified - with findings","unqualified - with no findings",
           "outstanding","audit outstanding","no report available","not available"}
    if not isinstance(label,str) or label.casefold().strip() not in known:
        raise ValueError("Unrecognised audit opinion label; review source.")
    if url not in (None,""):
        if not isinstance(url,str) or len(url)>2048:
            raise ValueError("Unexpected report reference.")
        u=urlsplit(url)
        if u.scheme not in ("http","https") or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError("Unexpected report reference; not followed.")
    return {"municipality_code":code,"municipality_name_source":row["demarcation.label"],
            "financial_year_end":2024,"status":"reported","opinion_code":opinion,
            "opinion_label":label,"report_url":url}

def treasury_spec():
    # ZIP storage overhead is local, not part of the API transfer budget.
    return ("HPI-DATA-007",TREASURY_MANIFEST,TREASURY_RAW,TREASURY_OUTPUT,TREASURY_REPORT,
            3*TREASURY_CAP+4096,None)

def treasury_acquire(root,reviewed,fetch=treasury_get,today=None,recovery=False):
    root=workspace(root)
    today=today or date.today()
    if not reviewed:
        raise ValueError("Review and accept the Treasury source terms before any request.")
    if not all((root/f).is_dir() for f in FOLDERS):
        raise ValueError("Use the existing initialised private workspace.")
    for relative in (TREASURY_ATTEMPT,TREASURY_RECOVERY,TREASURY_RAW,TREASURY_MANIFEST,TREASURY_OUTPUT,TREASURY_REPORT):
        p=root/relative
        workspace(p.parent)
        check_path(p)
        if p.exists() and not (recovery and relative==TREASURY_ATTEMPT):
            raise ValueError("007 attempt or output already exists; no repeat requests. Review existing status.")
    original_hash=None
    if recovery:
        original=read_bounded(root/TREASURY_ATTEMPT,4096)
        prior=json.loads(original)
        if (prior.get("dataset_id")!="HPI-DATA-007" or
                prior.get("approved_max_requests")!=3 or
                prior.get("approved_body_bytes")!=3*TREASURY_CAP or
                prior.get("retry_authorised") is not False or
                date.fromisoformat(prior["attempt_date"])!=date(2026,11,26)):
            raise ValueError("Original approved attempt marker differs; no recovery.")
        original_hash=sha(original)
    # Exclusive creation consumes the approved attempt, including failure.
    # Recovery has a separate marker; neither path overwrites the original.
    marker=TREASURY_RECOVERY if recovery else TREASURY_ATTEMPT
    record={"dataset_id":"HPI-DATA-007","attempt_date":today.isoformat(),
            "approved_max_requests":3,"approved_body_bytes":3*TREASURY_CAP,
            "retry_authorised":False}
    if recovery:
        record.update({"attempt":"recovery-1","original_attempt_sha256":original_hash,
                       "authority_date":"2026-11-26"})
    with (root/marker).open("xb") as f:
        f.write(json_bytes(record))
    payloads={}
    facts=[]
    for key,path in TREASURY_PATHS.items():
        # Count the dispatch before transport, and preserve a small local
        # diagnostic on failure without saving unvalidated response bodies.
        if recovery:
            publish(root/("07_Reports/HPI-DATA-007_recovery_"+key+"_dispatch.json"),
                    json_bytes({"request":key,"date":today.isoformat()}))
        raw=fetch(path)
        try:
            if key=="model":
                provenance=treasury_model(raw)
            else:
                facts.append(treasury_facts(raw,key))
        except (ValueError,KeyError,TypeError,AttributeError) as exc:
            if recovery:
                diagnostic={"request":key,"response_body_bytes":len(raw),
                            "response_sha256":sha(raw),"error_type":type(exc).__name__}
                if key=="model":
                    try:
                        obj=treasury_json(raw)["model"]
                        value=obj.get("last_updated")
                        diagnostic.update({"update_field_present":"last_updated" in obj,
                                           "update_value_type":type(value).__name__,
                                           "update_string_length":len(value) if isinstance(value,str) else None})
                    except (ValueError,KeyError,TypeError,AttributeError):
                        pass
                publish(root/("07_Reports/HPI-DATA-007_recovery_"+key+"_diagnostic.json"),
                        json_bytes(diagnostic))
                print("Recovery diagnostic:",json.dumps(diagnostic))
            raise
        payloads[key]=raw
    if recovery and sha(read_bounded(root/TREASURY_ATTEMPT,4096))!=original_hash:
        raise ValueError("Original attempt record changed during recovery; no registration.")
    body_count=sum(map(len,payloads.values()))
    if body_count>3*TREASURY_CAP:
        raise ValueError("Aggregate transfer budget exceeded.")
    if (date.fromisoformat(provenance["source_last_updated"]+"-01" if len(provenance["source_last_updated"])==7 else provenance["source_last_updated"][:10])>today or
            (provenance["publication_date"] and date.fromisoformat(provenance["publication_date"])>today)):
        raise ValueError("Source metadata date is in the future.")
    q={"requested_metros":2,"reported_outcomes":sum(x["status"]=="reported" for x in facts),
       "unavailable_outcomes":sum(x["status"]=="unavailable" for x in facts),
       "financial_year_end":2024,"api_requests":3,"response_body_bytes":body_count,
       "acquisition_attempt":"recovery-1" if recovery else "initial",
       "source_last_updated":provenance["source_last_updated"],"publication_date":provenance["publication_date"],
       "publication_date_verified":provenance["publication_date"] is not None,
       "display_authorised":False,"material_join":False,"report_links_followed":False}
    bundle=io.BytesIO()
    with zipfile.ZipFile(bundle,"w",compression=zipfile.ZIP_STORED) as z:
        for key,raw in payloads.items():
            z.writestr(zipfile.ZipInfo(key+".json"),raw)
    raw_bundle=bundle.getvalue()
    data=json_bytes({"source":"National Treasury, Municipal Money","terms_url":TREASURY_TERMS,
                     "retrieval_date":today.isoformat(),**provenance,"observations":facts,
                     "limitations":"Private qualification only. Update period is not publication date. No property, service quality, desirability or ranking inference."})
    manifest={"dataset_id":"HPI-DATA-007","manager_version":"0.6.0",
              "source":"National Treasury, Municipal Money audit_opinions",
              "source_url":"https://"+TREASURY_HOST+TREASURY_BASE+"/model",
              "source_licence":"Municipal Money terms: source/date attribution, no misleading use, no personal information or endorsement; private project scope",
              "attribution":"National Treasury, Municipal Money, audit_opinions; publication date separately recorded if supplied; independent HPI processing.",
              **provenance,"request_urls":{key:"https://"+TREASURY_HOST+path for key,path in TREASURY_PATHS.items()},
              "response_sha256":{key:sha(raw) for key,raw in payloads.items()},
              "source_bytes":len(raw_bundle),"source_sha256":sha(raw_bundle),"raw_path":TREASURY_RAW,
              "acquisition_attempt":"recovery-1" if recovery else "initial","original_attempt_sha256":original_hash,
              "first_intake_date":today.isoformat(),"terms_reviewed_by_owner":True,
              "retention_policy":TREASURY_POLICY,"retention":TREASURY_RETENTION,"do_not_retain_on_or_after":None,
              "processed_path":TREASURY_OUTPUT,"processed_sha256":sha(data),"quality_report":TREASURY_REPORT,"quality":q}
    planned=[(root/TREASURY_RAW,raw_bundle),(root/TREASURY_OUTPUT,data),
             (root/TREASURY_REPORT,json_bytes(q)),(root/TREASURY_MANIFEST,json_bytes(manifest))]
    for p,b in planned:
        check_target(p,b)
    for p,b in planned:
        publish(p,b)
    return manifest

def treasury_status(root):
    path=root/TREASURY_MANIFEST
    if not path.exists():
        return {"dataset_id":"HPI-DATA-007","registered":False,"attempt_started":(root/TREASURY_ATTEMPT).exists(),
                "recovery_started":(root/TREASURY_RECOVERY).exists()}
    m=json.loads(read_bounded(path))
    return {"dataset_id":"HPI-DATA-007","registered":True,**retention_status(m),
            "known_local_paths":[x for x in (TREASURY_RAW,TREASURY_OUTPUT,TREASURY_REPORT,TREASURY_MANIFEST,TREASURY_ATTEMPT,TREASURY_RECOVERY) if (root/x).exists()]}

def treasury_self_test():
    # Synthetic JSON and fake transport: no live requests.
    dims={d:{"attributes":{f.split(".")[1]:{"ref":f} for f in TREASURY_FIELDS if f.startswith(d+".")}}
          for d in ("financial_year_end","demarcation","opinion")}
    model={"status":"ok","model":{"dimensions":dims,"last_updated":"2026-06-15T13:42"}}
    for valid in ("2026-06","2026-06-15","2026-06-15T13:42"):
        sample={"status":"ok","model":{"dimensions":dims,"last_updated":valid}}
        assert treasury_model(json_bytes(sample))=={"source_last_updated":valid,"publication_date":None}
    for invalid in (None,"","2026-06-15T25:42","2026-02-30T13:42","2026-06-15T13:99","2020-10"):
        sample={"status":"ok","model":{"dimensions":dims,"last_updated":invalid}}
        try:
            treasury_model(json_bytes(sample))
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid/stale update metadata accepted")
    def fact(code):
        row={"financial_year_end.year":2024,"demarcation.code":code,"demarcation.label":TREASURY_NAMES[code],
             "opinion.code":"FIXTURE","opinion.label":"Qualified Opinion","opinion.report_url":None}
        return {"status":"ok","fields":sorted(TREASURY_FIELDS),"page":1,"page_size":5,"total_fact_count":1,"data":[row]}
    payloads={TREASURY_PATHS["model"]:json_bytes(model),
              **{TREASURY_PATHS[c]:json_bytes(fact(c)) for c in TREASURY_NAMES}}
    calls=[]
    def fetch(path):
        calls.append(path)
        return payloads[path]
    day=date(2026,11,26)
    with tempfile.TemporaryDirectory() as tmp:
        root=workspace(Path(tmp)/"private")
        initialise(root)
        publish(root/RAW,b"prior untouched")
        try:
            treasury_acquire(root,False,fetch,day)
        except ValueError:
            pass
        else:
            raise AssertionError("Missing terms accepted")
        assert not calls and not (root/TREASURY_ATTEMPT).exists()
        m=treasury_acquire(root,True,fetch,day)
        assert len(calls)==3 and m["quality"]["reported_outcomes"]==2
        assert m["quality"]["publication_date_verified"] is False and m["quality"]["display_authorised"] is False
        assert (root/RAW).read_bytes()==b"prior untouched"
        assert audit_registered(root,treasury_spec(),day)["status"]=="integrity checks passed"
        try:
            treasury_acquire(root,True,fetch,day)
        except ValueError:
            pass
        else:
            raise AssertionError("Repeat acquisition allowed")
        assert len(calls)==3
    empty=fact("CPT")
    empty["data"]=[];empty["total_fact_count"]=0
    assert treasury_facts(json_bytes(empty),"CPT")["status"]=="unavailable"
    for mode in ("wrong_year","wrong_code","duplicate","personal","extra","oversize"):
        obj=fact("CPT")
        if mode=="wrong_year": obj["data"][0]["financial_year_end.year"]=2025
        if mode=="wrong_code": obj["data"][0]["demarcation.code"]="TSH"
        if mode=="duplicate": obj["data"]*=2;obj["total_fact_count"]=2
        if mode=="personal": obj["data"][0]["email"]="fixture@example.invalid"
        if mode=="extra": obj["data"][0]["unexpected"]="fixture"
        try:
            treasury_facts(b"x"*(TREASURY_CAP+1) if mode=="oversize" else json_bytes(obj),"CPT")
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid Treasury scope accepted")
    with tempfile.TemporaryDirectory() as tmp:
        root=workspace(Path(tmp)/"private")
        initialise(root)
        attempted=[]
        def fail(path):
            attempted.append(path)
            raise ValueError("Invented transport failure")
        for _ in range(2):
            try:
                treasury_acquire(root,True,fail,day)
            except ValueError:
                pass
            else:
                raise AssertionError("Failure not propagated")
        assert len(attempted)==1 and (root/TREASURY_ATTEMPT).exists() and not (root/TREASURY_RAW).exists()
    # Recovery is separately approved, consumes its own marker once and
    # leaves the earlier attempt byte-for-byte unchanged.
    with tempfile.TemporaryDirectory() as tmp:
        root=workspace(Path(tmp)/"private")
        initialise(root)
        publish(root/RAW,b"prior untouched")
        n=len(calls)
        try:
            treasury_acquire(root,True,fetch,day,recovery=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Recovery without original marker accepted")
        assert len(calls)==n
        try:
            treasury_acquire(root,True,fail,day)
        except ValueError:
            pass
        original=read_bounded(root/TREASURY_ATTEMPT)
        m=treasury_acquire(root,True,fetch,day,recovery=True)
        assert len(calls)==n+3 and m["quality"]["acquisition_attempt"]=="recovery-1"
        assert m["original_attempt_sha256"]==sha(original)
        assert read_bounded(root/TREASURY_ATTEMPT)==original
        assert (root/RAW).read_bytes()==b"prior untouched"
        assert (root/TREASURY_RECOVERY).exists()
        assert audit_registered(root,treasury_spec(),day)["status"]=="integrity checks passed"
        for mode in (False,True):
            try:
                treasury_acquire(root,True,fetch,day,recovery=mode)
            except ValueError:
                pass
            else:
                raise AssertionError("Attempt replay accepted")
        assert len(calls)==n+3
    with tempfile.TemporaryDirectory() as tmp:
        root=workspace(Path(tmp)/"private")
        initialise(root)
        try:
            treasury_acquire(root,True,fail,day)
        except ValueError:
            pass
        original=read_bounded(root/TREASURY_ATTEMPT)
        broken={"status":"ok","model":{"dimensions":dims}}
        dispatched=[]
        def broken_fetch(path):
            dispatched.append(path)
            return json_bytes(broken)
        for _ in range(2):
            try:
                treasury_acquire(root,True,broken_fetch,day,recovery=True)
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid recovery accepted")
        assert dispatched==[TREASURY_PATHS["model"]]
        assert read_bounded(root/TREASURY_ATTEMPT)==original
        assert not (root/TREASURY_RAW).exists()
        diagnostic=json.loads(read_bounded(root/"07_Reports/HPI-DATA-007_recovery_model_diagnostic.json"))
        assert diagnostic["update_field_present"] is False
    print("PASS: one separately tracked Treasury recovery, original marker preserved, dispatch accounting and safe failure diagnostics.")
    class Response:
        status=302
        def getheader(self,k,default=None):
            return default
        def read(self,n):
            raise AssertionError("Redirect body read")
    class Connection:
        def __init__(self,*a,**k):
            pass
        def request(self,*a,**k):
            pass
        def getresponse(self):
            return Response()
        def close(self):
            pass
    try:
        treasury_get(TREASURY_PATHS["model"],Connection)
    except ValueError:
        pass
    else:
        raise AssertionError("Redirect accepted")
    print("PASS: bounded Treasury scope, three requests, no retry, missing result, provenance, rejection, isolation and integrity.")




# HPI-DATA-008: fixed revised municipal fact sheet; two aggregate rows only.
CENSUS_URL = "https://census.statssa.gov.za/assets/documents/2022/Census_2022_Municipal_factsheet-Web.pdf"
CENSUS_RAW = "02_Raw_Data/Census_2022_Municipal_factsheet-Web.pdf"
CENSUS_MANIFEST = "01_Source_Catalogue/HPI-DATA-008.json"
CENSUS_OUTPUT = "03_Processed_Data/HPI-DATA-008/household_services.csv"
CENSUS_REPORT = "07_Reports/HPI-DATA-008_quality.json"
CENSUS_MAX = 5*MIB
CENSUS_POLICY = "stats-sa-census-private-v1"
CENSUS_RETENTION = "Private noncommercial aggregate research only; source terms and law prevail; no automatic deletion."
CENSUS_TARGETS = (("City of Cape Town","Western Cape",30,35),
                  ("City of Johannesburg","Gauteng",25,30))
CENSUS_METRICS = (
    ("flush_toilet_sewerage","Flush Toilet Connected to sewerage (%)","flush toilet connected to"),
    ("weekly_refuse_removal","Weekly Refuse Removal (%)","weekly refuse removal"),
    ("piped_water_on_site","Piped Water on Site (Inside dwelling and in the yard) (%)","piped water on site"),
    ("electricity_for_lighting","Electricity for Lighting (%)","electricity for lighting"))
CENSUS_YEARS = (2011,2022)

def census_flat(value):
    return " ".join(value.split()).casefold()

def census_require(value,markers,gate):
    flat=census_flat(value)
    for marker in markers:
        if marker not in flat:
            raise ValueError("Census "+gate+" check failed: missing expected marker "+marker+".")

def census_row(layout,name,province,printed,page):
    import re
    lines=layout.splitlines()
    if not any(line.strip()==str(printed) for line in lines):
        raise ValueError("Census printed page marker differs on PDF page "+str(page)+".")
    year_lines=[i for i,line in enumerate(lines)
                if line.split()==["2011","2022"]*4]
    if len(year_lines)!=1:
        raise ValueError("Census paired year header missing or ambiguous on PDF page "+str(page)+".")
    header=lines[:year_lines[0]]
    census_require("\n".join(header),("households (cont.)","sewerage","inside dwelling","in the yard"),"service header")
    # Layout extraction preserves horizontal placement even when headers wrap
    # across multiple lines. Check each column-group start left to right.
    starts=[]
    for _,_,anchor in CENSUS_METRICS:
        hits=[match.start() for line in header for match in
              re.finditer(r"\s+".join(map(re.escape,anchor.split())),line,re.I)]
        if len(hits)!=1:
            raise ValueError("Census indicator header missing or duplicated: "+anchor+".")
        starts.append(hits[0])
    if starts!=sorted(set(starts)):
        raise ValueError("Census indicator column order differs on PDF page "+str(page)+".")
    # Each percentage group is explicitly marked, not assumed from values.
    if len(re.findall(r"\(\s*%\s*\)","\n".join(header)))!=4:
        raise ValueError("Census percentage-unit headers differ on PDF page "+str(page)+".")
    body=lines[year_lines[0]+1:]
    if not any(re.match(r"^\s*"+re.escape(province)+r"\s+\d",line) for line in body):
        raise ValueError("Census expected province context missing on PDF page "+str(page)+".")
    targets=[line for line in body if re.match(r"^\s*"+re.escape(name)+r"(?=\s|$)",line)]
    if len(targets)!=1:
        raise ValueError("Census expected exactly one target row for "+name+"; found "+str(len(targets))+".")
    tail=targets[0].strip()[len(name):].split()
    if len(tail)!=8:
        raise ValueError("Census target row cell count for "+name+": expected 8, found "+str(len(tail))+".")
    vals=[]
    for i,token in enumerate(tail):
        if not re.fullmatch(r"\d{1,3},\d",token):
            raise ValueError("Census decimal-comma format differs for "+name+" column "+str(i+1)+".")
        v=Decimal(token.replace(",","."))
        if not 0<=v<=100:
            raise ValueError("Census household percentage outside 0-100 for "+name+" column "+str(i+1)+".")
        vals.append(v)
    return [[name,province,"metro",key,label,year,str(vals[2*i+j]),"percent",
             "households; exact indicator denominator count not supplied in table",
             "2021 municipal frame",printed,page,"03-01-82","revised erratum edition"]
            for i,(key,label,_) in enumerate(CENSUS_METRICS) for j,year in enumerate(CENSUS_YEARS)]

def census_profile(raw):
    try:
        from pypdf import PdfReader, __version__
        from pypdf.errors import PdfReadError
    except ImportError as exc:
        raise ValueError("Install existing tested dependency: pypdf=="+CODE_PDF_VERSION) from exc
    if __version__!=CODE_PDF_VERSION:
        raise ValueError("Census requires existing tested pypdf version "+CODE_PDF_VERSION+".")
    if len(raw)>CENSUS_MAX or not raw.startswith(b"%PDF-"):
        raise ValueError("Census requires the bounded original PDF.")
    try:
        pdf=PdfReader(io.BytesIO(raw),strict=True)
        if pdf.is_encrypted or len(pdf.pages)!=41:
            raise ValueError("Census revised edition must have exactly 41 PDF pages, unencrypted.")
        census_require(pdf.pages[1].extract_text(),("municipal fact sheet","statistics south africa","03-01-82"),"publication identity")
        census_require(pdf.pages[2].extract_text(),("erratum for census 2022 municipal fact sheet","03-01-82",
                       "978-0-621-51626-5","thaba chweu","mbombela","revised"),"revision")
        census_require(pdf.pages[3].extract_text(),("statistics south africa","978-0-621-51626-5","2023",
                       "original source","independent processing","offered for sale","prior permission"),"source terms")
        census_require(pdf.pages[5].extract_text(),("census 2011 indicators","aligned census data","municipal boundaries (2021)"),"geographic frame")
        rows=[]
        for name,province,printed,page in CENSUS_TARGETS:
            rows.extend(census_row(pdf.pages[page-1].extract_text(extraction_mode="layout"),
                                  name,province,printed,page))
    except PdfReadError as exc:
        raise ValueError("Census PDF parsing failed; no registration.") from exc
    if len(rows)!=16 or len({(x[0],x[3],x[5]) for x in rows})!=16:
        raise ValueError("Census observation uniqueness/completeness failed.")
    out=io.StringIO(newline="")
    w=csv.writer(out,lineterminator="\n")
    w.writerow(["metro_name_source","province_source","geography_level","indicator_id","indicator_label_source",
                "census_year","value","unit","denominator_scope","geography_reference","printed_page","pdf_page",
                "report_number","edition"])
    w.writerows(rows)
    q={"metro_rows":2,"indicators":4,"census_years":[2011,2022],"observations":16,"unique_observations":16,
       "percentage_range_checks_passed":16,"pdf_pages":41,"source_pdf_pages":[30,35],
       "geography_reference":"2021 municipal frame","revision_notice_present":True,
       "source_publication_year":2023,"exact_revision_publication_date":None,
       "household_microdata":False,"material_join":False,"property_service_reliability_verified":False}
    return out.getvalue().encode("utf-8"),q

def census_spec():
    return ("HPI-DATA-008",CENSUS_MANIFEST,CENSUS_RAW,CENSUS_OUTPUT,CENSUS_REPORT,CENSUS_MAX,None)

def census_status(root):
    path=root/CENSUS_MANIFEST
    if not path.exists():
        return {"dataset_id":"HPI-DATA-008","registered":False}
    m=json.loads(read_bounded(path))
    return {"dataset_id":"HPI-DATA-008","registered":True,**retention_status(m),
            "known_local_paths":[x for x in (CENSUS_RAW,CENSUS_OUTPUT,CENSUS_REPORT,CENSUS_MANIFEST) if (root/x).exists()]}

def import_census(root,intake,terms_reviewed,confirm,deadline=None,today=None):
    root=workspace(root)
    today=today or date.today()
    if not terms_reviewed or not date(2025,8,5)<=intake<=today:
        raise ValueError("Confirm revised source terms and actual valid intake date.")
    if deadline is not None and (deadline<=intake or today>=deadline):
        raise ValueError("Invalid or expired retention deadline.")
    raw=read_bounded(root/CENSUS_RAW,CENSUS_MAX)
    digest=sha(raw)
    existing=root/CENSUS_MANIFEST
    if existing.exists():
        prior=json.loads(read_bounded(existing))
        old_deadline=stored_deadline(prior)
        if (prior["source_sha256"]!=digest or prior["first_intake_date"]!=intake.isoformat() or
                (deadline is not None and deadline!=old_deadline) or
                (old_deadline is not None and today>=old_deadline) or
                prior.get("retention_policy")!=CENSUS_POLICY or prior.get("visual_page_reviewed_by_owner") is not True):
            raise ValueError("Registered Census source or retention differs; no overwrite/renewal.")
        deadline=old_deadline
    data,q=census_profile(raw)
    if not existing.exists() and not confirm(data):
        raise ValueError("Census visual verification not confirmed; no registration.")
    q["visual_page_reviewed_by_owner"]=True
    m={"dataset_id":"HPI-DATA-008","manager_version":"0.7.0","source":"Statistics South Africa, revised Census 2022 Municipal fact sheet",
       "source_url":CENSUS_URL,"publication_year":2023,"revision_announcement_date":"2025-08-05",
       "exact_revision_publication_date":None,
       "source_licence":"Printed page ii: attribute Stats SA and independent processing; no sale of data, processed data or application without permission; private noncommercial scope",
       "attribution":"Statistics South Africa, Census 2022 Municipal fact sheet, report 03-01-82, revised erratum edition, pp25 and 30; independently processed by HPI.",
       "source_identity_evidence":"Official URL owner attestation, checked erratum and visually reviewed tables; local hash not publisher checksum.",
       "source_bytes":len(raw),"source_sha256":digest,"raw_path":CENSUS_RAW,"first_intake_date":intake.isoformat(),
       "terms_reviewed_by_owner":True,"visual_page_reviewed_by_owner":True,
       "retention_policy":CENSUS_POLICY,"retention":CENSUS_RETENTION,
       "do_not_retain_on_or_after":deadline.isoformat() if deadline else None,
       "processed_path":CENSUS_OUTPUT,"processed_sha256":sha(data),"quality_report":CENSUS_REPORT,"quality":q}
    planned=[(root/CENSUS_OUTPUT,data),(root/CENSUS_REPORT,json_bytes(q)),(existing,json_bytes(m))]
    for p,b in planned:
        check_target(p,b)
    for p,b in planned:
        publish(p,b)
    return m

def census_cli(root,args):
    prior=json.loads(read_bounded(root/CENSUS_MANIFEST)) if (root/CENSUS_MANIFEST).exists() else None
    intake=args.intake_date or (date.fromisoformat(prior["first_intake_date"]) if prior else date.fromisoformat(input("Actual revised PDF download date (YYYY-MM-DD): ").strip()))
    reviewed=args.terms_reviewed or (prior["terms_reviewed_by_owner"] is True if prior else
                                    input("Confirm PDF page 4 terms, attribution and private noncommercial processing (yes/no): ").strip().lower()=="yes")
    def confirm(data):
        print("\nPrivate preview: compare 16 observations against PDF pages 30 and 35 (printed 25 and 30), including each metric/year header.")
        print(data.decode("utf-8"))
        return input("All 16 values, metro labels and indicator/year headings visually match (yes/no): ").strip().lower()=="yes"
    m=import_census(root,intake,reviewed,confirm,args.retain_until)
    print(json.dumps({"import":"complete","quality":m["quality"],"status":census_status(root)},indent=2))
    return 0

def census_self_test():
    # Structural markers match public layout; every numeric value is invented.
    def lines(name,province,printed):
        return [str(printed),"HOUSEHOLDS (cont.)",
                "Flush Toilet Connected to   Weekly Refuse Removal (%)   Piped Water on Site (Inside dwelling and    Electricity for Lighting (%)",
                "sewerage (%)                                            in the yard) (%)",
                "2011 2022 2011 2022 2011 2022 2011 2022",
                province+"  1,0 2,0 3,0 4,0 5,0 6,0 7,0 8,0",
                name+"  11,1 22,2 33,3 44,4 55,5 66,6 77,7 88,8"]
    pages=[["Invented page"] for _ in range(41)]
    pages[1]=["Municipal fact sheet Statistics South Africa 03-01-82"]
    pages[2]=["Erratum for Census 2022 Municipal fact sheet 03-01-82 978-0-621-51626-5 Thaba Chweu Mbombela revised"]
    pages[3]=["Statistics South Africa 2023 978-0-621-51626-5 original source independent processing offered for sale prior permission"]
    pages[5]=["Census 2011 indicators aligned census data municipal boundaries (2021)"]
    for name,province,printed,page in CENSUS_TARGETS:
        pages[page-1]=lines(name,province,printed)
    raw=fixture_pdf(pages)
    data,q=census_profile(raw)
    assert q["observations"]==16 and q["percentage_range_checks_passed"]==16
    parsed=list(csv.DictReader(io.StringIO(data.decode())))
    assert parsed[0]["value"]=="11.1" and parsed[1]["value"]=="22.2" and parsed[2]["indicator_id"]=="weekly_refuse_removal"
    name,province,printed,page=CENSUS_TARGETS[0]
    good="\n".join(lines(name,province,printed))
    for bad in (good.replace("2011 2022","2022 2011",1),good.replace("88,8","101,0"),
                good.replace("88,8","88.8"),good.replace(" 88,8",""),good+"\n"+lines(name,province,printed)[-1],
                good.replace("Weekly Refuse Removal","Electricity for Lighting").replace("Electricity for Lighting (%)","Wrong (%)",1)):
        try:
            census_row(bad,name,province,printed,page)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid Census row/header accepted")
    for index in (2,3,5):
        bad=list(pages);bad[index]=["Wrong revision, terms or frame"]
        try:
            census_profile(fixture_pdf(bad))
        except ValueError:
            pass
        else:
            raise AssertionError("Wrong Census source accepted")
    day=date(2026,11,26)
    with tempfile.TemporaryDirectory() as tmp:
        root=workspace(Path(tmp)/"private")
        initialise(root)
        publish(root/CENSUS_RAW,raw)
        publish(root/RAW,b"existing historical fixture")
        publish(root/MARKET_OUTPUT,b"existing market fixture")
        for reviewed,confirmed in ((False,True),(True,False)):
            try:
                import_census(root,day,reviewed,lambda _:confirmed,today=day)
            except ValueError:
                pass
            else:
                raise AssertionError("Unreviewed Census import accepted")
            assert not (root/CENSUS_MANIFEST).exists() and not (root/CENSUS_OUTPUT).exists()
        first=import_census(root,day,True,lambda d:d==data,today=day)
        assert first==import_census(root,day,True,lambda _:False,today=day)
        assert (root/RAW).read_bytes()==b"existing historical fixture"
        assert (root/MARKET_OUTPUT).read_bytes()==b"existing market fixture"
        assert audit_registered(root,census_spec(),day)["status"]=="integrity checks passed"
        (root/CENSUS_OUTPUT).write_bytes(data+b"\n")
        try:
            audit_registered(root,census_spec(),day)
        except ValueError:
            pass
        else:
            raise AssertionError("Changed Census output accepted")
    print("PASS: invented revised Census PDF, 16 observations, source/header/range refusal, visual review, repeat, isolation and integrity.")



def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path.cwd())
    p.add_argument("--dataset",choices=("HPI-DATA-002","HPI-DATA-003","HPI-DATA-004","HPI-DATA-005","HPI-DATA-006","HPI-DATA-007","HPI-DATA-008"),default="HPI-DATA-002")
    p.add_argument("--retain-until",type=date.fromisoformat)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--acquire-treasury",action="store_true",help="One approved 007 intake; three fixed requests at most")
    p.add_argument("--recover-treasury",action="store_true",help="One separately approved 007 recovery; preserve original attempt")
    p.add_argument("--status",action="store_true")
    p.add_argument("--audit-workspace",action="store_true")
    p.add_argument("--geo-crosswalk",action="store_true",help="Private read-only candidate report for HPI-DATA-003/005")
    p.add_argument("--geo-alias",action="store_true",help="Private approved documentary alias candidate report")
    p.add_argument("--remove-internal-deadlines",action="store_true")
    p.add_argument("--init-only",action="store_true")
    p.add_argument("--intake-date",type=date.fromisoformat)
    p.add_argument("--terms-reviewed",action="store_true")
    args = p.parse_args()
    try:
        if args.acquire_treasury or args.recover_treasury:
            if (args.acquire_treasury and args.recover_treasury) or (args.dataset!="HPI-DATA-007" or args.self_test or args.status or args.audit_workspace or
                    args.geo_crosswalk or args.geo_alias or args.remove_internal_deadlines or args.init_only or
                    args.intake_date is not None or args.retain_until is not None):
                raise ValueError("Treasury acquisition must be a standalone explicit 007 action.")
            root=workspace(args.root)
            reviewed=args.terms_reviewed or input("Read and accept Municipal Money terms (source/date attribution, no personal data; private scope) (yes/no): ").strip().lower()=="yes"
            manifest=treasury_acquire(root,reviewed,recovery=args.recover_treasury)
            print(json.dumps({"import":"complete","quality":manifest["quality"],"status":treasury_status(root)},indent=2))
            return 0
        if args.geo_crosswalk or args.geo_alias:
            if (args.geo_crosswalk and args.geo_alias) or (args.self_test or args.status or args.audit_workspace or args.remove_internal_deadlines or args.init_only or
                    args.intake_date is not None or args.retain_until is not None or args.terms_reviewed or args.dataset != "HPI-DATA-002"):
                raise ValueError("Geographic crosswalk must be a standalone read-only action.")
            report=crosswalk_report(args.root)
            if args.geo_alias:
                report=alias_candidates(report)
            print(json.dumps(report,indent=2,ensure_ascii=False))
            return 0
        if args.self_test:
            self_test()
            district_self_test()
            building_self_test()
            retention_self_test()
            code_self_test()
            crosswalk_self_test()
            alias_self_test()
            market_self_test()
            treasury_self_test()
            census_self_test()
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
            print(json.dumps(census_status(root) if args.dataset == "HPI-DATA-008" else treasury_status(root) if args.dataset == "HPI-DATA-007" else market_status(root) if args.dataset == "HPI-DATA-006" else code_status(root) if args.dataset == "HPI-DATA-005" else building_status(root) if args.dataset == "HPI-DATA-004" else district_status(root) if args.dataset == "HPI-DATA-003" else status(root),indent=2))
            return 0
        if args.dataset == "HPI-DATA-007":
            raise ValueError("007 requires explicit --acquire-treasury; use --status for an existing attempt.")
        initialise(root)
        if args.init_only:
            print("Workspace initialised; existing files preserved.")
            return 0
        if args.dataset == "HPI-DATA-008":
            return census_cli(root,args)
        if args.dataset == "HPI-DATA-006":
            return market_cli(root,args)
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
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError, OSError, EOFError, InvalidOperation, zipfile.BadZipFile, csv.Error) as exc:
        print("STOP:",str(exc))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
