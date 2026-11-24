# House Price Intelligence: P0–P8 phase-gated delivery plan

**Established:** 22 November 2026. **Delivery-process extension approved:** 23 November 2026. **Planning status:** P0-P8 weights and exit gates retained. **Current owner-authorised milestone estimate:** 24 November 2026, **71.4% weighted MVP progress** (previous 66.5%; initial 22.8%).

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
| P0 | Product discovery, supported buyer/market, feasibility | 6% | 92% | 5.5 pts |
| P1 | Reproducible ingestion, cleaning, historical joins, provenance | 12% | 88% | 10.6 pts |
| P2 | Explainable comparable-selection and evaluation | 14% | 65% | 9.1 pts |
| P3 | Product contracts, domain model, architecture decisions | 10% | 88% | 8.8 pts |
| P4 | Database, ingestion-to-storage, backend API | 16% | 78% | 12.5 pts |
| P5 | Browser property investigation experience | 16% | 65% | 10.4 pts |
| P6 | Saved investigations, shortlist, side-by-side comparison | 12% | 85% | 10.2 pts |
| P7 | Integrated quality, rights, security and operational readiness | 8% | 50% | 4.0 pts |
| P8 | Deployment, credible demo, documentation and portfolio handoff | 6% | 5% | 0.3 pts |
| **Total** | **Bounded flagship MVP** | **100%** | **71.4% weighted** | **71.4 pts** |

## 24 November 2026: Production Runtime Integration V1 milestone reassessment

Verified application [240f5ce](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/240f5cefc3e6f1794118a71db881c0bf279b07ab): all eight push/PR workflows passed. [Runtime push](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45353116372) and [PR](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45353122394) each passed three integrated scenarios: PostgreSQL versioned import/frozen evidence, authenticated HTTP isolation/concurrency/restart, and two-context Chromium saved-note flow. Four concurrent additions to one shortlist produced three successes and one conflict; cross-owner reads, writes, map and association were denied. No-auth and missing-Origin requests refused; runtime source writes denied. [Regression push](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45353116287) and [PR](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45353122449) passed 189 Python and 16 legacy browser tests; [React push](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45353116101) and [PR](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45353122521) passed 33 browser tests; [PostgreSQL compatibility push](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45353116161) and [PR](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45353122451) passed five tests. Total 246 test executions across distinct suites at this application head, plus nine earlier cohort safeguards (not rerun). No duplicate PR counting.

| Stage | Previous | Revised | Evidence and remaining constraint |
| --- | ---: | ---: | --- |
| Architecture | 80% | 88% | Actual loopback PostgreSQL HTTP runtime, low-privilege login, transaction-local fictional identity and bounded pool; production provider, formal security/hosting approval remain open |
| Backend | 65% | 78% | Existing canonical API against PostgreSQL, revision importer and restart preservation verified; no real adapter, live source build switch or production deployment |
| Buyer workflow | 75% | 85% | Two fictional authenticated contexts, owner isolation, concurrent shortlist limit and saved notes verified; real identity, retention, final UX approval remain |
| Quality | 40% | 50% | Eight successful workflows, integrated ownership/concurrency/restart tests; production fault injection, performance, operational security, data rights and final acceptance remain |

P0/P1/P2/P5/P8 unchanged. PostgreSQL importer uses a separate disposable database, not buyer-runtime revision switching; HTTP Basic is a fictional loopback harness, not production authentication. No actual provider, real-data disclosure or deployment. Weighted estimate 66.5% to **71.4%**, +4.9 percentage points (rounded). All phase exit gates remain open. No extra credit for documentation. See [runtime contract](engineering/PRODUCTION_RUNTIME_V1.md).

## 24 November 2026: RD1–RD7 verified milestone reassessment (historical baseline)

The owner authorised bounded live cohort research and synthetic ingestion/disclosure implementation, with progress reassessment after verification. Application commit [a24ce43](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/a24ce43f5d97adf6af50646e9430ea38dfa459d1). [Python regression job](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45351485580) passed 189 Python tests including seven new ingestion/guard scenarios; [React push](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45351485778) and [PR](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45351492795) passed 33 browser tests; [PostgreSQL push](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45351485518) and [PR](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45351492770) passed five existing compatibility tests. Verify remaining full regression workflow results separately.

[Exact cohort audit](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45351485804) at a24ce43 ran 9 offline safeguards and replayed 3,539 sales, 39,401 building rows, 273 Class 203 sales, 262 distinct PIN/prior-year keys. All 262 had one nonblank address row, zero missing/blank/multiple, zero shared normalised labels among same-year single-row cohort keys. Metadata stable within run. Extracted 2026-11-24 07:53:33 UTC; source update epochs wvhk-k5uv 1794745762, x54s-btds 1794760638, 3723-97qp 1794745694. Counts coincide with previous audit; not proof of identical membership, market-wide uniqueness, physical building identity or historical availability. No property-level output.

| Stage | Previous | Revised | Evidence and remaining constraint |
| --- | ---: | ---: | --- |
| Discovery | 90% | 92% | Exact cohort address coverage measured; rights and final market still blocked |
| Data | 80% | 88% | Bounded replay, identity counts, synthetic manifests, idempotence and conflict rejection; real import and as-of unproven |
| Architecture | 75% | 80% | Candidate version-specific address resolution and default-deny source/field guard; production auth and approved identity/rights still open |
| Backend | 55% | 65% | Atomic canonical SQL candidate import, separate revisions and old frozen investigation/notes preserved; no production importer/runtime switch |
| Quality | 35% | 40% | New negative tests and actual source safeguards; release security, operational controls and full acceptance outstanding |

P2, P5, P6 and P8 unchanged: no independent comparable accuracy validation, new buyer UI, production account flow or release. Weighted estimate 62.9% → **66.5%**, +3.6 percentage points (rounded). No phase exit closes. Real property fields remain disabled; synthetic import candidate is isolated, not a deployed PostgreSQL importer. Indicative 70.1% target not awarded because source rights, production import/identity and independent evaluation remain open. See [RD contract](engineering/REAL_DATA_READINESS_V1.md).

## 24 November 2026: prior owner-authorised milestone reassessment (historical 62.9% baseline)

Evidence baseline: development [1cedf378e806f5fafc18639ba72207a70f2b4195](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/1cedf378e806f5fafc18639ba72207a70f2b4195). Six push/PR workflows passed: [regression](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45348798465), [React](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45348798449), [PostgreSQL](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45348798707), [PR regression](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45348805722), [PR React](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45348805701), [PR PostgreSQL](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45348805672). 182 Python + 16 legacy browser + 33 React + 5 PostgreSQL tests passed at this head; 4 address safeguards and the aggregate-only audit passed at earlier commit c6a16aa ([run](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45348627334)), unchanged audit code. 240 test executions across these distinct suites, not doubled for PRs. No new feature is credited for this documentation commit.

| Stage | Basis for partial credit | Remaining gate (all open) |
| --- | --- | --- |
| Discovery (90%) | Existing scope and source research; new bounded address metadata and aggregate results | Final market, rights, permitted release decision |
| Data (80%) | Prior bounded extraction, joins, exclusions and aggregate-address safeguards | Exact cohort identity, idempotent import, source-time and revision policy |
| Intelligence (65%) | Canonical matching, deterministic abstention and frozen exact-cent source evidence across integrated synthetic services | Independent holdout, real source-time provenance, similarity evaluation |
| Architecture (75%) | Owner provisionally accepted P3.1–P3.7 for synthetic scope; PostgreSQL candidate approved, tested; integrated UX | Production authentication, access/hosting, real identity/rights, final sign-off |
| Backend (55%) | Versioned SQL/HTTP, durable SQLite, PostgreSQL service parity and actual dump/restore | Curated real import, versioned refresh, concurrent production runtime and access |
| Frontend (65%) | React five-view workspace, history, dossiers, optional fictional MapLibre, responsive/keyboard checks | Actual real-data journey, accessibility and final owner UX |
| Shortlist (75%) | Saved notes, membership, comparison, restart, draft recovery and fictional ownership isolation | Integrated authentication/retention, final returning-buyer acceptance |
| Quality (35%) | Cross-layer regression, tamper refusal, migration recovery, ownership checks | Real data/time/rights, threat review, concurrency/load, operational and full accessibility acceptance |
| Release (5%) | Reproducible local setup, technical docs and actual screenshots | Approved demo mode, hosting, recruiter materials and release |

Reassessment moves the historical 22.8% baseline to **62.9% (+40.1 percentage points)**. It recognises accumulated, verified partial deliverables rather than waiting for whole-stage sign-off. These are subjective engineering planning estimates for the same bounded MVP, not measured labour, an acceptance percentage, or production readiness. No phase exit closes; the definition of done and conditional exclusion of ML remain unchanged. The owner authorised this reassessment, not new implementation, real data display or deployment. At each meaningful verified milestone reconcile both roadmaps and checkpoint; explicitly record prior/new score, evidence, unresolved gates and no-change where warranted. Do not give automatic credit for commits/tests alone.

## Phase-governed, vertical-slice delivery directive (23 November 2026)

Apply the [eight-step engineering lifecycle](engineering/LEAN_ENGINEERING_DIRECTIVE.md) proportionately to meaningful work. **Keep P0-P8 stage meanings, weights, acceptance and progress independent from implementation order.**

- **P3 is the immediate gate:** Review the current synthetic **address-candidate/PIN, parcel-only** domain and v0.3 HTTP/SQL/API contract, errors, v1–v3 migrations and hosted browser journey. Passing fixture CI alone is not design, rights or production contract acceptance.
- **P4/P5 cross-layer slices are already synthetically implemented and verified, but P3 acceptance remains pending:** Assess browser -> HTTP -> service -> curated SQLite -> unchanged matcher, including supported/insufficient/unknown cases. Any further production-oriented P4/P5 work still requires scoped approval. Backend P4 and browser P5 retain **distinct exit tests and completion credit**.
- **P6 synthetic journey is integrated and verified, but not phase-accepted:** Two or three fictitious properties, mutable notes, immutable evidence and opt-in restart recovery now pass browser/SQLite tests. Real access/retention, final owner UX, authorised data and full P6 acceptance remain open.
- **P0-P2 unresolved gates run in parallel:** Source rights, joins, historical publication time, leakage and independent comparable evaluation remain open while synthetic software is built.
- **P7 independently accepts integrated readiness; P8 requires authorised release.** Error handling, safe coding, privacy and security start with architecture and continue at every stage rather than being deferred until P7.

Classify each deliverable explicitly as **implemented, verified, integrated, accepted or released**. High-risk multi-layer changes should use compatible expansion, reproducible migration, controlled switching and recovery checks. Partial phase credit requires demonstrable, verified meaningful deliverables and an evidence-backed milestone review, not code quantity, test count or a documentation update. Full phase acceptance requires its exit gate.

## Granular deliverable and acceptance matrix (planning proposal, 23 November 2026)

**Purpose:** This is the task-level execution map for the existing P0–P8 stages, not a second roadmap, a new phase system or permission to change acceptance percentages. It is based on the [product brief](product/PRODUCT_BRIEF.md), [source register](research/SOURCE_REGISTER.md), [research audits](research/PHASE2_CLOUD_AUDIT_RESULTS.md), [P3 application contract](engineering/P3_APPLICATION_CONTRACT.md), [decisions](DECISIONS.md) and the current [development checkpoint](CHECKPOINT.md). The current stage summary and **71.4%** weighted assessment remain authoritative until the next evidence-backed milestone review. Each ID can be tracked independently as implementation advances.

**Progress vocabulary for this matrix:**

- **RESEARCH:** Documentary evidence, pilot analysis or a source survey exists. It is **not** a signed-off product deliverable.
- **VERIFIED:** Working implementation has relevant automated evidence on the **development** branch, generally synthetic only. This does **not** imply production readiness or owner acceptance.
- **PARTIAL:** Some design, code or evidence exists, but the deliverable described in its acceptance column is incomplete.
- **OPEN:** No completed delivery evidence yet.
- **BLOCKED:** Cannot be responsibly accepted before a named external decision, data permission or independent proof.

**Every item must eventually be accompanied by:** concrete output or code reference, the exact tested commit/CI or dated research evidence, owner review where necessary, and its resulting state: *proposed → implemented → verified → integrated → accepted → released*. For future progress reviews, record both **candidate implementation** and **accepted phase credit**. A long checklist is not itself evidence of completion. The historical Phase 0–2 audits remain distinct from delivery stages P0–P2.

### P0 | Buyer, market and product feasibility | Weight 6% | Recorded completion 92%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P0.1 | Define buyer decision and narrow value proposition | RESEARCH | Owner accepts Investigate → Compare → Decide for a single buyer comparing two or three homes, not a listings marketplace |
| P0.2 | Define explicit first-MVP inclusion/exclusion list | PARTIAL | Owner approves flagship features and non-goals, including conditional-only ML and no unverified live listings |
| P0.3 | Research one candidate geography and property segment | RESEARCH | Record market, source IDs, eligible-sale counts, supported class and limitations for the pilot |
| P0.4 | Validate source availability and property-entry feasibility | PARTIAL | Bounded exact township 17/Class 203 current-source replay: 262 of 262 keys had one nonblank address row; market-wide identity/rights not approved |
| P0.5 | Review field-by-field data rights, privacy and attribution | BLOCKED | Written reuse/display decision for each required source/field; define synthetic-only fallback if needed |
| P0.6 | Approve final first-market/class and intended buyer scenario | BLOCKED | Owner signs off market and class or documents a deliberate no-go/pivot with reasons |
| P0.7 | Issue bounded feasibility and release-path decision | BLOCKED | A go/no-go record reconciles coverage, quality, legal permissions, cost and the permitted demo mode |

**P0 exit:** Approved scope, first supported market/class, source register, field policy and a clear permitted release approach. Current evidence: Evanston township 17 and Class 203 are **research pilot candidates**, not permanent geography or public-display approval.

### P1 | Source extraction, cleaning and historical data | Weight 12% | Recorded completion 88%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P1.1 | Source inventory and schema/field register | RESEARCH | Dataset IDs, field definitions, source URLs, licence status and schema metadata captured |
| P1.2 | Deterministic bounded extraction in CI | RESEARCH | Re-running the documented query returns reproducible counts or explicitly explains any dataset revision |
| P1.3 | Data type, null, duplicate and exclusion policies | PARTIAL | Automated quality log tracks conversions, exclusions and source changes, including historical numeric parser issue |
| P1.4 | Preserve transaction, parcel, building and card grain | PARTIAL | Exact-cohort parcel/year and synthetic snapshot-specific address ambiguity verified; real building identity remains unverified |
| P1.5 | Historical as-of availability and late/backfilled changes | BLOCKED | Archived snapshot/publication evidence or an explicitly conservative non-as-of policy is reviewed and implemented |
| P1.6 | Versioned source manifest, drift/re-run comparison | PARTIAL | Metadata compared before/after bounded cohort replay; synthetic content/build manifests and revision tests passed; real refresh/drift history remains |
| P1.7 | Idempotent curated application-ready import | PARTIAL | Synthetic isolated canonical v3 import idempotence, stable identifiers and atomic conflicts verified; real permitted import still open |
| P1.8 | Publisher-safe output and operational reproducibility | PARTIAL | Aggregate-only city and exact cohort audits passed; no raw rows emitted; reuse rights remain open |

**P1 exit:** Reproducible ingestion, stable keys, explained exclusions, source lineage and legally safe curated storage. Research pilot counts include 3,539 sales, 39,401 building records and 1,285 accepted historical joins; those alone do not prove complete historical or legal validity.

### P2 | Explainable comparable-sales intelligence | Weight 14% | Recorded completion 65%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P2.1 | Deterministic eligibility and exclusion rules | RESEARCH | Earlier-only sales, correct class/township, area tolerance, valid window and excluded shared transactions tested |
| P2.2 | Prevent duplicate property/document comparables | RESEARCH | Each selected comparable is unique under defined PIN/document/source grain and explainable |
| P2.3 | Same-neighbourhood selection and stable ranking | RESEARCH | Rank and explain relevant previous sales without using sale price as a ranking input |
| P2.4 | Evaluate bounded geographic fallback | PARTIAL | Compare error, support and failure risks independently; current 2 km fallback must remain labelled exploratory |
| P2.5 | Validate insufficiency and abstention policy | PARTIAL | Canonical matcher abstention and zero-evidence states verified across SQLite/React and PostgreSQL candidate; real holdout remains open |
| P2.6 | Test better similarity and sale-quality factors | OPEN | Evidence-backed candidate features, exclusion reasons and controlled paired ablations recorded |
| P2.7 | Independent later chronological holdout | OPEN | A future withheld period measures coverage/error and protects against leakage or reuse of test cases in policy tuning |
| P2.8 | Prove time-valid source provenance and interpretability | BLOCKED | Every displayed sale has a traceable, permitted record and appropriate as-of/revision limitation |
| P2.9 | Accept evidence-only versus price-estimation boundary | BLOCKED | Owner approves when fallback may be displayed and how unsupported predictions/weak evidence are labelled |

**P2 exit:** Reliable, explainable comparable selection with a justified fallback and independent assessment. **Known limitation:** on the 17 fallback cases, exploratory 2 km retrospective MAE was about $209,471, worse than township comparison at about $192,153. Do **not** present the sample median as a validated house-price prediction.

### P3 | Domain model, service contracts and architecture | Weight 10% | Recorded completion 88%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P3.1 | Define inquiry, sale, parcel, building, assessment and evidence entities | VERIFIED | Owner accepted provisional synthetic ERD and grain; real source grain remains open |
| P3.2 | Define address resolution and ambiguous identity | VERIFIED | Owner accepted provisional synthetic parcel-only identity; real address/building resolver remains open |
| P3.3 | Define buyer input and server-owned fields | VERIFIED | Owner accepted provisional synthetic input/validation contract; real input provenance remains open |
| P3.4 | Define status/error/abstention contract | VERIFIED | Canonical status/error/abstention contract also runs on fictional PostgreSQL HTTP; production acceptance remains open |
| P3.5 | Define provenance, snapshots and frozen evidence | VERIFIED | Owner accepted provisional synthetic frozen evidence contract; historical availability remains open |
| P3.6 | Define exact-money and currency representation | VERIFIED | Owner accepted provisional synthetic integer cents and decimal USD contract; production limits remain open |
| P3.7 | Define schema evolution and recovery method | VERIFIED | Owner accepted provisional synthetic migration contract; SQLite restart and PostgreSQL candidate migration/restore verified; production plan open |
| P3.8 | Select application stack, hosting and access approach | PARTIAL | PostgreSQL loopback HTTP runtime, pooled request transactions and fictional identity verified; public hosting/provider not approved |
| P3.9 | Define secure, permission-aware buyer experience | PARTIAL | Fictional authenticated React workspaces and isolation tested; production privacy, security and owner UX review remain |
| P3.10 | Decide real geography/identity/as-of/field-rights boundaries | BLOCKED | Exact cohort address coverage measured, synthetic parcel-only resolver and default-deny field policy tested; real identity/field rights/as-of remain unapproved |
| P3.11 | Run formal P3 contract and design acceptance review | BLOCKED | Owner signs off ERD, migration, API, errors, evidence states, UX and threat/privacy plan with unresolved issues recorded |

**P3 exit:** A **signed-off**, test-backed domain, data, API, error, security and first-journey specification. A good synthetic CI run is important evidence, but does not mean real identity, usage rights or production migration has been accepted.

### P4 | Database, curated ingestion and backend APIs | Weight 16% | Recorded completion 78%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P4.1 | Implement relational constraints and migration runner | VERIFIED | Current synthetic SQLite v1–v3 constraints, checksum history, transaction rollback and preserved investigation tests pass |
| P4.2 | Implement versioned and validated investigation HTTP contract | VERIFIED | Synthetic same-origin API accepts permitted input and rejects malformed/conflicting/unauthorised requests |
| P4.3 | Join the existing pure matcher to curated SQL records | VERIFIED | End-to-end fixture run returns actual stored synthetic transactions, not hand-entered output totals |
| P4.4 | Store, check and reopen frozen comparable evidence | VERIFIED | Fixture JSON, transaction IDs, snapshot IDs and exact cents remain consistent in memory **and in opt-in trusted local SQLite files** after restart |
| P4.5 | Implement production-appropriate durable database | PARTIAL | PostgreSQL HTTP runtime and process restart verified, separate prior dump/restore; production infrastructure and recovery review open |
| P4.6 | Implement idempotent source-to-curated import | PARTIAL | Shared synthetic importer verified on SQLite and separate PostgreSQL database; real adapter and live revision switch remain |
| P4.7 | Resolve real buyer properties without unsupported guesses | BLOCKED | 262/262 cohort key address rows present, synthetic snapshot-specific ambiguity tested; permitted real resolver not implemented |
| P4.8 | Implement time-valid evidence and source refresh handling | PARTIAL | PostgreSQL synthetic revision builds preserve frozen evidence; buyer-runtime source switching, actual refresh and as-of open |
| P4.9 | Finalise API stability, error safety and operational boundaries | PARTIAL | Bounded pool, transaction-local identity, same-origin mutations and sanitised error boundary implemented; fault injection/deployment limits open |
| P4.10 | Run persistent database/API acceptance | PARTIAL | Actual authenticated HTTP and PostgreSQL process restart, concurrent membership, note preservation and React flow verified; real access/import acceptance open |

**P4 exit:** A durable, safe, source-aware backend supporting real permitted data or a clearly scoped synthetic-only publicly labelled mode. In-memory fixture storage alone does not satisfy the phase.

### P5 | Browser investigation experience | Weight 16% | Recorded completion 65%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P5.1 | Establish workspace/navigation and buyer entry flow | PARTIAL | Integrated five-view React shell and functional navigation verified; final owner UX remains |
| P5.2 | Address search, ambiguous candidate selection and validation | VERIFIED | Synthetic browser asks for explicit parcel choice and prevents accidental previous-property submission |
| P5.3 | Investigation result and comparable evidence cards | VERIFIED | Browser displays source-backed synthetic prices, selected comp count, dates and no numeric valuation |
| P5.4 | Buyer-reported asking price and source attribution | PARTIAL | Dossier separates asking price, sale cents and provenance; real-source permitted display not established |
| P5.5 | Differences and comparison-quality explanations | PARTIAL | Dossier and linked fictional map convey evidence and limitations; real geographic source and comparison quality remain open |
| P5.6 | Complete supported, exploratory, unknown and error states | PARTIAL | Synthetic ambiguity, abstention, network and optional map failure recovery verified; release-like coverage remains |
| P5.7 | Responsive, accessible browser acceptance | PARTIAL | Responsive 320px, reduced-motion, keyboard navigation and focus tested; contrast/screen-reader and owner review remain |
| P5.8 | Real-permitted market coverage and source explanation | BLOCKED | UI accurately states supported geography, as-of caveats and field-level reuse restrictions |
| P5.9 | Approve final buyer workflow, styling and information hierarchy | BLOCKED | Owner reviews tasks with one supported and one insufficient case; branding/map remains optional pending separate evidence |

**P5 exit:** A buyer can independently select a property, investigate eligible historical sales, understand why results are available or unavailable and act on the limitations, on the actual backend.

### P6 | Save, shortlist, compare and decide | Weight 12% | Recorded completion 85%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P6.1 | Save/reopen one synthetic investigation | VERIFIED | Frozen UUID-backed investigation reopens in memory and across restart with explicit `--fixture-db`; default memory-only demo remains temporary |
| P6.2 | Define shortlist and membership schema | PARTIAL | Integrated fictional two-owner HTTP and RLS with transaction-local identity verified; real provider and retention remain |
| P6.3 | Build durable save and restore across restarts | VERIFIED | Both SQLite and fictional PostgreSQL application process restart preserve saved evidence/shortlists; no production guarantee |
| P6.4 | Add and remove shortlist entries with notes | VERIFIED | Fixture-only add/remove and note editing preserve frozen response hash, original sale cents and comparable links |
| P6.5 | Build two- or three-property side-by-side view | VERIFIED | Real Chromium verifies aligned fictional-property asking prices, evidence statuses, eligible-sale counts, rules and no valuation; owner final visual acceptance pending |
| P6.6 | Preserve weak-evidence and excluded properties in shortlist | VERIFIED | At least one insufficient-data fictional property (0 eligible sales) remains visible alongside a three-sale property; broader real-market coverage not accepted |
| P6.7 | Keep immutable evidence/provenance alongside mutable notes | VERIFIED | Fixture notes stored separately; reopening rechecks source snapshot/role, saved cents, response hash, match rule and identity |
| P6.8 | Decide safe access and optional export/report rules | PARTIAL | Fictional HTTP Basic access and database isolation verified; real provider, retention and export policy blocked |
| P6.9 | Full returning-buyer comparison acceptance | PARTIAL | Two authenticated Chromium contexts and saved-note workflow pass; final owner UX and production access acceptance open |

**P6 exit:** An owner-accepted, responsible **Investigate → Compare → Decide** buyer workflow with two or three reopenable properties, notes, defensible evidence and appropriate data/access/retention and UX gates. The **implemented fictional-only P6 workflow** is verified, but it is not a production or formal P6 acceptance.

### P7 | Cross-layer correctness, privacy and readiness | Weight 8% | Recorded completion 50%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P7.1 | Automated regression across Python, SQL, HTTP and browser | VERIFIED | 240f5ce: 189 Python, 16 legacy browser, 33 React, five PostgreSQL compatibility, three integrated runtime scenarios; all eight workflows passed |
| P7.2 | Validate hostile/invalid/unsupported requests | PARTIAL | Missing authentication/Origin and cross-owner read/write/association denied over actual HTTP; public security validation open |
| P7.3 | Prove evidence integrity and migration rollback | PARTIAL | PostgreSQL revision import and frozen evidence verified alongside prior recovery and rollback; operational failure drills remain |
| P7.4 | Test historical leakage, duplicate sales and source revision | PARTIAL | Bounded cohort replay metadata stable; synthetic source revision/frozen evidence tests passed; chronological validation remains open |
| P7.5 | Accessibility, responsiveness and buyer failure recovery | PARTIAL | Real Chromium responsive/keyboard and map failure recovery checks; full accessibility review open |
| P7.6 | Authentication/privacy/retention and secrets review | PARTIAL | Fictional HTTP identity, low-privilege login, transaction-local owner and RLS verified; provider, sessions/retention and production security remain |
| P7.7 | Load, rate, recovery and operational monitoring checks | PARTIAL | Four concurrent adds limited to three, process restart verified; pool exhaustion/failure injection, load and monitoring open |
| P7.8 | Licence, attribution and source-time release audit | BLOCKED | Permitted fields, display mode and honest historical availability approved for intended deployment |
| P7.9 | Full user journey and release-readiness sign-off | BLOCKED | Separate P7 acceptance suite passes against release-like storage, APIs and browser; owner approves readiness |

**P7 exit:** A reproducible and verified **release candidate**, with privacy/security/rights gates satisfied. CI-verified synthetic fixtures are not the same thing as a release security review.

### P8 | Deployment, credible demonstration and recruiter handoff | Weight 6% | Recorded completion 5%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P8.1 | Decide public demonstration mode and data | BLOCKED | Owner approves licensed permitted field display or a clearly marked fabricated fixture-only demo |
| P8.2 | Provide reproducible clean setup and deployment config | PARTIAL | Reproducible local fixture startup and locked React build; production deployment config not approved |
| P8.3 | Configure authorised hosting and safe endpoints | OPEN | Deployment uses reviewed network/auth/configuration; no localhost-only fixture WSGI accidentally exposed publicly |
| P8.4 | Demonstrate the complete buyer decision journey | PARTIAL | Full synthetic buyer journey tested with real Chromium and actual screenshots; recruiter demo and release mode remain open |
| P8.5 | Publish clear architecture, data dictionary and evidence lineage | PARTIAL | Existing docs are condensed into an accurate reviewer-friendly diagram, API overview and limitations |
| P8.6 | Prepare technical recruiter walkthrough and failure demonstration | OPEN | Explain a SQL join, matcher eligibility, one blocked data condition and an automated regression test |
| P8.7 | Final project README, portfolio links and demo recording | OPEN | User can follow documented steps; video/screenshots show actual permitted, working features |
| P8.8 | Owner acceptance, integration and release handoff | BLOCKED | Approved P7 readiness, reviewed \`main\` merge, correct demo URL/artifacts and final handoff record |

**P8 exit:** A recruiter can try or watch the completed **Investigate → Compare → Decide** application and independently inspect a truthful code/test/evidence story. No deployment or release has yet been authorised.

### Critical path and workable parallel tracks

1. **Decisions first (P0/P3):** Accept exact MVP buyer journey, real pilot coverage, source rights/display approach, address→parcel→building handling, v0.3 contract boundaries, production storage and security assumptions. A synthetic-only portfolio demonstration is a legitimate *proposal* if rights block real property display, but its release still needs approval.
2. **Research/data risk in parallel (P1/P2):** Quantify exclusions/drift, investigate as-of availability and defensible sales, evaluate fallback honestly, and establish the permitted input/output dataset. These external-evidence tasks may block public real-data claims even when software is ready.
3. **Build cohesive P4/P5 slices:** A durable curated property record → server investigation → evidence/abstention UI; migrate/version safely and verify each slice in both backend and Chromium. P4 and P5 keep **separate gates**, even though implementation overlaps.
4. **Review integrated P6 for owner acceptance before calling this a flagship product:** Two/three fictional enquiries, notes, side-by-side evidence and frozen-restart reopening are code-verified. Complete missing UX, access, retention, approved source display and release-like cases.
5. **Treat P7 and P8 as independent release gates:** Security, rights, accessibility, performance, safe deployment and portfolio walkthrough. A green development build is not public release authorisation.

**Suggested next milestone:** resolve permitted release/data rights and retrospective policy, then close the controlled source-build switching and release security gaps. Production Runtime Integration V1 is verified only for fictional loopback scope. Real-data publication, provider, hosting and deployment require separate owner authorisation.

**Scoring rule:** Existing P0–P8 stage weights and exit gates remain fixed. The latest owner-authorised 24 November reassessment is **71.4%**; change estimates only at meaningful milestone reviews, not from this breakdown alone. Subitem statuses are *not numeric percentages*. At each milestone review, revisit the phase's exit gate, inspect exact commit/CI and dated research/owner evidence, then update both this roadmap and [CHECKPOINT.md](CHECKPOINT.md) with a defensible completion estimate and any remaining blocked items. Do not add a second spreadsheet or independent score ledger unless explicitly approved.

## Full process and phase exit gates

### P0: Discovery and feasibility — 6% weight; 92% estimated complete

**Goal:** Define a credible buyer decision, one supported geography and housing segment, a useful first product scope and viability boundaries.

**Evidence:** Product brief/pinnacle concept; Cook County township 17 (Evanston) candidate; official-source investigation; Class 203 research slice; real extraction and feasibility observations.

**Remaining:** Explicit owner sign-off on pilot geography/segment; source display/reuse rights, privacy and redistribution constraints; establish where user-entered properties can realistically be supported.

**Exit gate:** Approved bounded product brief, source register, class/geography decisions, permitted field display policy and a documented go/no-go decision. No claim of live listings or commercial appraisals.

### P1: Data engineering — 12% weight; 88% estimated complete

**Goal:** A repeatable extraction-to-cleaned-data pipeline with credible record grain, stable IDs and source/version lineage.

**Evidence:** GitHub Actions Phase 0/1 extraction, 3,539 recorded sales, 39,401 historical improvement records, 1,285 accepted joins and 273 Class 203 sales; numeric parser regression fixed; privacy-conscious aggregate report artifacts.

**Remaining:** Snapshot/version integrity, reproducible refresh and drift checks; schema and data dictionary review; policy for late-reported sales, historical backfills and ambiguous property identities; curated application-ready storage.

**Exit gate:** Reproducible dataset build with explicit inclusion/exclusion logs, validated grain and keys, provenance, tests for schema change and stable re-runs; raw records excluded from public repository/artifacts.

### P2: Comparable-sales intelligence — 14% weight; 65% estimated complete

**Goal:** Explainable, conservative same-market historical comparables, ranking, evidence and abstention.

**Evidence:** Phase 2 matcher, 42 offline tests across the pipeline, actual cloud evaluation: 83 Class 203 historical 2024 subjects; 66 with >=3 same-neighbourhood sales and 17 recovered by 2 km fallback.

**Remaining:** Fallback's retrospective price error is worse than township baseline on those 17 cases. More property similarity features, source-time limitations, untouched later holdout, error/coverage/abstention calibration and safe output evidence contract remain unresolved.

**Exit gate:** Deterministic eligibility and no-future-sale rules, one-property-one-comparable accounting, complete explanation/provenance, independent evaluation, justified fallback rules and truthful insufficiency response. Do not promote experimental median to a validated price estimate.

### P3: Product architecture and contracts — 10% weight; 88% estimated complete

**Goal:** Translate the research engine into explicit, testable business objects and contracts for a real application.

**Evidence:** P3.1–P3.7 provisionally accepted for synthetic scope, React and geographic evidence integrated, workspace tested, PostgreSQL candidate approved and verified. See [production readiness](engineering/PRODUCTION_READINESS_V1.md).

**Remaining:** Real address/building identity, source rights and historical availability; production authentication, pooling, concurrency, hosting and owner UX/security sign-off.

**Exit gate:** Accepted database ERD and migration plan, endpoint/request/response contract, error and unsupported states, first end-to-end journey specification, security/privacy rules and contract-test fixtures.

### P4: Backend API and database — 16% weight; 78% estimated complete

**Goal:** Running server and durable application storage connecting curated data to enquiries and evidence.

**Planned:** SQL schema and constraints; migrations; idempotent curated-data import; safe data access; validated property investigation endpoints; matcher service integration; source/version lineage; correctness integration tests.

**Exit gate:** A client can submit a supported subject, retrieve ranked and explained earlier comparable sales, retrieve truthful insufficient-data results, and recover an investigation from persisted storage. Tests demonstrate these behaviours without handwritten fake totals.

### P5: Property investigation frontend — 16% weight; 65% estimated complete

**Goal:** A usable browser experience rather than a notebook or audit dashboard.

**Planned:** Market coverage explanation, property entry/validation, asking-price field clearly user-reported, comparable cards/evidence, ranked differences and dates, transparent neighbourhood vs exploratory radius, loading/empty/failure states, responsive and accessible UX.

**Exit gate:** User completes add property -> inspect relevant historical comps -> understand why selected or why unavailable, in the browser, against the actual backend. No unsupported price claims.

### P6: Saved buyer decision workflow — 12% weight; 85% estimated complete

**Goal:** The distinctive complete micro-application experience.

**Planned:** Save and reopen at least two enquiries; per-property notes and shortlist; side-by-side comparison; recorded sale evidence linked to source/version and rule revision; simple decision report/export only where field rights permit. Authentication only if the product requires accounts.

**Exit gate:** A returning buyer can open two saved properties, compare supported evidence and notes, and reopen identical source/rule-referenced results. An insufficient-data home is still savable.

### P7: Integrated QA and readiness — 8% weight; 50% estimated complete

**Goal:** Prove the complete system is reliable, secure and honest.

**Planned:** API/database/browser end-to-end tests; malformed property submissions, duplicate/revised sales, date leakage, ambiguous joins, migration backup/recovery, accessibility, resource performance and source rights; verify no raw private records or credentials leak to Git or artifacts; monitor pipeline failures and source changes.

**Exit gate:** Accepted integration/demo journeys, reproducible clean build, documented limitations, suitable rate/resource controls and permission to expose chosen fields. Public exposure blocked if source reuse rights remain unresolved.

### P8: Release and portfolio demonstration — 6% weight; 5% estimated complete

**Goal:** Ship a coherent portfolio-quality application and explain technical decisions to recruiters.

**Planned:** Deploy only after P7; representative allowed data or unmistakably labelled synthetic/demo fixtures where public display rights are unresolved; README, architecture diagram, clean setup, demo walkthrough/video, source and QA evidence, explanation of matching/risk trade-offs; working app URL if deployment is authorized.

**Exit gate:** Reproducible installation and deployed/demo functionality: add two properties -> inspect ranked comps -> demonstrate fallback warning/abstention -> save/reopen -> compare -> explain test-backed joins and provenance.

## Conditional post-MVP branch, excluded from 100%

**M1: statistical pricing / machine learning.** Requires a credible later chronological holdout, fully time-appropriate features, strong baseline comparisons, useful accuracy and defensible uncertainty calibration. If it fails, ship without a predicted price. No forced "AI" feature.

**Deferred:** Global listing search, property photos, mortgages, multi-market expansion, notification infrastructure and professional-appraisal claims.

## Near-term execution, complexity last

1. Reconcile real-data readiness: exact cohort identity and bounded research, permitted fields, idempotent curated ingestion and disclosure guard, subject to separate authorisation.
2. Extend existing P4/P5 integrated services only after verified data/rights decisions; preserve SQLite and canonical matcher until production runtime is reviewed.
3. Complete integrated ownership/authentication, privacy, retention and final buyer UX for P6.
4. Independently verify P7 release readiness, then seek P8 release approval. No main merge, hosting or public real-data display without permission.
5. Reassess partial progress at meaningful verified milestones; do not close an exit gate prematurely or force ML into MVP.

## Evidence and reporting policy

**Verified as of 22 November 2026:** GitHub Actions [run 45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782); [Phase 2 retrospective results](research/PHASE2_CLOUD_AUDIT_RESULTS.md); [project checkpoint](CHECKPOINT.md).

**Progress tracking:** On every meaningful verified milestone review, update this file's stage figures, explain evidence and changed assumptions, and update `docs/CHECKPOINT.md`. Document rejected experiments rather than reporting them as successful features. No automatic %-increase per commit or test count. The original House Price Intelligence exploratory roadmap is preserved at [docs/archive/INITIAL_ROADMAP_2026-11-22.md](archive/INITIAL_ROADMAP_2026-11-22.md).
