# Phase 0 real-data audit: Cook County Township 17

**Recorded:** 22 November 2026. **Basis:** user-executed Phase 0 v2 offline reanalysis of live source extracts. Original user audit outputs are local-only, not committed. **No model is trained or validated.**

## Actual measurements

| Result | Count |
| --- | ---: |
| Source sale rows from 2022–2024 | 3,539 |
| Historical improvement rows in original extract | 39,401 |
| Sales passing the conservative pilot screens | 2,583 |
| Sales with accepted prior-tax-year building joins | 1,285 |
| Accepted joined records with class code `203` | 273 |
| Selected 2024 historical subjects checked (all sampled classes) | 20 |
| Selected subjects with at least 3 eligible comparisons | 19 |

The 19/20 result is for **multiple classes** using a township-wide match, 365-day window and building area +/-25%. It must not be represented as Class 203-only coverage, overall Cook County coverage, or measured valuation accuracy.

### Remaining unresolved exclusions

- 1,270 screened sales lacked a prior-year building record; of these, 1,266 PINs were not observed among selected historical improvement rows in any year.
- 27 sales had multiple prior-year building rows; one had a building area outside the provisional range.
- Sale screens are provisional and not proof of arm's-length status.
- Card-count parsing error discovered in Phase 0 v1 has been corrected; 779 previously rejected records had a number formatted as `1.0`.
- Historic source records can be backfilled or revised; prior tax-year data is **not equivalent to an archived point-in-time release**.

## Subsequent experiments completed

This original Phase 0 report is retained as the record of the first successful extraction. The planned Class 203 enrichment was subsequently implemented in [Phase 1](PHASE1_CLOUD_AUDIT_RESULTS.md), and a neighbourhood-first selection engine with an exploratory 2 km fallback was evaluated in [Phase 2](PHASE2_CLOUD_AUDIT_RESULTS.md). The 19/20 multi-class sample from Phase 0 must not be confused with the later 83-subject Class 203 evaluation.

**Current next step:** P3 product/domain and API contracts, while unresolved field rights and historical point-in-time validity remain blockers for public product claims. See [checkpoint](../CHECKPOINT.md).

No current home-price prediction or live listing claims may be made until proper data feasibility, time-respecting validation, representativeness, disclosure and licence review are complete.

Sources: [Cook County Parcel Sales](https://datacatalog.cookcountyil.gov/d/wvhk-k5uv), [Historical Improvement Characteristics](https://datacatalog.cookcountyil.gov/d/x54s-btds), [Historical Parcel Universe](https://datacatalog.cookcountyil.gov/d/nj4t-kc8j), [Classifications](https://www.cookcountyassessoril.gov/classifications-real-property).
