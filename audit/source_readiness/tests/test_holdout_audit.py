import unittest
from unittest.mock import patch
from audit.source_readiness import holdout_audit as h
def row(n,when):
    return {"pin":f"{n:014d}","doc_no":f"doc-{n}","sale_date":when,"sale_price":400000+n*1000,"class":"203","township_code":"17","sqft":1600,"nbhd_code":"A","lat":42.04,"lon":-87.68}
class HoldoutTests(unittest.TestCase):
    def test_future_never_enters_candidate_pool(self):
        rows=[row(i,"2024-12-01") for i in range(1,6)]+[row(i,"2025-01-01") for i in range(6,16)]
        original=h.match_property
        def guard(subject,population,**kwargs):
            self.assertTrue(all(r["sale_date"]<subject["sale_date"] for r in population))
            return original(subject,population,**kwargs)
        with patch.object(h,"match_property",side_effect=guard):
            result=h.evaluate(rows)
        self.assertEqual(result["subjects"],10)
        self.assertEqual(result["all_methods"]["current"]["count"],10)
        self.assertFalse(result["policy_adopted"])
        self.assertNotIn("doc-",str(result))
    def test_suppresses_small_groups(self):
        self.assertIsNone(h.metrics([{"actual":1,"x":2}],"x")["mae_usd"])
    def test_rejects_wrong_period_and_empty(self):
        for rows in ([],[row(1,"2023-01-01")]):
            with self.assertRaises(ValueError):h.evaluate(rows)
    def test_universe_exact_year_representation(self):
        pin="00000000000001"
        for year in (2024, 2024.0, "2024.0"):
            with self.subTest(year=year):
                record={"pin":pin,"year":year,"nbhd_code":"A","lat":42.04,"lon":-87.68}
                with patch.object(h,"query",return_value=[record]):
                    self.assertEqual(h.universe({(pin,2024)},h.UNIVERSE_FIELDS),[record])

    def test_universe_refuses_fractional_or_out_of_scope_year(self):
        pin="00000000000001"
        for year in (2024.5, "2024.5", "2023.0", True, None, "NaN", "Infinity"):
            with self.subTest(year=year):
                with patch.object(h,"query",return_value=[{"pin":pin,"year":year}]):
                    with self.assertRaisesRegex(ValueError,"Unexpected universe response"):
                        h.universe({(pin,2024)},h.UNIVERSE_FIELDS)
        with patch.object(h,"query",return_value=[{"pin":"00000000000002","year":"2024.0"}]):
            with self.assertRaisesRegex(ValueError,"Unexpected universe response"):
                h.universe({(pin,2024)},h.UNIVERSE_FIELDS)

    def test_unexpected_universe_fields(self):
        with self.assertRaises(ValueError):h.universe({("00000000000001",2023)},{"pin","year"})
