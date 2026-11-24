import copy
import unittest
from backend.synthetic_demo import in_memory_demo,example_request
from backend.buyer_evidence_preview import buyer_evidence_preview,project_buyer_evidence
from backend.disclosure_guard import DisclosureDenied

class BuyerEvidencePreviewTests(unittest.TestCase):
    def setUp(self):
        self.conn,self.store=in_memory_demo()
        self.addCleanup(self.conn.close)
        self.record=self.store.create(example_request())
    def test_minimised_frozen_projection(self):
        p=buyer_evidence_preview(self.store,self.record["investigation_id"])
        self.assertEqual(p["selected_count"],3)
        self.assertEqual(p["sales"][0]["sale_price_usd"],"525000.00")
        self.assertEqual(p["sales"][0]["assessment_year"],2023)
        self.assertFalse(p["provenance"]["publisher_attributed"])
        self.assertIsNone(p["valuation"])
        self.assertNotIn("subject",p)
        self.assertEqual(set(p["sales"][0]),{"rank","sale_date","sale_price_usd","age_days","area_difference_pct","assessment_year","location_evidence"})
        self.assertEqual(self.store.reopen(self.record["investigation_id"]),self.record)
    def test_reject_real_and_approval_flags(self):
        for key,val in (("source_kind","historical_research"),("public_property_display_approved",True),("historical_as_of_verified",True)):
            item=copy.deepcopy(self.record);item["data_build"][key]=val
            with self.subTest(key=key),self.assertRaises(DisclosureDenied):project_buyer_evidence(item)
    def test_omit_arbitrary_fields_and_text(self):
        item=copy.deepcopy(self.record)
        item["comparables"][0]["explanation"]="private marker"
        item["comparables"][0]["owner_name"]="private marker"
        item["subject"]["label"]="private marker"
        self.assertNotIn("private marker",str(project_buyer_evidence(item)))
    def test_invalid_chronology_or_money_refused(self):
        for key,val in (("assessment_year",2024),("age_days",0),("sale_price_usd",525000.0)):
            item=copy.deepcopy(self.record);item["comparables"][0][key]=val
            with self.subTest(key=key),self.assertRaises(DisclosureDenied):project_buyer_evidence(item)
    def test_empty_evidence_has_no_fabricated_sales(self):
        req=example_request();req["subject"]["pin"]="00000000009999"
        p=buyer_evidence_preview(self.store,self.store.create(req)["investigation_id"])
        self.assertEqual(p["sales"],[])
        self.assertEqual(p["selected_count"],0)
