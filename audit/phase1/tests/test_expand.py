import unittest
import json
import tempfile
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from expand import (baseline_price, distance_km, enrich_joined, evaluation,
                    fetch_for_keys, geo_point, group_by_key, phase0_class203, prior_comparables)


def subject(pin, dt='2024-06-01', sqft=1200, neighborhood='17001', price=500000):
    return {'pin': pin, 'doc_no': f'D{pin}', 'sale_date': dt, 'sqft': sqft,
            'class': '203', 'sale_price': price, 'township_code': '17',
            'nbhd_code': neighborhood, 'lat': 42.05, 'lon': -87.71}


class ExpansionTests(unittest.TestCase):
    def test_neighborhood_filter_and_future_exclusion(self):
        s = subject('00000000000001')
        same = subject('00000000000002', '2024-03-01')
        other = subject('00000000000003', '2024-03-01', neighborhood='17002')
        future = subject('00000000000004', '2024-07-01')
        self.assertEqual(len(prior_comparables(s, [same, other, future])), 2)
        self.assertEqual(prior_comparables(s, [same, other, future], same_neighborhood=True), [same])

    def test_ranking_does_not_use_price(self):
        s = subject('00000000000001')
        exact = subject('00000000000002', '2024-01-01', sqft=1200, price=1_000_000)
        less = subject('00000000000003', '2024-05-01', sqft=1230, price=20_000)
        ordered = prior_comparables(s, [less, exact])
        self.assertEqual(ordered[0]['pin'], exact['pin'])

    def test_neighborhood_needs_evidence(self):
        s = subject('00000000000001', neighborhood=None)
        other = subject('00000000000002', '2024-04-01')
        self.assertEqual(prior_comparables(s, [other], same_neighborhood=True), [])

    def test_different_year_only_joins_same_year(self):
        s = subject('00000000000001')
        s['characteristics_year'] = 2023
        loc = {'pin': s['pin'], 'year': 2022, 'nbhd_code': '17003'}
        records, issues = enrich_joined([s], [loc], [])
        self.assertIsNone(records[0]['nbhd_code'])
        self.assertEqual(issues['universe_missing'], 1)

    def test_duplicate_location_rows_are_not_silently_selected(self):
        s = subject('00000000000001'); s['characteristics_year'] = 2023
        loc = {'pin': s['pin'], 'year': 2023, 'nbhd_code': '17001'}
        r, issues = enrich_joined([s], [loc, loc], [])
        self.assertIsNone(r[0]['nbhd_code'])
        self.assertEqual(issues['universe_ambiguous'], 1)

    def test_invalid_geo_not_used(self):
        self.assertEqual(geo_point({'lat': '99', 'lon': '-87.7'}), (None, None))
        self.assertEqual(geo_point({'lat': '42.02', 'lon': '-87.7'}), (42.02, -87.7))

    def test_fractional_year_is_not_truncated_to_another_year(self):
        rows = [{'pin': '00000000000001', 'year': '2023.5'},
                {'pin': '00000000000001', 'year': '2023.0'}]
        index = group_by_key(rows)
        self.assertEqual(len(index[('00000000000001', 2023)]), 1)

    def test_distance(self):
        a = subject('00000000000001'); b = dict(a)
        self.assertAlmostEqual(distance_km(a, b), 0)

    def test_model_abstains_when_fewer_than_three_comparables(self):
        self.assertIsNone(baseline_price([subject('00000000000001')]))
        self.assertEqual(baseline_price([subject('00000000000001', price=100),
                                         subject('00000000000002', price=200),
                                         subject('00000000000003', price=300)]), 200)

    def test_paired_subset_evaluation(self):
        old = [subject(f'{i:014d}', '2023-11-01', neighborhood='17001', price=100000+i) for i in range(1, 5)]
        newer = subject('00000000000050', '2024-06-01', neighborhood='17001', price=200000)
        other = subject('00000000000051', '2024-06-01', neighborhood='17003', price=210000)
        out = evaluation(old+[newer, other])
        self.assertEqual(out['2024_subjects'], 2)
        self.assertEqual(out['neighborhood_supported_2024'], 1)
        self.assertEqual(out['paired_supported_2024'], 1)

    def test_end_to_end_outputs_using_mocked_enrichment(self):
        import expand
        sample = {'pin': '12345678901234', 'sale_date': '2024-06-01',
                  'sale_price': '350000', 'doc_no': 'X', 'township_code': '17',
                  'is_multisale': False, 'num_parcels_sale': '1.0',
                  'sale_filter_less_than_10k': False, 'sale_filter_deed_type': False,
                  'sale_filter_same_sale_within_365': False}
        building = {'pin': sample['pin'], 'year': '2023', 'card': '1',
                    'class': '203', 'township_code': '17', 'char_bldg_sf': '1200',
                    'pin_num_cards': '1.0'}
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder); p0 = p / 'p0'; output = p / 'p1'; p0.mkdir()
            (p0 / 'audit_summary_v2.json').write_text(json.dumps({
                'audit_code_version': 'phase0-v2',
                'source_sale_rows': 1, 'source_building_rows': 1,
                'extraction_capped': {'sales': False, 'buildings': False}}), encoding='utf-8')
            (p0 / 'sales_selected_fields.jsonl').write_text(json.dumps(sample) + '\n', encoding='utf-8')
            (p0 / 'buildings_selected_fields.jsonl').write_text(json.dumps(building) + '\n', encoding='utf-8')
            def fake_fetch(dataset_id, keys, wanted, required, **_):
                if dataset_id == expand.UNIVERSE_ID:
                    return ([{'pin': sample['pin'], 'year': 2023, 'nbhd_code': '17001',
                              'lat': '42.04', 'lon': '-87.70'}],
                            {'downloaded_rows': 1, 'dataset_id': dataset_id})
                return ([dict(building, char_beds='3', char_fbath='2')],
                        {'downloaded_rows': 1, 'dataset_id': dataset_id})
            with patch.object(expand, 'fetch_for_keys', side_effect=fake_fetch), \
                 patch('sys.argv', ['expand.py', '--phase0', str(p0), '--out', str(output)]):
                expand.main()
            report = json.loads((output / 'phase1_summary.json').read_text(encoding='utf-8'))
            self.assertEqual(report['eligible_class203_sales'], 1)
            self.assertEqual(report['evaluation']['2024_subjects'], 1)
            self.assertEqual(report['enrichment_issues'], {})
            self.assertTrue((output / 'phase1_report.md').exists())
            self.assertEqual(len((output / 'class203_enriched_sales.jsonl').read_text().splitlines()), 1)

    def test_class203_only(self):
        sale = {'pin': '12345678901234', 'sale_date': '2024-06-01', 'sale_price': '350000', 'doc_no': 'X',
                'township_code': '17', 'is_multisale': False, 'num_parcels_sale': '1.0',
                'sale_filter_less_than_10k': False, 'sale_filter_deed_type': False,
                'sale_filter_same_sale_within_365': False}
        b = {'pin': sale['pin'], 'year': '2023', 'card': '1', 'class': '203',
             'township_code': '17', 'char_bldg_sf': '1200', 'pin_num_cards': '1.0'}
        self.assertEqual(len(phase0_class203([sale], [b])), 1)
        b['class'] = '211'
        self.assertEqual(phase0_class203([sale], [b]), [])


if __name__ == '__main__':
    unittest.main()
