"""P6 local shortlist contract: fictional property identity and mutable decisions."""
from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from backend.durable_fixture import open_file_demo
from backend.synthetic_demo import example_request, in_memory_demo
from backend.synthetic_investigation_store import EvidenceStoreError
from backend.synthetic_shortlists import ShortlistError, SyntheticShortlistService


def enquiry(store, pin: str, label: str):
    request = example_request()
    request["subject"]["pin"] = pin
    request["subject"]["label"] = label
    return store.create(request)


class ShortlistTests(unittest.TestCase):
    def setUp(self):
        self.conn, self.store = in_memory_demo()
        self.service = SyntheticShortlistService(self.store)
        self.addCleanup(self.conn.close)

    def make_list(self):
        return self.service.create({"label": "  My fictional comparison  "})["shortlist_id"]

    def test_known_and_unknown_enquiries_remain_separate_with_frozen_evidence(self):
        good = enquiry(self.store, "00000000000001", "Property A")
        unknown = enquiry(self.store, "00000000000099", "Property B")
        self.assertEqual(good["status"], "supported_neighbourhood")
        self.assertEqual(unknown["status"], "insufficient_data")
        sid = self.make_list()
        self.service.add(sid, {"investigation_id": good["investigation_id"], "note_text": "First viewing"})
        result = self.service.add(sid, {"investigation_id": unknown["investigation_id"]})
        self.assertEqual(result["label"], "My fictional comparison")
        self.assertEqual(result["max_entries"], 3)
        self.assertEqual([e["investigation"]["status"] for e in result["entries"]],
                         ["supported_neighbourhood", "insufficient_data"])
        self.assertEqual([e["investigation"]["selected_count"] for e in result["entries"]], [3, 0])
        self.assertEqual(result["entries"][0]["note_text"], "First viewing")
        self.assertIsNone(result["entries"][1]["investigation"]["valuation"])
        self.assertEqual(self.service.get(sid), result)

    def test_notes_change_separately_from_saved_evidence_and_hash(self):
        good = enquiry(self.store, "00000000000001", "Property A")
        iid = good["investigation_id"]
        sid = self.make_list()
        self.service.add(sid, {"investigation_id": iid})
        before = self.conn.execute(
            "SELECT response_json, result_sha256 FROM investigation_results WHERE investigation_id=?",
            (iid,),
        ).fetchone()
        old_price = self.conn.execute(
            "SELECT sale_price_usd_cents FROM comparable_evidence WHERE investigation_id=? ORDER BY rank",
            (iid,),
        ).fetchall()
        updated = self.service.set_note(sid, iid, {"note_text": "Needs inspection\nCheck the roof"})
        self.assertEqual(updated["entries"][0]["note_text"], "Needs inspection\nCheck the roof")
        self.assertEqual(self.store.reopen(iid), good)
        self.assertEqual(self.conn.execute(
            "SELECT response_json, result_sha256 FROM investigation_results WHERE investigation_id=?",
            (iid,),
        ).fetchone(), before)
        self.assertEqual(self.conn.execute(
            "SELECT sale_price_usd_cents FROM comparable_evidence WHERE investigation_id=? ORDER BY rank",
            (iid,),
        ).fetchall(), old_price)

    def test_duplicate_ids_and_same_known_parcel_rejected_without_side_effects(self):
        sid = self.make_list()
        first = enquiry(self.store, "00000000000001", "First version")
        second = enquiry(self.store, "00000000000001", "Second version")
        self.service.add(sid, {"investigation_id": first["investigation_id"]})
        for iid, reason in ((first["investigation_id"], "duplicate_investigation"),
                            (second["investigation_id"], "duplicate_property")):
            with self.subTest(reason=reason), self.assertRaisesRegex(ShortlistError, reason):
                self.service.add(sid, {"investigation_id": iid})
        self.assertEqual(len(self.service.get(sid)["entries"]), 1)

    def test_three_distinct_property_limit_and_listing(self):
        sid = self.make_list()
        for number in (1, 2, 3):
            saved = enquiry(self.store, f"{number:014d}", f"House {number}")
            self.service.add(sid, {"investigation_id": saved["investigation_id"]})
        fourth = enquiry(self.store, "00000000000004", "House 4")
        with self.assertRaisesRegex(ShortlistError, "shortlist_full"):
            self.service.add(sid, {"investigation_id": fourth["investigation_id"]})
        listed = self.service.list()
        self.assertEqual(listed["source_kind"], "synthetic_fixture")
        self.assertEqual(listed["shortlists"][0]["entry_count"], 3)
        self.assertEqual(len(self.service.get(sid)["entries"]), 3)

    def test_removal_only_changes_shortlist_membership(self):
        sid = self.make_list()
        one = enquiry(self.store, "00000000000001", "Property A")
        two = enquiry(self.store, "00000000000099", "Unknown property")
        self.service.add(sid, {"investigation_id": one["investigation_id"]})
        self.service.add(sid, {"investigation_id": two["investigation_id"]})
        after = self.service.remove(sid, one["investigation_id"])
        self.assertEqual([e["investigation_id"] for e in after["entries"]], [two["investigation_id"]])
        self.assertEqual(self.store.reopen(one["investigation_id"]), one)
        with self.assertRaisesRegex(ShortlistError, "shortlist_entry_not_found"):
            self.service.remove(sid, one["investigation_id"])

    def test_unknown_ids_and_input_validation_fail_closed(self):
        sid = self.make_list()
        valid = enquiry(self.store, "00000000000001", "Property A")
        iid = valid["investigation_id"]
        for bad in ({"label": ""}, {"label": "X" * 81}, {"label": 1}, {"label": "A\nB"},
                    {"label": "Valid", "build_id": "real-market"}):
            with self.subTest(bad=bad), self.assertRaises(ShortlistError):
                self.service.create(bad)
        for bad in ({"investigation_id": iid, "note_text": "A" * 801},
                    {"investigation_id": iid, "note_text": None},
                    {"investigation_id": iid, "build_id": "real-market"}):
            with self.subTest(bad=bad), self.assertRaises(ShortlistError):
                self.service.add(sid, bad)
        with self.assertRaisesRegex(ShortlistError, "invalid_identifier"):
            self.service.get("../bad")
        with self.assertRaisesRegex(ShortlistError, "investigation_not_found"):
            self.service.add(sid, {"investigation_id": "00000000-0000-4000-8000-000000000000"})
        with self.assertRaisesRegex(ShortlistError, "shortlist_not_found"):
            self.service.get("00000000-0000-4000-8000-000000000000")
        self.assertEqual(self.service.get(sid)["entries"], [])

    def test_note_update_rejects_untrusted_fields_and_missing_membership(self):
        sid = self.make_list()
        good = enquiry(self.store, "00000000000001", "Good")
        iid = good["investigation_id"]
        for bad in ({}, {"note_text": "ok", "sale_price_usd": "0.01"},
                    {"note_text": "\x00bad"}, {"note_text": "a" * 801}):
            with self.subTest(bad=bad), self.assertRaises(ShortlistError):
                self.service.set_note(sid, iid, bad)
        with self.assertRaisesRegex(ShortlistError, "shortlist_entry_not_found"):
            self.service.set_note(sid, iid, {"note_text": "not yet member"})
        self.assertEqual(self.store.reopen(iid), good)

    def test_corrupted_evidence_blocks_list_access_and_membership_changes(self):
        sid = self.make_list()
        saved = enquiry(self.store, "00000000000001", "Protected")
        iid = saved["investigation_id"]
        self.service.add(sid, {"investigation_id": iid})
        self.conn.execute("UPDATE investigation_results SET response_json='{}' WHERE investigation_id=?", (iid,))
        self.conn.commit()
        with self.assertRaises(EvidenceStoreError):
            self.service.get(sid)
        with self.assertRaises(EvidenceStoreError):
            self.service.set_note(sid, iid, {"note_text": "must fail"})
        with self.assertRaises(EvidenceStoreError):
            self.service.remove(sid, iid)
        self.assertEqual(self.conn.execute(
            "SELECT note_text FROM shortlist_investigations WHERE investigation_id=?", (iid,)
        ).fetchone(), ("",))

    def test_restart_recovers_two_properties_notes_and_original_transactions(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fictional-shortlist.sqlite"
            first, store = open_file_demo(path)
            try:
                shortlist = SyntheticShortlistService(store)
                sid = shortlist.create({"label": "Returning buyer"})["shortlist_id"]
                good = enquiry(store, "00000000000001", "A")
                unknown = enquiry(store, "00000000000099", "B")
                shortlist.add(sid, {"investigation_id": good["investigation_id"]})
                shortlist.add(sid, {"investigation_id": unknown["investigation_id"]})
                before = shortlist.set_note(sid, good["investigation_id"],
                                           {"note_text": "Return for inspection"})
                sale_rows = first.execute(
                    "SELECT transaction_id, price_usd_cents FROM sale_transactions ORDER BY transaction_id"
                ).fetchall()
            finally:
                first.close()
            reopened, saved_store = open_file_demo(path)
            try:
                after = SyntheticShortlistService(saved_store).get(sid)
                self.assertEqual(after, before)
                self.assertEqual(after["entries"][1]["investigation"]["status"], "insufficient_data")
                self.assertEqual(reopened.execute(
                    "SELECT transaction_id, price_usd_cents FROM sale_transactions ORDER BY transaction_id"
                ).fetchall(), sale_rows)
            finally:
                reopened.close()


if __name__ == "__main__":
    unittest.main()
