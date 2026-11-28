"""Invented metadata only; no network or property records."""
import json
import unittest

from tools.nyc_metadata_notice import (
    SOURCE_IDS, MAX_DOCUMENT_BYTES, MAX_NOTICE_CHARS, metadata_path,
    project_notice, project_notice_batch,
)
from tools.nyc_qualification import FIELDS, QualificationError


def payload(dataset, **extra):
    return json.dumps(dict(id=dataset, rowsUpdatedAt=10, viewLastModified=20, **extra)).encode()


class NoticeTests(unittest.TestCase):
    def setUp(self):
        self.dataset = SOURCE_IDS[0]

    def project(self, **extra):
        return project_notice(self.dataset, payload(self.dataset, **extra), "10:20")

    def test_complete_exact_batch(self):
        self.assertEqual(set(SOURCE_IDS), set(FIELDS))
        docs = {d: payload(d, licenseId="invented-license") for d in SOURCE_IDS}
        pins = {d: "10:20" for d in SOURCE_IDS}
        result = project_notice_batch(docs, pins)
        self.assertEqual(set(result["sources"]), set(SOURCE_IDS))
        self.assertFalse(result["rights_accepted"])
        self.assertFalse(result["property_collection_authorised"])
        for d, item in result["sources"].items():
            self.assertEqual(item["metadata_path"], f"/api/views/{d}.json")
            self.assertEqual(item["revision"], pins[d])
            self.assertTrue(item["manual_review_required"])

    def test_absent_explicit_empty_and_unreviewed(self):
        absent = self.project()
        blank = self.project(licenseId=None, termsOfUse="  ")
        present = self.project(licenseId="invented", termsOfUse="Invented notice.")
        self.assertEqual(absent["license_id"], {"state":"not_present"})
        self.assertEqual(blank["license_id"], {"state":"explicit_empty"})
        self.assertEqual(blank["notice_fields"]["termsOfUse"]["state"], "explicit_empty")
        self.assertEqual(present["notice_fields"]["termsOfUse"],
                         {"state":"present_unreviewed","value":"Invented notice."})
        self.assertFalse(present["rights_accepted"])

    def test_allowlisted_notice_and_link_projection(self):
        item = self.project(license={"name":"Invented licence",
                                    "termsLink":"https://www.nyc.gov/site/example.page"},
                            metadata={"custom_fields":{"Dataset Information":{
                                "Disclaimer":"Invented disclaimer",
                                "Terms of Use URL":"https://creativecommons.org/licenses/by/4.0/"
                            }}})
        self.assertEqual(item["license_detail"]["termsLink"]["state"], "present_unreviewed")
        self.assertEqual(item["custom_fields"]["notices"]["Disclaimer"]["value"], "Invented disclaimer")
        self.assertFalse(item["custom_fields"]["other_fields_unreviewed"])

    def test_non_notice_values_never_projected(self):
        item = self.project(description="INVENTED DESCRIPTION", attribution="INVENTED PERSON",
            owner={"displayName":"INVENTED OWNER"}, columns=[{"cachedContents":{"top":[{"item":"INVENTED SAMPLE"}]}}],
            metadata={"custom_fields":{"Dataset Information":{"Contact":"INVENTED CONTACT"}},
                      "attachments":[{"filename":"INVENTED ATTACHMENT"}]})
        self.assertNotIn("INVENTED", json.dumps(item))
        self.assertEqual(item["description_state"], "present_unreviewed")
        self.assertTrue(item["custom_fields"]["other_fields_unreviewed"])

    def test_wrong_id_revision_or_endpoint_refused(self):
        for dataset, raw, revision in (
            ("bad-id", payload(self.dataset), "10:20"),
            (self.dataset, payload(SOURCE_IDS[1]), "10:20"),
            (self.dataset, payload(self.dataset), "10:21"),
            (self.dataset, payload(self.dataset), "010:20"),
        ):
            with self.subTest(dataset=dataset, revision=revision), self.assertRaises(QualificationError):
                project_notice(dataset, raw, revision)
        for source in ("../resource/usep-8jbt", self.dataset+"?x=1", None):
            with self.assertRaises(QualificationError):
                metadata_path(source)

    def test_invalid_revision_types(self):
        for value in (True, 0, -1, "10", 10.0, 2**53):
            raw = json.dumps(dict(id=self.dataset, rowsUpdatedAt=value, viewLastModified=20)).encode()
            with self.subTest(value=value), self.assertRaisesRegex(QualificationError, "invalid_metadata_revision"):
                project_notice(self.dataset, raw, "10:20")

    def test_incomplete_or_extra_batch_refused(self):
        docs = {d: payload(d) for d in SOURCE_IDS}
        pins = {d: "10:20" for d in SOURCE_IDS}
        for bad in ({}, dict(docs, unknown=b"{}"), {d:v for d,v in docs.items() if d!=self.dataset}):
            with self.assertRaisesRegex(QualificationError, "incomplete_notice_batch"):
                project_notice_batch(bad, pins)
        pins[self.dataset] = "11:20"
        with self.assertRaisesRegex(QualificationError, "metadata_revision_mismatch"):
            project_notice_batch(docs, pins)

    def test_malformed_json_duplicate_and_record_envelope(self):
        for raw in (b"", b"{", b"\xff", b"[]", b'{"id": "a", "id":"b"}',
                    b'{"x": NaN}', payload(self.dataset, rows=[])):
            with self.subTest(raw=raw[:50]), self.assertRaises(QualificationError):
                project_notice(self.dataset, raw, "10:20")

    def test_bounds(self):
        with self.assertRaisesRegex(QualificationError, "metadata_byte_limit"):
            project_notice(self.dataset, b" "*(MAX_DOCUMENT_BYTES+1), "10:20")
        with self.assertRaisesRegex(QualificationError, "invalid_notice_text"):
            self.project(disclaimer="x"*(MAX_NOTICE_CHARS+1))
        with self.assertRaisesRegex(QualificationError, "invalid_custom_fields"):
            self.project(metadata={"custom_fields":{str(i):{} for i in range(33)}})

    def test_unsafe_links(self):
        for link in ("http://www.nyc.gov/terms", "https://www.nyc.gov.evil.example/",
                     "https://user@www.nyc.gov/", "https://www.nyc.gov/?secret=x",
                     "javascript:alert(1)", "https://www.nyc.gov:443/",
                     "https://www.nyc.gov/\nfoo"):
            with self.subTest(link=link), self.assertRaises(QualificationError):
                self.project(termsOfUseUrl=link)

    def test_malformed_notice_fields_are_redacted(self):
        for extra in ({"disclaimer": ["INVENTED LEAK"]}, {"licenseId":"INVENTED LEAK"},
                      {"license":{"name":"OK","extra":"INVENTED LEAK"}},
                      {"termsOfUse":"contact@example.invalid"},
                      {"termsOfUse":"<script>INVENTED LEAK</script>"},
                      {"metadata":{"custom_fields":{"Dataset Information":[]}}}):
            with self.subTest(extra=extra), self.assertRaises(QualificationError) as error:
                self.project(**extra)
            self.assertNotIn("INVENTED LEAK", str(error.exception))

    def test_duplicate_custom_notice_refused(self):
        with self.assertRaisesRegex(QualificationError, "ambiguous_custom_notice"):
            self.project(metadata={"custom_fields":{
                "Dataset Information":{"Disclaimer":"Invented A"},
                "Licensing":{"Disclaimer":"Invented B"}}})


if __name__ == "__main__":
    unittest.main()
