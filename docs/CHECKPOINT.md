# House Price Intelligence: current development checkpoint

**Last updated: 22 November 2026**

House Price Intelligence has its own GitHub repository. The South African graduate-programme research repository remains a separate, unchanged source of career-research documentation.

## Completed

- Phase 0 live Cook County extraction and corrected analysis: 3,539 sales, 39,401 building rows, 2,583 sales screened, 1,285 prior-year joins, including 273 Class 203 sales.
- Identified and fixed an integral-decimal card-count parsing defect with regression tests.
- Phase 1 targeted historical parcel universe and characteristics enrichment for 262 distinct Class 203 PIN-year keys.
- Phase 1 descriptive baseline analysis on 83 historical 2024 subjects; 66 have >=3 same-neighbourhood comparables.
- **GitHub Actions cloud automation verified:** tests, Phase 0, Phase 1, summary reports and artifact upload succeeded on [run 45045580458](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45045580458).
- The cloud workflow saves only aggregate reports; no raw source extracts are published as artifacts. No manual PowerShell steps are required for routine audits.

See [Phase 0 findings](research/PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1 cloud findings](research/PHASE1_CLOUD_AUDIT_RESULTS.md), and [cloud audit operating instructions](AUTOMATED_DATA_AUDIT.md).

## Remaining problems

- Historical publication-time correctness is not guaranteed by prior-year data; recorded sales and neighbourhood data may arrive or be backfilled later.
- Neighbourhood matching improves paired descriptive error but sacrifices 17 of 83 subjects' three-comparable coverage.
- Property class, sale screening, source terms and a robust comparable evidence contract still need review.
- No approved ML valuation, production database, deployed backend or buyer interface exists.

## Next engineering work

Phase 2 now implements a deterministic **same-neighbourhood first / 2 km bounded radius / insufficient-evidence** comparable selector. It is intentionally not a property valuation service. Offline tests cover out-of-window, future and same-day sales; duplicate property transactions; absent coordinates; class/area mismatches; price-blind ranking; fallback rationale; and abstention cases.

The cloud workflow will evaluate Phase 2 on 2024 historical Class 203 subjects after Phase 1, comparing adaptive, township and strict-neighbourhood median-of-five reference baselines on **paired groups**, including fallback-only cases. The next product decision must use those real Phase 2 metrics. Then scope a buyer-facing evidence contract and complete vertical slice, while retaining date-availability and public-data-display safeguards.

When source or audit code changes are pushed to `main`, the [cloud data audit](../.github/workflows/data-audit.yml) automatically reruns. For a manual rerun without code changes, use GitHub Actions → Cook County data audit → Run workflow. No local dataset download or ZIP upload is needed.
