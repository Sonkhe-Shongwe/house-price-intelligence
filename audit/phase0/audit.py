#!/usr/bin/env python3
"""Cook County property-sales and building-characteristics feasibility audit.

No training, inference, application deployment, or claims of validated valuations.
Only named, non-personal source fields are downloaded.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://datacatalog.cookcountyil.gov"
SALES_ID = "wvhk-k5uv"
BUILDINGS_ID = "x54s-btds"
SALES_REQUIRED = {"pin", "sale_date", "sale_price", "doc_no", "township_code",
                  "is_multisale", "num_parcels_sale", "sale_filter_less_than_10k",
                  "sale_filter_deed_type", "sale_filter_same_sale_within_365"}
SALES_OPTIONAL = {"class"}
BUILDINGS_REQUIRED = {"pin", "year", "card", "class", "township_code", "char_bldg_sf"}
BUILDINGS_OPTIONAL = {"pin_num_cards", "pin_is_multicard", "char_yrblt"}


def fetch_json(url: str, retries: int = 4):
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "HousePriceIntelligence-Feasibility/0.1", "Accept": "application/json"})
            with urlopen(req, timeout=35) as response:
                return json.load(response)
        except Exception as e:
            if attempt == retries - 1:
                raise RuntimeError(f"Failed to access {url.split('?')[0]} after {retries} tries: {e}") from e
            time.sleep(2 ** attempt)


def metadata(dataset_id):
    data = fetch_json(f"{BASE}/api/views/{dataset_id}.json")
    fields = {c.get("fieldName") for c in data.get("columns", []) if c.get("fieldName")}
    if not fields:
        raise ValueError(f"No API columns returned for {dataset_id}")
    return fields, data.get("rowsUpdatedAt"), data.get("name")


def collect(dataset_id, select_fields, where_clause, max_rows, output_file):
    all_records = []
    offset, page_size = 0, 2000
    while offset < max_rows:
        params = {"$select": ",".join(select_fields), "$where": where_clause,
                  "$limit": min(page_size, max_rows - offset), "$offset": offset,
                  "$order": "pin ASC" + (",sale_date ASC" if dataset_id == SALES_ID else ",year ASC,card ASC")}
        url = f"{BASE}/resource/{dataset_id}.json?{urlencode(params)}"
        page = fetch_json(url)
        if not isinstance(page, list):
            raise ValueError("Unexpected Socrata response format; expected a JSON array")
        all_records.extend(page)
        print(f"{dataset_id}: received {len(all_records)} rows", flush=True)
        if len(page) < params["$limit"]:
            break
        offset += len(page)
        time.sleep(0.07)
    # The cap may have truncated the data. Report this; never label a truncated download complete.
    capped = len(all_records) >= max_rows
    with output_file.open("w", encoding="utf-8") as f:
        for item in all_records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return all_records, capped


def normalize_pin(value):
    s = str(value or "").strip().replace("-", "")
    return s.zfill(14) if s.isdigit() and 0 < len(s) <= 14 else None


def bool_value(value):
    if value is True or str(value).lower() == "true":
        return True
    if value is False or str(value).lower() == "false":
        return False
    return None


def whole_count(value):
    """Parse Socrata numeric counts without truncation.

    Socrata Number fields may arrive as strings like "1.0". A non-integral,
    non-finite, empty, or boolean value is not a valid number of items.
    """
    if value is None or isinstance(value, bool) or str(value).strip() == "":
        return None
    try:
        n = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not n.is_finite() or n != n.to_integral_value() or n < 0:
        return None
    return int(n)


def positive_price(value):
    try:
        x = Decimal(str(value))
        return x if x.is_finite() and 20_000 <= x <= 5_000_000 else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def sale_reject_reasons(sale):
    """A conservative ANALYST screen, not proof a sale was arm's length."""
    failures = []
    if not normalize_pin(sale.get("pin")):
        failures.append("invalid_pin")
    if not positive_price(sale.get("sale_price")):
        failures.append("price_outside_pilot_bounds")
    try:
        date.fromisoformat(str(sale["sale_date"])[:10])
    except (KeyError, ValueError, TypeError):
        failures.append("invalid_sale_date")
    if not sale.get("doc_no"):
        failures.append("missing_document_number")
    for f in ("sale_filter_less_than_10k", "sale_filter_deed_type", "sale_filter_same_sale_within_365"):
        flag = bool_value(sale.get(f))
        if flag is None:
            failures.append(f"missing_or_invalid_{f}")
        elif flag is True:
            failures.append(f"flagged_{f}")
    multi = bool_value(sale.get("is_multisale"))
    if multi is None:
        failures.append("missing_or_invalid_is_multisale")
    elif multi:
        failures.append("multi_parcel_sale")
    parcels = whole_count(sale.get("num_parcels_sale"))
    if parcels is None:
        failures.append("missing_num_parcels_sale")
    elif parcels != 1:
        failures.append("not_one_parcel_sale")
    return failures


def building_rows_by_key(buildings):
    lookup = defaultdict(list)
    for item in buildings:
        pin = normalize_pin(item.get("pin"))
        try:
            year = int(item["year"])
        except (KeyError, TypeError, ValueError):
            continue
        if pin:
            lookup[(pin, year)].append(item)
    return lookup


def join_sale_to_prior_building(sale, building_lookup):
    """Pilot policy: use tax-year prior to sale; not a verified publication-time snapshot."""
    pin = normalize_pin(sale.get("pin"))
    year = date.fromisoformat(str(sale["sale_date"])[:10]).year - 1
    building_rows = building_lookup.get((pin, year), [])
    if len(building_rows) != 1:
        return None, "no_prior_building" if not building_rows else "multiple_prior_buildings"
    b = building_rows[0]
    if bool_value(b.get("pin_is_multicard")) is True:
        return None, "multicard_flag"
    cards = b.get("pin_num_cards")
    if cards not in (None, ""):
        count = whole_count(cards)
        if count is None:
            return None, "invalid_card_count"
        if count != 1:
            return None, "multi_card_count"
    try:
        area = float(b["char_bldg_sf"])
        if not (250 <= area <= 20_000):
            return None, "implausible_building_area"
    except (ValueError, TypeError, KeyError):
        return None, "missing_building_area"
    cls = str(b.get("class") or "").strip()
    if not cls:
        return None, "missing_building_class"
    return {"pin": pin, "sale_date": str(sale["sale_date"])[:10],
            "sale_price": float(sale["sale_price"]), "doc_no": str(sale["doc_no"]),
            "class": cls, "sqft": area, "township_code": str(sale.get("township_code", ""))}, None


def eligible_comparables(subject, candidates, days=365, size_tolerance=.25):
    when = date.fromisoformat(subject["sale_date"])
    low = when - timedelta(days=days)
    return [c for c in candidates
            if c["pin"] != subject["pin"] and c["doc_no"] != subject["doc_no"]
            and c["class"] == subject["class"]
            and c["township_code"] == subject["township_code"]
            and low <= date.fromisoformat(c["sale_date"]) < when
            and abs(c["sqft"] / subject["sqft"] - 1) <= size_tolerance]


def run_analysis(sales, buildings, *, township, start, end):
    rejections = Counter()
    accepted = []
    seen_identical = set()
    for s in sales:
        failures = sale_reject_reasons(s)
        if failures:
            rejections.update(failures)
            continue
        ident = (normalize_pin(s["pin"]), str(s["doc_no"]), str(s["sale_date"])[:10])
        if ident in seen_identical:
            rejections["duplicate_sale_identity"] += 1
            continue
        seen_identical.add(ident)
        accepted.append(s)
    lookup = building_rows_by_key(buildings)
    joined, join_rejections = [], Counter()
    screened_by_year = Counter(str(s["sale_date"])[:4] for s in accepted)
    source_sales_by_year = Counter(str(s.get("sale_date", ""))[:4] for s in sales)
    joined_by_year = Counter()
    join_rejections_by_year = defaultdict(Counter)
    one_record_card_values = Counter()
    building_years_by_pin = defaultdict(set)
    for (bpin, byear) in lookup:
        building_years_by_pin[bpin].add(byear)
    absent_prior_breakdown = Counter()
    for s in accepted:
        year = str(s["sale_date"])[:4]
        prior_key = (normalize_pin(s.get("pin")), int(year) - 1)
        hits = lookup.get(prior_key, [])
        if len(hits) == 1:
            # Only distributions, not IDs, are kept in aggregate audit results.
            value = hits[0].get("pin_num_cards")
            one_record_card_values[str(value)] += 1
        record, error = join_sale_to_prior_building(s, lookup)
        if error:
            join_rejections[error] += 1
            join_rejections_by_year[year][error] += 1
            if error == "no_prior_building":
                if building_years_by_pin.get(normalize_pin(s.get("pin"))):
                    absent_prior_breakdown["pin_seen_in_other_selected_year"] += 1
                else:
                    absent_prior_breakdown["pin_not_seen_in_selected_building_records"] += 1
        else:
            joined.append(record)
            joined_by_year[year] += 1
    # Existing class codes must be checked with the official code dictionary before calling this 'detached houses'.
    subject_pool = sorted([x for x in joined if x["sale_date"].startswith("2024-")],
                          key=lambda x: (x["sale_date"], x["pin"]))
    if len(subject_pool) > 20:
        indexes = [round(i * (len(subject_pool) - 1) / 19) for i in range(20)]
        subject_pool = [subject_pool[i] for i in indexes]
    examples = []
    for s in subject_pool:
        comps = sorted(eligible_comparables(s, joined), key=lambda x: x["sale_date"], reverse=True)
        examples.append({"subject_pin": s["pin"], "subject_date": s["sale_date"],
                         "class": s["class"], "subject_sqft": s["sqft"],
                         "comparable_count": len(comps),
                         "first_three": [{"pin": x["pin"], "date": x["sale_date"],
                                          "price": x["sale_price"], "sqft": x["sqft"],
                                          "document": x["doc_no"]} for x in comps[:3]]})
    return {
        "audited_township_code": township, "sale_start_inclusive": start, "sale_end_exclusive": end,
        "source_sale_rows": len(sales), "source_building_rows": len(buildings),
        "sales_after_screen": len(accepted), "joined_sale_candidates": len(joined),
        "source_sales_by_year": dict(sorted(source_sales_by_year.items())),
        "screened_sales_by_year": dict(sorted(screened_by_year.items())),
        "joined_sales_by_year": dict(sorted(joined_by_year.items())),
        "join_rejections_by_year": {year: dict(sorted(counts.items())) for year, counts in sorted(join_rejections_by_year.items())},
        "single_prior_record_card_value_counts": dict(one_record_card_values.most_common(15)),
        "no_prior_building_diagnostics": dict(sorted(absent_prior_breakdown.items())),
        "sale_reasons_not_mutually_exclusive": dict(rejections),
        "join_rejection_counts": dict(join_rejections),
        "class_counts_in_joined_candidates": dict(Counter(x["class"] for x in joined).most_common()),
        "2024_subjects_tested": len(examples),
        "2024_subjects_with_3_or_more_comps": sum(x["comparable_count"] >= 3 for x in examples),
        "example_properties": examples,
        "limitations": [
            "Prior tax-year characteristics are a proxy, not proof of their publication date at sale time.",
            "Source data may contain late-reported transactions even for old sale dates.",
            "Sale filtering does not establish independent arm's-length verification.",
            "Exact class code selection for detached single-family properties is not yet verified.",
            "Pilot bounds $20k-$5m and 25% size matching are analytic assumptions, not official thresholds.",
            "No automated valuation model is trained or evaluated by this audit.",
        ],
    }


def report_markdown(summary, *, capped_sales, capped_buildings, sales_meta, buildings_meta):
    def sect_dict(d):
        return "\n".join(f"- {k}: {v}" for k,v in sorted(d.items())) or "- None reported"
    incomplete = capped_sales or capped_buildings
    return f"""# House Price Intelligence: Cook County Pilot Audit

**Status:** {'INCOMPLETE: extraction hit a row cap' if incomplete else 'Extracted selected source records; further validation required'}

**Township:** {summary['audited_township_code']}  
**Sales period:** {summary['sale_start_inclusive']} to (excluding) {summary['sale_end_exclusive']}  
**Sales source:** {BASE}/d/{SALES_ID}  
**Buildings source:** {BASE}/d/{BUILDINGS_ID}  
**Data set update timestamps (Unix seconds when supplied):** sales {sales_meta}, characteristics {buildings_meta}

## Results

| Measure | Result |
|---|---:|
| Downloaded sale rows | {summary['source_sale_rows']} |
| Downloaded historical building rows | {summary['source_building_rows']} |
| Sale rows passing pilot screening | {summary['sales_after_screen']} |
| Sales with exactly one acceptable prior-year building | {summary['joined_sale_candidates']} |
| Historical subject sales tested (2024) | {summary['2024_subjects_tested']} |
| Subjects with 3 or more eligible prior sales | {summary['2024_subjects_with_3_or_more_comps']} |

## Rejection reasons (not mutually exclusive)

### Sale screening
{sect_dict(summary['sale_reasons_not_mutually_exclusive'])}

### Join screening
{sect_dict(summary['join_rejection_counts'])}

## Property class distribution (not yet validated as single-family)
{sect_dict(summary['class_counts_in_joined_candidates'])}

## Breakdown by sale year
### Screened sales
{sect_dict(summary.get('screened_sales_by_year', {}))}
### Joined sales
{sect_dict(summary.get('joined_sales_by_year', {}))}

## Card counts from exactly-one-row prior-year matches
{sect_dict(summary.get('single_prior_record_card_value_counts', {}))}

## Unmatched prior-year records (exploratory only)
{sect_dict(summary.get('no_prior_building_diagnostics', {}))}

## Limitations and decision guards
""" + "\n".join("- " + s for s in summary["limitations"]) + "\n\n**Not a commercial-quality, legal-rights, valuation or historical backtest certification.**\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--township", default="17", help="Cook County township code (pilot: 17)")
    parser.add_argument("--start", default="2022-01-01")
    parser.add_argument("--end", default="2025-01-01", help="Exclusive end date")
    parser.add_argument("--max-rows", default=200_000, type=int, help="Extraction cap per dataset")
    parser.add_argument("--out", default="output")
    args = parser.parse_args()
    if not (args.township.isdigit() and len(args.township) <= 3):
        parser.error("township must be a 1-3 digit code")
    start_date, end_date = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if end_date <= start_date:
        parser.error("End date must be after start date")
    if args.max_rows < 100:
        parser.error("max-rows must be >= 100")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sales_fields, sales_stamp, _ = metadata(SALES_ID)
    building_fields, building_stamp, _ = metadata(BUILDINGS_ID)
    for name, found, required in (("sales", sales_fields, SALES_REQUIRED),
                                  ("buildings", building_fields, BUILDINGS_REQUIRED)):
        missing = required - found
        if missing:
            raise RuntimeError(f"STOP: {name} dataset is missing required API fields: {sorted(missing)}. "
                               "Do not silently guess aliases. Check the data dictionary and update the audit instrument.")
    with (out / "field_inventory.json").open("w", encoding="utf-8") as f:
        json.dump({"sales": sorted(sales_fields), "buildings": sorted(building_fields)}, f, indent=2)
    township = args.township
    where_sales = (f"township_code = '{township}' AND sale_date >= '{start_date.isoformat()}T00:00:00' "
                   f"AND sale_date < '{end_date.isoformat()}T00:00:00'")
    where_buildings = (f"township_code = '{township}' AND year >= {start_date.year - 1} "
                       f"AND year <= {end_date.year - 2}")
    sales, capped_sales = collect(SALES_ID, sorted(SALES_REQUIRED | (SALES_OPTIONAL & sales_fields)),
                                  where_sales, args.max_rows, out / "sales_selected_fields.jsonl")
    buildings, capped_buildings = collect(BUILDINGS_ID, sorted(BUILDINGS_REQUIRED | (BUILDINGS_OPTIONAL & building_fields)),
                                          where_buildings, args.max_rows, out / "buildings_selected_fields.jsonl")
    summary = run_analysis(sales, buildings, township=township, start=args.start, end=args.end)
    summary["extraction_capped"] = {"sales": capped_sales, "buildings": capped_buildings}
    with (out / "audit_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    (out / "audit_report.md").write_text(report_markdown(summary, capped_sales=capped_sales,
                                                          capped_buildings=capped_buildings,
                                                          sales_meta=sales_stamp, buildings_meta=building_stamp),
                                            encoding="utf-8")
    print(f"Audit saved in {out}. Check audit_report.md and audit_summary.json.")
    if capped_sales or capped_buildings:
        print("WARNING: extraction capped, counts are incomplete. Increase --max-rows and rerun.")


if __name__ == "__main__":
    main()
