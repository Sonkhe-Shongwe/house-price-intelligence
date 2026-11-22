#!/usr/bin/env python3
"""Export aggregate, non-personal Phase 0/1/2 reports for a GitHub Actions artifact.

Only allowlisted summary fields are copied. Do not upload source JSONL or per-PIN
examples, even when the underlying dataset is publicly accessible.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

PHASE0_FIELDS = (
    'audited_township_code', 'sale_start_inclusive', 'sale_end_exclusive',
    'source_sale_rows', 'source_building_rows', 'sales_after_screen',
    'joined_sale_candidates', 'extraction_capped', 'source_sales_by_year',
    'screened_sales_by_year', 'joined_sales_by_year', 'join_rejections_by_year',
    'sale_reasons_not_mutually_exclusive', 'join_rejection_counts',
    'class_counts_in_joined_candidates', '2024_subjects_tested',
    '2024_subjects_with_3_or_more_comps', 'no_prior_building_diagnostics',
    'single_prior_record_card_value_counts', 'limitations',
)
PHASE1_FIELDS = ('audited_source', 'eligible_class203_sales',
                 'pin_year_keys', 'enrichment_issues', 'evaluation')
PHASE2_FIELDS = ('scope', 'policy', 'total_class203_sales', 'subject_count',
                 'tier_counts', 'reason_counts', 'adaptive_all_supported',
                 'township_all_supported', 'neighborhood_all_supported',
                 'paired_with_township', 'paired_with_neighborhood',
                 'spatial_fallback_only', 'limitations')


def export_summary(payload: dict, allowed: tuple[str, ...]) -> dict:
    """Return only approved aggregate fields; drop identifiers and examples."""
    return {name: payload[name] for name in allowed if name in payload}


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'Expected object in {path}')
    return data


def write_summary(text: str) -> None:
    print(text, flush=True)
    step_summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if step_summary:
        with open(step_summary, 'a', encoding='utf-8') as f:
            f.write(text + '\n')


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase0', type=Path, required=True)
    p.add_argument('--phase1', type=Path, required=True)
    p.add_argument('--phase2', type=Path, default=None)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'github_sha': os.getenv('GITHUB_SHA', 'local'),
        'github_run_id': os.getenv('GITHUB_RUN_ID', 'local'),
        'raw_property_extracts_uploaded': False,
        'phase0_status': 'not_completed', 'phase1_status': 'not_completed',
        'phase2_status': 'not_completed',
    }
    write_summary('## House Price Intelligence: cloud data audit')
    write_summary('Historical experimental analysis only. No validated property values.')

    p0 = args.phase0 / 'audit_summary_v2.json'
    if p0.is_file():
        data = read_json(p0)
        sanitized = export_summary(data, PHASE0_FIELDS)
        (args.out / 'phase0_summary.json').write_text(json.dumps(sanitized, indent=2), encoding='utf-8')
        report = args.phase0 / 'audit_report_v2.md'
        if report.is_file():
            (args.out / 'phase0_report.md').write_text(report.read_text(encoding='utf-8'), encoding='utf-8')
        manifest['phase0_status'] = ('incomplete_capped' if any(data.get('extraction_capped', {}).values()) else 'complete')
        write_summary(f"- Phase 0: {data.get('source_sale_rows', 0)} sales fetched; "
                      f"{data.get('joined_sale_candidates', 0)} accepted historical building matches")
    else:
        write_summary('- Phase 0: no report available; inspect failed workflow step')

    p1 = args.phase1 / 'phase1_summary.json'
    if p1.is_file():
        data = read_json(p1)
        sanitized = export_summary(data, PHASE1_FIELDS)
        (args.out / 'phase1_summary.json').write_text(json.dumps(sanitized, indent=2), encoding='utf-8')
        report = args.phase1 / 'phase1_report.md'
        if report.is_file():
            (args.out / 'phase1_report.md').write_text(report.read_text(encoding='utf-8'), encoding='utf-8')
        manifest['phase1_status'] = 'complete'
        ev = data.get('evaluation', {})
        write_summary(f"- Phase 1: {data.get('eligible_class203_sales', 0)} Class 203 sales; "
                      f"2024 township supported {ev.get('township_supported_2024', 0)} / "
                      f"neighbourhood supported {ev.get('neighborhood_supported_2024', 0)}")
        write_summary(f"- Paired historical subjects: {ev.get('paired_supported_2024', 0)}")
    else:
        write_summary('- Phase 1: no report available; inspect failed workflow step')

    p2 = args.phase2 / 'phase2_summary.json' if args.phase2 is not None else None
    if p2 is not None and p2.is_file():
        data = read_json(p2)
        sanitized = export_summary(data, PHASE2_FIELDS)
        (args.out / 'phase2_summary.json').write_text(json.dumps(sanitized, indent=2), encoding='utf-8')
        report = args.phase2 / 'phase2_report.md'
        if report.is_file():
            (args.out / 'phase2_report.md').write_text(report.read_text(encoding='utf-8'), encoding='utf-8')
        manifest['phase2_status'] = 'complete'
        write_summary(f"- Phase 2: {data.get('subject_count', 0)} test subjects; "
                      f"neighbourhood-first {data.get('tier_counts', {}).get('same_neighborhood', 0)}, "
                      f"spatial fallback {data.get('tier_counts', {}).get('spatial_fallback', 0)}, "
                      f"insufficient {data.get('tier_counts', {}).get('none', 0)}")
    else:
        write_summary('- Phase 2: no report available; inspect failed workflow step')

    (args.out / 'run_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    write_summary('Only aggregate summaries and aggregate Markdown reports are retained as artifacts.')


if __name__ == '__main__':
    main()
