"""Invented fixtures only; no acquisition or real records."""
import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import d02_register as p
from tools import hpi_data_manager as dm
from tools import d02_file_profile as fp


def fixture():
    rows=[]
    for i in range(4):
        k=i if i<2 else i-1
        # rows 1 and 2 share all three keys; row 3 has invalid spatial type.
        rows.append({"type":"Feature","properties":{"OBJECTID":i,"SG26_CODE":str(k).zfill(26),
             "PRTY_NMBR":str(k).zfill(3),"SL_LAND_PRCL_KEY":k,"OFC_SBRB_NAME":"Pinelands",
             "LU_LGL_STS_DSCR":"Invented","ZONING":"Z"*327,"ADR_NO":5},
             "geometry":{"type":"Polygon","coordinates":[[[18.5,-33.9],[18.51,-33.9],[18.51,-33.91],[18.5,-33.9]]]}})
    rows[3]["geometry"]={"type":"Point","coordinates":[18.5,-33.9]}
    return {"type":"FeatureCollection","features":rows}


class RegistrationTests(unittest.TestCase):
    def test_projection_flags_and_duplicates(self):
        data,q=p.derive(dm.json_bytes(fixture()))
        rows=json.loads(data)["features"]
        self.assertEqual(len(rows),4)
        self.assertEqual(q["ambiguous_identity_rows"],2)
        self.assertEqual(q["spatial_candidates"],1)
        self.assertEqual(q["duplicate_assessment"]["SG26_CODE"]["topologically_equal_groups"],1)
        self.assertTrue(q["cross_key_cardinality"]["SG26_CODE__PRTY_NMBR"]["identical_duplicate_membership"])
        self.assertEqual(rows[3]["geometry"]["type"],"Point")
        self.assertFalse(rows[3]["properties"]["quality_flags"]["spatial_candidate"])
        self.assertNotIn("ADR_NO",rows[0]["properties"])
        self.assertEqual(rows[0]["properties"]["PRTY_NMBR"],"000")

    def test_mismatched_groups_not_inferred(self):
        obj=fixture()
        obj["features"][2]["properties"]["PRTY_NMBR"]="000"
        _,q=p.derive(dm.json_bytes(obj))
        pair=q["cross_key_cardinality"]["SG26_CODE__PRTY_NMBR"]
        self.assertFalse(pair["identical_duplicate_membership"])
        self.assertEqual(pair["left_keys_multiple_right"],1)
        self.assertEqual(pair["right_keys_multiple_left"],1)
        self.assertEqual(q["ambiguous_identity_rows"],3)

    def test_duplicate_conflict_and_geometry(self):
        obj=fixture()
        obj["features"][2]["properties"]["ZONING"]="Other"
        obj["features"][2]["geometry"]=None
        _,q=p.derive(dm.json_bytes(obj))
        a=q["duplicate_assessment"]["SG26_CODE"]
        self.assertEqual(a["context_attribute_conflict_groups"],1)
        self.assertEqual(a["topology_unassessed_groups"],1)

    def test_registration_and_audit_no_overwrite(self):
        raw=dm.json_bytes(fixture())
        with tempfile.TemporaryDirectory() as td, patch.object(dm,"PARCEL_SHA",dm.sha(raw)), patch.object(fp,"OBSERVED_BYTES",len(raw)), patch.object(fp,"DISPLAYED_ROWS",4):
            root=Path(td)
            dm.initialise(root)
            dm.publish(root/dm.PARCEL_RAW,raw)
            day=date(2026,11,27)
            with self.assertRaisesRegex(ValueError,"RETENTION_WINDOW"):
                p.register(root,today=date(2026,12,27))
            with self.assertRaisesRegex(ValueError,"RETENTION_WINDOW"):
                p.register(root,deadline=date(2027,1,1),today=day)
            result=p.register(root,today=day)
            self.assertEqual(result["status"],"integrity checks passed")
            self.assertEqual(p.register(root,today=day),result)
            self.assertEqual((root/dm.PARCEL_RAW).read_bytes(),raw)
            out=root/dm.PARCEL_OUTPUT
            out.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"Processed checksum"):
                dm.audit_registered(root,dm.parcel_spec(),today=day)
            with self.assertRaisesRegex(ValueError,"no overwrite"):
                p.register(root,today=day)
            self.assertEqual(out.read_bytes(),b"tampered")

    def test_snapshot_and_privacy_refusal(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            dm.initialise(root)
            dm.publish(root/dm.PARCEL_RAW,b"wrong")
            with self.assertRaisesRegex(ValueError,"SNAPSHOT_MISMATCH"):
                p.register(root,today=date(2026,11,27))
            self.assertFalse((root/dm.PARCEL_MANIFEST).exists())
        obj=fixture()
        obj["features"][0]["properties"]["OwnerName"]="Invented"
        with self.assertRaises(ValueError):
            p.derive(dm.json_bytes(obj))
        obj=fixture()
        obj["features"][0]["geometry"]["foreign"]="Invented"
        with self.assertRaisesRegex(ValueError,"GEOMETRY_STRUCTURE"):
            p.derive(dm.json_bytes(obj))


if __name__=="__main__":
    unittest.main()
