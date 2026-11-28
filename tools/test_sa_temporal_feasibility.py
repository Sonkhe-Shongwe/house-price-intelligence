import unittest
from dataclasses import replace
from datetime import date, timedelta

from tools.sa_temporal_feasibility import InventedSale, InventedExtentVersion, qualify_fixture


class TemporalFeasibilityTests(unittest.TestCase):
    def setUp(self):
        self.day = date(2025, 1, 1)
        self.cutoff = self.day + timedelta(days=90)
        self.sale = InventedSale("fictional-reference", self.day,
                                 self.day + timedelta(days=20),
                                 self.day + timedelta(days=30), True, True)
        self.attr = InventedExtentVersion(self.sale.parcel, self.day - timedelta(days=30),
                                          None, self.day - timedelta(days=1), self.day)

    def q(self, sale=None, attrs=None, mode="as_of", subject="fictional-subject"):
        return qualify_fixture(sale or self.sale, [self.attr] if attrs is None else attrs,
                               subject, self.cutoff, mode)

    def test_separate_modes_and_cutoff_boundary(self):
        self.assertEqual(self.q(), "fixture_as_of_qualified")
        self.assertEqual(self.q(mode="retrospective"), "fixture_retrospective_only")
        self.assertEqual(self.q(replace(self.sale, available=self.cutoff)), "fixture_as_of_qualified")

    def test_late_or_unknown_availability(self):
        for sale, expected in (
            (replace(self.sale, available=None), "availability_unknown"),
            (replace(self.sale, available=self.cutoff + timedelta(days=1)), "not_available_at_cutoff"),
        ):
            self.assertEqual(self.q(sale), expected)
            self.assertEqual(self.q(sale, mode="retrospective"), "fixture_retrospective_only")
        self.assertEqual(self.q(attrs=[replace(self.attr, available=None)]), "availability_unknown")
        self.assertEqual(self.q(attrs=[replace(self.attr, available=self.cutoff + timedelta(days=1))]),
                         "not_available_at_cutoff")

    def test_event_chronology_and_group(self):
        self.assertEqual(self.q(replace(self.sale, registered=None)), "registration_unknown")
        self.assertEqual(self.q(replace(self.sale, registered=self.day-timedelta(days=1))),
                         "event_chronology_conflict")
        self.assertEqual(self.q(replace(self.sale, available=self.day)), "event_chronology_conflict")
        self.assertEqual(self.q(replace(self.sale, single_property=False)), "event_not_qualified")
        self.assertEqual(self.q(replace(self.sale, event_valid=False)), "event_not_qualified")

    def test_attribute_versions_and_historical_applicability(self):
        self.assertEqual(self.q(attrs=[]), "attribute_version_missing_or_ambiguous")
        self.assertEqual(self.q(attrs=[self.attr, self.attr]), "attribute_version_missing_or_ambiguous")
        self.assertEqual(self.q(attrs=[replace(self.attr, effective_to=self.day)]),
                         "attribute_version_missing_or_ambiguous")
        late = replace(self.attr, observed=self.day+timedelta(days=1),
                       available=self.day+timedelta(days=2))
        self.assertEqual(self.q(attrs=[late], mode="retrospective"), "historical_attribute_unqualified")
        self.assertEqual(self.q(attrs=[replace(late, historical_applicability_documented=True)]),
                         "fixture_as_of_qualified")
        self.assertEqual(self.q(attrs=[replace(self.attr, available=self.day-timedelta(days=2))]),
                         "attribute_chronology_conflict")

    def test_subject_same_day_future_and_fixture_boundary(self):
        self.assertEqual(self.q(subject=self.sale.parcel), "subject_property")
        for day in (self.cutoff, self.cutoff+timedelta(days=1)):
            self.assertEqual(self.q(replace(self.sale, reported=day)), "not_strictly_earlier")
        with self.assertRaisesRegex(ValueError, "invented fixture"):
            self.q(replace(self.sale, parcel="not-a-fixture"))
        with self.assertRaisesRegex(ValueError, "unknown mode"):
            self.q(mode="production")


if __name__ == "__main__":
    unittest.main()
