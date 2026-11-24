import unittest
from backend.curated_ingestion_candidate import (open_candidate,import_fixture,investigation_store,address_candidates,ImportRefused)
from backend.disclosure_guard import project_fields,DisclosureDenied
from backend.synthetic_demo import example_request,in_memory_demo
from backend.synthetic_investigation_store import EvidenceStoreError
from backend.synthetic_shortlists import SyntheticShortlistService

class CuratedCandidateTests(unittest.TestCase):
    def setUp(self):self.conn=open_candidate()
    def tearDown(self):self.conn.close()
    def test_idempotent_canonical_import_and_revision(self):
        first=import_fixture(self.conn,"v1")
        counts=lambda:tuple(self.conn.execute("SELECT COUNT(*) FROM "+t).fetchone()[0] for t in ("curated_builds","source_snapshots","sale_transactions","assessment_records","candidate_addresses"))
        baseline=counts()
        store=investigation_store(self.conn,"v1")
        original=store.create(example_request())
        sid=SyntheticShortlistService(store).create({"label":"Fictional revision"})["shortlist_id"]
        SyntheticShortlistService(store).add(sid,{"investigation_id":original["investigation_id"],"note_text":"old"})
        self.assertEqual(import_fixture(self.conn,"v1"),first)
        self.assertEqual(counts(),baseline)
        second=import_fixture(self.conn,"v2")
        self.assertNotEqual(first,second)
        changed=investigation_store(self.conn,"v2").create(example_request())
        self.assertNotEqual([c["sale_price_usd"] for c in original["comparables"]],[c["sale_price_usd"] for c in changed["comparables"]])
        self.assertEqual(store.reopen(original["investigation_id"]),original)
        self.assertEqual(SyntheticShortlistService(store).get(sid)["entries"][0]["note_text"],"old")
        with self.assertRaises(EvidenceStoreError):investigation_store(self.conn,"v2").reopen(original["investigation_id"])
    def test_ambiguous_and_unknown_address(self):
        import_fixture(self.conn,"v1")
        a=address_candidates(self.conn,"v1","105 fictional way, demonstration district")
        self.assertEqual(a["status"],"ambiguous")
        self.assertEqual(len(a["candidates"]),2)
        self.assertFalse(a["building_identity_verified"])
        self.assertEqual(address_candidates(self.conn,"v1","unknown")["status"],"no_match")
    def test_immutable_conflict_and_no_silent_repair(self):
        import_fixture(self.conn,"v1")
        self.conn.execute("DELETE FROM candidate_addresses WHERE pin='00000000000001'")
        self.conn.commit()
        with self.assertRaises(ImportRefused):import_fixture(self.conn,"v1")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM candidate_addresses").fetchone()[0],5)
    def test_transaction_rollback(self):
        self.conn.execute("INSERT INTO parcels VALUES('00000000000004','wrong')")
        self.conn.commit()
        with self.assertRaises(ImportRefused):import_fixture(self.conn,"v1")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM curated_builds").fetchone()[0],0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM source_snapshots").fetchone()[0],0)
    def test_refuses_existing_runtime_and_unknown_revision(self):
        old,_=in_memory_demo()
        try:
            with self.assertRaises(ImportRefused):import_fixture(old,"v1")
        finally:old.close()
        with self.assertRaises(ImportRefused):import_fixture(self.conn,"real")
    def test_disclosure_default_deny(self):
        r={"pin":"00000000000001","owner_name":"invented","sale_price_usd_cents":50000}
        self.assertEqual(project_fields(kind="synthetic_fixture",dataset="synthetic-sales",query="fabricated",record=r,fields=["pin"]),{"pin":r["pin"]})
        for kind,dataset,query,fields in [("historical_research","wvhk-k5uv","fabricated",["pin"]),("synthetic_fixture","wvhk-k5uv","fabricated",["pin"]),("synthetic_fixture","synthetic-sales","publisher",["pin"]),("synthetic_fixture","synthetic-sales","fabricated",["owner_name"]),("synthetic_fixture","synthetic-unknown","fabricated",["pin"])]:
            with self.assertRaises(DisclosureDenied):project_fields(kind=kind,dataset=dataset,query=query,record=r,fields=fields)
    def test_frozen_result_refuses_reclassified_build(self):
        db,store=in_memory_demo()
        try:
            result=store.create(example_request())
            db.execute("UPDATE curated_builds SET build_kind='historical_research'")
            db.commit()
            with self.assertRaises(EvidenceStoreError):store.reopen(result["investigation_id"])
        finally:db.close()
