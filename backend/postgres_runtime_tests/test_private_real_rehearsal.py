"""Offline full rehearsal in actual disposable PostgreSQL, no network."""
import os
import unittest
from backend.tests.test_real_source_intake import sample
from backend.private_real_rehearsal import new_report,verify_rehearsal

class PrivateRehearsalTests(unittest.TestCase):
    def test_complete_aggregate_rehearsal(self):
        args=sample()
        for i in range(2,13):
            pin=f"{i:014d}"
            for role,rows in args["rows"].items():
                added=dict(rows[0],pin=pin)
                if role=="sales":
                    added.update(doc_no=f"FICT-{i}",sale_date=f"2025-01-{i:02d}T00:00:00")
                if role=="address":
                    added["prop_address_full"]=f"{i} Fictional Court"
                rows.append(added)
        # One shared label and one missing address: both must abstain.
        args["rows"]["address"][1]["prop_address_full"]=args["rows"]["address"][0]["prop_address_full"]
        args["rows"]["address"].pop()
        report=verify_rehearsal(os.environ["HPI_PG_DSN"],args,new_report())
        self.assertEqual(report["status"],"completed")
        self.assertEqual(report["stored_sales"],12)
        self.assertEqual(report["canonical_match_parity_verified"],12)
        self.assertEqual(report["address_review_counts"],{"unique_token_review":9,"ambiguous_withheld":2,"unavailable":1})
        self.assertTrue(report["disposable_database_removed"])
        self.assertFalse(report["public_display_approved"])
        self.assertNotIn("Fictional",str(report))
        self.assertNotIn("00000000000001",str(report))
        self.assertNotIn("relational_sha256",str(report))
