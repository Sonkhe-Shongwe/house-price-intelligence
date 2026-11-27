import unittest
from dataclasses import replace
from datetime import date

from backend import sa_investigation_v2 as sa


class SouthAfricanContractTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 1, 1)
        self.request = {"contract_version": sa.VERSION, "market": "ZA", "currency": "ZAR",
                        "area_unit": "m2", "subject_key": sa.wire_key("fictional-erf-000001"),
                        "analysis_date": "2025-07-01", "mode": "as_of", "asking_price": "2500000.01"}
        self.props, self.events = sa.fixture()

    def run_fixture(self, events=None, props=None, **updates):
        return sa._evaluate(self.request | updates, self.props if props is None else props,
                            self.events if events is None else events, today=self.today)

    def keys(self, result):
        return [c["property_key"]["value"] for c in result["comparables"]]

    def test_primary_and_extended_windows(self):
        q = self.run_fixture()
        self.assertEqual(q["status"], "fictional_supported")
        self.assertEqual(q["window_days"], 365)
        self.assertEqual(q["selected_count"], 5)
        self.assertEqual(q["eligible_unique_by_window"], {"365": 5, "730": 5})
        self.assertEqual(q["subject"]["asking_price"]["minor_units"], 250000001)
        self.assertTrue(q["fictional_as_of_qualified"])
        self.assertFalse(q["historical_as_of_verified"])
        self.assertIsNone(q["valuation"])
        old = tuple(replace(e, chronology=replace(e.chronology, reported=date(2024,1,1),
                      registered=date(2024,1,11), available=date(2024,1,21))) if
                      e.chronology.parcel.endswith(("000003","000004")) else e for e in self.events)
        q = self.run_fixture(events=old)
        self.assertEqual(q["window_days"], 365)  # three remain within 365
        old = tuple(replace(e, chronology=replace(e.chronology, reported=date(2024,2,1),
                      registered=date(2024,2,11), available=date(2024,2,21))) if
                      e.chronology.parcel.endswith("000005") else e for e in old)
        self.assertEqual(self.run_fixture(events=old)["window_days"], 730)

    def test_price_free_rank_and_repeat_selection(self):
        q = self.run_fixture()
        altered = tuple(replace(e, cents=1+1000*j) for j,e in enumerate(reversed(self.events)))
        other = self.run_fixture(events=altered, asking_price="1.00")
        self.assertEqual(self.keys(q), self.keys(other))
        self.assertIn("fictional-event-000002-b", [c["event_id"] for c in q["comparables"]])
        self.assertEqual(len(set(self.keys(q))), q["selected_count"])

    def test_exclusions_and_retrospective(self):
        q = self.run_fixture()
        self.assertEqual(set(self.keys(q)), {f"fictional-erf-{i:06d}" for i in range(2,7)})
        self.assertIn(2000**2, [c["distance_squared_metres"] for c in q["comparables"]])
        retro = self.run_fixture(mode="retrospective")
        self.assertEqual(retro["eligible_unique_by_window"]["365"], 6)
        self.assertFalse(retro["fictional_as_of_qualified"])
        self.assertFalse(retro["real_data_approved"])
        self.assertEqual(self.run_fixture(subject_key=sa.wire_key("fictional-erf-000010"))["reason"],
                         "subject_identity_unresolved")

    def test_conflicts_and_insufficient(self):
        event = self.events[0]
        duplicate_day = replace(event, event_id="fictional-event-000002-c")
        q = self.run_fixture(events=(event, duplicate_day, self.events[2]))
        self.assertEqual(q["selected_count"], 0)
        self.assertEqual(q["eligible_unique_by_window"]["730"], 1)
        with self.assertRaisesRegex(sa.ContractError, "duplicate"):
            self.run_fixture(events=(event,event))
        p = replace(self.props[0], versions=self.props[0].versions*2)
        self.assertEqual(self.run_fixture(props=(p,*self.props[1:]))["reason"],
                         "subject_attributes_or_location_unqualified")

    def test_strict_wire_boundary(self):
        for update in ({"market":"US"}, {"currency":"USD"}, {"area_unit":"sqft"},
                       {"contract_version":"p3-draft-v0.2"}, {"asking_price":1.01},
                       {"asking_price":"1.001"}, {"asking_price":"0"},
                       {"analysis_date":"2027-01-01"}, {"analysis_date":"2025-7-1"},
                       {"subject_key":{"namespace":"sg26","value":"123"}},
                       {"subject_key":sa.wire_key("fictional-erf-1")},
                       {"data_build":"real"}, {"mode":"production"}):
            with self.subTest(update=update), self.assertRaises(sa.ContractError):
                self.run_fixture(**update)
        self.assertEqual(sa.parse_money("1.01"),101)
        self.assertEqual(sa.money(101)["decimal"],"1.01")
        self.assertEqual(sa.investigate(self.request,today=self.today), self.run_fixture())


if __name__ == "__main__":
    unittest.main()
