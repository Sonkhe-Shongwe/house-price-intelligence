import unittest
from unittest.mock import patch
from audit.source_readiness import coverage_diagnostic as d
class CoverageTests(unittest.TestCase):
    def test_count_only(self):
        with patch.object(d,"query",return_value=[{"row_count":"12","nonnull_pin_count":"12","distinct_pin_count":"10"}]) as q:
            self.assertEqual(d.counts("fixture","year = 2024",{"pin"})["distinct_pin_count"],10)
            self.assertEqual(q.call_args.args[1]["$limit"],1)
            self.assertTrue(q.call_args.args[1]["$select"].startswith("count(*)"))
    def test_reject_row_payload(self):
        with patch.object(d,"query",return_value=[{"pin":"00000000000001"}]):
            with self.assertRaises(ValueError):d.counts("fixture","year = 2024",{"pin"})
