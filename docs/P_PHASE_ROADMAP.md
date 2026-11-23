# House Price Intelligence: P0–P8 phase-gated delivery plan

**Established:** 22 November 2026. **Delivery-process extension approved:** 23 November 2026. **Planning status:** P0-P8 weights and exit gates retained. **Current baseline:** approximately 22.8% weighted progress.

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

## Phase-governed, vertical-slice delivery directive (23 November 2026)

Apply the [eight-step engineering lifecycle](engineering/LEAN_ENGINEERING_DIRECTIVE.md) proportionately to meaningful work. **Keep P0-P8 stage meanings, weights, acceptance and progress independent from implementation order.**

- **P3 is the immediate gate:** Review and accept the already-integrated, synthetic-only PIN-first domain/SQL/API contract, error states and real-browser journey. Passing fixture CI alone is not contract acceptance.
- **P4/P5 may overlap in implementation once P3 is accepted:** Build complete buyer slices through browser -> HTTP -> service -> curated SQL -> unchanged matcher, verifying supported, exploratory, insufficient and out-of-coverage behaviour. Backend P4 and browser P5 retain **distinct exit tests and completion credit**; there is no automatic percentage transfer.
- **P6 completes the decision workflow:** Save, reopen and compare at least two subject enquiries with notes and frozen evidence. A temporary one-property P3 save is not an accepted P6 shortlist.
- **P0-P2 unresolved gates run in parallel:** Source rights, joins, historical publication time, leakage and independent comparable evaluation remain open while synthetic software is built.
- **P7 independently accepts integrated readiness; P8 requires authorised release.** Error handling, safe coding, privacy and security start with architecture and continue at every stage rather than being deferred until P7.

Classify each deliverable explicitly as **implemented, verified, integrated, accepted or released**. High-risk multi-layer changes should use compatible expansion, reproducible migration, controlled switching and recovery checks. Phase credit requires accepted evidence, not code quantity, test count or a documentation update.

## Granular deliverable and acceptance matrix (planning proposal, 23 November 2026)

**Purpose:** This is the task-level execution map for the existing P0–P8 stages, not a second roadmap, a new phase system or permission to change acceptance percentages. It is based on the [product brief](product/PRODUCT_BRIEF.md), [source register](research/SOURCE_REGISTER.md), [research audits](research/PHASE2_CLOUD_AUDIT_RESULTS.md), [P3 application contract](engineering/P3_APPLICATION_CONTRACT.md), [decisions](DECISIONS.md) and the current [development checkpoint](CHECKPOINT.md). The existing stage summary and **22.8%** weighted assessment remain authoritative. Each ID can be tracked independently as implementation advances.

**Progress vocabulary for this matrix:**

- **RESEARCH:** Documentary evidence, pilot analysis or a source survey exists. It is **not** a signed-off product deliverable.
- **VERIFIED:** Working implementation has relevant automated evidence on the **development** branch, generally synthetic only. This does **not** imply production readiness or owner acceptance.
- **PARTIAL:** Some design, code or evidence exists, but the deliverable described in its acceptance column is incomplete.
- **OPEN:** No completed delivery evidence yet.
- **BLOCKED:** Cannot be responsibly accepted before a named external decision, data permission or independent proof.

**Every item must eventually be accompanied by:** concrete output or code reference, the exact tested commit/CI or dated research evidence, owner review where necessary, and its resulting state: *proposed → implemented → verified → integrated → accepted → released*. For future progress reviews, record both **candidate implementation** and **accepted phase credit**. A long checklist is not itself evidence of completion. The historical Phase 0–2 audits remain distinct from delivery stages P0–P2.

### P0 | Buyer, market and product feasibility | Weight 6% | Recorded completion 85%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P0.1 | Define buyer decision and narrow value proposition | RESEARCH | Owner accepts Investigate → Compare → Decide for a single buyer comparing two or three homes, not a listings marketplace |
| P0.2 | Define explicit first-MVP inclusion/exclusion list | PARTIAL | Owner approves flagship features and non-goals, including conditional-only ML and no unverified live listings |
| P0.3 | Research one candidate geography and property segment | RESEARCH | Record market, source IDs, eligible-sale counts, supported class and limitations for the pilot |
| P0.4 | Validate source availability and property-entry feasibility | PARTIAL | Demonstrate which real inputs a buyer can legally and reliably identify, including unmatchable/ambiguous addresses |
| P0.5 | Review field-by-field data rights, privacy and attribution | BLOCKED | Written reuse/display decision for each required source/field; define synthetic-only fallback if needed |
| P0.6 | Approve final first-market/class and intended buyer scenario | BLOCKED | Owner signs off market and class or documents a deliberate no-go/pivot with reasons |
| P0.7 | Issue bounded feasibility and release-path decision | BLOCKED | A go/no-go record reconciles coverage, quality, legal permissions, cost and the permitted demo mode |

**P0 exit:** Approved scope, first supported market/class, source register, field policy and a clear permitted release approach. Current evidence: Evanston township 17 and Class 203 are **research pilot candidates**, not permanent geography or public-display approval.

### P1 | Source extraction, cleaning and historical data | Weight 12% | Recorded completion 75%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P1.1 | Source inventory and schema/field register | RESEARCH | Dataset IDs, field definitions, source URLs, licence status and schema metadata captured |
| P1.2 | Deterministic bounded extraction in CI | RESEARCH | Re-running the documented query returns reproducible counts or explicitly explains any dataset revision |
| P1.3 | Data type, null, duplicate and exclusion policies | PARTIAL | Automated quality log tracks conversions, exclusions and source changes, including historical numeric parser issue |
| P1.4 | Preserve transaction, parcel, building and card grain | PARTIAL | Uniqueness and ambiguous/multi-parcel tests reconcile rows without allocating one sale to each parcel |
| P1.5 | Historical as-of availability and late/backfilled changes | BLOCKED | Archived snapshot/publication evidence or an explicitly conservative non-as-of policy is reviewed and implemented |
| P1.6 | Versioned source manifest, drift/re-run comparison | PARTIAL | Extract timestamp, query, schema/source update time and drift assertions can be checked across two runs |
| P1.7 | Idempotent curated application-ready import | OPEN | Duplicate import leaves stable record counts, durable IDs and valid source-build membership |
| P1.8 | Publisher-safe output and operational reproducibility | PARTIAL | Aggregate audits run without exposing raw/identifying records; rights-per-field decision remains required |

**P1 exit:** Reproducible ingestion, stable keys, explained exclusions, source lineage and legally safe curated storage. Research pilot counts include 3,539 sales, 39,401 building records and 1,285 accepted historical joins; those alone do not prove complete historical or legal validity.

### P2 | Explainable comparable-sales intelligence | Weight 14% | Recorded completion 55%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P2.1 | Deterministic eligibility and exclusion rules | RESEARCH | Earlier-only sales, correct class/township, area tolerance, valid window and excluded shared transactions tested |
| P2.2 | Prevent duplicate property/document comparables | RESEARCH | Each selected comparable is unique under defined PIN/document/source grain and explainable |
| P2.3 | Same-neighbourhood selection and stable ranking | RESEARCH | Rank and explain relevant previous sales without using sale price as a ranking input |
| P2.4 | Evaluate bounded geographic fallback | PARTIAL | Compare error, support and failure risks independently; current 2 km fallback must remain labelled exploratory |
| P2.5 | Validate insufficiency and abstention policy | PARTIAL | Missing/unsupported records produce a deterministic honest result with no manufactured estimate |
| P2.6 | Test better similarity and sale-quality factors | OPEN | Evidence-backed candidate features, exclusion reasons and controlled paired ablations recorded |
| P2.7 | Independent later chronological holdout | OPEN | A future withheld period measures coverage/error and protects against leakage or reuse of test cases in policy tuning |
| P2.8 | Prove time-valid source provenance and interpretability | BLOCKED | Every displayed sale has a traceable, permitted record and appropriate as-of/revision limitation |
| P2.9 | Accept evidence-only versus price-estimation boundary | BLOCKED | Owner approves when fallback may be displayed and how unsupported predictions/weak evidence are labelled |

**P2 exit:** Reliable, explainable comparable selection with a justified fallback and independent assessment. **Known limitation:** on the 17 fallback cases, exploratory 2 km retrospective MAE was about $209,471, worse than township comparison at about $192,153. Do **not** present the sample median as a validated house-price prediction.

### P3 | Domain model, service contracts and architecture | Weight 10% | Recorded completion 10%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P3.1 | Define inquiry, sale, parcel, building, assessment and evidence entities | VERIFIED | Owner reviews canonical [proposed ERD](engineering/P3_APPLICATION_CONTRACT.md), grain, cardinalities and no-false-identity rules |
| P3.2 | Define address resolution and ambiguous identity | VERIFIED | Synthetic v3 handles same-address/multi-parcel candidates; accept a *real* source-validated address/building/parcel design separately |
| P3.3 | Define buyer input and server-owned fields | VERIFIED | Contract tests disallow user selection of trusted source facts; cover unknown, conflicting and missing inputs |
| P3.4 | Define status/error/abstention contract | VERIFIED | Versioned requests and deterministic supported, exploratory, insufficient and out-of-coverage outcomes tested and reviewed |
| P3.5 | Define provenance, snapshots and frozen evidence | VERIFIED | Source-build membership, original sale cents, response hash and reopening invalidation have negative tests |
| P3.6 | Define exact-money and currency representation | VERIFIED | Synthetic v0.3 uses integer cents and canonical two-decimal USD text; production currency, scale and range limits still require approval |
| P3.7 | Define schema evolution and recovery method | VERIFIED | Fixture SQLite v1–v3 checksum, rollback, refusal of unknown databases and data-preserving upgrade tested; production plan still open |
| P3.8 | Select application stack, hosting and access approach | PARTIAL | Owner accepts modular Python/SQL/browser approach and justifies production DB, auth and hosting choice |
| P3.9 | Define secure, permission-aware buyer experience | PARTIAL | UX acceptance cases, privacy boundaries, accessible evidence and error disclosure reviewed; existing teal UI is provisional |
| P3.10 | Decide real geography/identity/as-of/field-rights boundaries | BLOCKED | Specific source and rights evidence connects the final market to safe real property selection and display |
| P3.11 | Run formal P3 contract and design acceptance review | BLOCKED | Owner signs off ERD, migration, API, errors, evidence states, UX and threat/privacy plan with unresolved issues recorded |

**P3 exit:** A **signed-off**, test-backed domain, data, API, error, security and first-journey specification. A good synthetic CI run is important evidence, but does not mean real identity, usage rights or production migration has been accepted.

### P4 | Database, curated ingestion and backend APIs | Weight 16% | Recorded completion 0%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P4.1 | Implement relational constraints and migration runner | VERIFIED | Current synthetic SQLite v1–v3 constraints, checksum history, transaction rollback and preserved investigation tests pass |
| P4.2 | Implement versioned and validated investigation HTTP contract | VERIFIED | Synthetic same-origin API accepts permitted input and rejects malformed/conflicting/unauthorised requests |
| P4.3 | Join the existing pure matcher to curated SQL records | VERIFIED | End-to-end fixture run returns actual stored synthetic transactions, not hand-entered output totals |
| P4.4 | Store, check and reopen frozen comparable evidence | VERIFIED | Saved JSON, transaction IDs, snapshot IDs and cents remain consistent in current running process |
| P4.5 | Implement production-appropriate durable database | OPEN | Data survive clean restart, selected migrations are tested on backup/recovery and access is bounded |
| P4.6 | Implement idempotent source-to-curated import | OPEN | Re-importing one authorised data build avoids duplicate sale/property records and tracks exclusions |
| P4.7 | Resolve real buyer properties without unsupported guesses | BLOCKED | Approved address/parcel/building resolver and clear ambiguous/not-found outcomes tested against allowed records |
| P4.8 | Implement time-valid evidence and source refresh handling | BLOCKED | Revisions, retired builds and as-of limitations are explicit; old saved results remain reproducible |
| P4.9 | Finalise API stability, error safety and operational boundaries | PARTIAL | Contract/response compatibility, safe errors, safe query handling and deployment-specific limits reviewed |
| P4.10 | Run persistent database/API acceptance | OPEN | Restart/reopen, migrations, duplicate import, excluded sales and insufficient property flow pass against durable storage |

**P4 exit:** A durable, safe, source-aware backend supporting real permitted data or a clearly scoped synthetic-only publicly labelled mode. In-memory fixture storage alone does not satisfy the phase.

### P5 | Browser investigation experience | Weight 16% | Recorded completion 0%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P5.1 | Establish workspace/navigation and buyer entry flow | PARTIAL | Owner agrees actual user journey, hierarchy, layout and navigation; teal prototype is not final brand approval |
| P5.2 | Address search, ambiguous candidate selection and validation | VERIFIED | Synthetic browser asks for explicit parcel choice and prevents accidental previous-property submission |
| P5.3 | Investigation result and comparable evidence cards | VERIFIED | Browser displays source-backed synthetic prices, selected comp count, dates and no numeric valuation |
| P5.4 | Buyer-reported asking price and source attribution | PARTIAL | Every displayed value has clear user/sale/provenance status and cannot be mistaken for live listings |
| P5.5 | Differences and comparison-quality explanations | PARTIAL | User sees relevant area, sale recency, geography, ranking, exclusions and evidence limitations rather than only prices |
| P5.6 | Complete supported, exploratory, unknown and error states | PARTIAL | Manual and browser checks cover loading, empty, fallback warning, no data and safe recovery from a failed request |
| P5.7 | Responsive, accessible browser acceptance | OPEN | Keyboard-only, named controls, visible focus, mobile/reflow, contrast and screen-reader status tests plus owner UX review |
| P5.8 | Real-permitted market coverage and source explanation | BLOCKED | UI accurately states supported geography, as-of caveats and field-level reuse restrictions |
| P5.9 | Approve final buyer workflow, styling and information hierarchy | BLOCKED | Owner reviews tasks with one supported and one insufficient case; branding/map remains optional pending separate evidence |

**P5 exit:** A buyer can independently select a property, investigate eligible historical sales, understand why results are available or unavailable and act on the limitations, on the actual backend.

### P6 | Save, shortlist, compare and decide | Weight 12% | Recorded completion 0%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P6.1 | Save/reopen one synthetic investigation | VERIFIED | Current process reopens a frozen UUID-backed investigation; results disappear on process shutdown |
| P6.2 | Define shortlist and membership schema | PARTIAL | Proposed shortlist tables exist; final owner/session, access and note rules remain open |
| P6.3 | Build durable save and restore across restarts | OPEN | At least two different properties remain available after restarting the supported application |
| P6.4 | Add and remove shortlist entries with notes | OPEN | Notes and user labels are editable without modifying original recorded sale evidence |
| P6.5 | Build two- or three-property side-by-side view | OPEN | Each saved enquiry has a separate asking price, evidence status, comparable count and matching rules |
| P6.6 | Preserve weak-evidence and excluded properties in shortlist | OPEN | Insufficient/out-of-coverage enquiries can be saved and fairly compared without a fake valuation |
| P6.7 | Keep immutable evidence/provenance alongside mutable notes | OPEN | Reopen retains source/rule versions and archived result while user decisions/notes evolve separately |
| P6.8 | Decide safe access and optional export/report rules | BLOCKED | Owner accepts user storage/auth/retention model; export includes only fields approved for disclosure |
| P6.9 | Full returning-buyer comparison acceptance | OPEN | New session opens two saved homes, compares evidence and notes, and demonstrates unsupported-case honesty |

**P6 exit:** A real **Investigate → Compare → Decide** workflow with two or three reopenable properties, notes and defensible frozen evidence. The current transient one-property save does **not** satisfy P6.

### P7 | Cross-layer correctness, privacy and readiness | Weight 8% | Recorded completion 0%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P7.1 | Automated regression across Python, SQL, HTTP and browser | VERIFIED | Current synthetic CI includes 148 Python and 7 Chromium checks at the last corrected v3 code revision |
| P7.2 | Validate hostile/invalid/unsupported requests | PARTIAL | Input validation, same-origin guards, error contracts and non-fabrication are checked and extended to real deployment assumptions |
| P7.3 | Prove evidence integrity and migration rollback | PARTIAL | Synthetic hash/snapshot/cents guards and v1–v3 upgrade safety tested; production backup/restore still absent |
| P7.4 | Test historical leakage, duplicate sales and source revision | PARTIAL | Extend research invariants to accepted end-to-end imports and dated data builds |
| P7.5 | Accessibility, responsiveness and buyer failure recovery | OPEN | Record browser-based and owner-accepted results for keyboard, screen-reader, reflow and error recovery |
| P7.6 | Authentication/privacy/retention and secrets review | BLOCKED | Access control follows actual user-data design; no private property/user records or secrets in public Git/CI |
| P7.7 | Load, rate, recovery and operational monitoring checks | OPEN | Representative latency, resource ceilings, backup drill and clear failure/runbook criteria recorded |
| P7.8 | Licence, attribution and source-time release audit | BLOCKED | Permitted fields, display mode and honest historical availability approved for intended deployment |
| P7.9 | Full user journey and release-readiness sign-off | BLOCKED | Separate P7 acceptance suite passes against release-like storage, APIs and browser; owner approves readiness |

**P7 exit:** A reproducible and verified **release candidate**, with privacy/security/rights gates satisfied. CI-verified synthetic fixtures are not the same thing as a release security review.

### P8 | Deployment, credible demonstration and recruiter handoff | Weight 6% | Recorded completion 0%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P8.1 | Decide public demonstration mode and data | BLOCKED | Owner approves licensed permitted field display or a clearly marked fabricated fixture-only demo |
| P8.2 | Provide reproducible clean setup and deployment config | OPEN | A clean environment boots the accepted app and database without manual secret copying |
| P8.3 | Configure authorised hosting and safe endpoints | OPEN | Deployment uses reviewed network/auth/configuration; no localhost-only fixture WSGI accidentally exposed publicly |
| P8.4 | Demonstrate the complete buyer decision journey | OPEN | Add/restore two homes, inspect eligible comparables and weakness warnings, compare and save notes |
| P8.5 | Publish clear architecture, data dictionary and evidence lineage | PARTIAL | Existing docs are condensed into an accurate reviewer-friendly diagram, API overview and limitations |
| P8.6 | Prepare technical recruiter walkthrough and failure demonstration | OPEN | Explain a SQL join, matcher eligibility, one blocked data condition and an automated regression test |
| P8.7 | Final project README, portfolio links and demo recording | OPEN | User can follow documented steps; video/screenshots show actual permitted, working features |
| P8.8 | Owner acceptance, integration and release handoff | BLOCKED | Approved P7 readiness, reviewed \`main\` merge, correct demo URL/artifacts and final handoff record |

**P8 exit:** A recruiter can try or watch the completed **Investigate → Compare → Decide** application and independently inspect a truthful code/test/evidence story. No deployment or release has yet been authorised.

### Critical path and workable parallel tracks

1. **Decisions first (P0/P3):** Accept exact MVP buyer journey, real pilot coverage, source rights/display approach, address→parcel→building handling, v0.3 contract boundaries, production storage and security assumptions. A synthetic-only portfolio demonstration is a legitimate *proposal* if rights block real property display, but its release still needs approval.
2. **Research/data risk in parallel (P1/P2):** Quantify exclusions/drift, investigate as-of availability and defensible sales, evaluate fallback honestly, and establish the permitted input/output dataset. These external-evidence tasks may block public real-data claims even when software is ready.
3. **Build cohesive P4/P5 slices:** A durable curated property record → server investigation → evidence/abstention UI; migrate/version safely and verify each slice in both backend and Chromium. P4 and P5 keep **separate gates**, even though implementation overlaps.
4. **Complete P6 before calling this a flagship product:** Persist two or three enquiries and notes, side-by-side compare, reopen frozen source/rule evidence and preserve insufficient cases.
5. **Treat P7 and P8 as independent release gates:** Security, rights, accessibility, performance, safe deployment and portfolio walkthrough. A green development build is not public release authorisation.

**Suggested first acceptance review (next project session):** P3.1/3.2 domain and candidate identity, P3.3/3.4 HTTP and errors, P3.5/3.6 evidence/money, P3.7 migration, P3.8/3.9 stack/security/UX, then P3.10 rights/real-market dependencies and P3.11 formal sign-off. Document accepted, accepted-for-fixture-only, deferred and rejected aspects separately. Complete only the decisions supported by evidence; do not assert real field permissions or historical point-in-time data without proof.

**Scoring rule:** Existing P0–P8 stage weights, completion estimates and **22.8%** overall baseline do not change from this breakdown alone. Subitem statuses are *not numeric percentages*. At each milestone review, revisit the phase's exit gate, inspect exact commit/CI and dated research/owner evidence, then update both this roadmap and [CHECKPOINT.md](CHECKPOINT.md) with a defensible completion estimate and any remaining blocked items. Do not add a second spreadsheet or independent score ledger unless explicitly approved.

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

**Evidence:** High-level product brief and invariants exist. Synthetic-only P3 SQLite, HTTP, UI and test candidate is integrated at [`e8b8f70`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/e8b8f70de2bb10fd61b9cec9cc1d12aabdc6cfef) with [125-test successful CI](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45059455620). Production architecture and schemas, final buyer input and graphical browser flow remain unapproved.

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

1. **Now P3:** Review the integrated fixture-only contracts and ERD, validate the separate guard patch when authorised, and run a real graphical supported/insufficient/reopen journey. Preserve open buyer-input and rights decisions.
2. **Then P4/P5 overlapping vertical slices:** Introduce compatible curated-build ingestion/storage and the smallest browser-backed query, evidence and error interactions. Test against controlled fixtures; accept P4 and P5 separately.
3. **Next P6:** Persist multi-property notes and shortlist/reopen/side-by-side comparison with frozen rule/source evidence.
4. **Throughout:** Continue P0-P2 source quality and rights review; run risk-focused security, migrations, rollback and error checks. P7 is independent readiness; P8 is separately approved release.
5. Defer speculative AI valuation, wholesale framework changes and public record display until evidence and permissions justify them.

## Evidence and reporting policy

**Verified as of 22 November 2026:** GitHub Actions [run 45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782); [Phase 2 retrospective results](research/PHASE2_CLOUD_AUDIT_RESULTS.md); [project checkpoint](CHECKPOINT.md).

**Progress tracking:** On every substantial accepted milestone, update this file's stage figures, explain evidence and changed assumptions, and update `docs/CHECKPOINT.md`. Document rejected experiments rather than reporting them as successful features. No automatic %-increase per commit or test count. The original House Price Intelligence exploratory roadmap is preserved at [docs/archive/INITIAL_ROADMAP_2026-11-22.md](archive/INITIAL_ROADMAP_2026-11-22.md).
