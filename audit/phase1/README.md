# Phase 1: Enrich historical Class 203 comparable sales

**Status (22 November 2026):** Phase 1 extraction and evaluation **completed** in [verified cloud run 45045580458](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45045580458), followed by [Phase 2 comparable evaluation](../../docs/research/PHASE2_CLOUD_AUDIT_RESULTS.md). The historical research is experimental; **no current price-prediction model is validated**.

## Why this phase exists

Phase 0 identified **1,285** pilot sales with accepted historical building joins in Cook County township **17** (Evanston). **273** of those are Class **203**. Phase 0's 19/20 comparable coverage reflected several classes, not Class 203 alone. This phase measures Class 203 in isolation and checks whether neighbourhood matching improves or reduces historical comparable coverage.

Phase 1 reuses Phase 0's saved `sales_selected_fields.jsonl` and `buildings_selected_fields.jsonl`, downloads historical **Parcel Universe** geography and the selected older residential-characteristic fields for the *eligible Class 203 PIN-year keys only*, then evaluates two transparent historical comparable baselines.

Data sources: [sales](https://datacatalog.cookcountyil.gov/d/wvhk-k5uv), [residential characteristics](https://datacatalog.cookcountyil.gov/d/x54s-btds), [historical Parcel Universe](https://datacatalog.cookcountyil.gov/d/nj4t-kc8j), and [official Class 203 description](https://www.cookcountyassessoril.gov/classifications-real-property).

Class 203 is a *one-story residence of 1,000 to 1,800 square feet*. It does not certify a property's condition, interior quality, or exact market comparability. The property classes and taxonomy can change over time.

## Optional local execution

Routine audits already run in [GitHub Actions](../../docs/AUTOMATED_DATA_AUDIT.md); no local execution or ZIP uploads are necessary. For debugging from the project root (after `git pull origin main`):

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

## Subsequent progress and open quality gates

- **Completed:** The 273 Class 203 joined sales yielded 262 matching historical parcel-universe keys; 66 of 83 retrospective 2024 subjects had at least three same-neighbourhood comparables. See [Phase 1 results](../../docs/research/PHASE1_CLOUD_AUDIT_RESULTS.md).
- **Completed:** Phase 2 tested a 2 km fallback on the remaining 17 subjects and found worse price errors than the township baseline on those 17. See [Phase 2 results](../../docs/research/PHASE2_CLOUD_AUDIT_RESULTS.md).
- **Still pending:** Repeatable historical data provenance, source-rights review, meaningful real-world buyer input mapping, independent holdout evaluation and an application evidence response contract. The current deliverable priority is delivery **P3**; see [checkpoint](../../docs/CHECKPOINT.md).
