#!/usr/bin/env python3
"""Re-run a Phase 0 audit against previously downloaded JSONL records.

No network requests. Does not overwrite original audit results or raw extracts.
Use only with the source records retrieved by audit.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from audit import run_analysis, report_markdown


def read_json_lines(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"Required local extract is missing: {path}")
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="output", help="Folder containing the first audit's saved extracts")
    args = parser.parse_args()
    out = Path(args.out)
    prior_path = out / "audit_summary.json"
    if not prior_path.is_file():
        parser.error(f"Missing original audit summary: {prior_path}")
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    sales = read_json_lines(out / "sales_selected_fields.jsonl")
    buildings = read_json_lines(out / "buildings_selected_fields.jsonl")
    if len(sales) != prior.get("source_sale_rows") or len(buildings) != prior.get("source_building_rows"):
        parser.error("Local extract row counts do not match original summary; STOP and inspect files.")
    if prior.get("extraction_capped", {}).get("sales") or prior.get("extraction_capped", {}).get("buildings"):
        print("WARNING: Original extract was capped; counts and coverage may be incomplete.")

    summary = run_analysis(sales, buildings,
                           township=prior["audited_township_code"],
                           start=prior["sale_start_inclusive"],
                           end=prior["sale_end_exclusive"])
    summary["extraction_capped"] = prior.get("extraction_capped", {})
    summary["audit_code_version"] = "phase0-v2"
    summary["source_reuse_note"] = "Analyzed locally saved source extracts without additional API requests"

    sales_stamp, buildings_stamp = "original extract", "original extract"
    original_report = out / "audit_report.md"
    if original_report.is_file():
        match = re.search(r"Data set update timestamps.*?sales (\d+), characteristics (\d+)",
                          original_report.read_text(encoding="utf-8"))
        if match:
            sales_stamp, buildings_stamp = match.groups()
    (out / "audit_summary_v2.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    content = report_markdown(summary,
                              capped_sales=bool(summary["extraction_capped"].get("sales")),
                              capped_buildings=bool(summary["extraction_capped"].get("buildings")),
                              sales_meta=sales_stamp,
                              buildings_meta=buildings_stamp)
    (out / "audit_report_v2.md").write_text(
        "**Phase 0 v2: reanalyzed from existing local extracts; the original audit files are preserved.**\n\n" + content,
        encoding="utf-8")
    print("Reanalysis complete (no network requests).")
    print("Sales passed screening:", summary["sales_after_screen"])
    print("Accepted prior-year joins:", summary["joined_sale_candidates"])
    print("2024 subjects tested:", summary["2024_subjects_tested"])
    print("2024 subjects with >=3 prior comparables:", summary["2024_subjects_with_3_or_more_comps"])
    print("Join rejections:", summary["join_rejection_counts"])
    print("Card-count values:", summary["single_prior_record_card_value_counts"])
    print("Wrote:", out / "audit_summary_v2.json", "and", out / "audit_report_v2.md")


if __name__ == "__main__":
    main()
