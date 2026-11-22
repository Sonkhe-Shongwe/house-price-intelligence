# Phase 1 verified cloud audit: Class 203 neighbourhood enrichment

**Run:** 22 November 2026, GitHub Actions [run 45045580458](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45045580458), commit [`edda0a1`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/edda0a1b98192b0c11477589d22eb51e1c504c60). Both phases and artifact upload completed successfully. [Aggregate report artifact](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45045580458/artifacts/14763313317) (14-day retention); this document preserves the main findings longer term.

**Scope:** Cook County, Illinois; Evanston township code 17; sales in calendar years 2022–2024; Phase 1 property class `203` (one-story residence in the Assessor classification). These are **descriptive historical experiments**, not current-market app valuations or leakage-safe model validation.

## Data and join counts

| Measure | Count |
| --- | ---: |
| Phase 0 downloaded sale rows | 3,539 |
| Phase 0 downloaded residential characteristic rows | 39,401 |
| Phase 0 sales passing pilot screens | 2,583 |
| Phase 0 accepted prior-year building joins | 1,285 |
| Accepted Class 203 historical sales | **273** |
| Distinct Class 203 PIN / prior-year lookup keys | **262** |
| Phase 1 historic parcel universe records fetched | 262 |
| Phase 1 further building-detail records fetched | 262 |
| Phase 1 missing/ambiguous enrichment issues | **0 reported** |

The numeric parsing correction remains necessary: the source includes integral counts encoded as `1.0`. Other missing historical joins remain unresolved and are not silently imputed.

## Historical comparable coverage (2024)

| Measurement | Township-wide | Same assessor neighbourhood |
| --- | ---: | ---: |
| Eligible Class 203 sale subjects in 2024 | 83 | 83 |
| Subjects with at least three eligible earlier sale comparables | 83 | **66** |
| Subjects lacking that three-comparable minimum | 0 | **17** |

Comparable rules: same class and township, recorded sale within 365 days *before* subject sale, building area within ±25%, other PIN/document, ranked by size similarity then recency. The experimental estimate is a median of up to five matches. No price is used in selecting or ranking the matches.

### Fair paired error comparison (same 66 supported subjects)

| Metric | Township comparables | Neighbourhood comparables |
| --- | ---: | ---: |
| Subjects | 66 | 66 |
| Mean absolute error, USD | **149,026.50** | **103,527.26** |
| Median absolute percentage error | **22.92%** | **18.35%** |

Additional unpaired township-only cohort (83 subjects) had MAE **$157,859.64** and MdAPE **24.03%**. Do not compare its performance directly against the smaller 66-subject neighbourhood cohort. The matched comparison supports further investigation of neighbourhood relevance, **not** a claim of causal or generalizable predictive superiority.

## Unresolved quality / product constraints

- This audit does not establish availability of comparable sales on the relevant historical **analysis date**; late reports, revised data and backfilled parcel geography can leak later information into retrospective evaluations.
- A neighbourhood requirement improves paired descriptive errors but loses comparison coverage for 17 subjects. We need a transparent, tested geographic fallback instead of either silently expanding scope or pretending those properties can be valued accurately.
- Property condition, renovations, micro-location, sale circumstances and other relevant attributes remain unmodelled.
- The selection sample is one township and one property class. Do not extrapolate coverage or errors to all Cook County or present-day houses.
- The publisher's reuse/display terms and reliable public-facing fields still require a specific review before any deployed buyer product.
- A validated valuation model, calibrated prediction interval, application database and buyer interface do not yet exist.

## Next engineering decision

Prototype and test **neighbourhood-first comparable selection with an explicitly labelled fallback** (spatial distance or broader-area rule only when justified). Measure coverage and error on the same historical subjects, document failure and abstention states, and only then define an application-facing comparable evidence API.
