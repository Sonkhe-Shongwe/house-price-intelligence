"""One approved GHSL archive, private owner Windows workspace only."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import shutil
import stat
import tempfile
import time
import zipfile

from tools.hpi_data_manager import check_path, workspace
from tools.world_bank_pilot import PinnedHTTPS, Refused, exclusive_json, remaining

HOST = "jeodpp.jrc.ec.europa.eu"
STEM = "GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_R13_C21"
REQUEST = ("/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/"
           "GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100/V1-0/tiles/" + STEM + ".zip")
CAP = 25 * 1024**2
EXPANDED = 256 * 1024**2
CHUNK = 64 * 1024
ATTEMPT = "AE0-ghsl-raster-once"
POINTS = ((28.0, -26.2), (28.1, -26.2))
MEDIA = ("application/zip", "application/x-zip-compressed", "application/octet-stream")
CODES = frozenset(("TRANSPORT", "HTTP", "MEDIA", "FRAMING", "CAP", "ARCHIVE",
                   "MEMBERS", "RIGHTS", "RASTER", "WINDOW", "NODATA", "VALUES",
                   "DEADLINE", "WORKER", "STORAGE", "MEMBERS_COUNT", "MEMBERS_PATH",
                   "MEMBERS_DUPLICATE", "MEMBERS_TYPE", "MEMBERS_MODE", "MEMBERS_ENCRYPTED",
                   "MEMBERS_COMPRESSION", "MEMBERS_SIZE", "MEMBERS_UNKNOWN", "MEMBERS_RASTER",
                   "RIGHTS_MISSING"))


class PilotRefused(Refused):
    def __init__(self, code):
        self.code = code if code in CODES else "WORKER"
        super().__init__(self.code)


class GhslHTTPS(PinnedHTTPS):
    HOSTNAME = HOST


def stream_body(response, target, deadline):
    if response.status != 200:
        raise PilotRefused("HTTP")
    def one(name, default=""):
        values = response.headers.get_all(name, [])
        if len(values) > 1:
            raise PilotRefused("FRAMING")
        return values[0] if values else default
    if (one("Content-Type").split(";")[0].strip().lower() not in MEDIA or
            one("Content-Encoding", "identity").strip().lower() != "identity"):
        raise PilotRefused("MEDIA")
    length, transfer = one("Content-Length"), one("Transfer-Encoding").lower().strip()
    if transfer not in ("", "chunked") or (length and transfer):
        raise PilotRefused("FRAMING")
    expected = None
    if length:
        if not length.isascii() or not length.isdigit() or len(length) > 10:
            raise PilotRefused("FRAMING")
        expected = int(length)
        if not 0 < expected <= CAP:
            raise PilotRefused("CAP")
    count = 0
    digest = hashlib.sha256()
    with target.open("xb") as stream:
        while count < (expected if expected is not None else CAP):
            remaining(deadline)
            raw = response.read(min(CHUNK, (expected if expected is not None else CAP)-count))
            if not raw:
                break
            count += len(raw)
            if count > CAP:
                raise PilotRefused("CAP")
            stream.write(raw)
            digest.update(raw)
        if not count or (expected is not None and count != expected):
            raise PilotRefused("FRAMING")
        if expected is None and count == CAP:
            raise PilotRefused("CAP")
        remaining(deadline)
        stream.flush()
        os.fsync(stream.fileno())
    return {"bytes": count, "sha256": digest.hexdigest()}


def download(target, deadline):
    conn = GhslHTTPS(deadline)
    try:
        remaining(deadline)
        conn.request("GET", REQUEST, headers={"Accept": ", ".join(MEDIA),
                     "Accept-Encoding": "identity", "Connection": "close",
                     "User-Agent": "HPI-bounded-research/1.0"})
        return stream_body(conn.getresponse(), target, deadline)
    finally:
        conn.close()


def member_kind(name):
    # Explicit flat or exact tile-folder paths; never use archive paths for writes.
    for prefix in ("", STEM + "/"):
        if name == prefix + STEM + ".tif":
            return "raster"
        if name == prefix + "copyright.txt":
            return "rights"
        if name in (prefix + STEM + ".tif.ovr", prefix + STEM + ".ovr"):
            return "overview"
    return None


def copy_member(archive, info, out, deadline):
    count = 0
    with archive.open(info) as source, out.open("xb") as dest:
        while True:
            remaining(deadline)
            data = source.read(min(CHUNK, info.file_size-count+1))
            if not data:
                break
            count += len(data)
            if count > info.file_size or count > EXPANDED:
                raise PilotRefused("CAP")
            dest.write(data)
        if count != info.file_size:
            raise PilotRefused("ARCHIVE")
    return count


def inspect_members(infos, deadline):
    """Inspect central directory only. No extraction or arbitrary diagnostic strings.

    OVR is a documented product auxiliary format, not an observed exact tile member.
    Never open or extract it. Bundled rights remain mandatory in the original pilot.
    """
    if not 1 <= len(infos) <= 4:
        raise PilotRefused("MEMBERS_COUNT")
    members, names, total = {}, set(), 0
    for info in infos:
        remaining(deadline)
        name = info.filename
        if (info.orig_filename != name or not name or len(name) > 256 or
                "\\" in name or ":" in name or name.startswith("/") or
                any(part in ("", ".", "..") for part in name.rstrip("/").split("/")) or
                any(ord(ch) < 32 or ord(ch) > 126 for ch in name)):
            raise PilotRefused("MEMBERS_PATH")
        if name.casefold() in names:
            raise PilotRefused("MEMBERS_DUPLICATE")
        names.add(name.casefold())
        mode = stat.S_IFMT(info.external_attr >> 16)
        if info.flag_bits & 1:
            raise PilotRefused("MEMBERS_ENCRYPTED")
        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise PilotRefused("MEMBERS_COMPRESSION")
        if info.is_dir():
            if name != STEM + "/":
                raise PilotRefused("MEMBERS_UNKNOWN")
            if mode not in (0, stat.S_IFDIR):
                raise PilotRefused("MEMBERS_TYPE")
            if info.file_size:
                raise PilotRefused("MEMBERS_SIZE")
            continue
        if mode not in (0, stat.S_IFREG):
            raise PilotRefused("MEMBERS_TYPE")
        if (info.external_attr >> 16) & 0o111:
            raise PilotRefused("MEMBERS_MODE")
        if not 0 < info.file_size <= EXPANDED:
            raise PilotRefused("MEMBERS_SIZE")
        total += info.file_size
        if total > EXPANDED:
            raise PilotRefused("CAP")
        kind = member_kind(name)
        if not kind:
            raise PilotRefused("MEMBERS_UNKNOWN")
        if kind in members:
            raise PilotRefused("MEMBERS_DUPLICATE")
        if kind == "rights" and info.file_size > 16384:
            raise PilotRefused("CAP")
        members[kind] = info
    if "raster" not in members:
        raise PilotRefused("MEMBERS_RASTER")
    return members, total


def unpack(archive_path, directory, deadline):
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members, total = inspect_members(archive.infolist(), deadline)
            if "rights" not in members:
                raise PilotRefused("RIGHTS_MISSING")
            rights_path = directory / "copyright.txt"
            copy_member(archive, members["rights"], rights_path, deadline)
            rights = rights_path.read_text(encoding="utf-8-sig")
            normal = " ".join(rights.casefold().split())
            # Conservative documentary gate, not an automated legal determination.
            if (not any(s in normal for s in ("cc by 4.0", "creativecommons.org/licenses/by/4.0",
                       "creative commons attribution 4.0")) or
                    not any(s in normal for s in ("european commission", "european union", "joint research centre")) or
                    any(s in normal for s in ("non-commercial", "noncommercial", "no derivatives",
                        "all rights reserved", "permission required", "not permitted", "prohibited"))):
                raise PilotRefused("RIGHTS")
            raster = directory / "tile.tif"
            copy_member(archive, members["raster"], raster, deadline)
            return raster, rights, total
    except (zipfile.BadZipFile, UnicodeError, RuntimeError, NotImplementedError) as exc:
        raise PilotRefused("ARCHIVE") from exc


def analyse(raster):
    import rasterio
    from rasterio.crs import CRS
    from rasterio.windows import Window, bounds
    from pyproj import Transformer
    with raster.open("rb") as stream:
        if stream.read(4) not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
            raise PilotRefused("RASTER")
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", PROJ_NETWORK="OFF",
                      GDAL_PAM_ENABLED="NO", GDAL_CACHEMAX=32*1024**2,
                      GDAL_NUM_THREADS="1"):
        with rasterio.open(raster, driver="GTiff", sharing=False) as src:
            t = src.transform
            if (src.driver != "GTiff" or src.count != 1 or src.dtypes != ("uint16",)
                    or src.crs != CRS.from_string("ESRI:54009") or src.nodata != 65535
                    or src.width != 10000 or src.height != 10000
                    or (t.a,t.b,t.d,t.e) != (100,0,0,-100)
                    or not all(float(v).is_integer() for v in (t.c,t.f))
                    or src.scales != (1.0,) or src.offsets != (0.0,)
                    or src.block_shapes[0][0]*src.block_shapes[0][1]*2 > 16*1024**2):
                raise PilotRefused("RASTER")
            transformer = Transformer.from_crs("EPSG:4326", "ESRI:54009", always_xy=True)
            windows, output = [], []
            for lon,lat in POINTS:
                x,y = transformer.transform(lon,lat)
                row,col = src.index(x,y)
                r,c = row-5,col-5
                if r < 0 or c < 0 or r+10 > src.height or c+10 > src.width:
                    raise PilotRefused("WINDOW")
                if any(r < rr+10 and rr < r+10 and c < cc+10 and cc < c+10 for rr,cc in windows):
                    raise PilotRefused("WINDOW")
                windows.append((r,c))
                win = Window(c,r,10,10)
                data = src.read(1,window=win,masked=True)
                if data.shape != (10,10) or data.mask.any():
                    raise PilotRefused("NODATA")
                if (data.data > 10000).any():
                    raise PilotRefused("VALUES")
                total = sum(int(v) for v in data.data.flat)
                output.append({"reference_lon":lon,"reference_lat":lat,"row":r,"col":c,
                    "bounds_m":list(bounds(win,t)), "cells":100,"built_m2":total,
                    "coverage_pct":format(Decimal(total)/10000,"f")})
            return {"crs":"ESRI:54009","transform":list(t)[:6],
                    "width":src.width,"height":src.height,"nodata":65535,"windows":output,
                    "difference_percentage_points":format(Decimal(output[1]["coverage_pct"])-Decimal(output[0]["coverage_pct"]),"f")}


def download_worker(directory, deadline):
    try:
        result = download(directory/"source.zip",deadline)
        exclusive_json(directory/"download.json",{"status":"PASS",**result})
    except Exception as exc:
        exclusive_json(directory/"download.json",{"status":"STOP",
            "reason":exc.code if isinstance(exc,PilotRefused) else "TRANSPORT"})


def raster_worker(directory, deadline):
    try:
        raster, rights, size = unpack(directory/"source.zip",directory,deadline)
        result = analyse(raster)
        remaining(deadline)
        exclusive_json(directory/"analysis.json",{"status":"PASS","expanded_bytes":size,
            "copyright":rights,**result})
    except Exception as exc:
        exclusive_json(directory/"analysis.json",{"status":"STOP",
            "reason":exc.code if isinstance(exc,PilotRefused) else "RASTER"})


def supervise(worker, directory, report, seconds):
    deadline = time.monotonic()+seconds
    child = mp.get_context("spawn").Process(target=worker,args=(directory,deadline),daemon=True)
    child.start()
    try:
        child.join(timeout=max(0,deadline-time.monotonic()))
        if child.is_alive() or time.monotonic() >= deadline:
            raise PilotRefused("DEADLINE")
        if child.exitcode != 0:
            raise PilotRefused("WORKER")
        path = directory/report
        if not path.is_file() or path.stat().st_size > 32768:
            raise PilotRefused("WORKER")
        result=json.loads(path.read_text(encoding="utf-8"))
        if result.get("status") != "PASS":
            raise PilotRefused(result.get("reason","WORKER"))
        return result
    finally:
        if child.is_alive():
            child.kill()
            child.join(timeout=2)
        if child.is_alive():
            raise PilotRefused("WORKER")
        child.close()


def preflight():
    import rasterio
    import pyproj
    if rasterio.__version__ != "1.5.2" or pyproj.__version__ != "3.7.2":
        raise PilotRefused("WORKER")
    # Fail before consuming permission on missing CRS support.
    pyproj.Transformer.from_crs("EPSG:4326","ESRI:54009",always_xy=True).transform(*POINTS[0])


def execute(root, runner=supervise):
    preflight()
    root=workspace(root)
    for target in (root/"01_Source_Catalogue",root/"02_Raw_Data",root/"07_Reports"):
        check_path(target)
        if not target.is_dir():
            raise PilotRefused("STORAGE")
    if shutil.disk_usage(root).free < 512*1024**2:
        raise PilotRefused("STORAGE")
    attempt=root/"02_Raw_Data"/ATTEMPT
    check_path(attempt)
    try:
        attempt.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise Refused("GHSL attempt already consumed; never remove or replay") from exc
    started=datetime.now(timezone.utc)
    exclusive_json(attempt/"attempt.json",{"approval":"2026-11-27 GHSL exact pilot",
        "started_utc":started.isoformat(),"max_requests":1,"max_body_bytes":CAP})
    download_result=None
    # Only newly created transient files are removed on exit; prior evidence untouched.
    with tempfile.TemporaryDirectory(dir=attempt,prefix="staging-") as temp:
        directory=Path(temp)
        exclusive_json(attempt/"dispatch-1.json",{"host":HOST,"path":REQUEST})
        try:
            download_result=runner(download_worker,directory,"download.json",90)
            analysis=runner(raster_worker,directory,"analysis.json",90)
            bundle={**analysis,"source":"European Commission JRC, Pesaresi and Politis (2023)",
                    "doi":"10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA",
                    "licence":"CC BY 4.0","epoch":2020,"tile":STEM,"endpoint":"https://"+HOST+REQUEST,
                    "acquired_utc":started.isoformat(),"requests":1,"bytes":download_result["bytes"],
                    "sha256":download_result["sha256"],"registered":False,
                    "limitation":"Historical estimated built-up surface / whole grid area; not property floor area, current conditions or land-only denominator"}
            exclusive_json(directory/"validated.json",bundle)
            check_path(attempt/"source.zip")
            check_path(attempt/"validated.json")
            os.link(directory/"source.zip",attempt/"source.zip")
            os.link(directory/"validated.json",attempt/"validated.json")
        except (Refused,OSError) as exc:
            result={"status":"STOP","reason":exc.code if isinstance(exc,PilotRefused) else "STORAGE",
                    "bytes":None if download_result is None else download_result["bytes"],
                    "sha256":None if download_result is None else download_result["sha256"]}
            exclusive_json(attempt/"refusal.json",result)
            return result
    return {"status":"PASS","requests":1,"bytes":bundle["bytes"],"sha256":bundle["sha256"],
            "cells":200,"windows":2,"registered":False,"result":"validated.json"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    if not args.execute or os.name!="nt":
        parser.error("explicit --execute on owner Windows required")
    try:
        checkout=Path(__file__).absolute().parents[1]
        check_path(checkout)
        result=execute(checkout.parent/"HPI-Data-Workspace")
    except (ImportError,ValueError,OSError) as exc:
        print("STOP:",str(exc) if isinstance(exc,Refused) else type(exc).__name__)
        print("Do not rerun; preserve any attempt marker.")
        return 1
    print(json.dumps(result,sort_keys=True))
    return 0 if result["status"]=="PASS" else 1


if __name__=="__main__":
    raise SystemExit(main())
