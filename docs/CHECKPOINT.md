# House Price Intelligence: current checkpoint

**As of:** 23 November 2026, post-continuity/document audit.  
**Repository:** [Sonkhe-Shongwe/house-price-intelligence](https://github.com/Sonkhe-Shongwe/house-price-intelligence), branch `main`; last checked source before documentation update: `317149392678646455a0eb6080c086d682bca293`. Re-read HEAD and CI next session.  
**Active stage:** P3 product architecture/contracts, **10% estimated complete**; **22.8% estimated weighted MVP progress**. P3 exit gate remains **open**; no progress added by design discussion or docs.

## Product direction and approvals

HPI is an **original, data-first, geography-flexible property investigation and decision workspace**: **Investigate -> Compare -> Decide**. Borrow interaction ideas from property platforms but do not copy protected listings, visual identity or databases; do not build a full listing marketplace instead of the approved buyer workflow. No South African-market constraint: select one first market/class from verified usable sales, attributes, identity, location coverage, temporal integrity and legal reuse. Cook County township 17 / Evanston Class 203 remains the tested **research pilot**, not permanent public coverage.

**First flagship:** Buyer-entered enquiry, prior completed-sale evidence with explanations and clear limits, save/reopen two or three properties, notes and side-by-side comparison. Buyer asking price is not a verified listing. **No approved numerical valuation.** The exploratory 2 km fallback must not be promoted to an estimate.

**UX:** Owner positively received the *workspace-first low-fidelity exploration*; this is not approval of final navigation, colour palette, brand, cards or current teal styling. Three visual studies remain in [UX research](design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md). **Maps** are a promising proposal to link verified subject/comparable locations and the evidence table; no map, provider, tiles, data rights or real coordinates are approved for a buyer-facing UI.

## Verified research and source limits

[Phase 0-2 cloud run 45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782): 3,539 historical sales rows, 39,401 building records, 2,583 provisional screened sales, 1,285 accepted prior-year joins, 273 Class 203 joined sales and 83 historical 2024 subjects. Neighbourhood evidence supported 66; an exploratory 2 km fallback supported 17. On those 17, the fallback median MAE was **$209,470.65**, worse than the township baseline **$192,153**. See [Phase 2 report](research/PHASE2_CLOUD_AUDIT_RESULTS.md).

Historical tax-year matching does **not** establish when property facts were first published; late sales and later backfills remain possible. Dataset-specific property-field display/reuse/attribution and real-sale eligibility are **not approved**. Do not expose source-level personal/private raw records in Git or public artifacts.

## Exact implementation and test status

| State | Evidence | Boundary |
| --- | --- | --- |
| **Committed `main`** | Synthetic-only Python/SQLite/WSGI investigation + plain HTML/CSS/JS, four API statuses, saved in-memory investigation UUID/reopen, 15-table draft schema. **125 tests** passed in [CI 45059455620](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45059455620). Recent docs-only HEAD [CI 45126415402](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45126415402) also successful | No production API, permitted real-data frontend, stable consumer address lookup, persistent multi-property shortlist or map |
| **Separate isolated Windows patch** | User screenshots: **127 Python tests**, **15 Chromium DOM scenarios**, and full synthetic **browser -> HTTP -> Python -> SQLite** supported/insufficient/reopen/error journey passed | **Not integrated** into `main`; two additional backend guard tests and frontend/backend safety patch are not in GitHub CI. Original repository reported untouched by isolated runner |
| **Production and release** | None | No authenticated production app, approved data-field display or deployment |

**Four statuses:** `supported_neighbourhood`, `exploratory_spatial`, `insufficient_data`, `out_of_coverage`. The local server persists only within its in-memory SQLite lifetime. Current committed reopen checks hash, count and comparable identities; the stricter sale-price/sales-snapshot guard remains in a review-only patch.

## Confirmed directive

[Eight-step Lean Engineering and Delivery Directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md) **retained without amendment**: buyer problem, contract, risk, minimal end-to-end implementation, appropriate automated tests, actual integrated UX tests, controlled reviewed integration, single source-of-truth handoff. Preserve one authoritative codebase, safe source/build provenance and price-free ranking. Avoid mandatory React/FastAPI/PostgreSQL/microservices/ML by fashion alone. Include UX design approval, coordinate semantics and provider/copyright restrictions inside existing lifecycle reviews.

## Priority grey areas

**Critical:** property-level display rights; actual historical publication timing; correct address/parcel/building/transaction identity; credible comparable eligibility and independent later evaluation.

**High:** final buyer input; supported geography/class; persistence/privacy; integrating locally tested safety patch and browser checks.

**Proposed/later:** map coordinate and provider contract; original UX/visual direction; production migration/hosting/security.

**Specific review target:** SQL prices are exact cents, but synthetic comparable response uses `cents / 100` floating-point conversion; define an exact external-money contract before extending use. Complete 11-item list in [continuity audit](reviews/CONTINUITY_AND_DIRECTIVE_AUDIT_2026-11-23.md).

## New-tab action plan

1. **Read** [Master Continuation Prompt](MASTER_CONTINUATION_PROMPT.md), this checkpoint, [Decision Register](DECISIONS.md), [P3 Contract](engineering/P3_APPLICATION_CONTRACT.md), [latest continuity audit](reviews/CONTINUITY_AND_DIRECTIVE_AUDIT_2026-11-23.md) and [UX research](design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md); verify current GitHub HEAD and CI.
2. **P3 contract review:** Settle first buyer/market, credible consumer property identity, domain/ERD (transaction/parcel/building/assessment, source builds and evidence), API error/status semantics, versioning and save/reopen rules. No automatic P3 acceptance because synthetic browser tests passed.
3. **Engineering after owner approval:** Reconcile actual Windows working tree, inspect verified integrated safety patch exactly, add relevant backend/JS regressions and reproducible Chromium journey into one authoritative repository, and verify GitHub CI for the resulting commit. Preserve untracked files. The current documentation request is **not** approval to integrate code.
4. Continue rights/time/identity/source evaluation in parallel; only then justify P4/P5 connected slices and map-provider implementation. P6 shortlist remains a required MVP user feature, not yet delivered.

**Current true commands:** `python tools/dev_check.py` and `python -m backend.run_synthetic_api --fixture-only --port 8765` from the repository root. The convenient `tools/bootstrap.ps1`, `tools/check.ps1`, `tools/run.ps1` scripts have **not been created**.

**Windows checkout last shared:** `C:\Users\Lenovo\Downloads\Github Projects\house-price-intelligence`; temporary review at `C:\Users\Lenovo\Downloads\HPI-P3-review`. Earlier actual repo status showed three untracked research ZIPs. GitHub connector cannot inspect current Windows worktree. No deletion, force checkout or ZIP overwrite.

**Progress:** P3 **10%**; total weighted MVP **22.8%**; unchanged.
