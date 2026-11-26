"""Offline HPI data workspace manager. No network, deletion or cloud operations."""
import argparse
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
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
    root = Path(root).expanduser().absolute()
    check_path(root)
    if any((p / ".git").exists() for p in (root, *root.parents)):
        raise ValueError("Use a private workspace outside every Git checkout.")
    return root

def read_bounded(path, limit=10*MIB):
    check_path(path)
    if not path.is_file() or path.stat().st_size > limit:
        raise ValueError("Missing or oversized file: " + path.name)
    with path.open("rb") as f:
        data = f.read(limit+1)
    if len(data) > limit:
        raise ValueError("File exceeds limit.")
    return data

def check_target(path, data):
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

def import_rppi(root, intake, terms_reviewed, expected=APPROVED_SHA, today=None):
    today = today or date.today()
    if not terms_reviewed:
        raise ValueError("Owner must review and confirm applicable terms before import.")
    if intake > today or today >= intake + timedelta(days=30):
        raise ValueError("Future or expired intake; no new copies or renewal.")
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
        "do_not_retain_on_or_after":(intake+timedelta(days=30)).isoformat(),
        "retention":"Maximum 30 days; shorter terms prevail; owner-approved disposal only; no renewal",
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
    deadline = date.fromisoformat(manifest["do_not_retain_on_or_after"])
    copies = [p for p in (ARCHIVE, RAW, "HPI_DATA_002_processed.zip",
                 "HPI_DATA_002_processed", OUTPUT) if (root/p).exists()]
    return {"registered":True,"dataset_id":"HPI-DATA-002","deadline":deadline.isoformat(),
            "retention_due_or_expired":date.today() >= deadline,"known_local_paths":copies,
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
        rejects(lambda: import_rppi(root,day,True,sha(archive),day+timedelta(days=30)))
        rejects(lambda: import_rppi(root,day,True,"bad",day))
        first = import_rppi(root,day,True,sha(archive),day)
        assert first["quality"]["observations"] == 2983
        assert import_rppi(root,day,True,sha(archive),day) == first
        rejects(lambda: import_rppi(root,day+timedelta(days=1),True,sha(archive),day+timedelta(days=1)))
        assert (root/ARCHIVE).read_bytes() == archive
        (root/OUTPUT).write_text("existing different file")
        rejects(lambda: import_rppi(root,day,True,sha(archive),day))
        assert (root/OUTPUT).read_text() == "existing different file"
        (root/".git").mkdir()
        rejects(lambda: workspace(root))
    print("PASS: offline import, limits, retention, exact-version, idempotence, no overwrite and Git boundary checks.")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path.cwd())
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--status",action="store_true")
    p.add_argument("--init-only",action="store_true")
    p.add_argument("--intake-date",type=date.fromisoformat)
    p.add_argument("--terms-reviewed",action="store_true")
    args = p.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        root = workspace(args.root)
        if args.status:
            print(json.dumps(status(root),indent=2))
            return 0
        initialise(root)
        if args.init_only:
            print("Workspace initialised; existing files preserved.")
            return 0
        existing = root / MANIFEST
        if existing.exists():
            prior = json.loads(read_bounded(existing))
            intake = args.intake_date or date.fromisoformat(prior["first_intake_date"])
            reviewed = prior["terms_reviewed_by_owner"] is True or args.terms_reviewed
        else:
            intake = args.intake_date or date.fromisoformat(input("Actual first download date (YYYY-MM-DD): ").strip())
            reviewed = args.terms_reviewed or input("Confirm applicable terms permit this private import and retention (yes/no): ").strip().lower()=="yes"
        manifest = import_rppi(root,intake,reviewed)
        print(json.dumps({"import":"complete","quality":manifest["quality"],"status":status(root)},indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, EOFError, InvalidOperation, zipfile.BadZipFile) as exc:
        print("STOP:",str(exc))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
