import unittest
from backend.real_source_collection import collect_intake
from backend.real_source_intake import DATASETS, IntakeRefused, prepare_intake
from backend.tests.test_real_source_intake import sample

class SourceTransport:
    def __init__(self):
        self.args=sample(); self.calls=[]; self.metadata_reads=0
        self.fault=None
    def metadata(self,dataset):
        self.metadata_reads+=1
        meta=self.args["metadata_before"][dataset]
        epoch=meta["epoch"]+(self.fault=="revision" and self.metadata_reads>4)
        return set(meta["fields"]),epoch
    def page(self,dataset,params,fields,cap):
        self.calls.append((dataset,dict(params)))
        role=next(role for role,d in DATASETS.items() if d==dataset)
        rows=self.args["rows"][role]
        if params["$select"]=="count(*) as row_count":
            n=5000 if self.fault=="cap" and role=="sales" else len(rows)
            if self.fault=="count_change" and role=="sales" and sum(d==dataset and p["$select"]=="count(*) as row_count" for d,p in self.calls)>1:n+=1
            return [{"row_count":str(n)}]
        offset=params["$offset"]
        if self.fault=="short" and role=="sales":return []
        if self.fault=="extra" and role=="sales" and offset==len(rows):return rows[:1]
        if self.fault=="wrong_key" and role=="address" and offset==0:return [dict(rows[0],pin="00000000000002")]
        if self.fault=="private_field" and role=="address" and offset==0:return [dict(rows[0],owner_name="invented")]
        return rows[offset:offset+params["$limit"]]
    def collect(self):
        return collect_intake(metadata=self.metadata,page=self.page,extracted_at_utc=self.args["extracted_at_utc"])

class CollectionTests(unittest.TestCase):
    def test_fixed_four_source_replay_and_terminal_counts(self):
        t=SourceTransport(); args=t.collect()
        self.assertEqual(prepare_intake(**args),prepare_intake(**sample()))
        self.assertEqual(t.metadata_reads,8)
        self.assertEqual(len(t.calls),16)
        for dataset,p in t.calls:
            self.assertIn("$where",p)
            if p["$select"]!="count(*) as row_count":
                self.assertIn(":id ASC",p["$order"])
                self.assertNotIn("owner_name",p["$select"])
        self.assertTrue(all("2024" in p["$where"] and "'00000000000001'" in p["$where"]
                            for dataset,p in t.calls if dataset in (DATASETS["geography"],DATASETS["address"])))

    def test_count_cap_short_page_and_extra_row_refused(self):
        for fault,reason in (("cap","count_missing_or_capped"),("short","page_count_mismatch"),("extra","terminal_page_not_empty"),("count_change","count_changed")):
            t=SourceTransport();t.fault=fault
            with self.subTest(fault=fault),self.assertRaisesRegex(IntakeRefused,reason):t.collect()

    def test_revision_and_enrichment_scope_fail_closed(self):
        for fault,reason in (("revision","source_revision"),("wrong_key","enrichment_scope"),("private_field","unexpected_collection_response")):
            t=SourceTransport();t.fault=fault
            with self.subTest(fault=fault),self.assertRaisesRegex(IntakeRefused,reason):t.collect()
