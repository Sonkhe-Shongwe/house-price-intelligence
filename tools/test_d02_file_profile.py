"""Invented-only offline profiles."""
import copy
import json
import unittest
from unittest.mock import patch
from tools import d02_file_profile as p


def sample():
    return {"type":"FeatureCollection","features":[{"type":"Feature",
        "properties":{"OBJECTID":1,"SG26_CODE":"0"*26,"PRTY_NMBR":"001",
            "OFC_SBRB_NAME":"PINELANDS","ZONING":"Z"*1024,"ADR_NO":4},
        "geometry":{"type":"Polygon","coordinates":[[[18.5,-33.9],[18.51,-33.9],[18.51,-33.91],[18.5,-33.9]]]}}]}


class ProfileTests(unittest.TestCase):
    def run_profile(self,obj):
        return p.profile(json.dumps(obj).encode())

    def test_profile_not_strict_rejection(self):
        obj=sample()
        second=copy.deepcopy(obj["features"][0])
        second["properties"]["OBJECTID"]=2
        second["properties"]["PRTY_NMBR"]=1
        second["geometry"]=None
        obj["features"].append(second)
        r=self.run_profile(obj)
        self.assertEqual(r["status"],"PROFILED")
        self.assertEqual(r["fields"]["ZONING"]["maximum_string_length"],1024)
        self.assertEqual(r["fields"]["SG26_CODE"]["duplicate_groups"],1)
        self.assertEqual(r["fields"]["PRTY_NMBR"]["distinct_present"],2)
        self.assertEqual(r["geometry"]["valid_polygons"],1)
        self.assertEqual(r["geometry"]["missing"],1)
        self.assertEqual(r["unprofiled_field_count"],1)
        self.assertNotIn("0"*26,json.dumps(r))
        self.assertNotIn("ADR_NO",json.dumps(r))
        self.assertNotIn("Z"*1024,json.dumps(r))

    def test_alias_and_scope(self):
        obj=sample()
        props=obj["features"][0]["properties"]
        props["Official Suburb Name"]=props.pop("OFC_SBRB_NAME")
        self.assertEqual(self.run_profile(obj)["pinelands_matches"],1)
        props["Official Suburb Name"]="Other"
        self.assertEqual(self.run_profile(obj)["reason"],"SUBURB_SCOPE")
        del props["Official Suburb Name"]
        with self.assertRaisesRegex(p.ProfileStop,"SUBURB_FIELD_UNRESOLVED"):
            self.run_profile(obj)

    def test_privacy_and_limits(self):
        for name,value in (("OwnerName","PRIVATE"),("other","private@example.org"),("extra",{"a":1})):
            obj=sample()
            obj["features"][0]["properties"][name]=value
            with self.assertRaisesRegex(p.ProfileStop,"POSSIBLE_PERSONAL"):
                self.run_profile(obj)
        with patch.object(p,"MAX_ROWS",0):
            with self.assertRaisesRegex(p.ProfileStop,"FEATURE_LIMIT"):
                self.run_profile(sample())
        with patch.object(p,"CAP",1):
            with self.assertRaisesRegex(p.ProfileStop,"BYTE_LIMIT"):
                self.run_profile(sample())

    def test_invalid_geometry_is_quality_finding(self):
        obj=sample()
        obj["features"][0]["geometry"]={"type":"Point","coordinates":[18.5,-33.9]}
        r=self.run_profile(obj)
        self.assertEqual(r["status"],"PROFILED")
        self.assertEqual(r["geometry"]["invalid_or_unsupported"],1)


if __name__=="__main__":
    unittest.main()
