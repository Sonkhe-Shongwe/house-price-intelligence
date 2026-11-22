"""Safety checks for the public workflow artifact exporter."""
import unittest
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from export_reports import export_summary, PHASE0_FIELDS, PHASE1_FIELDS, PHASE2_FIELDS


class ExportTests(unittest.TestCase):
    def test_phase0_identifying_examples_not_exported(self):
        original = {'source_sale_rows': 3539, 'joined_sale_candidates': 1285,
                    'example_properties': [{'subject_pin': '01234567890123',
                                            'first_three': [{'document': 'secret-example'}]}]}
        result = export_summary(original, PHASE0_FIELDS)
        self.assertEqual(result, {'source_sale_rows': 3539, 'joined_sale_candidates': 1285})
        self.assertNotIn('01234567890123', json.dumps(result))

    def test_phase1_raw_data_not_exported(self):
        original = {'eligible_class203_sales': 273,
                    'evaluation': {'2024_subjects': 90},
                    'enriched_sales': [{'pin': '00000000000123', 'sale_price': 500000}],
                    'sources': {'raw_rows': [{'pin': '00000000000123'}]}}
        result = export_summary(original, PHASE1_FIELDS)
        self.assertNotIn('pin', json.dumps(result))
        self.assertEqual(result['evaluation']['2024_subjects'], 90)

    def test_phase2_summary_does_not_export_identifying_examples(self):
        summary = {'subject_count': 83, 'tier_counts': {'same_neighborhood': 66},
                   'per_property_evidence': [{'pin': '00000000000222', 'document': 'SECRET'}]}
        safe = export_summary(summary, PHASE2_FIELDS)
        self.assertEqual(safe, {'subject_count': 83, 'tier_counts': {'same_neighborhood': 66}})
        self.assertNotIn('SECRET', json.dumps(safe))

    def test_partial_failure_still_exports_safe_phase0_results(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            p0 = base / 'phase0'
            p0.mkdir()
            (p0 / 'audit_summary_v2.json').write_text(json.dumps({
                'source_sale_rows': 100, 'joined_sale_candidates': 44,
                'example_properties': [{'subject_pin': '12345678901234'}]
            }), encoding='utf-8')
            (p0 / 'audit_report_v2.md').write_text('# Report\n', encoding='utf-8')
            script = Path(__file__).resolve().parents[1] / 'export_reports.py'
            env = dict(os.environ)
            env.pop('GITHUB_STEP_SUMMARY', None)
            subprocess.run([sys.executable, str(script), '--phase0', str(p0),
                            '--phase1', str(base / 'not-created'), '--out', str(base / 'reports')],
                           check=True, capture_output=True, text=True, env=env)
            result = json.loads((base / 'reports' / 'phase0_summary.json').read_text(encoding='utf-8'))
            self.assertNotIn('example_properties', result)
            manifest = json.loads((base / 'reports' / 'run_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['phase1_status'], 'not_completed')


if __name__ == '__main__':
    unittest.main()
