"""Invented fixtures only."""
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import d01_strict_corroboration as c
from tools import d01_register as s
from tools import d01_file_profile as sf
from tools import d02_file_profile as pf
from tools import d02_register as p
from tools import hpi_data_manager as dm
from tools.test_d01_register import parcels
from tools.test_d01_file_profile import fixture, csv_bytes


def inputs():
    raw = parcels()
    for feature in raw["features"]:
        props = feature["properties"]
        props["SG26_CODE"] = c.REGION + props["SG26_CODE"][8:]
        props.update(ADR_NO=11 + props["OBJECTID"], ADR_NO_SFX=None,
                     STR_NAME="Fictional", LU_STR_NAME_TYPE="Street")
    rows = fixture()
    for row in rows[:2]:
        row[1] = "11 FICTIONAL STREET PINELANDS"
    return raw, rows


def assess(raw, original, diagnose=False):
    with patch.object(sf, "EXPECTED", len(original)):
        rows, _ = s.derive(csv_bytes(original))
    derived, _ = p.derive(dm.json_bytes(raw))
    return c.assess(rows, json.loads(derived), raw, [r[1] for r in original], expected=None, diagnose=diagnose)


class StrictTests(unittest.TestCase):
    def test_repeat_sales_agreement_privacy(self):
        raw, rows = inputs()
        q = assess(raw, rows)
        self.assertEqual(q["strict"]["unique"], 2)
        self.assertEqual(q["address_outcomes"]["agree"], 2)
        self.assertEqual(q["region_and_address_spatial_candidates"], 2)
        self.assertEqual(q["legacy_to_strict"]["unique"]["unique"], 2)
        self.assertEqual(q["verified_identity_matches"], 0)
        self.assertNotIn("FICTIONAL", json.dumps(q).upper())
        self.assertNotIn("INVENTED-1", json.dumps(q))
        self.assertFalse(q["persistent_join"])

    def test_wrong_region_malformed_and_portion(self):
        raw, rows = inputs()
        props = raw["features"][0]["properties"]
        original = props["SG26_CODE"]
        props["SG26_CODE"] = "C0160007" + original[8:]
        q = assess(raw, rows)
        self.assertEqual(q["legacy_to_strict"]["unique"]["unmatched"], 2)
        self.assertEqual(q["parcel_region_quality"]["wrong_region"], 1)
        props["SG26_CODE"] = "?" * 26
        q = assess(raw, rows)
        self.assertEqual(q["parcel_region_quality"]["malformed"], 1)
        self.assertEqual(q["strict"]["unmatched"], 2)
        props["SG26_CODE"] = original[:16] + "00001" + original[21:]
        q = assess(raw, rows)
        self.assertEqual(q["parcel_region_quality"]["nonzero_portion_or_suffix"], 1)
        self.assertEqual(q["strict"]["unmatched"], 2)

    def test_duplicate_and_exact_conflict(self):
        raw, rows = inputs()
        raw["features"][1]["properties"]["SG26_CODE"] = raw["features"][0]["properties"]["SG26_CODE"]
        q = assess(raw, rows)
        self.assertEqual(q["strict"]["ambiguous"], 2)
        self.assertEqual(q["address_assessed_denominator"], 0)
        raw, rows = inputs()
        rows[0][0] = "001"
        q = assess(raw, rows)
        self.assertEqual(q["strict_exact_reference_conflicts"], 1)
        self.assertEqual(q["strict"]["ambiguous"], 1)

    def test_address_abstention(self):
        raw, rows = inputs()
        rows[0][1] = "99 Fictional Street PINELANDS"
        self.assertEqual(assess(raw, rows)["address_outcomes"]["mismatch"], 1)
        props = raw["features"][0]["properties"]
        props["ADR_NO_SFX"] = "A"
        self.assertEqual(assess(raw, rows)["address_outcomes"]["unsupported"], 2)
        props["ADR_NO_SFX"] = None
        props["STR_NAME"] = None
        self.assertEqual(assess(raw, rows)["address_outcomes"]["missing"], 2)
        raw, rows = inputs()
        raw["features"][3]["properties"]["ADR_NO"] = 11
        self.assertEqual(assess(raw, rows)["address_outcomes"]["ambiguous"], 2)
        for feature in raw["features"]:
            del feature["properties"]["LU_STR_NAME_TYPE"]
        q = assess(raw, rows)
        self.assertEqual(q["address_schema"], "missing")
        self.assertEqual(q["address_outcomes"]["missing"], 2)

    def test_diagnostic_lexical_categories(self):
        right = "11 fictional street pinelands"
        for left, kind in [
            ("12 fictional street pinelands", "house_number_only"),
            ("11 other street pinelands", "street_name_tokens_only"),
            ("11 fictional road pinelands", "street_type_token_only"),
            ("12 other road pinelands", "multiple_components"),
        ]:
            self.assertEqual(c.mismatch_reason(left, right, "street"), kind)
        self.assertEqual(c.mismatch_reason("11 other street pinelands", right, "access road"),
                         "unknown_component_boundary")
        self.assertEqual(c.unsupported_reason("unsupported", "comparable"), "sale_structure_only")
        self.assertEqual(c.unsupported_reason("comparable", "unsupported"), "parcel_structure_only")
        self.assertEqual(c.unsupported_reason("unsupported", "unsupported"), "both_structures")
        self.assertEqual(c.unsupported_reason("missing", "unsupported"), "unknown")

    def test_diagnostic_baseline_and_no_new_matches(self):
        raw, rows = inputs()
        rows[0][1] = "11 Fictional Rd PINELANDS"
        rows[1][1] = "11A Fictional Street PINELANDS"
        baseline = assess(raw, rows)
        self.assertEqual(baseline["address_outcomes"]["mismatch"], 1)
        self.assertEqual(baseline["address_outcomes"]["unsupported"], 1)
        with self.assertRaisesRegex(ValueError, "ADDRESS_DIAGNOSTIC_BASELINE_MISMATCH"):
            assess(raw, rows, diagnose=True)
        with patch.object(c, "DIAGNOSTIC_BASELINE", baseline):
            result = assess(raw, rows, diagnose=True)
        diag = result.pop("mismatch_diagnosis")
        self.assertEqual(result, baseline)
        self.assertEqual(diag["mismatch_reasons"]["street_type_token_only"], 1)
        self.assertEqual(diag["unsupported_reasons"]["sale_structure_only"], 1)
        self.assertEqual(diag["new_matches"], 0)
        self.assertNotIn("FICTIONAL", json.dumps(diag).upper())
        self.assertEqual(sum(diag["mismatch_reasons"].values()), diag["mismatch_denominator"])
        self.assertEqual(sum(diag["unsupported_reasons"].values()), diag["unsupported_denominator"])

    def test_audited_files_no_writes_expiry_tamper(self):
        raw, rows = inputs()
        pb, sb = dm.json_bytes(raw), csv_bytes(rows)
        day = date(2026, 11, 27)
        with tempfile.TemporaryDirectory() as td, patch.object(sf, "EXPECTED", 4), \
                patch.object(sf, "OBSERVED_BYTES", len(sb)), patch.object(dm, "SALE_SHA", dm.sha(sb)), \
                patch.object(dm, "PARCEL_SHA", dm.sha(pb)), patch.object(pf, "OBSERVED_BYTES", len(pb)), \
                patch.object(pf, "DISPLAYED_ROWS", 4):
            root = Path(td)
            dm.initialise(root)
            dm.publish(root / dm.PARCEL_RAW, pb)
            dm.publish(root / dm.SALE_RAW, sb)
            with self.assertRaisesRegex(ValueError, "AUDIT_REQUIRED"):
                c.run(root, today=day, expected=None)
            p.register(root, today=day)
            s.register(root, today=day)
            snapshot = {f.relative_to(root): f.read_bytes() for f in root.rglob("*") if f.is_file()}
            q = c.run(root, today=day, expected=(2, 2, 0, 0))
            self.assertEqual(q["region_and_address_corroborated"], 2)
            with patch.object(c, "DIAGNOSTIC_BASELINE", {"address_outcomes": q["address_outcomes"]}):
                diag = c.run(root, today=day, expected=(2, 2, 0, 0), diagnose=True)
            self.assertEqual(diag["mismatch_diagnosis"]["new_matches"], 0)
            self.assertTrue(diag["mismatch_diagnosis"]["baseline_reproduced"])
            self.assertEqual(snapshot, {f.relative_to(root): f.read_bytes() for f in root.rglob("*") if f.is_file()})
            with self.assertRaisesRegex(ValueError, "LEGACY_BASELINE_MISMATCH"):
                c.run(root, today=day)
            with self.assertRaisesRegex(ValueError, "RETENTION_WINDOW"):
                c.run(root, today=sf.REVIEW, expected=None, diagnose=True)
            (root / dm.SALE_RAW).write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "checksum"):
                c.run(root, today=day, expected=None, diagnose=True)


if __name__ == "__main__":
    unittest.main()
