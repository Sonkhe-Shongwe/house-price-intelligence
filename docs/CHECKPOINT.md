# House Price Intelligence: current development checkpoint

**Last updated: 22 November 2026, Phase 2 cloud evaluation completed**

House Price Intelligence has its own GitHub repository. The South African graduate-programme research repository remains a separate, unchanged source of career-research documentation.

## Completed

- Phase 0 live Cook County extraction and corrected analysis: 3,539 sales, 39,401 building rows, 2,583 sales screened, 1,285 prior-year joins, including 273 Class 203 sales.
- Identified and fixed an integral-decimal card-count parsing defect with regression tests.
- Phase 1 targeted historical parcel universe and characteristics enrichment for 262 distinct Class 203 PIN-year keys.
- Phase 1 descriptive baseline analysis on 83 historical 2024 subjects; 66 have >=3 same-neighbourhood comparables.
- **GitHub Actions cloud automation verified:** Phase 0, Phase 1 and report upload succeeded on [run 45045580458](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45045580458).
- **Phase 2 matching engine completed:** neighbourhood-first, bounded 2 km geographic fallback, property deduplication, explanation, and abstention states. End-to-end [cloud evaluation succeeded](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782) with 42 offline unit tests. On 83 historical subjects, 66 had at least three neighbourhood comparables and 17 needed the 2 km fallback. The fallback's MAE was worse than township-wide matching on those same 17 subjects; do not promote fallback median as a credible valuation.
- The cloud workflow saves only aggregate reports; no raw source extracts are published as artifacts. No manual PowerShell steps are required for routine audits.

See [Phase 0 findings](research/PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1 findings](research/PHASE1_CLOUD_AUDIT_RESULTS.md), [Phase 2 findings](research/PHASE2_CLOUD_AUDIT_RESULTS.md) and [cloud audit operating instructions](AUTOMATED_DATA_AUDIT.md).

## Remaining problems

- Historical publication-time correctness is not guaranteed by prior-year data; recorded sales and neighbourhood data may arrive or be backfilled later.
- Neighbourhood matching improves paired descriptive error but sacrifices 17 of 83 subjects' three-comparable coverage.
- Property class, sale screening, source terms and a robust comparable evidence contract still need review.
- No approved ML valuation, production database, deployed backend or buyer interface exists.

## Next engineering work

The Phase 2 engine and live evaluation are complete. **Next priority:** build the first user-facing property investigation vertical slice, with a documented evidence response contract, subject input validation, traceable comparable sale explanations and clear distinctions between recorded facts, historical analysis and not-yet-approved predictions. Do not show fallback median prices as reliable valuations.

Before a public buyer app, review per-field source reuse/display rights, personal-record exclusion, historical availability, and current-market coverage. Continue evaluating geographical matching against a truly later holdout, not by overfitting to these 83 retrospectively analysed subjects.

Relevant GitHub Actions workflows run automatically on audit source changes; the results stay in a 14-day artifact, and verified findings must also be documented here.
