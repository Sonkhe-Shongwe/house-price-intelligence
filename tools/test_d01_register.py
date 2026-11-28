"""Invented-only regression tests for 011 and candidate matching."""
from datetime import date
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from tools import d01_register as s
from tools import d01_file_profile as fp
from tools import hpi_data_manager as dm
from tools import d02_register as pr
from tools import d02_file_profile as pp
from tools.test_d01_file_profile import csv_bytes, fixture
from tools.test_d02_register import fixture as parcel_fixture


def parcels():
    obj=parcel_fixture()
    for row in obj["features"]:
        p=row["properties"]
        k=p["SL_LAND_PRCL_KEY"]
        p["SG26_CODE"]="C0160007"+str(k+123).zfill(8)+"0000000000"
    return obj


class RegistrationTests(unittest.TestCase):
    def test_projection_and_repeat_sales(self):
        rows=fixture()
        rows.append(rows[0][:])
        with patch.object(fp,"EXPECTED",5):
            result,q=s.derive(csv_bytes(rows))
        self.assertEqual(len(result),5)
        self.assertEqual(q["ambiguous_event_rows"],2)
        self.assertEqual(q["screened_candidates"],1)
        self.assertEqual(result[0]["consideration_cents"],100000000)
        self.assertEqual(result[2]["consideration_cents"],0)
        self.assertNotIn("Invented PINELANDS",json.dumps(result))

    def test_candidate_counts_and_conflict(self):
        with patch.object(fp,"EXPECTED",4):
            rows,_=s.derive(csv_bytes(fixture()))
        data,_=pr.derive(dm.json_bytes(parcels()))
        p=json.loads(data)
        result=s.match(rows,p)
        self.assertEqual(result["screened_cohort"]["candidate_unique"],2)
        self.assertEqual(result["screened_cohort"]["candidate_spatial_flag"],2)
        self.assertEqual(result["verified_identity_matches"],0)
        rows[0]["valuation_reference"]="001"
        result=s.match(rows,p)
        self.assertEqual(result["screened_cohort"]["methods_conflict"],1)
        self.assertEqual(result["screened_cohort"]["candidate_ambiguous"],1)
        self.assertNotIn("INVENTED-1",json.dumps(result))

    def test_registration_audit_and_no_overwrite(self):
        raw=csv_bytes(fixture())
        parcel=dm.json_bytes(parcels())
        day=date(2026,11,27)
        with tempfile.TemporaryDirectory() as td, patch.object(fp,"EXPECTED",4), patch.object(fp,"OBSERVED_BYTES",len(raw)), patch.object(dm,"SALE_SHA",dm.sha(raw)), patch.object(dm,"PARCEL_SHA",dm.sha(parcel)), patch.object(pp,"OBSERVED_BYTES",len(parcel)), patch.object(pp,"DISPLAYED_ROWS",4):
            root=Path(td)
            dm.initialise(root)
            dm.publish(root/dm.SALE_RAW,raw)
            with self.assertRaisesRegex(ValueError,"PARCEL_AUDIT_REQUIRED"):
                s.register(root,today=day)
            self.assertFalse((root/dm.SALE_MANIFEST).exists())
            dm.publish(root/dm.PARCEL_RAW,parcel)
            pr.register(root,today=day)
            with self.assertRaisesRegex(ValueError,"RETENTION_WINDOW"):
                s.register(root,today=fp.REVIEW)
            result=s.register(root,today=day)
            self.assertTrue(result["registered"])
            self.assertEqual(result["audit"]["status"],"integrity checks passed")
            self.assertEqual(s.register(root,today=day),result)
            self.assertEqual((root/dm.SALE_RAW).read_bytes(),raw)
            (root/dm.SALE_OUTPUT).write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"Processed checksum"):
                dm.audit_registered(root,dm.sale_spec(),today=day)
            with self.assertRaisesRegex(ValueError,"no overwrite"):
                s.register(root,today=day)
            self.assertEqual((root/dm.SALE_OUTPUT).read_bytes(),b"tampered")

    def test_expired_parcel_refuses(self):
        raw=csv_bytes(fixture())
        parcel=dm.json_bytes(parcels())
        day=date(2026,11,27)
        with tempfile.TemporaryDirectory() as td, patch.object(fp,"EXPECTED",4), patch.object(fp,"OBSERVED_BYTES",len(raw)), patch.object(dm,"SALE_SHA",dm.sha(raw)), patch.object(dm,"PARCEL_SHA",dm.sha(parcel)), patch.object(pp,"OBSERVED_BYTES",len(parcel)), patch.object(pp,"DISPLAYED_ROWS",4):
            root=Path(td)
            dm.initialise(root)
            dm.publish(root/dm.SALE_RAW,raw)
            dm.publish(root/dm.PARCEL_RAW,parcel)
            pr.register(root,deadline=date(2026,11,28),today=day)
            with self.assertRaisesRegex(ValueError,"expired"):
                s.register(root,today=date(2026,11,28))
            self.assertFalse((root/dm.SALE_MANIFEST).exists())


if __name__=="__main__":
    unittest.main()
