"""Synthetic archives and raster windows only; no network."""
from email.message import Message
import hashlib
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile
import stat
import socket

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.windows import Window
from pyproj import Transformer
from tools import ghsl_raster_pilot as p

RIGHTS=b"European Commission Joint Research Centre. CC BY 4.0."


def make_raster(path, bad=None):
    # Sparse compressed invented full-size grid; write only two 10x10 windows.
    t=from_origin(2500000,-3000000,100,100)
    with rasterio.open(path,"w",driver="GTiff",width=10000,height=10000,
        count=1,dtype="uint16",crs="ESRI:54009",transform=t,nodata=65535,
        tiled=True,blockxsize=256,blockysize=256,compress="deflate",SPARSE_OK=True) as dst:
        tr=Transformer.from_crs("EPSG:4326","ESRI:54009",always_xy=True)
        for i,point in enumerate(p.POINTS):
            row,col=dst.index(*tr.transform(*point))
            data=np.full((10,10),2000+3000*i,dtype=np.uint16)
            if i==0 and bad is not None:
                data[0,0]=bad
            dst.write(data,1,window=Window(col-5,row-5,10,10))


def archive(directory, rights=RIGHTS, extra=None):
    tif=directory/"fixture.tif"
    make_raster(tif)
    out=directory/"source.zip"
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
        info=zipfile.ZipInfo(p.STEM+".tif")
        info.external_attr=(stat.S_IFREG|0o600)<<16
        info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,tif.read_bytes())
        if rights is not None:
            z.writestr("copyright.txt",rights)
        if extra:
            z.writestr(extra,b"x")
    return out


class Response:
    status=200
    def __init__(self,data,media="application/zip",length=None):
        self.data=data
        self.headers=Message()
        self.headers["Content-Type"]=media
        self.headers["Content-Length"]=str(len(data) if length is None else length)
    def read(self,n):
        data,self.data=self.data[:n],self.data[n:]
        return data


def sleeper(directory,deadline):
    time.sleep(10)


class GhslTests(unittest.TestCase):
    def test_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"source.zip"
            raw=b"fictional zip bytes"
            self.assertEqual(p.stream_body(Response(raw),target,time.monotonic()+5),
                {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()})
            for response,reason in ((Response(b"x",length=p.CAP+1),"CAP"),
                                    (Response(b"x",media="text/html"),"MEDIA"),
                                    (Response(b"x",length=2),"FRAMING")):
                with self.assertRaisesRegex(p.PilotRefused,reason):
                    p.stream_body(response,Path(tmp)/("bad-"+reason),time.monotonic()+5)
        with patch.object(socket,"getaddrinfo",return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,"",("127.0.0.1",443))]):
            with self.assertRaises(p.Refused):
                p.GhslHTTPS(time.monotonic()+5).connect()

    def test_exact_request(self):
        self.assertEqual(p.HOST,"jeodpp.jrc.ec.europa.eu")
        self.assertTrue(p.REQUEST.endswith("/tiles/"+p.STEM+".zip"))
        with patch.object(p,"GhslHTTPS") as conn,patch.object(p,"stream_body",return_value={"bytes":1}):
            p.download(Path("unused"),time.monotonic()+5)
            self.assertEqual(conn.return_value.request.call_count,1)
            self.assertEqual(conn.return_value.request.call_args.args,("GET",p.REQUEST))

    def test_archive_and_calculation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            tif,rights,size=p.unpack(archive(root),root,time.monotonic()+30)
            result=p.analyse(tif)
            self.assertEqual([w["built_m2"] for w in result["windows"]],[200000,500000])
            self.assertEqual([w["coverage_pct"] for w in result["windows"]],["20","50"])
            self.assertEqual(result["difference_percentage_points"],"30")
            self.assertLess(size,p.EXPANDED)

    def test_archive_rejections(self):
        for rights,extra,reason in ((None,None,"RIGHTS_MISSING"),(b"All rights reserved",None,"RIGHTS"),
             (RIGHTS,"../escape.txt","MEMBERS"),(RIGHTS,"evil.exe","MEMBERS")):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                with self.assertRaisesRegex(p.PilotRefused,reason):
                    p.unpack(archive(root,rights,extra),root,time.monotonic()+30)

    def test_documented_overview_is_never_extracted(self):
        for suffix in (".tif.ovr", ".ovr"):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                source=archive(root,extra=p.STEM+suffix)
                tif,rights,total=p.unpack(source,root,time.monotonic()+30)
                self.assertEqual(p.analyse(tif)["difference_percentage_points"],"30")
                self.assertFalse((root/(p.STEM+suffix)).exists())
                self.assertFalse((root/"tile.tif.ovr").exists())
                self.assertIn(b"CC BY 4.0",rights.encode())

    def test_specific_safe_inventory_reasons(self):
        def item(name, size=1, mode=stat.S_IFREG|0o600, flags=0, compression=zipfile.ZIP_STORED):
            info=zipfile.ZipInfo(name)
            info.file_size=size
            info.external_attr=mode<<16
            info.flag_bits=flags
            info.compress_type=compression
            return info
        raster=item(p.STEM+".tif")
        rights=item("copyright.txt")
        for info,reason in (
            (item("../unknown"),"MEMBERS_PATH"),
            (item("secret.exe"),"MEMBERS_UNKNOWN"),
            (item(p.STEM+".ovr",mode=stat.S_IFLNK|0o600),"MEMBERS_TYPE"),
            (item(p.STEM+".ovr",mode=stat.S_IFREG|0o700),"MEMBERS_MODE"),
            (item(p.STEM+".ovr",flags=1),"MEMBERS_ENCRYPTED"),
            (item(p.STEM+".ovr",compression=zipfile.ZIP_BZIP2),"MEMBERS_COMPRESSION"),
            (item(p.STEM+".ovr",size=0),"MEMBERS_SIZE"),
            (item(p.STEM+".ovr",size=p.EXPANDED),"CAP"),
            (item(p.STEM+"/"+p.STEM+".tif"),"MEMBERS_DUPLICATE"),
        ):
            with self.subTest(reason=reason), self.assertRaisesRegex(p.PilotRefused,"^"+reason+"$"):
                p.inspect_members([raster,rights,info],time.monotonic()+5)
        with self.assertRaisesRegex(p.PilotRefused,"^MEMBERS_COUNT$"):
            p.inspect_members([raster]*5,time.monotonic()+5)
        with self.assertRaisesRegex(p.PilotRefused,"^MEMBERS_RASTER$"):
            p.inspect_members([rights],time.monotonic()+5)
        members,total=p.inspect_members([raster],time.monotonic()+5)
        self.assertEqual(set(members),{"raster"})
        self.assertEqual(total,1)

    def test_unknown_member_reason_survives_worker_and_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for d in ("01_Source_Catalogue","02_Raw_Data","07_Reports"): (root/d).mkdir()
            def runner(worker,directory,report,seconds):
                if worker is p.download_worker:
                    raw=archive(directory,extra="private_unknown.exe").read_bytes()
                    return {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
                return p.supervise(worker,directory,report,seconds)
            result=p.execute(root,runner)
            attempt=root/"02_Raw_Data"/p.ATTEMPT
            self.assertEqual(result["reason"],"MEMBERS_UNKNOWN")
            self.assertNotIn("private_unknown",(attempt/"refusal.json").read_text())
            self.assertFalse((attempt/"source.zip").exists())
            self.assertFalse((attempt/"validated.json").exists())

    def test_nodata_and_invalid_values(self):
        for value,reason in ((65535,"NODATA"),(10001,"VALUES")):
            with tempfile.TemporaryDirectory() as tmp:
                tif=Path(tmp)/"fixture.tif"
                make_raster(tif,value)
                with self.assertRaisesRegex(p.PilotRefused,reason):
                    p.analyse(tif)

    def test_wrong_crs_resolution_extent_and_overlap(self):
        for crs,res,reason in (("EPSG:3857",100,"RASTER"),("ESRI:54009",200,"RASTER")):
            with tempfile.TemporaryDirectory() as tmp:
                tif=Path(tmp)/"fixture.tif"
                with rasterio.open(tif,"w",driver="GTiff",width=10000,height=10000,count=1,
                    dtype="uint16",crs=crs,nodata=65535,transform=from_origin(2500000,-3000000,res,res),
                    tiled=True,SPARSE_OK=True): pass
                with self.assertRaisesRegex(p.PilotRefused,reason):
                    p.analyse(tif)
        with tempfile.TemporaryDirectory() as tmp:
            tif=Path(tmp)/"fixture.tif"
            make_raster(tif)
            for points in (((0,0),p.POINTS[1]),(p.POINTS[0],p.POINTS[0])):
                with patch.object(p,"POINTS",points),self.assertRaisesRegex(p.PilotRefused,"WINDOW"):
                    p.analyse(tif)

    def test_worker_deadline(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(p.PilotRefused,"DEADLINE"):
                p.supervise(sleeper,Path(tmp),"unused.json",0.5)

    def test_success_and_consumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for d in ("01_Source_Catalogue","02_Raw_Data","07_Reports"): (root/d).mkdir()
            calls=[]
            def runner(worker, directory,report,seconds):
                calls.append(report)
                if worker is p.download_worker:
                    raw=archive(directory).read_bytes()
                    return {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
                tif,rights,size=p.unpack(directory/"source.zip",directory,time.monotonic()+30)
                return {"status":"PASS","copyright":rights,"expanded_bytes":size,**p.analyse(tif)}
            result=p.execute(root,runner)
            self.assertEqual(result["cells"],200)
            attempt=root/"02_Raw_Data"/p.ATTEMPT
            self.assertTrue((attempt/"validated.json").exists())
            self.assertTrue((attempt/"source.zip").exists())
            with self.assertRaisesRegex(p.Refused,"consumed"): p.execute(root,runner)
            self.assertEqual(calls,["download.json","analysis.json"])

    def test_failure_no_accepted_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for d in ("01_Source_Catalogue","02_Raw_Data","07_Reports"): (root/d).mkdir()
            def runner(worker,directory,report,seconds):
                (directory/"source.zip").write_bytes(b"unvalidated")
                raise p.PilotRefused("ARCHIVE")
            result=p.execute(root,runner)
            attempt=root/"02_Raw_Data"/p.ATTEMPT
            self.assertEqual(result["reason"],"ARCHIVE")
            self.assertFalse((attempt/"validated.json").exists())
            self.assertFalse((attempt/"source.zip").exists())
            with self.assertRaisesRegex(p.Refused,"consumed"): p.execute(root,runner)


if __name__=="__main__":
    unittest.main()
