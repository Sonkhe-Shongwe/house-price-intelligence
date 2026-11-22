#!/usr/bin/env python3
"""Phase 1: enrich VERIFIED Phase 0 class-203 sales and evaluate local comparables.

Uses saved Phase 0 JSONL records, then fetches ONLY source records for their
eligible parcel IDs and prior tax years. Never changes Phase 0 data. Does not
train a model or claim present-day valuation accuracy.

Run from any directory: python expand.py --phase0 ../phase0/output --out output
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import json
from math import radians, sin, cos, asin, sqrt
from pathlib import Path
import statistics
import sys
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'phase0'))
from audit import (BASE, SALES_ID, BUILDINGS_ID, building_rows_by_key,
                   fetch_json, join_sale_to_prior_building, metadata,
                   normalize_pin, sale_reject_reasons)

UNIVERSE_ID = 'nj4t-kc8j'
UNIVERSE_WANTED = {'pin', 'year', 'nbhd_code', 'lat', 'lon', 'class'}
DETAIL_WANTED = {'pin', 'year', 'card', 'class', 'char_beds', 'char_fbath',
                 'char_hbath', 'char_rooms', 'char_yrblt', 'char_land_sf',
                 'char_bldg_sf'}
REQUIRED_UNIVERSE = {'pin', 'year', 'nbhd_code'}
REQUIRED_DETAIL = {'pin', 'year', 'card', 'char_bldg_sf'}


def load_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def save_jsonl(path, records):
    with Path(path).open('w', encoding='utf-8') as out:
        for r in records:
            out.write(json.dumps(r, ensure_ascii=False) + '\n')


def phase0_class203(sales, buildings):
    """Replay the original screen/dedupe/join without changing its policy."""
    prior = building_rows_by_key(buildings)
    seen = set()
    eligible = []
    for sale in sales:
        if sale_reject_reasons(sale):
            continue
        key = (normalize_pin(sale['pin']), str(sale['doc_no']), str(sale['sale_date'])[:10])
        if key in seen:
            continue
        seen.add(key)
        joined, error = join_sale_to_prior_building(sale, prior)
        if not error and joined['class'] == '203':
            joined['characteristics_year'] = int(joined['sale_date'][:4]) - 1
            eligible.append(joined)
    return eligible


def fetch_for_keys(dataset_id, keys, wanted, required, *, batch_size=35):
    """Fetch only PIN-year pairs. Fail on unavailable required columns or page cap."""
    fields, updated_at, _ = metadata(dataset_id)
    missing = required - fields
    if missing:
        raise RuntimeError(f'{dataset_id} missing required fields: {sorted(missing)}')
    chosen = sorted(wanted & fields)
    by_year = defaultdict(set)
    for pin, year in keys:
        if not pin or not (1999 <= year <= 2100):
            raise ValueError(f'Invalid PIN-year key: {pin!r} {year!r}')
        by_year[year].add(pin)
    collected = []
    for year, pins in sorted(by_year.items()):
        pins = sorted(pins)
        for n in range(0, len(pins), batch_size):
            selection = pins[n:n + batch_size]
            # PINs are normalised digits only, so quoting cannot inject SoQL.
            assert all(p.isdigit() and len(p) == 14 for p in selection)
            quoted = ','.join("'" + pin + "'" for pin in selection)
            where = f"year = {year} AND pin IN ({quoted})"
            # Small bounded batches. A full batch with >2000 rows is rejected,
            # rather than silently losing records and overstating coverage.
            params = {'$select': ','.join(chosen), '$where': where, '$limit': 2000,
                      '$order': 'pin ASC, year ASC' + (', card ASC' if 'card' in chosen else '')}
            url = f'{BASE}/resource/{dataset_id}.json?{urlencode(params)}'
            rows = fetch_json(url)
            if not isinstance(rows, list):
                raise RuntimeError(f'{dataset_id}: unexpected response type')
            if len(rows) >= 2000:
                raise RuntimeError(f'{dataset_id}: query batch hit row limit; reduce batch size')
            collected.extend(rows)
            print(f'{dataset_id}: {len(collected)} rows, year {year}, PIN batch {n//batch_size+1}', flush=True)
    return collected, {'dataset_id': dataset_id, 'columns_available': sorted(fields),
                       'columns_selected': chosen, 'rows_updated_at_unix': updated_at,
                       'requested_pin_year_keys': len(set(keys)),
                       'downloaded_rows': len(collected)}


def group_by_key(rows):
    out = defaultdict(list)
    for r in rows:
        pin = normalize_pin(r.get('pin'))
        try:
            year_dec = Decimal(str(r.get('year')))
            if not year_dec.is_finite() or year_dec != year_dec.to_integral_value():
                continue
            year = int(year_dec)
        except (InvalidOperation, ValueError, TypeError):
            continue
        if pin:
            out[(pin, year)].append(r)
    return out


def finite_number(value):
    if value is None or value == '':
        return None
    try:
        x = Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        return None
    return float(x) if x.is_finite() else None


def geo_point(record):
    lat, lon = finite_number(record.get('lat')), finite_number(record.get('lon'))
    if lat is None or lon is None or not (40 <= lat <= 43 and -89 <= lon <= -86):
        return None, None
    return lat, lon


def enrich_joined(joined, universe, details):
    geo_by_key, details_by_key = group_by_key(universe), group_by_key(details)
    quality = Counter()
    enhanced = []
    for s in joined:
        key = (s['pin'], s['characteristics_year'])
        locs = geo_by_key.get(key, [])
        chars = details_by_key.get(key, [])
        if len(locs) != 1:
            quality['universe_missing' if not locs else 'universe_ambiguous'] += 1
        if len(chars) != 1:
            quality['detail_missing' if not chars else 'detail_ambiguous'] += 1
        loc = locs[0] if len(locs) == 1 else {}
        det = chars[0] if len(chars) == 1 else {}
        lat, lon = geo_point(loc)
        n = str(loc.get('nbhd_code') or '').strip() or None
        if not n:
            quality['neighborhood_missing'] += 1
        if lat is None:
            quality['coordinates_missing_or_invalid'] += 1
        if det:
            det_class = str(det.get('class') or '').strip()
            if det_class and det_class != '203':
                quality['detail_class_mismatch'] += 1
                det = {}  # Do not attach characteristics from a conflicting class.
        entry = dict(s)
        entry.update({'nbhd_code': n, 'lat': lat, 'lon': lon,
                      'bedrooms': finite_number(det.get('char_beds')),
                      'full_baths': finite_number(det.get('char_fbath')),
                      'half_baths': finite_number(det.get('char_hbath')),
                      'rooms': finite_number(det.get('char_rooms')),
                      'year_built': finite_number(det.get('char_yrblt')),
                      'land_sqft': finite_number(det.get('char_land_sf'))})
        enhanced.append(entry)
    return enhanced, dict(quality)


def distance_km(a, b):
    if None in (a.get('lat'), a.get('lon'), b.get('lat'), b.get('lon')):
        return None
    x1, y1, x2, y2 = (radians(v) for v in (a['lat'], a['lon'], b['lat'], b['lon']))
    dlat, dlon = x2-x1, y2-y1
    z = sin(dlat / 2)**2 + cos(x1)*cos(x2)*sin(dlon / 2)**2
    return 6371.0088 * 2 * asin(min(1.0, sqrt(z)))


def prior_comparables(subject, population, *, same_neighborhood=False, days=365, size_tolerance=.25):
    """No price in the ranking. Never use same/future-day sales."""
    when = date.fromisoformat(subject['sale_date'])
    low = when - timedelta(days=days)
    matches = []
    for other in population:
        if other['pin'] == subject['pin'] or other['doc_no'] == subject['doc_no']:
            continue
        if other['class'] != subject['class'] or other['township_code'] != subject['township_code']:
            continue
        if not (low <= date.fromisoformat(other['sale_date']) < when):
            continue
        if abs(other['sqft'] / subject['sqft'] - 1) > size_tolerance:
            continue
        if same_neighborhood and (not subject['nbhd_code'] or
                                   not other['nbhd_code'] or subject['nbhd_code'] != other['nbhd_code']):
            continue
        matches.append(other)
    matches.sort(key=lambda o: (abs(o['sqft'] / subject['sqft'] - 1),
                                (when - date.fromisoformat(o['sale_date'])).days,
                                o['pin'], o['doc_no']))
    return matches


def baseline_price(matched, *, min_comps=3, max_comps=5):
    return statistics.median(x['sale_price'] for x in matched[:max_comps]) if len(matched) >= min_comps else None


def evaluation(rows):
    """Descriptive 2024 historical check; NOT a leakage-safe model validation."""
    subjects = [x for x in rows if x['sale_date'].startswith('2024-')]
    by_neighborhood = Counter(r['nbhd_code'] or 'MISSING' for r in rows)
    results = []
    for subject in subjects:
        township = prior_comparables(subject, rows)
        local = prior_comparables(subject, rows, same_neighborhood=True)
        base_pred, local_pred = baseline_price(township), baseline_price(local)
        results.append({'subject_date': subject['sale_date'], 'subject_price': subject['sale_price'],
                        'township_count': len(township), 'neighborhood_count': len(local),
                        'township_pred': base_pred, 'neighborhood_pred': local_pred,
                        'has_neighborhood': subject['nbhd_code'] is not None})
    both = [x for x in results if x['township_pred'] is not None and x['neighborhood_pred'] is not None]
    township_supported = [x for x in results if x['township_pred'] is not None]
    neighborhood_supported = [x for x in results if x['neighborhood_pred'] is not None]

    def metrics(cases, name):
        if not cases:
            return {'count': 0, 'mae_usd': None, 'median_absolute_percentage_error': None}
        errors = [abs(x[name] - x['subject_price']) for x in cases]
        fractions = [err / x['subject_price'] for err, x in zip(errors, cases) if x['subject_price'] > 0]
        return {'count': len(cases), 'mae_usd': round(statistics.mean(errors), 2),
                'median_absolute_percentage_error': round(statistics.median(fractions), 4) if fractions else None}

    return {'class': '203', 'observed_market': 'Cook County township 17, historic 2022-2024',
            'total_class203_sales': len(rows), '2024_subjects': len(subjects),
            'subjects_with_neighborhood': sum(x['has_neighborhood'] for x in results),
            'township_supported_2024': len(township_supported),
            'neighborhood_supported_2024': len(neighborhood_supported),
            'paired_supported_2024': len(both),
            'township_all_supported': metrics(township_supported, 'township_pred'),
            'neighborhood_all_supported': metrics(neighborhood_supported, 'neighborhood_pred'),
            'township_on_paired': metrics(both, 'township_pred'),
            'neighborhood_on_paired': metrics(both, 'neighborhood_pred'),
            'neighborhood_codes_counts': dict(by_neighborhood),
            'subjects_with_zero_neighborhood_comps': sum(x['neighborhood_count'] == 0 for x in results),
            'limitations': [
                'Source sales may have been reported after their recorded sale date.',
                'Prior-year characteristic/geo snapshots are proxies and may contain later backfills or corrections.',
                'Evaluation uses a selected market and class; results are not generalizable beyond this slice.',
                'The 2024 recorded sale price is only used for evaluation, not comparable selection or ranking.',
                'A five-sale median is an experimental baseline; no valuation model is validated.',
                'Class 203 denotes one-story residential properties of 1,000-1,800 sq ft under the official code.',
                'The matching rules do not control for property condition, renovations, seller circumstances, or market microstructure.',
            ]}


def markdown(summary):
    ev = summary['evaluation']
    def metric(m):
        return f"{m['count']} subjects, MAE {m['mae_usd']} USD, MdAPE {m['median_absolute_percentage_error']}" 
    return f"""# Phase 1: Class 203 targeted property enrichment

**Status:** Experimental, not valuation or current-market validation.  
**Official sources:** parcel sales ({SALES_ID}), residential characteristics ({BUILDINGS_ID}), historical parcel universe ({UNIVERSE_ID}).

## Record and enrichment coverage

- Reused Phase 0 validated Class 203 records: **{summary['eligible_class203_sales']}**
- Unique eligible PIN-year lookup keys: **{summary['pin_year_keys']}**
- Historical Parcel Universe downloaded rows: **{summary['sources']['universe']['downloaded_rows']}**
- Additional building-characteristic downloaded rows: **{summary['sources']['details']['downloaded_rows']}**
- Missing/ambiguous location and detail counts: `{json.dumps(summary['enrichment_issues'])}`

## Experimental 2024 evaluation

- Class 203 recorded sales: {ev['total_class203_sales']}
- 2024 subjects evaluated: {ev['2024_subjects']}
- 2024 subjects with a neighborhood: {ev['subjects_with_neighborhood']}
- Supported by >=3 township comparables: {ev['township_supported_2024']}
- Supported by >=3 *same-neighborhood* comparables: {ev['neighborhood_supported_2024']}
- Supported by both (fair paired comparison): {ev['paired_supported_2024']}
- Township baseline on paired: {metric(ev['township_on_paired'])}
- Neighborhood baseline on paired: {metric(ev['neighborhood_on_paired'])}

These are historical descriptive baselines. They do **not** prove a public valuation model is accurate or a matching rule is superior for every property.

## Guardrails

""" + '\n'.join('- ' + x for x in ev['limitations']) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--phase0', type=Path, default=Path('../phase0/output'))
    ap.add_argument('--out', type=Path, default=Path('output'))
    args = ap.parse_args()
    p0, out = args.phase0, args.out
    if not (p0 / 'audit_summary_v2.json').is_file():
        ap.error(f"Phase 0 v2 summary missing: {p0 / 'audit_summary_v2.json'}")
    original_summary = json.loads((p0 / 'audit_summary_v2.json').read_text(encoding='utf-8'))
    if original_summary.get('audit_code_version') != 'phase0-v2':
        ap.error('Expected a Phase 0 v2 summary; do not use the uncorrected audit')
    if any(original_summary.get('extraction_capped', {}).values()):
        ap.error('Phase 0 source extraction hit a row cap; rerun with complete data')
    sales = load_jsonl(p0 / 'sales_selected_fields.jsonl')
    buildings = load_jsonl(p0 / 'buildings_selected_fields.jsonl')
    if (len(sales), len(buildings)) != (original_summary['source_sale_rows'], original_summary['source_building_rows']):
        ap.error('Raw extract counts do not match the Phase 0 summary')
    joined = phase0_class203(sales, buildings)
    if not joined:
        ap.error('No accepted Class 203 records. Stop rather than fabricate coverage')
    keys = {(r['pin'], r['characteristics_year']) for r in joined}
    out.mkdir(parents=True, exist_ok=True)
    locations, source_u = fetch_for_keys(UNIVERSE_ID, keys, UNIVERSE_WANTED, REQUIRED_UNIVERSE)
    details, source_d = fetch_for_keys(BUILDINGS_ID, keys, DETAIL_WANTED, REQUIRED_DETAIL)
    save_jsonl(out / 'historical_parcel_universe_subset.jsonl', locations)
    save_jsonl(out / 'historical_building_details_subset.jsonl', details)
    enriched, issues = enrich_joined(joined, locations, details)
    save_jsonl(out / 'class203_enriched_sales.jsonl', enriched)
    summary = {'audited_source': 'Phase 0 v2 Cook County township 17, 2022-2024',
               'eligible_class203_sales': len(joined), 'pin_year_keys': len(keys),
               'sources': {'universe': source_u, 'details': source_d},
               'enrichment_issues': issues, 'evaluation': evaluation(enriched)}
    (out / 'phase1_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (out / 'phase1_report.md').write_text(markdown(summary), encoding='utf-8')
    print('Phase 1 complete. Class 203 sales:', len(joined))
    print('2024 baseline support: township', summary['evaluation']['township_supported_2024'],
          '/ neighborhood', summary['evaluation']['neighborhood_supported_2024'])
    print('Wrote:', out / 'phase1_summary.json', out / 'phase1_report.md')


if __name__ == '__main__':
    main()
