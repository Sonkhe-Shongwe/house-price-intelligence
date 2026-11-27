"""Offline invented-only tests; never dispatch a live request."""
import copy
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO
from tools import hpi_data_manager as manager
from tools import d02_parcel_pilot as p
from tools.world_bank_pilot import Refused


def fixture():
    props = {"OBJECTID":1,"SG26_CODE":"FICTIONAL","PRTY_NMBR":"X1",
             "OFC_SBRB_NAME":"Invented","LU_LGL_STS_DSCR":"Invented","ZONING":"Invented"}
    ring = [[18.465,-33.965],[18.466,-33.965],[18.466,-33.964],[18.465,-33.965]]
    return {"type":"FeatureCollection","features":[{"type":"Feature","properties":props,
        "geometry":{"type":"Polygon","coordinates":[ring]}}]}


def raw(obj):
    return json.dumps(obj).encode()


def seed_prior(root):
    for name in ("01_Source_Catalogue","02_Raw_Data","07_Reports"):
        (root/name).mkdir()
    prior=root/"07_Reports"/p.PRIOR_ATTEMPT
    prior.mkdir()
    record={"approval":"2026-11-27 D02-P1","source":"City of Cape Town",
            "endpoint":"https://"+p.HOST+p.REQUEST,
            "started_utc":"2026-11-27T04:30:29.640838+00:00",
            "max_requests":1,"max_body_bytes":p.CAP,"deadline_seconds":p.SECONDS,
            "max_features":p.MAX_ROWS,"max_coordinate_pairs":p.MAX_PAIRS,
            "raw_retained":False,"registered":False}
    (prior/"attempt.json").write_bytes(raw(record))
    (prior/"result.json").write_bytes(raw(dict(record,status="STOP",reason="SCHEMA",
        bytes=90232,sha256="0"*64,requests_dispatched_max=1)))
    return prior


class PilotTests(unittest.TestCase):
    def setUp(self):
        patcher=patch.object(p,"PRIOR_SHA","0"*64)
        patcher.start()
        self.addCleanup(patcher.stop)

    def profile(self,obj):
        return p.profile(raw(obj),time.monotonic()+5)

    def test_aggregate_only(self):
        obj=fixture()
        second=copy.deepcopy(obj["features"][0])
        second["properties"]["OBJECTID"]=2
        second["properties"]["ZONING"]=None
        obj["features"].append(second)
        result=self.profile(obj)
        self.assertEqual(result["features"],2)
        self.assertEqual(result["valid_polygons"],2)
        self.assertEqual(result["valid_polygon_bounds_intersect_request"],2)
        self.assertEqual(result["missing_fields"]["ZONING"],1)
        self.assertEqual(result["duplicate_key_groups"]["SG26_CODE"],1)
        self.assertNotIn("FICTIONAL",json.dumps(result))
        self.assertNotIn("18.465",json.dumps(result))

    def test_arcgis_collection_metadata(self):
        obj=fixture()
        obj["properties"]={"exceededTransferLimit":True}
        self.assertIs(self.profile(obj)["source_transfer_limit_flag"],True)
        obj["exceededTransferLimit"]=False
        with self.assertRaisesRegex(Refused,"COLLECTION_METADATA"): self.profile(obj)
        del obj["exceededTransferLimit"]
        obj["properties"]["owner"]="PRIVATE"
        with self.assertRaisesRegex(Refused,"COLLECTION_METADATA"): self.profile(obj)
        with self.assertRaisesRegex(Refused,"API_ERROR"):
            self.profile({"error":{"message":"PRIVATE"}})
        with self.assertRaisesRegex(Refused,"JSON"):
            p.profile(b"not json",time.monotonic()+5)

    def test_schema_and_caps(self):
        for change in ("extra","api_error","too_many","empty","geometry","nonfinite"):
            with self.subTest(change=change):
                obj=fixture()
                if change=="extra": obj["features"][0]["properties"]["OWNER"]="Private"
                if change=="api_error": obj={"error":{"message":"Private"}}
                if change=="too_many": obj["features"]*=101
                if change=="empty": obj["features"]=[]
                if change=="geometry": obj["features"][0]["geometry"]["type"]="Point"
                if change=="nonfinite": obj["features"][0]["geometry"]["coordinates"][0][0][0]=float("nan")
                with self.assertRaises(Refused): self.profile(obj)
        with patch.object(p,"MAX_PAIRS",3):
            with self.assertRaises(Refused): self.profile(fixture())
        with self.assertRaises(Refused): p.profile(b"x"*(p.CAP+1),time.monotonic()+5)
        with self.assertRaises(Refused): p.profile(raw(fixture()),time.monotonic()-1)

    def test_missing_and_invalid_geometry(self):
        obj=fixture()
        obj["features"][0]["geometry"]=None
        self.assertEqual(self.profile(obj)["invalid_or_missing_polygons"],1)

    def test_one_attempt_no_raw_retention(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            prior=seed_prior(root)
            before={f.name:f.read_bytes() for f in prior.iterdir()}
            with patch.object(p,"fetch_once",side_effect=AssertionError("live request")):
                calls=[]
                def fetch(seconds):
                    calls.append(seconds)
                    return raw(fixture())
                result=p.execute(root,fetch)
                self.assertEqual(result["status"],"PASS")
                self.assertEqual(len(calls),1)
                with self.assertRaises(Refused): p.execute(root,fetch)
                self.assertEqual(len(calls),1)
            files=list((root/"07_Reports"/p.ATTEMPT).glob("*.json"))
            self.assertEqual({f.name for f in files},{"attempt.json","result.json"})
            self.assertEqual(len(files),2)
            self.assertEqual({f.name:f.read_bytes() for f in prior.iterdir()},before)
            self.assertEqual(result["approval"],"2026-11-27 D02-P2")
            self.assertFalse(list((root/"02_Raw_Data").iterdir()))
            for f in files:
                self.assertNotIn("FICTIONAL",f.read_text())
                self.assertNotIn("18.465",f.read_text())

    def test_failure_consumes_attempt_and_redacts(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            seed_prior(root)
            result=p.execute(root,lambda _:b'{"error":{"message":"SECRET"}}')
            self.assertEqual(result["status"],"STOP")
            self.assertNotIn("SECRET",json.dumps(result))
            with self.assertRaises(Refused): p.execute(root,lambda _:self.fail("replay"))

    def test_prior_missing_or_changed_refuses_before_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            prior=seed_prior(root)
            result_path=prior/"result.json"
            original=result_path.read_bytes()
            for changed in (None, raw(dict(json.loads(original),sha256="bad")),
                            raw(dict(json.loads(original),status="PASS"))):
                if changed is None:
                    result_path.unlink()
                else:
                    result_path.write_bytes(changed)
                with self.assertRaisesRegex(Refused,"Original D02-P1"):
                    p.execute(root,lambda _:self.fail("unexpected dispatch"))
                self.assertFalse((root/"07_Reports"/p.ATTEMPT).exists())
                result_path.write_bytes(original)

    def test_consumed_cli_and_combination_refused(self):
        for args in (["--d02-pilot"],["--d02-pilot","--d02-p2"],
                     ["--d02-p2","--self-test"],["--d02-p2","--audit-workspace"]):
            with self.subTest(args=args), patch("sys.argv",["manager",*args]), \
                    patch.object(p,"owner_execute",side_effect=AssertionError("dispatch")), \
                    redirect_stdout(StringIO()):
                self.assertEqual(manager.main(),1)

    def test_exact_request(self):
        self.assertEqual(p.PARAMS["resultRecordCount"],"100")
        self.assertEqual(p.PARAMS["outFields"],",".join(p.FIELDS))
        self.assertEqual(p.CAP,5*1024**2)
        self.assertEqual(p.SECONDS,60)
        self.assertEqual(p.HOST,"citymaps.capetown.gov.za")

if __name__=="__main__":
    unittest.main()
