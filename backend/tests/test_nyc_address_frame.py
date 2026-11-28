"""Invented full-frame data only; no I/O or live request."""
import json
import unittest
from decimal import Decimal

from tools import nyc_address_frame as frame
from tools.nyc_qualification import QualificationError, SUBJECT_FIELDS


def row(n=1, **extra):
    value = {"bbl": f"499001{n:04d}", "borough": "QN", "zipcode": "11361",
             "address": f"99-{n} INVENTED STREET", "bldgclass": "A2",
             "numbldgs": "1", "unitsres": "1", "unitstotal": "1",
             "bldgarea": "1000", "version": frame.VERSION, "areasource": "2"}
    value.update(extra)
    return value


def qualify(rows, **extra):
    inputs = dict(count_before=len(rows), count_after=len(rows),
                  revision_before=frame.REVISION, revision_after=frame.REVISION)
    inputs.update(extra)
    return frame.qualify_fixture_frame(rows, **inputs)


class AddressFrameTests(unittest.TestCase):
    def test_fixed_complete_frame_plan(self):
        plan = frame.request_plan(334)
        self.assertEqual(len(plan), frame.MAX_REQUESTS)
        self.assertEqual(plan[0], plan[-1])
        self.assertEqual(plan[1], plan[3])
        self.assertEqual(plan[2][0], "/resource/64uk-42ks.json")
        self.assertEqual(set(plan[2][1]["$select"].split(",")), set(SUBJECT_FIELDS))
        self.assertEqual(plan[2][1]["$where"], "borough = 'QN' AND zipcode = 11361")
        self.assertEqual(plan[2][1]["$limit"], "334")
        self.assertNotIn("$offset", plan[2][1])
        for count in (0, -1, True, "334", frame.MAX_ROWS+1):
            with self.assertRaises(QualificationError):
                frame.request_plan(count)

    def test_eligible_and_ineligible_competitors(self):
        rows = [row(1), row(2), row(3, address=" 99-2  invented street ", bldgclass="A1"),
                row(4, bldgclass="V0")]
        result = qualify(rows)
        self.assertEqual(result["frame_rows"], 4)
        self.assertEqual(result["eligible_shape_rows"], 2)
        self.assertEqual(result["eligible_outcomes"], dict(invalid_identity=0,
                         ambiguous_address=1, duplicate_bbl=0, unique_eligible=1))
        self.assertEqual(result["duplicate_address_groups"], 1)
        self.assertEqual(result["noneligible_shape_rows"], 2)

    def test_duplicate_key_even_with_different_addresses(self):
        result = qualify([row(1), row(2, bbl=Decimal("4990010001.0"), bldgclass="A1")])
        self.assertEqual(result["duplicate_bbl_groups"], 1)
        self.assertEqual(result["eligible_outcomes"]["duplicate_bbl"], 1)
        self.assertEqual(result["eligible_outcomes"]["unique_eligible"], 0)

    def test_invalid_competing_key_still_blocks_address(self):
        result = qualify([row(1), row(2, bbl=None, address=row(1)["address"], bldgclass="V0")])
        self.assertEqual(result["invalid_bbl_rows"], 1)
        self.assertEqual(result["eligible_outcomes"]["ambiguous_address"], 1)

    def test_missing_and_street_only_address_and_invalid_key(self):
        result = qualify([row(1, address=None), row(2, address="INVENTED STREET"),
                          row(3, bbl="invalid"), row(4, address="99-4 INVENTED STREET")])
        self.assertEqual(result["missing_address_rows"], 1)
        self.assertEqual(result["unusable_address_rows"], 1)
        self.assertEqual(result["invalid_bbl_rows"], 1)
        self.assertEqual(result["eligible_outcomes"]["invalid_identity"], 3)
        self.assertEqual(result["eligible_outcomes"]["unique_eligible"], 1)

    def test_exact_hyphen_no_alias_merging(self):
        result = qualify([row(1, address="99-1 INVENTED STREET"),
                          row(2, address="991 INVENTED STREET")])
        self.assertEqual(result["eligible_outcomes"]["unique_eligible"], 2)
        self.assertFalse(result["aliases_verified"])

    def test_scope_version_extra_and_bad_scalar_refused(self):
        for bad in (row(zipcode="11362"), row(borough="BK"), row(version="old"),
                    row(owner="INVENTED SECRET"), row(address=["bad"]),
                    row(address="99-1 INVENTED\nSTREET"), row(unitsres=True)):
            with self.subTest(bad=bad), self.assertRaises(QualificationError):
                qualify([bad])

    def test_revision_and_completeness_fail_closed(self):
        for extra in ({"revision_before":"old"}, {"revision_after":"old"},
                      {"count_before":2,"count_after":2}, {"count_after":2},
                      {"count_before":True}, {"count_before":frame.MAX_ROWS+1}):
            with self.subTest(extra=extra), self.assertRaises(QualificationError):
                qualify([row()], **extra)

    def test_eligibility_excludes_uncertain_measurements(self):
        rows = [row(1, areasource="1"), row(2, bldgarea=None),
                row(3, unitsres="2"), row(4, numbldgs="2"), row(5, bldgarea="1000.0")]
        result = qualify(rows)
        self.assertEqual(result["eligible_shape_rows"], 1)
        self.assertEqual(result["eligible_outcomes"]["unique_eligible"], 1)

    def test_output_only_counts_no_identity_or_authority(self):
        result = qualify([row(1)])
        encoded = json.dumps(result)
        self.assertNotIn("INVENTED", encoded)
        self.assertNotIn("4990010001", encoded)
        self.assertTrue(result["fixture_only"])
        self.assertFalse(result["actual_entry_verified"])
        self.assertFalse(result["property_collection_authorised"])
        self.assertEqual(sum(result["eligible_outcomes"].values()), result["eligible_shape_rows"])


if __name__ == "__main__":
    unittest.main()
