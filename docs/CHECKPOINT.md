# House Price Intelligence: current checkpoint

**As of:** 23 November 2026 (engineering process audit; previous delivered-code baseline retained)  
**Project:** [house-price-intelligence](https://github.com/Sonkhe-Shongwe/house-price-intelligence), branch `main`  
**Delivery-stage baseline:** P3 (synthetic vertical slice integrated; contract acceptance next); **22.8% estimated weighted MVP progress**, unchanged pending formal acceptance of the integrated candidate. This percentage is a planning judgment, not measured development output.

## Verified engineering evidence

- **Data audit Phase 0:** 3,539 sales and 39,401 historical building rows retrieved for Cook County township 17, 2022–2024; 2,583 passed provisional screening; 1,285 accepted prior-year building joins. The `1.0` numeric-count bug was fixed and covered by regression tests.
- **Data audit Phase 1:** 273 Class 203 sales enriched using 262 distinct PIN/prior-year keys; 83 retrospective 2024 subject sales considered, of which 66 had at least three eligible same-neighbourhood comparisons.
- **Data audit Phase 2:** Neighbourhood-first, 2 km bounded fallback, one-PIN deduplication, selection explanation and abstention engine implemented; 17 remaining 2024 subjects recovered by the exploratory fallback.
- **Quality/operations:** 42 offline tests passed and all three live phases completed in [GitHub Actions run 45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782). Aggregate-only cloud reports can be fetched without asking the user to run scripts. The latest source findings are recorded in [Phase 0](research/PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1](research/PHASE1_CLOUD_AUDIT_RESULTS.md) and [Phase 2](research/PHASE2_CLOUD_AUDIT_RESULTS.md) documentation.

**Interpretation:** These are *historical feasibility and algorithm experiments*, not a live product. The Phase 2 fallback's retrospective median-price MAE was **$209,470.65** versus **$192,153.00** for the township baseline on the same 17 fallback cases. Its candidates may be explored as sales evidence; do not present a fallback-derived value as a reliable valuation.

## P3 synthetic application integration (22 November 2026)

The owner authorised integration of the consolidated P3 candidate. The repository now includes a **synthetic-only** Python/SQLite investigation service, local loopback HTTP API, HTML/CSS/JavaScript frontend, saved-investigation retrieval, a 15-table draft schema and **83 fixture-only application tests** alongside the 42 research tests. The code was tested locally (125/125 on Python 3.13). The [post-integration GitHub Actions run 45059455620](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45059455620) has now been independently inspected: 12 Phase 0, 12 Phase 1, 14 Phase 2, 4 exporter and 83 P3 synthetic application tests passed (**125** total), plus documentation checks on Python 3.12. This does not verify a graphical browser or approve P3 contracts.

The research Phase 2 matcher is preserved byte-for-byte. This is **not** a production database, authorised publisher data display, real property ingestion, trained price model, public API or deployed application. The browser-to-HTTP flow has been tested without a graphical browser; real Chromium graphical acceptance was blocked by administrator policy. Refer to the [P3 application contract](engineering/P3_APPLICATION_CONTRACT.md) and [fixture-only backend](../backend/README.md).

## Owner-approved engineering process and documentation audit (23 November 2026)

The owner approved the [eight-step engineering directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md) with proportional architecture/risk planning, end-to-end slices, layered verification, safe migration and explicit implemented/verified/integrated/accepted/released states. **Existing P0-P8 stages, weights and gates remain unchanged.** After P3 acceptance, P4/P5 backend/browser work may overlap while stage credit remains separate.

**Source verified:** remote `main` at [`e8b8f70`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/e8b8f70de2bb10fd61b9cec9cc1d12aabdc6cfef); [CI run 45059455620](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45059455620) succeeded on the unmodified integrated code. Windows local active branch and uncommitted changes cannot be inspected. The proposed reopen sale-price/snapshot fix is a separate review-only patch, not on `main`.

The [23 November audit](reviews/ENGINEERING_DIRECTIVE_AUDIT_2026-11-23.md) reconciles stale P3 and CI status wording. No code, source research, production schema, real property records or live workflows were changed by adopting the process. **P3 remains 10% with gate open; overall weighted MVP remains 22.8%.**

## Local P3 browser evidence and UX discovery (23 November 2026)

**User-provided Windows screenshots:** From the correct HPI repository at `3f08060`, an isolated review runner SHA-verified 64 committed files, applied the pending backend/JavaScript safety patch to a disposable checkout and passed **127 Python tests**, **15 real Chromium DOM scenarios** and a synthetic **browser-to-Python-to-SQLite** journey. It reported the original Windows repository was unchanged. These results were **local on the proposed isolated patch**, not committed GitHub CI and not public-data/production acceptance. The older "graphical browser was blocked" statement above remains a dated historical observation, now superseded **for this isolated synthetic verification only**.

The owner requested that UX/visual direction be discussed before further aesthetic changes. A detailed [23 Nov UX research and concept record](design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md) now preserves design principles, references, the proposed shortlist-first information architecture, three candidate palettes, the Precision Slate illustrative concept, responsive/accessibility guidance and unresolved design choices. **No design system, site redesign, consumer address input or new product feature was approved.**

P3 remains **10%**, weighted MVP **22.8%**, with formal product/domain/source gates still open. The reviewed patch is still **unintegrated** into GitHub `main`.

## Current blockers and pending approvals

1. **Source policy (P0/P7):** Field-specific public display, attribution, redistribution and privacy rules have not been approved. This blocks public exposure of property-level records.
2. **Time integrity (P1/P2):** Prior tax-year joins, late-reported sales and backfilled neighbourhood data do not establish what was available on each historical sale date. There is no untouched later holdout.
3. **Product contract (P3):** Database schema, API response/evidence contract and exact buyer inputs are not yet accepted. Pilot geography/Class 203 are research choices, not the final product boundary.
4. **Application (P4–P8):** The repository now has a local synthetic-only API, SQLite and browser candidate, but **no production database/API, approved real-source property UI, working shortlist user feature, graphical browser acceptance or deployment**.

## Next milestone: review and accept the integrated P3 contract

The synthetic candidate is code-integrated, **not automatically accepted**. Review and verify, in order:
1. **Domain model/ERD:** sale transaction, parcel, building and assessment-year source record as distinct entities; buyer-entered property inquiry; matching run; selected comparable evidence; saved investigation and shortlist. Keep source snapshot, rule version and enquiry time traceable.
2. **API contract:** Validated subject input and statuses `supported_neighbourhood`, `exploratory_spatial`, `insufficient_data`, `out_of_coverage`; explicit error cases, provenance and date labels. No numeric valuation in exploratory/unsupported results.
3. **Technical decisions:** Document evidence-based Python API, relational database, browser framework and hosting options without silently selecting a permanent stack.
4. **Acceptance fixtures:** Supported enquiry, spatial fallback warning, insufficient evidence, out-of-area/class, future sale blocked, duplicate PIN, stale source and invalid asking price.

**P3 exits only when those contracts and decisions have been reviewed and accepted.** Then complete production-oriented P4 ingestion/storage planning and a genuinely verified browser-to-database investigation path, without exposing unapproved publisher records. Work on unresolved P0–P2 quality gates may continue in parallel.

## Lean engineering process directive (22 November 2026)

The owner adopted [Lean Engineering and Delivery Directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md) for future development: keep the authorised, integrated P3 candidate in one authoritative codebase, prioritise complete buyer workflows, reduce speculative abstractions and infrastructure, keep fast risk-focused tests, and preserve source/time/data correctness and release permissions. Framework and dependency options are **not yet binding stack choices**. The code integration does **not constitute P3 acceptance** or change the 22.8% weighted MVP baseline. The owner's Windows working tree remains outside current GitHub verification.

## Continuation protocol

For future ChatGPT or coding sessions, start with the [Master Continuation Prompt](MASTER_CONTINUATION_PROMPT.md), using [AGENTS.md](../AGENTS.md) where supported. It restores the latest authoritative state, mandates evidence-checked work, distinguishes local from remote changes and respects approval boundaries. **P3 has an integrated synthetic code candidate, not a completed phase gate:** the 22.8% weighted delivery baseline remains unchanged. This note does not establish the state of the owner's uninspected Windows clone.

## Where to continue

- [Documentation index](DOCUMENTATION_INDEX.md)
- [P0–P8 roadmap and weighted baseline](P_PHASE_ROADMAP.md)
- [Decision register](DECISIONS.md)
- [Current audit findings](research/PHASE2_CLOUD_AUDIT_RESULTS.md)
- [Engineering directive audit (23 November)](reviews/ENGINEERING_DIRECTIVE_AUDIT_2026-11-23.md)
- [Historical docs cleanup audit (22 November)](reviews/DOCUMENTATION_AUDIT_2026-11-22.md)

**Naming rule:** `audit/phase0`, `audit/phase1`, `audit/phase2` describe research experiments; P0–P8 describe overall software delivery. Do not equate completion of a research experiment with completing the identically numbered P-stage.
