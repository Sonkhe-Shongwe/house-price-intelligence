"""Approved final staged GHSL experiment. Original attempt is never reused."""
import argparse
from datetime import datetime, timezone
import hashlib
import math
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import tempfile
import time
import zipfile

from tools import ghsl_raster_pilot as p
from tools.hpi_data_manager import check_path, workspace
from tools.world_bank_pilot import PinnedHTTPS, Refused, exclusive_json, remaining

HOST = "ghsl.jrc.ec.europa.eu"
REQUEST = "/download/GHSL_data_54009_shapefile.zip"
CAP = 2 * 1024**2
EXPANDED = 16 * 1024**2
LAYER = "GHSL2_0_MWD_L1_tile_schema_land"
TILE = "R13_C21"
ATTEMPT = "AE0-ghsl-staged-once"
NOTICE = "https://jeodpp.jrc.ec.europa.eu" + p.REQUEST.rsplit("/",1)[0] + "/copyright.txt"
REQUIRED = {".shp", ".shx", ".dbf", ".prj"}
OPTIONAL = {".cpg", ".sbn", ".sbx", ".shp.xml"}
REASONS = {"INDEX_SCHEMA","INDEX_GEOMETRY","INDEX_CRS","INDEX_MEMBERS","INDEX_CAP",
           "INDEX_RIGHTS","INDEX_TRANSPORT","INDEX_STORAGE","INDEX_WORKER","INDEX_DEADLINE",
           "RASTER_MISMATCH"} | p.CODES


class StagedRefused(Refused):
    def __init__(self, code):
        self.code = code if code in REASONS else "INDEX_WORKER"
        super().__init__(self.code)


class IndexHTTPS(PinnedHTTPS):
    HOSTNAME = HOST


def index_download(directory, deadline):
    conn = IndexHTTPS(deadline)
    try:
        remaining(deadline)
        conn.request("GET", REQUEST, headers={"Accept": ", ".join(p.MEDIA),
                    "Accept-Encoding": "identity", "Connection": "close",
                    "User-Agent": "HPI-bounded-research/1.0"})
        return p.stream_body(conn.getresponse(), directory/"index.zip", deadline, cap=CAP)
    finally:
        conn.close()


def inspect_index(archive, directory, deadline):
    """Allow exact land-layer files, no arbitrary extraction paths or native sidecars."""
    entries = archive.infolist()
    if not 4 <= len(entries) <= 20:
        raise StagedRefused("INDEX_MEMBERS")
    seen, selected, total = set(), {}, 0
    for item in entries:
        remaining(deadline)
        name = item.filename
        mode = stat.S_IFMT(item.external_attr >> 16)
        if (item.orig_filename != name or name.casefold() in seen or
            item.flag_bits & 1 or item.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED)):
            raise StagedRefused("INDEX_MEMBERS")
        seen.add(name.casefold())
        if item.is_dir():
            if name != LAYER+"/" or item.file_size or mode not in (0,stat.S_IFDIR):
                raise StagedRefused("INDEX_MEMBERS")
            continue
        if (mode not in (0,stat.S_IFREG) or (item.external_attr>>16)&0o111 or
            not 0 < item.file_size <= EXPANDED):
            raise StagedRefused("INDEX_MEMBERS")
        total += item.file_size
        if total > EXPANDED:
            raise StagedRefused("INDEX_CAP")
        prefix = LAYER+"/" if name.startswith(LAYER+"/") else ""
        base = name[len(prefix):]
        if base == "copyright.txt":
            ext = "rights"
        elif base.startswith(LAYER):
            ext = base[len(LAYER):]
        else:
            raise StagedRefused("INDEX_MEMBERS")
        if ext not in REQUIRED|OPTIONAL|{"rights"} or ext in selected:
            raise StagedRefused("INDEX_MEMBERS")
        selected[ext] = item
    if not REQUIRED <= selected.keys():
        raise StagedRefused("INDEX_MEMBERS")
    if "rights" in selected:
        item=selected["rights"]
        if item.file_size > 16384:
            raise StagedRefused("INDEX_RIGHTS")
        text=archive.read(item).decode("utf-8-sig").casefold()
        if (not any(s in text for s in ("cc by 4.0","creativecommons.org/licenses/by/4.0",
                "creative commons attribution 4.0")) or any(s in text for s in
                ("non-commercial","noncommercial","all rights reserved","no derivatives",
                 "not permitted","prohibited","permission required"))):
            raise StagedRefused("INDEX_RIGHTS")
    for ext in REQUIRED:
        p.copy_member(archive, selected[ext], directory/("grid"+ext), deadline)
    return total


def rectangle(shape):
    if shape.shapeType != 5 or list(shape.parts)!=[0] or len(shape.points)!=5:
        raise StagedRefused("INDEX_GEOMETRY")
    points=[tuple(x) for x in shape.points]
    if points[0]!=points[-1] or not all(math.isfinite(v) for xy in points for v in xy):
        raise StagedRefused("INDEX_GEOMETRY")
    left,bottom,right,top=map(float,shape.bbox)
    corners={(left,bottom),(left,top),(right,bottom),(right,top)}
    if set(points[:-1])!=corners or any(a[0]!=b[0] and a[1]!=b[1] for a,b in zip(points,points[1:])):
        raise StagedRefused("INDEX_GEOMETRY")
    if not all(float(v).is_integer() for v in (left,bottom,right,top)):
        raise StagedRefused("INDEX_GEOMETRY")
    if right-left!=1000000 or top-bottom!=1000000:
        raise StagedRefused("INDEX_GEOMETRY")
    return [left,bottom,right,top]


def verify_index(directory, deadline):
    import shapefile
    from pyproj import CRS, Transformer
    from pyproj import network
    network.set_network_enabled(False)
    try:
        with zipfile.ZipFile(directory/"index.zip") as z:
            total=inspect_index(z,directory,deadline)
        prj=directory/"grid.prj"
        if prj.stat().st_size > 16384 or not CRS.from_wkt(prj.read_text(encoding="utf-8-sig")).equals(
                CRS.from_user_input("ESRI:54009"),ignore_axis_order=True):
            raise StagedRefused("INDEX_CRS")
        with (directory/"grid.dbf").open("rb") as f:
            header=f.read(32)
        if len(header)!=32:
            raise StagedRefused("INDEX_SCHEMA")
        count, hlen, rlen=struct.unpack_from("<IHH",header,4)
        if not 1<=count<=700 or not 33<=hlen<=4096 or not 1<=rlen<=4096:
            raise StagedRefused("INDEX_SCHEMA")
        with shapefile.Reader(str(directory/"grid"),encoding="utf-8") as reader:
            fields=[f[0] for f in reader.fields[1:]]
            if len(reader)!=count or reader.shapeType!=5 or fields.count("tile_id")!=1:
                raise StagedRefused("INDEX_SCHEMA")
            found=None
            ids=set()
            for record in reader.iterShapeRecords():
                remaining(deadline)
                tid=record.record["tile_id"]
                if not isinstance(tid,str) or not re.fullmatch(r"R[1-9][0-9]?_C[1-9][0-9]?",tid) or tid in ids:
                    raise StagedRefused("INDEX_SCHEMA")
                ids.add(tid)
                if tid==TILE:
                    found=rectangle(record.shape)
            if len(ids)!=count or found is None:
                raise StagedRefused("INDEX_SCHEMA")
        left,bottom,right,top=found
        transformer=Transformer.from_crs("EPSG:4326","ESRI:54009",always_xy=True)
        for point in p.POINTS:
            x,y=transformer.transform(*point)
            if not math.isfinite(x) or not math.isfinite(y):
                raise StagedRefused("INDEX_GEOMETRY")
            r,c=math.floor((top-y)/100),math.floor((x-left)/100)
            if not (5<=r<=9995 and 5<=c<=9995):
                raise StagedRefused("INDEX_GEOMETRY")
        return {"tile_id":TILE,"bounds":found,"width":10000,"height":10000,
                "crs":"ESRI:54009","features_inspected":count,"expanded_bytes":total}
    except StagedRefused:
        raise
    except (ValueError,OSError,UnicodeError,zipfile.BadZipFile,shapefile.ShapefileException):
        raise StagedRefused("INDEX_SCHEMA") from None


def report(directory, name, action):
    try:
        result={"status":"PASS",**action()}
    except Exception as exc:
        result={"status":"STOP","reason":getattr(exc,"code","INDEX_WORKER")}
    exclusive_json(directory/name,result)


def index_download_worker(directory,deadline):
    report(directory,"index-download.json",lambda:index_download(directory,deadline))


def index_worker(directory,deadline):
    report(directory,"index-analysis.json",lambda:verify_index(directory,deadline))


def staged_raster_worker(directory,deadline):
    import json
    def action():
        index=json.loads((directory/"index-analysis.json").read_text(encoding="utf-8"))
        if index.get("status")!="PASS" or index.get("tile_id")!=TILE:
            raise StagedRefused("INDEX_GEOMETRY")
        raster,rights,total=p.unpack(directory/"source.zip",directory,deadline,staged=True)
        result=p.analyse(raster,expected_bounds=index["bounds"])
        remaining(deadline)
        return {"expanded_bytes":total,"copyright":rights,**result}
    report(directory,"analysis.json",action)


def supervise(worker,directory,name,seconds):
    # Original supervisor has bounded reports and killable children. Extend only reason mapping.
    import multiprocessing as mp
    import json
    deadline=time.monotonic()+seconds
    child=mp.get_context("spawn").Process(target=worker,args=(directory,deadline),daemon=True)
    child.start()
    try:
        child.join(timeout=max(0,deadline-time.monotonic()))
        if child.is_alive() or time.monotonic()>=deadline:
            raise StagedRefused("DEADLINE")
        file=directory/name
        if child.exitcode!=0 or not file.is_file() or file.stat().st_size>32768:
            raise StagedRefused("INDEX_WORKER")
        result=json.loads(file.read_text(encoding="utf-8"))
        if result.get("status")!="PASS":
            raise StagedRefused(result.get("reason"))
        return result
    finally:
        if child.is_alive():
            child.kill()
            child.join(timeout=2)
        if child.is_alive():
            raise StagedRefused("INDEX_WORKER")
        child.close()


def check_digest(file, evidence, cap):
    count=file.stat().st_size
    if not 0<count<=cap or count!=evidence.get("bytes"):
        raise StagedRefused("CAP")
    with file.open("rb") as f:
        digest=hashlib.file_digest(f,"sha256").hexdigest()
    if digest!=evidence.get("sha256"):
        raise StagedRefused("INDEX_WORKER")


def execute(root,runner=supervise):
    import shapefile
    if shapefile.__version__!="2.3.1":
        raise StagedRefused("INDEX_WORKER")
    p.preflight()
    root=workspace(root)
    for target in (root/"01_Source_Catalogue",root/"02_Raw_Data",root/"07_Reports"):
        check_path(target)
        if not target.is_dir():
            raise StagedRefused("STORAGE")
    if shutil.disk_usage(root).free<512*1024**2:
        raise StagedRefused("STORAGE")
    attempt=root/"02_Raw_Data"/ATTEMPT
    check_path(attempt)
    try:
        attempt.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise Refused("staged GHSL attempt consumed; never replay") from exc
    started=datetime.now(timezone.utc)
    exclusive_json(attempt/"attempt.json",{"approval":"2026-11-27 staged GHSL",
        "started_utc":started.isoformat(),"max_requests":2,"max_body_bytes":CAP+p.CAP})
    requests=0
    index_download_result=None
    raster_download_result=None
    index_validated=False
    with tempfile.TemporaryDirectory(dir=attempt,prefix="staging-") as temp:
        directory=Path(temp)
        try:
            exclusive_json(attempt/"dispatch-1.json",{"host":HOST,"path":REQUEST})
            requests=1
            index_download_result=runner(index_download_worker,directory,"index-download.json",90)
            check_digest(directory/"index.zip",index_download_result,CAP)
            index=runner(index_worker,directory,"index-analysis.json",90)
            if (index.get("tile_id")!=TILE or index.get("crs")!="ESRI:54009" or
                    index.get("width")!=10000 or index.get("height")!=10000):
                raise StagedRefused("INDEX_GEOMETRY")
            exclusive_json(attempt/"index-validated.json",{"index":index,"source":"European Commission JRC",
                "endpoint":"https://"+HOST+REQUEST,"acquired_utc":started.isoformat(),
                "rights":"GHSL publisher reuse terms; attribution required",**index_download_result})
            os.link(directory/"index.zip",attempt/"index.zip")
            index_validated=True
            exclusive_json(attempt/"dispatch-2.json",{"host":p.HOST,"path":p.REQUEST})
            requests=2
            raster_download_result=runner(p.download_worker,directory,"download.json",90)
            check_digest(directory/"source.zip",raster_download_result,p.CAP)
            analysis=runner(staged_raster_worker,directory,"analysis.json",90)
            if list(analysis["transform"])[:6]!=[100,0,index["bounds"][0],0,-100,index["bounds"][3]]:
                raise StagedRefused("RASTER_MISMATCH")
            bundle={**analysis,"source":"European Commission JRC, Pesaresi and Politis (2023)",
                "doi":"10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA",
                "licence":"CC BY 4.0","publisher_notice":NOTICE,"epoch":2020,"tile":p.STEM,
                "index":index,"index_sha256":index_download_result["sha256"],
                "index_bytes":index_download_result["bytes"],"endpoint":"https://"+p.HOST+p.REQUEST,
                "acquired_utc":started.isoformat(),"requests":2,"registered":False,
                **raster_download_result,
                "limitation":"2020 estimated built-up surface, whole grid denominator; not parcel, dwelling or current conditions"}
            exclusive_json(directory/"validated.json",bundle)
            os.link(directory/"source.zip",attempt/"source.zip")
            os.link(directory/"validated.json",attempt/"validated.json")
        except (Refused,OSError,ValueError,KeyError) as exc:
            result={"status":"STOP","reason":getattr(exc,"code","STORAGE"),"requests":requests,
                "index_validated":index_validated,"index_bytes":None if index_download_result is None else index_download_result["bytes"],
                "raster_bytes":None if raster_download_result is None else raster_download_result["bytes"]}
            exclusive_json(attempt/"refusal.json",result)
            return result
    return {"status":"PASS","requests":2,"index_validated":True,
        "index_bytes":bundle["index_bytes"],"raster_bytes":bundle["bytes"],
        "total_bytes":bundle["index_bytes"]+bundle["bytes"],"sha256":bundle["sha256"],
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
        return 1
    import json
    print(json.dumps(result,sort_keys=True))
    return 0 if result["status"]=="PASS" else 1


if __name__=="__main__":
    raise SystemExit(main())
