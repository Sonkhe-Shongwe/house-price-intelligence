import unittest
from unittest.mock import patch
from audit.source_readiness import cohort_audit as a
class CohortAuditTests(unittest.TestCase):
    def test_key_states_and_ambiguity(self):
        cohort=[{"pin":f"{i:014}","characteristics_year":2023} for i in range(1,7)]
        cohort.append(dict(cohort[0]))
        def row(i,label):return {"pin":f"{i:014}","year":"2023","prop_address_full":label}
        result=a.summarise(cohort,[row(1," 1 FICTIONAL WAY"),row(2,"1 fictional way"),row(3,""),row(4,"two"),row(4,"two"),row(5,"five")])
        self.assertEqual(result["key_states"],{"no_record":1,"blank_only":1,"multiple_rows":1,"one_nonblank_row":3})
        self.assertEqual(result["sales_with_one_nonblank_address_row"],4)
        self.assertEqual(result["keys_sharing_label_with_other_single_row_keys_same_year"],2)
        self.assertNotIn("fictional",str(result))
    def test_unrequested_key_refused(self):
        with self.assertRaises(ValueError):a.summarise([{"pin":"00000000000001","characteristics_year":2023}],[{"pin":"00000000000002","year":"2023"}])
    def test_unknown_fields_refused(self):
        with patch.object(a,"fetch",return_value=[{"owner_name":"fake"}]):
            with self.assertRaises(ValueError):a.query(a.ADDRESS,{},{"pin"},500)
    def test_cap_fails_closed(self):
        with patch.dict(a.CAPS,{a.SALES_ID:2}),patch.object(a,"query",return_value=[{},{}]):
            with self.assertRaises(ValueError):a.collect(a.SALES_ID,a.SALES_REQUIRED)
    def test_replay_uses_same_research_function(self):
        self.assertEqual(a.phase0_class203([],[]),[])
