import unittest
from unittest.mock import patch
from audit.source_readiness import full_release_qualification as q
def sale(n,y,**kw):
    r={"pin":f"{n:014d}","doc_no":f"doc-{n}","sale_date":f"{y}-05-01","sale_price":400000,"township_code":"17","class":"203","is_multisale":False,"num_parcels_sale":1,"sale_filter_less_than_10k":False,"sale_filter_deed_type":False,"sale_filter_same_sale_within_365":False}
    r.update(kw);return r
def building(n,y,**kw):
    r={"pin":f"{n:014d}","year":y,"township_code":"17","card":"1","class":"203","char_bldg_sf":1600,"pin_num_cards":1,"pin_is_multicard":False}
    r.update(kw);return r
class QualificationTests(unittest.TestCase):
    def test_funnel_matches_original_policy(self):
        s=[sale(1,2024),sale(2,2025),sale(2,2025),sale(3,2025,is_multisale=True,num_parcels_sale=2),sale(4,2025),sale(5,2025),sale(6,2025)]
        b=[building(1,2023),building(2,2024),building(4,2023),building(5,2024),building(5,2024,card="2"),building(6,2024,**{"class":"204"})]
        cohort,r=q.diagnose(s,b)
        self.assertEqual(len(cohort),2)
        f=r["2025"]["funnel"]
        self.assertEqual([f[k] for k in ("source_rows","screen_rejected","duplicate_rejected","screened_unique","join_rejected","joined_other_class","eligible_class203")],[6,1,1,4,2,1,1])
        self.assertEqual(r["2025"]["join_reasons_exclusive"],{"no_prior_building":1,"multiple_prior_buildings":1})
        self.assertEqual(f["missing_prior_pin_seen_other_year"],1)
        self.assertEqual(r["2025"]["screen_reasons_overlapping"]["multi_parcel_sale"],1)
        self.assertNotIn("doc-",str(r))
        self.assertNotIn("000000000000",str(r))
    def test_missing_flag_still_rejected(self):
        cohort,r=q.diagnose([sale(1,2025,sale_filter_deed_type=None)],[building(1,2024)])
        self.assertEqual(cohort,[])
        self.assertEqual(r["2025"]["screen_reasons_overlapping"],{"missing_or_invalid_sale_filter_deed_type":1})
    def test_sale_class_not_authoritative(self):
        cohort,r=q.diagnose([sale(1,2025,**{"class":"204"})],[building(1,2024)])
        self.assertEqual(len(cohort),1)
        self.assertEqual(r["2025"]["funnel"]["eligible_class203_not_reported203"],1)
    def test_scope_rejected(self):
        with self.assertRaises(ValueError):q.diagnose([sale(1,2023)],[])
    def test_metadata_only_bounded(self):
        with patch.object(q,"fetch",return_value={"licenseId":None,"rowsUpdatedAt":123,"private":"not output"}):
            self.assertEqual(len(q.license_summary()),4)
        with patch.object(q,"fetch",return_value={"licenseId":"invalid text with spaces","rowsUpdatedAt":123}):
            with self.assertRaises(ValueError):q.license_summary()
