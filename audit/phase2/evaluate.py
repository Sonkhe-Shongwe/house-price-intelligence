#!/usr/bin/env python3
"""Historical Class 203 comparison audit of bounded neighbourhood/spatial selection.

Aggregate metrics only in summary/report. Raw enriched data stays in Phase 1 output.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase1"))
from expand import load_jsonl, prior_comparables, baseline_price
from matcher import MatchPolicy, match_property


def error_metrics(cases, pred_key):
    eligible = [(case["price"], case[pred_key]) for case in cases if case.get(pred_key) is not None]
    if not eligible:
        return {"count": 0, "mae_usd": None, "median_absolute_percentage_error": None}
    errors = [abs(actual - predicted) for actual, predicted in eligible]
    pct_errors = [err / actual for (actual, _), err in zip(eligible, errors) if actual > 0]
    return {"count": len(eligible), "mae_usd": round(statistics.mean(errors), 2),
            "median_absolute_percentage_error": round(statistics.median(pct_errors), 4) if pct_errors else None}


def evaluate(rows, *, policy=MatchPolicy()):
    subjects = [row for row in rows if str(row.get("sale_date", "")).startswith("2024-") and row.get("class") == policy.class_code]
    cases = []
    reasons = Counter()
    tiers = Counter()
    for subject in subjects:
        result = match_property(subject, rows, policy=policy)
        tiers[result["tier"]] += 1
        reasons[result["reason"]] += 1
        comps = result["comparables"]
        # Sale prices are consulted only *after* matching is complete.
        selected = statistics.median(comp["sale_price"] for comp in comps) if result["status"] == "supported" else None
        township = baseline_price(prior_comparables(subject, rows))
        neighborhood = baseline_price(prior_comparables(subject, rows, same_neighborhood=True))
        cases.append({"price": subject["sale_price"], "adaptive": selected,
                      "township": township, "neighborhood": neighborhood,
                      "tier": result["tier"]})

    paired_township = [c for c in cases if c["adaptive"] is not None and c["township"] is not None]
    paired_neighborhood = [c for c in cases if c["adaptive"] is not None and c["neighborhood"] is not None]
    fallback = [c for c in cases if c["tier"] == "spatial_fallback"]
    return {
        "scope": "Cook County Evanston township 17, Class 203; sales 2022-2024; subjects 2024",
        "policy": {"history_days": policy.history_days, "size_tolerance": policy.size_tolerance,
                   "radius_km": policy.radius_km, "min_comps": policy.min_comps, "max_comps": policy.max_comps,
                   "neighborhood_first": True, "no_township_only_fallback": True},
        "total_class203_sales": len(rows), "subject_count": len(subjects),
        "tier_counts": dict(sorted(tiers.items())), "reason_counts": dict(sorted(reasons.items())),
        "adaptive_all_supported": error_metrics(cases, "adaptive"),
        "township_all_supported": error_metrics(cases, "township"),
        "neighborhood_all_supported": error_metrics(cases, "neighborhood"),
        "paired_with_township": {"adaptive": error_metrics(paired_township, "adaptive"),
                                 "township": error_metrics(paired_township, "township")},
        "paired_with_neighborhood": {"adaptive": error_metrics(paired_neighborhood, "adaptive"),
                                     "neighborhood": error_metrics(paired_neighborhood, "neighborhood")},
        "spatial_fallback_only": {"adaptive": error_metrics(fallback, "adaptive"),
                                  "township": error_metrics(fallback, "township")},
        "limitations": [
            "Historical sale dates do not establish when the source first published the transactions.",
            "Historical neighbourhood and building data may be backfilled or revised.",
            "The 2 km radius, size tolerance, and comparison counts are exploratory policy choices.",
            "Matched errors describe one historical township and class; no independent final holdout.",
            "No calibrated prediction interval, model validation, or present-day valuation claim.",
            "Missing property condition and renovation information may cause material price differences.",
        ],
    }


def markdown(summary):
    def metrics(name):
        m = summary[name]
        return f"{m['count']} subjects; MAE {m['mae_usd']} USD; MdAPE {m['median_absolute_percentage_error']}"

    tw = summary["paired_with_township"]
    neighborhood = summary["paired_with_neighborhood"]
    fallback = summary["spatial_fallback_only"]
    return f"""# Phase 2: Explainable neighbourhood-first selection

**Status:** Research evaluation only, not validated property valuations.  
**Scope:** {summary['scope']}.

## Counts and support
- 2024 subjects: **{summary['subject_count']}**
- Selection tiers: `{json.dumps(summary['tier_counts'], sort_keys=True)}`
- Reasons: `{json.dumps(summary['reason_counts'], sort_keys=True)}`
- Adaptive policy supported: {metrics('adaptive_all_supported')}
- Township baseline supported: {metrics('township_all_supported')}
- Neighbourhood baseline supported: {metrics('neighborhood_all_supported')}

## Paired error comparisons (same subjects)
- Adaptive vs township: {tw['adaptive']['count']} supported; adaptive MAE {tw['adaptive']['mae_usd']} USD; township MAE {tw['township']['mae_usd']} USD
- Adaptive vs neighbourhood: {neighborhood['adaptive']['count']} supported; adaptive MAE {neighborhood['adaptive']['mae_usd']} USD; neighbourhood MAE {neighborhood['neighborhood']['mae_usd']} USD
- Spatial-fallback cases only: {fallback['adaptive']['count']} supported; adaptive MAE {fallback['adaptive']['mae_usd']} USD; township MAE {fallback['township']['mae_usd']} USD

## Limitations
""" + "\n".join("- " + line for line in summary["limitations"]) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase1", type=Path, default=Path("../phase1/output"))
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()
    source = args.phase1 / "class203_enriched_sales.jsonl"
    if not source.is_file():
        parser.error(f"Missing Phase 1 enriched sales: {source}")
    summary = evaluate(load_jsonl(source))
    if not summary["subject_count"]:
        parser.error("No eligible historical subjects; cannot evaluate")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "phase2_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (args.out / "phase2_report.md").write_text(markdown(summary), encoding="utf-8")
    print(f"Phase 2: {summary['subject_count']} 2024 historical subjects; tiers {summary['tier_counts']}")
    print("Phase 2 summary and report saved in", args.out)


if __name__ == "__main__":
    main()
