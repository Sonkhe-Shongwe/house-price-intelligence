import unittest
from tools.review_python_dependencies import summarize

class PythonReviewTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{"name":n,"version":"1.2.3"} for n in
                   ("psycopg","psycopg-binary","psycopg_pool","PyJWT","cryptography")]
        self.audit={"dependencies":[{**r,"vulns":[]} for r in self.rows]}

    def test_complete_inventory_and_clean_result(self):
        report=summarize(self.rows,self.audit,0)
        self.assertEqual(report["status"],"passed")
        self.assertEqual(report["package_count"],5)

    def test_advisories_block_even_on_zero_exit(self):
        self.audit["dependencies"][0]["vulns"]=[{"id":"PYSEC-2026-1","description":"not emitted"}]
        report=summarize(self.rows,self.audit,0)
        self.assertEqual(report["status"],"blocked")
        self.assertEqual(report["advisories"],1)
        self.assertNotIn("description",str(report))

    def test_missing_skipped_or_different_version_blocks(self):
        for rows in (self.audit["dependencies"][1:],
                     [{**r,"version":"9"} for r in self.audit["dependencies"]],
                     [{**r,"skip_reason":"unknown"} for r in self.audit["dependencies"]]):
            with self.assertRaises(ValueError):
                summarize(self.rows,{"dependencies":rows},0)
        self.assertEqual(summarize(self.rows,self.audit,2)["status"],"blocked")

    def test_duplicate_and_missing_runtime_package_blocks(self):
        with self.assertRaises(ValueError):
            summarize(self.rows+[self.rows[0]],self.audit,0)
        with self.assertRaises(ValueError):
            summarize(self.rows[:-1],self.audit,0)
