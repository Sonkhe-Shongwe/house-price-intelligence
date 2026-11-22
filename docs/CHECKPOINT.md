# House Price Intelligence: current checkpoint

**As of:** 22 November 2026  
**Project:** [house-price-intelligence](https://github.com/Sonkhe-Shongwe/house-price-intelligence), branch `main`  
**Delivery-stage baseline:** P3 (architecture/contracts next); **22.8% estimated weighted MVP progress**, unchanged by the documentation cleanup. This percentage is a planning judgment, not measured development output.

## Verified engineering evidence

- **Data audit Phase 0:** 3,539 sales and 39,401 historical building rows retrieved for Cook County township 17, 2022–2024; 2,583 passed provisional screening; 1,285 accepted prior-year building joins. The `1.0` numeric-count bug was fixed and covered by regression tests.
- **Data audit Phase 1:** 273 Class 203 sales enriched using 262 distinct PIN/prior-year keys; 83 retrospective 2024 subject sales considered, of which 66 had at least three eligible same-neighbourhood comparisons.
- **Data audit Phase 2:** Neighbourhood-first, 2 km bounded fallback, one-PIN deduplication, selection explanation and abstention engine implemented; 17 remaining 2024 subjects recovered by the exploratory fallback.
- **Quality/operations:** 42 offline tests passed and all three live phases completed in [GitHub Actions run 45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782). Aggregate-only cloud reports can be fetched without asking the user to run scripts. The latest source findings are recorded in [Phase 0](research/PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1](research/PHASE1_CLOUD_AUDIT_RESULTS.md) and [Phase 2](research/PHASE2_CLOUD_AUDIT_RESULTS.md) documentation.

**Interpretation:** These are *historical feasibility and algorithm experiments*, not a live product. The Phase 2 fallback's retrospective median-price MAE was **$209,470.65** versus **$192,153.00** for the township baseline on the same 17 fallback cases. Its candidates may be explored as sales evidence; do not present a fallback-derived value as a reliable valuation.

## Current blockers and pending approvals

1. **Source policy (P0/P7):** Field-specific public display, attribution, redistribution and privacy rules have not been approved. This blocks public exposure of property-level records.
2. **Time integrity (P1/P2):** Prior tax-year joins, late-reported sales and backfilled neighbourhood data do not establish what was available on each historical sale date. There is no untouched later holdout.
3. **Product contract (P3):** Database schema, API response/evidence contract and exact buyer inputs are not yet accepted. Pilot geography/Class 203 are research choices, not the final product boundary.
4. **Application (P4–P8):** No production database, API service, browser interface, shortlist persistence, end-to-end app test or deployed application exists.

## Next milestone: P3 acceptance package

Prepare and review, in order:
1. **Domain model/ERD:** sale transaction, parcel, building and assessment-year source record as distinct entities; buyer-entered property inquiry; matching run; selected comparable evidence; saved investigation and shortlist. Keep source snapshot, rule version and enquiry time traceable.
2. **API contract:** Validated subject input and statuses `supported_neighbourhood`, `exploratory_spatial`, `insufficient_data`, `out_of_coverage`; explicit error cases, provenance and date labels. No numeric valuation in exploratory/unsupported results.
3. **Technical decisions:** Document evidence-based Python API, relational database, browser framework and hosting options without silently selecting a permanent stack.
4. **Acceptance fixtures:** Supported enquiry, spatial fallback warning, insufficient evidence, out-of-area/class, future sale blocked, duplicate PIN, stale source and invalid asking price.

**P3 exits only when those contracts and decisions have been reviewed and accepted.** Then start P4: curated SQL ingestion and one real browser-to-database investigation path. Work on unresolved P0–P2 quality gates may continue in parallel.

## Continuation protocol

For future ChatGPT or coding sessions, start with the [Master Continuation Prompt](MASTER_CONTINUATION_PROMPT.md), using [AGENTS.md](../AGENTS.md) where supported. It restores the latest authoritative state, mandates evidence-checked work, distinguishes local from remote changes and respects approval boundaries. **This is a process/documentation improvement only:** P3 and the 22.8% weighted delivery baseline remain unchanged. This note does not establish the state of the owner's uninspected Windows clone.

## Where to continue

- [Documentation index](DOCUMENTATION_INDEX.md)
- [P0–P8 roadmap and weighted baseline](P_PHASE_ROADMAP.md)
- [Decision register](DECISIONS.md)
- [Current audit findings](research/PHASE2_CLOUD_AUDIT_RESULTS.md)
- [Latest docs cleanup audit](reviews/DOCUMENTATION_AUDIT_2026-11-22.md)

**Naming rule:** `audit/phase0`, `audit/phase1`, `audit/phase2` describe research experiments; P0–P8 describe overall software delivery. Do not equate completion of a research experiment with completing the identically numbered P-stage.
