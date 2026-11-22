# Phase 1: Enrich historical Class 203 comparable sales

**Status: experimental; no validated price-prediction model.**

## Why this phase exists

Phase 0 identified **1,285** pilot sales with accepted historical building joins in Cook County township **17** (Evanston). **273** of those are Class **203**. Phase 0's 19/20 comparable coverage reflected several classes, not Class 203 alone. This phase measures Class 203 in isolation and checks whether neighbourhood matching improves or reduces historical comparable coverage.

Phase 1 reuses Phase 0's saved `sales_selected_fields.jsonl` and `buildings_selected_fields.jsonl`, downloads historical **Parcel Universe** geography and the selected older residential-characteristic fields for the *eligible Class 203 PIN-year keys only*, then evaluates two transparent historical comparable baselines.

Data sources: [sales](https://datacatalog.cookcountyil.gov/d/wvhk-k5uv), [residential characteristics](https://datacatalog.cookcountyil.gov/d/x54s-btds), [historical Parcel Universe](https://datacatalog.cookcountyil.gov/d/nj4t-kc8j), and [official Class 203 description](https://www.cookcountyassessoril.gov/classifications-real-property).

Class 203 is a *one-story residence of 1,000 to 1,800 square feet*. It does not certify a property's condition, interior quality, or exact market comparability. The property classes and taxonomy can change over time.

## Run on Windows

From the project root (after `git pull origin main`):

```powershell
cd audit\phase1
python -m unittest discover -s tests -v
python expand.py --phase0 ..\phase0\output --out output
```

The script requires internet access for approximately a handful of small, targeted API batches. It **does not re-download the original 3,539 sales or 39,401 building records**, does not call any paid geocoding provider, and does not overwrite Phase 0 outputs.

It writes:

- `output/phase1_summary.json` and `output/phase1_report.md`: aggregate measurements; these are the only files to share for review.
- `output/class203_enriched_sales.jsonl`: local research data for each joined sale.
- `output/historical_parcel_universe_subset.jsonl` and `output/historical_building_details_subset.jsonl`: local research extracts.

**Do not commit any generated output directory or raw extracted records to GitHub.** The repository's `.gitignore` excludes them.

## Validation and interpretation

- The code checks published API fields before requesting them. Missing required columns halt the extraction; missing optional fields are recorded in metadata.
- Only exact `(PIN, prior tax year)` links are accepted. If a key has multiple rows, the enrichment is withheld rather than guessing.
- Baseline candidates must have an earlier sale date, same class, same township, floor area within 25%, and sales within 365 days. Candidates are **ranked by floor-area similarity, then recency**, without looking at their price.
- The neighbourhood variant additionally requires the same assessor neighbourhood. It does not silently expand its search when coverage is thin.
- Both variants use the **median of up to five eligible historical sales**, and require at least three to produce a descriptive estimate.
- The report shows how many 2024 sales are supported by each, and compares their sale-price errors **on the same paired subjects** to avoid comparing different populations.

These baseline results are **research measurements, not user-facing valuations**. County sales can arrive late; historical geography may be backfilled and building records revised. This cannot establish what was observable on a historical decision date, nor does it prove price prediction accuracy for today's market.

## Next decisions

1. Confirm coverage of neighbourhood, coordinates, bedrooms/baths and year built, and measure class mismatches.
2. Assess whether requiring an assessor neighbourhood destroys comparable coverage.
3. Compare historical paired error without claiming the method is production-ready.
4. Only then consider a spatial distance rule and an app-facing comparable explainability contract.
