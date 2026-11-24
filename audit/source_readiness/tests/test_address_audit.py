import unittest
from audit.source_readiness.address_audit import plan,validated_counts
class AddressAuditTests(unittest.TestCase):
    def test_only_fixed_aggregate_fields_and_scope(self):
        label,scope,address,select=plan({"pin","year","township_code","prop_address_full","owner_name","mail_address"})
        self.assertEqual(scope,"township_code = '17'")
        self.assertEqual(address,"prop_address_full")
        self.assertNotIn("owner_name",select)
        self.assertNotIn("mail_address",select)
        self.assertNotIn("select *",select.lower())
    def test_city_fallback_is_not_township(self):
        label,scope,address,select=plan({"pin","year","prop_address_city_name"})
        self.assertIn("not township",label)
        self.assertIsNone(address)
        self.assertNotIn("address_count",select)
    def test_refuse_missing_scope_and_row_level_payload(self):
        with self.assertRaises(ValueError):plan({"pin","year"})
        with self.assertRaises(ValueError):validated_counts([{"pin":"00000000000001"}],None)
        with self.assertRaises(ValueError):validated_counts([{"row_count":"2","nonnull_pin_count":"2","distinct_pin_count":"3"}],None)
    def test_counts_valid(self):
        self.assertEqual(validated_counts([{"row_count":"2","nonnull_pin_count":"2","distinct_pin_count":"1"}],None)["row_count"],2)
