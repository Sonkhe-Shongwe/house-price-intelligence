import copy
import unittest
from backend.real_source_intake import DATASETS, REQUIRED, OPTIONAL, IntakeRefused, exact_cents, prepare_intake

PIN = "00000000000001"

def sample():
    rows = {
        "sales": [dict(pin=PIN, sale_date="2025-04-01T00:00:00", sale_price="525000.01", doc_no="FICT-1",
                       township_code="17", is_multisale=False, num_parcels_sale="1.0", sale_filter_less_than_10k=False,
                       sale_filter_deed_type=False, sale_filter_same_sale_within_365=False)],
        "assessment": [dict(pin=PIN, year="2024.0", card="1", **{"class":"203"}, township_code="17", char_bldg_sf="1600")],
        "geography": [dict(pin=PIN, year="2024.0", nbhd_code="FICT", lat="42.04", lon="-87.68")],
        "address": [dict(pin=PIN, year="2024.0", prop_address_full="1 Fictional Court")],
    }
    meta = {dataset: {"epoch": 1, "fields": sorted(REQUIRED[role] | OPTIONAL[role])} for role,dataset in DATASETS.items()}
    return dict(rows=rows, metadata_before=meta, metadata_after=copy.deepcopy(meta), extracted_at_utc="2026-11-24T00:00:00Z")


class IntakeTests(unittest.TestCase):
    def test_exact_cents_and_inactive_source_plan(self):
        plan=prepare_intake(**sample())
        self.assertEqual(plan["sales"][0]["sale_price_usd_cents"],52500001)
        self.assertEqual(plan["parcel_years"][0]["tax_year"],2024)
        for field in ("active","public_display_approved","historical_asof_verified"):
            self.assertFalse(plan[field])
        self.assertFalse(plan["parcel_years"][0]["building_identity_verified"])
        self.assertEqual(plan,prepare_intake(**sample()))

    def test_fractional_cents_and_float_refused(self):
        for bad in ("525000.001","NaN","Infinity",525000.01,True,"525000.00000000000000000000000000000001"):
            with self.subTest(bad=bad), self.assertRaises(IntakeRefused): exact_cents(bad)

    def test_revision_change_refused(self):
        args=sample(); args["metadata_after"][DATASETS["sales"]]["epoch"]=2
        with self.assertRaisesRegex(IntakeRefused,"source_revision"): prepare_intake(**args)

    def test_unnecessary_private_fields_refused(self):
        args=sample(); args["rows"]["address"][0]["owner_name"]="invented"
        with self.assertRaisesRegex(IntakeRefused,"unexpected_source_fields"): prepare_intake(**args)

    def test_conflicting_duplicate_refused(self):
        args=sample(); other=dict(args["rows"]["sales"][0],sale_price="525001.01"); args["rows"]["sales"].append(other)
        with self.assertRaisesRegex(IntakeRefused,"conflicting_sale_identity"): prepare_intake(**args)

    def test_ambiguous_address_not_selected(self):
        args=sample(); args["rows"]["address"].append(dict(args["rows"]["address"][0]))
        item=prepare_intake(**args)["parcel_years"][0]
        self.assertEqual(item["address_state"],"ambiguous"); self.assertIsNone(item["display_address"])

    def test_missing_address_and_geography(self):
        args=sample(); args["rows"]["address"]=[]; args["rows"]["geography"]=[]
        item=prepare_intake(**args)["parcel_years"][0]
        self.assertEqual(item["address_state"],"missing"); self.assertIsNone(item["latitude"])

    def test_wrong_scope_and_fractional_year(self):
        for field,val in [("township_code","18"),("year","2024.5")]:
            args=sample(); args["rows"]["assessment"][0][field]=val
            with self.assertRaises(IntakeRefused): prepare_intake(**args)

    def test_ambiguous_assessment_refused(self):
        args=sample(); args["rows"]["assessment"].append(dict(args["rows"]["assessment"][0],card="2"))
        with self.assertRaisesRegex(IntakeRefused,"empty_eligible_cohort"): prepare_intake(**args)

    def test_unexpected_enrichment_key_refused(self):
        args=sample(); args["rows"]["geography"][0]["pin"]="00000000000002"
        with self.assertRaisesRegex(IntakeRefused,"unexpected_enrichment_key"): prepare_intake(**args)

    def test_revised_source_fingerprint_changes(self):
        args=sample(); old=prepare_intake(**args)
        args["rows"]["sales"][0]["sale_price"]="525000.02"
        new=prepare_intake(**args)
        self.assertNotEqual(old["build_hash_sha256"],new["build_hash_sha256"])
        self.assertEqual(old["sales"][0]["sale_price_usd_cents"],52500001)
