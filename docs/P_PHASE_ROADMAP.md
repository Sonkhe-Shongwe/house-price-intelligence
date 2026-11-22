# House Price Intelligence: P0–P8 phase-gated delivery plan

**Established:** 22 November 2026. **Planning status:** adopted as the portfolio-MVP tracking framework, subject to owner revision. **Current baseline:** approximately 22.8% weighted progress.

## Origin and scope

This is an **adaptation of the PilotODIN complexity-last P0–P8 process**, not a claim that PilotODIN's original feature-specific P0–P8 acceptance cases apply unchanged. Source reference: `PilotODIN_1.0_Master_Status_Roadmap_and_Continuity_2026-10-24.docx`, section "5. Complexity-last implementation roadmap". The original PilotODIN framework required verifiable local acceptance at each stage, robust deterministic foundations before advanced intelligence, and complex release packaging last.

House Price Intelligence has a different product, market, platform and release target. Its P0–P8 stages are defined below specifically for a bounded, portfolio-grade **property investigation and shortlist application**. The original numbered Phase 0/1/2 **research audits** remain separate and are *not* the same as these higher-level P-stages.

### Progress methodology

- **Phase weight** means the estimated share of the bounded flagship MVP's total work, adding to 100%. It is a planning allocation, not a measured hours or lines-of-code share.
- **Phase completion** is a judgment informed by verified deliverables and unresolved acceptance gates, not an official instrument measurement. A passed unit test is evidence for a specific claim only.
- **Project contribution** = weight x phase completion / 100. Overall is the sum.
- Update estimated completion after demonstrable deliverables, tests, and acceptance evidence. Never call a stage done just because code was committed. Rebaseline and explain changed scope.
- **ML valuation prediction is conditional and excluded** from the MVP denominator until a true chronological evaluation justifies including it.

| P-stage | Focus | Weight | Estimated done | Contribution |
| --- | --- | ---: | ---: | ---: |
| P0 | Product discovery, supported buyer/market, feasibility | 6% | 85% | 5.1 pts |
| P1 | Reproducible ingestion, cleaning, historical joins, provenance | 12% | 75% | 9.0 pts |
| P2 | Explainable comparable-selection and evaluation | 14% | 55% | 7.7 pts |
| P3 | Product contracts, domain model, architecture decisions | 10% | 10% | 1.0 pts |
| P4 | Database, ingestion-to-storage, backend API | 16% | 0% | 0.0 pts |
| P5 | Browser property investigation experience | 16% | 0% | 0.0 pts |
| P6 | Saved investigations, shortlist, side-by-side comparison | 12% | 0% | 0.0 pts |
| P7 | Integrated quality, rights, security and operational readiness | 8% | 0% | 0.0 pts |
| P8 | Deployment, credible demo, documentation and portfolio handoff | 6% | 0% | 0.0 pts |
| **Total** | **Bounded flagship MVP** | **100%** | **22.8% weighted** | **22.8 pts** |

Progress is deliberately conservative because **no production database, property API, buyer UI, saved buyer workflow or deployment exists**. A tested data/audit engine is not a completed application.

The **22.8%** weighted progress is a subjective planning estimate derived from accepted evidence and unresolved phase gates. A documentation-only cleanup does **not** add delivered features and therefore does not change this estimate. The phases are delivery stages, distinct from the Phase 0–2 research experiments.

## Full process and phase exit gates

### P0: Discovery and feasibility — 6% weight; 85% estimated complete

**Goal:** Define a credible buyer decision, one supported geography and housing segment, a useful first product scope and viability boundaries.

**Evidence:** Product brief/pinnacle concept; Cook County township 17 (Evanston) candidate; official-source investigation; Class 203 research slice; real extraction and feasibility observations.

**Remaining:** Explicit owner sign-off on pilot geography/segment; source display/reuse rights, privacy and redistribution constraints; establish where user-entered properties can realistically be supported.

**Exit gate:** Approved bounded product brief, source register, class/geography decisions, permitted field display policy and a documented go/no-go decision. No claim of live listings or commercial appraisals.

### P1: Data engineering — 12% weight; 75% estimated complete

**Goal:** A repeatable extraction-to-cleaned-data pipeline with credible record grain, stable IDs and source/version lineage.

**Evidence:** GitHub Actions Phase 0/1 extraction, 3,539 recorded sales, 39,401 historical improvement records, 1,285 accepted joins and 273 Class 203 sales; numeric parser regression fixed; privacy-conscious aggregate report artifacts.

**Remaining:** Snapshot/version integrity, reproducible refresh and drift checks; schema and data dictionary review; policy for late-reported sales, historical backfills and ambiguous property identities; curated application-ready storage.

**Exit gate:** Reproducible dataset build with explicit inclusion/exclusion logs, validated grain and keys, provenance, tests for schema change and stable re-runs; raw records excluded from public repository/artifacts.

### P2: Comparable-sales intelligence — 14% weight; 55% estimated complete

**Goal:** Explainable, conservative same-market historical comparables, ranking, evidence and abstention.

**Evidence:** Phase 2 matcher, 42 offline tests across the pipeline, actual cloud evaluation: 83 Class 203 historical 2024 subjects; 66 with >=3 same-neighbourhood sales and 17 recovered by 2 km fallback.

**Remaining:** Fallback's retrospective price error is worse than township baseline on those 17 cases. More property similarity features, source-time limitations, untouched later holdout, error/coverage/abstention calibration and safe output evidence contract remain unresolved.

**Exit gate:** Deterministic eligibility and no-future-sale rules, one-property-one-comparable accounting, complete explanation/provenance, independent evaluation, justified fallback rules and truthful insufficiency response. Do not promote experimental median to a validated price estimate.

### P3: Product architecture and contracts — 10% weight; 10% estimated complete

**Goal:** Translate the research engine into explicit, testable business objects and contracts for a real application.

**Evidence:** High-level product brief and engineering invariants exist; production service architecture and schemas have not been approved.

**Planned:** Define subject/property inquiry (user-reported data), source sale, historical building/parcel, matching run and evidence, saved investigation and shortlist. Specify source/version/date timestamps and snapshot semantics. Define a request/response schema for `supported_neighbourhood`, `exploratory_spatial`, `insufficient_data` and out-of-coverage. Decide Python API, SQL database, frontend and deploy strategy only after examining real domain needs.

**Exit gate:** Accepted database ERD and migration plan, endpoint/request/response contract, error and unsupported states, first end-to-end journey specification, security/privacy rules and contract-test fixtures.

### P4: Backend API and database — 16% weight; 0%

**Goal:** Running server and durable application storage connecting curated data to enquiries and evidence.

**Planned:** SQL schema and constraints; migrations; idempotent curated-data import; safe data access; validated property investigation endpoints; matcher service integration; source/version lineage; correctness integration tests.

**Exit gate:** A client can submit a supported subject, retrieve ranked and explained earlier comparable sales, retrieve truthful insufficient-data results, and recover an investigation from persisted storage. Tests demonstrate these behaviours without handwritten fake totals.

### P5: Property investigation frontend — 16% weight; 0%

**Goal:** A usable browser experience rather than a notebook or audit dashboard.

**Planned:** Market coverage explanation, property entry/validation, asking-price field clearly user-reported, comparable cards/evidence, ranked differences and dates, transparent neighbourhood vs exploratory radius, loading/empty/failure states, responsive and accessible UX.

**Exit gate:** User completes add property -> inspect relevant historical comps -> understand why selected or why unavailable, in the browser, against the actual backend. No unsupported price claims.

### P6: Saved buyer decision workflow — 12% weight; 0%

**Goal:** The distinctive complete micro-application experience.

**Planned:** Save and reopen at least two enquiries; per-property notes and shortlist; side-by-side comparison; recorded sale evidence linked to source/version and rule revision; simple decision report/export only where field rights permit. Authentication only if the product requires accounts.

**Exit gate:** A returning buyer can open two saved properties, compare supported evidence and notes, and reopen identical source/rule-referenced results. An insufficient-data home is still savable.

### P7: Integrated QA and readiness — 8% weight; 0%

**Goal:** Prove the complete system is reliable, secure and honest.

**Planned:** API/database/browser end-to-end tests; malformed property submissions, duplicate/revised sales, date leakage, ambiguous joins, migration backup/recovery, accessibility, resource performance and source rights; verify no raw private records or credentials leak to Git or artifacts; monitor pipeline failures and source changes.

**Exit gate:** Accepted integration/demo journeys, reproducible clean build, documented limitations, suitable rate/resource controls and permission to expose chosen fields. Public exposure blocked if source reuse rights remain unresolved.

### P8: Release and portfolio demonstration — 6% weight; 0%

**Goal:** Ship a coherent portfolio-quality application and explain technical decisions to recruiters.

**Planned:** Deploy only after P7; representative allowed data or unmistakably labelled synthetic/demo fixtures where public display rights are unresolved; README, architecture diagram, clean setup, demo walkthrough/video, source and QA evidence, explanation of matching/risk trade-offs; working app URL if deployment is authorized.

**Exit gate:** Reproducible installation and deployed/demo functionality: add two properties -> inspect ranked comps -> demonstrate fallback warning/abstention -> save/reopen -> compare -> explain test-backed joins and provenance.

## Conditional post-MVP branch, excluded from 100%

**M1: statistical pricing / machine learning.** Requires a credible later chronological holdout, fully time-appropriate features, strong baseline comparisons, useful accuracy and defensible uncertainty calibration. If it fails, ship without a predicted price. No forced "AI" feature.

**Deferred:** Global listing search, property photos, mortgages, multi-market expansion, notification infrastructure and professional-appraisal claims.

## Near-term execution, complexity last

1. **Now:** P3 domain schema, API evidence contract, field-level reuse constraints and first browser journey. Do this while explicitly tracking unfinished P0/P1/P2 gates.
2. **Next:** P4 curated database ingest + one subject query API integrating the already-tested matcher; prove browser-to-API-to-database correctness early.
3. **Then:** P5 basic browser investigation; P6 persistence and shortlist; P7 quality/security; P8 release.
4. Avoid building a predictive model, AI agent or complicated operations stack before the buyer workflow and evidence quality exist.

## Evidence and reporting policy

**Verified as of 22 November 2026:** GitHub Actions [run 45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782); [Phase 2 retrospective results](research/PHASE2_CLOUD_AUDIT_RESULTS.md); [project checkpoint](CHECKPOINT.md).

**Progress tracking:** On every substantial accepted milestone, update this file's stage figures, explain evidence and changed assumptions, and update `docs/CHECKPOINT.md`. Document rejected experiments rather than reporting them as successful features. No automatic %-increase per commit or test count. The original House Price Intelligence exploratory roadmap is preserved at [docs/archive/INITIAL_ROADMAP_2026-11-22.md](archive/INITIAL_ROADMAP_2026-11-22.md).
