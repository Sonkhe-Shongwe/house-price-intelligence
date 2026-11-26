"""Invented index and raster fixtures only."""
import hashlib
from pathlib import Path
import tempfile
import time
import unittest
import zipfile

import shapefile
from pyproj import CRS
from tools import ghsl_staged_pilot as s
from tools import ghsl_raster_pilot as p
from tools.test_ghsl_raster_pilot import archive, Response


def index_fixture(directory, tile=s.TILE, crs="ESRI:54009", left=2500000, top=-3000000, extra=None):
    stem=directory/s.LAYER
    with shapefile.Writer(str(stem),shapeType=5) as w:
        w.field("tile_id","C",16)
        r,b=left+1000000,top-1000000
        w.poly([[[left,b],[left,top],[r,top],[r,b],[left,b]]])
        w.record(tile)
    stem.with_suffix(".prj").write_text(CRS.from_user_input(crs).to_wkt(),encoding="utf-8")
    with zipfile.ZipFile(directory/"index.zip","w") as z:
        for ext in s.REQUIRED:
            file=stem.with_suffix(ext)
            z.write(file,file.name)
        if extra:
            z.writestr(extra,b"x")
    return directory/"index.zip"


def evidence(file):
    raw=file.read_bytes()
    return {"status":"PASS","bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}


class StagedTests(unittest.TestCase):
    def test_index_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            index_fixture(d)
            result=s.verify_index(d,time.monotonic()+30)
            self.assertEqual(result["bounds"],[2500000,-4000000,3500000,-3000000])
            self.assertEqual(result["features_inspected"],1)

    def test_index_rejections(self):
        for kwargs,reason in (({"tile":"R1_C1"},"INDEX_SCHEMA"),
                ({"crs":"EPSG:3857"},"INDEX_CRS"),({"left":0},"INDEX_GEOMETRY"),
                ({"extra":"../escape.exe"},"INDEX_MEMBERS")):
            with tempfile.TemporaryDirectory() as temp:
                d=Path(temp)
                index_fixture(d,**kwargs)
                with self.assertRaisesRegex(s.StagedRefused,reason):
                    s.verify_index(d,time.monotonic()+30)

    def test_index_transfer_cap(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(p.PilotRefused,"CAP"):
                p.stream_body(Response(b"x",length=s.CAP+1),Path(temp)/"index.zip",
                              time.monotonic()+5,cap=s.CAP)

    def test_external_rights_only_staged_and_pdf_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            file=archive(d,rights=None,extra="GHSL_Data_Package_2023_light.pdf")
            with self.assertRaises(p.PilotRefused):
                p.unpack(file,d,time.monotonic()+30)
            tif,rights,total=p.unpack(file,d,time.monotonic()+30,staged=True)
            self.assertIn("External",rights)
            self.assertFalse((d/"GHSL_Data_Package_2023_light.pdf").exists())
            self.assertEqual(p.analyse(tif,expected_bounds=[2500000,-4000000,3500000,-3000000])["difference_percentage_points"],"30")
            with self.assertRaisesRegex(p.PilotRefused,"RASTER"):
                p.analyse(tif,expected_bounds=[0,0,1,1])
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            with self.assertRaisesRegex(p.PilotRefused,"RIGHTS"):
                p.unpack(archive(d,rights=b"All rights reserved"),d,time.monotonic()+30,staged=True)

    def test_index_failure_never_dispatches_raster(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in ("01_Source_Catalogue","02_Raw_Data","07_Reports"): (root/name).mkdir()
            calls=[]
            def runner(worker,directory,name,seconds):
                calls.append(name)
                if worker is s.index_download_worker:
                    return evidence(index_fixture(directory,tile="R1_C1"))
                if worker is s.index_worker:
                    return s.verify_index(directory,time.monotonic()+30)
                self.fail("unexpected raster dispatch")
            result=s.execute(root,runner)
            attempt=root/"02_Raw_Data"/s.ATTEMPT
            self.assertEqual(result["requests"],1)
            self.assertFalse((attempt/"dispatch-2.json").exists())
            self.assertFalse((attempt/"validated.json").exists())
            with self.assertRaisesRegex(Refused,"consumed"):
                s.execute(root,runner)

    def test_success_and_original_attempt_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in ("01_Source_Catalogue","02_Raw_Data","07_Reports"): (root/name).mkdir()
            previous=root/"02_Raw_Data"/p.ATTEMPT
            previous.mkdir()
            def runner(worker,directory,name,seconds):
                if worker is s.index_download_worker:
                    return evidence(index_fixture(directory))
                if worker is p.download_worker:
                    return evidence(archive(directory,rights=None))
                return s.supervise(worker,directory,name,seconds)
            result=s.execute(root,runner)
            self.assertEqual(result["status"],"PASS")
            self.assertEqual(result["requests"],2)
            self.assertEqual(result["cells"],200)
            self.assertTrue(previous.is_dir())
            self.assertTrue((root/"02_Raw_Data"/s.ATTEMPT/"validated.json").exists())


from tools.world_bank_pilot import Refused

if __name__=="__main__":
    unittest.main()
