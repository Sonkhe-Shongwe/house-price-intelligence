# Phase 2: Explainable comparable-selection engine

**Status:** Experimental rule-based engine; no validated current price predictions.

## Purpose

Phase 1 measured 83 historical Class 203 2024 sales in Evanston, of which 66 had at least three earlier same-neighbourhood comparables. Phase 2 tests a bounded alternative for properties where neighbourhood matching is insufficient.

### Selection contract

1. Only Class 203, same township, valid positive floor area, other property and other document.
2. Only sales *before* the analysis date and within the preceding 365 days; living area within ±25%.
3. A house contributes only its most recent eligible sale. Never count two sales from the same PIN as independent comparable homes.
4. First, require at least three same-assessor-neighbourhood sales. Rank those by floor-area similarity, then recency. Choose at most five.
5. If that fails, test a **2 km geographic radius**, requiring valid coordinates on both the subject and comparable. Rank eligible sales by distance, then size similarity and recency. Choose at most five, requiring at least three.
6. If neither tier qualifies, return `insufficient_data` with a coded reason. **Do not silently broaden to township-wide comparisons.**
7. Return evidence for each chosen comparable: recorded sale date, source transaction ID, floor-area difference, days earlier, distance if available, selected tier and an explanation. **Never use recorded price in matching or ranking.**

2 km is a proposed experimental policy, **not** an empirically validated ideal distance. A location can be nearby yet from a substantially different market segment. The matcher currently assumes the Phase 0/1 records are correctly screened, and its output should not be exposed publicly before provenance, licensing, historical availability and display policy review.

### Evaluation

Run after Phase 1 has produced `class203_enriched_sales.jsonl`:

```bash
cd audit/phase2
python -m unittest discover -s tests -v
python evaluate.py --phase1 ../phase1/output --out output
```

The evaluator tests 2024 historical recorded sales, compares the median of the selected up-to-five comparables against Phase 1 township and strict-neighbourhood baselines, and reports support and error **on paired subjects**. It separately reports the fallback cases and explicit abstentions. It does not leak property identifiers or per-property sales to the published CI artifact.

### Limitations

- These are retrospectively available source records; publication-date leakage and parcel-geography backfills are unresolved.
- The median comparator is an experimental descriptive baseline, not a production valuation model, calibrated interval or appraisal.
- The reference township is only one geography, and the pilot only supports Class 203.
- Property condition, renovations and sale circumstances remain outside the data.
- The rule may improve coverage while making median error worse. The experiment must reveal this rather than optimise results after seeing them.
