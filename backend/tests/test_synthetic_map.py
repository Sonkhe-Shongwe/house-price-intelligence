import unittest
import tempfile
from pathlib import Path
from backend.synthetic_demo import in_memory_demo, example_request
from backend.synthetic_map import map_evidence, POSITIONS, POSITION_SOURCE
from backend.synthetic_investigation_store import EvidenceStoreError
from backend.durable_fixture import open_file_demo

class MapEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.conn,self.store=in_memory_demo()
        self.result=self.store.create(example_request())
        self.iid=self.result["investigation_id"]
    def tearDown(self):
        self.conn.close()
    def test_distinct_points_bound_to_frozen_order_and_no_writes(self):
        before=self.store.reopen(self.iid)
        changes=self.conn.total_changes
        response=map_evidence(self.store,self.iid,enabled=True)
        self.assertTrue(response["map_available"])
        self.assertFalse(response["real_geography_verified"])
        self.assertFalse(response["distance_supported"])
        self.assertEqual(response["position_source_id"],POSITION_SOURCE)
        features=response["feature_collection"]["features"]
        self.assertEqual([f["properties"]["pin"] for f in features],
            [before["subject"]["pin"]]+[c["pin"] for c in before["comparables"]])
        self.assertEqual([f["geometry"]["coordinates"] for f in features],
            [list(POSITIONS[f["properties"]["pin"]]) for f in features])
        self.assertEqual(len({tuple(f["geometry"]["coordinates"]) for f in features}),4)
        self.assertEqual(self.store.reopen(self.iid),before)
        self.assertEqual(self.conn.total_changes,changes)
    def test_disabled_and_unknown_are_empty(self):
        self.assertEqual(map_evidence(self.store,self.iid,enabled=False)["feature_collection"]["features"],[])
        request=example_request()
        request["subject"]["pin"]="99999999999999"
        result=self.store.create(request)
        self.assertFalse(map_evidence(self.store,result["investigation_id"],enabled=True)["map_available"])
    def test_tampered_geography_fails_closed(self):
        self.conn.execute("UPDATE parcel_geographies SET latitude=43 WHERE pin='00000000000002'")
        with self.assertRaises(EvidenceStoreError):
            map_evidence(self.store,self.iid,enabled=True)
    def test_existing_durable_file_reopens_without_reseed_or_map_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"legacy.sqlite"
            conn,store=open_file_demo(path)
            result=store.create(example_request())
            conn.close()
            before=path.read_bytes()
            conn,store=open_file_demo(path)
            try:
                response=map_evidence(store,result["investigation_id"],enabled=True)
                self.assertTrue(response["map_available"])
                self.assertEqual(store.reopen(result["investigation_id"]),result)
            finally:conn.close()
            self.assertEqual(path.read_bytes(),before)
