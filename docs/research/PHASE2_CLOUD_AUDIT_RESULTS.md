# Phase 2 cloud evaluation: neighbourhood-first matching with bounded fallback

**Run:** 22 November 2026, GitHub Actions [run 45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782), source commit [`f825c14`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/f825c14bebe9297ead749ae51bb56d02ed65e083). The cloud pipeline, offline tests and artifact upload completed successfully. [Aggregate artifact](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782/artifacts/14764136546) expires after 14 days. This document preserves the results.

**Scope:** Cook County / Evanston, township 17; historical transactions 2022–2024; Assessor class 203; historical subjects sold in 2024. **Research audit only; no verified current values or production valuation model.**

## Matching rules (experimental)

- Only another valid property with the same class and township, a sale date earlier than the analysis date within the last 365 days, and building area within ±25%.
- Deduplicate properties by PIN to avoid multiple transaction rows from the same property becoming independent comparable houses; do not reuse the same transaction document.
- Prefer at least three sales in the **same assessor neighbourhood**, ranked by size similarity and sale recency.
- Otherwise use **up to five eligible sales within 2 km** of the subject, with valid coordinates. Rank by distance, then size similarity and recency. At least three needed.
- Otherwise mark **insufficient_data**. Never silently fall back to all township sales.
- Sale price is not part of the matching/ranking algorithm; only used in subsequent retrospective baseline evaluation.

## Cloud results

| Historical measure | Result |
| --- | ---: |
| Enriched class 203 sales in selected market | 273 |
| Historical 2024 sale subjects | 83 |
| Met 3-comparable same-neighbourhood requirement | **66** |
| Needed and received 2 km spatial fallback | **17** |
| Abstentions in this evaluated cohort | **0** |
| Adaptive support (>=3 comparables) | **83/83** |

The absence of abstentions is **specific to the 83 historical test subjects**, not a promise for buyer-entered properties, other geographies, later dates, or other property classes.

### Error, assessed on matched subjects

| Method / group | Subjects | MAE USD | Median absolute percentage error |
| --- | ---: | ---: | ---: |
| Adaptive, all supported | 83 | **125,985.54** | **20.00%** |
| Township baseline, same 83 | 83 | 157,859.64 | 24.03% |
| Strict-neighbourhood baseline, its supported cohort | 66 | 103,527.26 | 18.35% |
| Adaptive on the strict-neighbourhood 66 | 66 | 104,481.80 | 18.35% |
| Adaptive on fallback-only 17 | 17 | **209,470.65** | **31.81%** |
| Township baseline on that same fallback-only 17 | 17 | **192,153.00** | **26.56%** |

The adaptive method improved the historical 83-subject overall MAE relative to township-wide matching, but **its 2 km fallback produced worse errors than township-wide matching on the very 17 properties it rescued**. The fallback is therefore useful for surfacing nearby sale evidence, not proof that the resulting sample median is accurate enough for a financial decision.

The small difference between the strict-neighbourhood and adaptive methods on the 66 same-neighbourhood subjects is consistent with the adaptive engine's one-sale-per-PIN deduplication and deterministic ranking; those methods are not guaranteed identical.

## Decisions and safeguards

- **Keep the neighbourhood-first engine** as a useful candidate for the buyer's explainable historical comparable explorer.
- **Keep the 2 km fallback explicitly labelled experimental**; display it as supplemental evidence only. Do not promote its median to a validated price estimate.
- Continue to **abstain** on thin data and missing geographic evidence. This historical cohort happening to have zero abstentions does not remove the abstention requirement.
- Prioritise a first browser/API vertical slice that can show a subject, ranked eligible sales, selection rationale, provenance, and a clear insufficiency state, while keeping property-price predictions disabled.
- Test alternative geographical policies and property-feature similarity separately, with a later chronological holdout and controlled paired comparisons rather than tuning to these same 83 outcomes.

## Limitations

These are retrospective results from selected data observed in 2026. Recorded transactions can appear late in the source, historical building and parcel records can be revised or backfilled, and the present extraction is **not a historical point-in-time snapshot**. No final untouched test, calibrated confidence interval, independent manual sale verification, current market validation, or source-specific public display/redistribution rights review has been completed. None of these numbers is a warranty of commercial appraisal accuracy.
