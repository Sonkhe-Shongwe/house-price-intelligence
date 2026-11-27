# House Price Intelligence: P0–P8 phase-gated delivery plan

**Established:** 22 November 2026. **Delivery-process extension approved:** 23 November 2026. **Planning status:** P0-P8 weights and exit gates retained. **Current owner-authorised milestone estimate:** 24 November 2026, **87.1% weighted MVP progress** (previous 85.7%; initial 22.8%).

**26 November operational reconciliation:** Latest application a90a101 passed 10/10 workflows; 206 backend, 40 React and 47 PostgreSQL runtime tests passed, Python/npm known-advisory gates clean, 14-view automated accessibility passed. FE1–FE7 core qualified, Atlas owner-approved; fictional geographic and generated contextual PMTiles qualified. Bounded real basemap approval remains unused/deferred due to upstream extractor security. Combined actual Auth0/Neon invented save/compare and owner-observed reopen/sign-out verified; restricted roles disabled, zero sessions last independently verified. Actual combined restart/note persistence/cross-owner/old-cookie probes not independently demonstrated. Independent invented Drive recovery verified; local rekey CI passed, owner key replacement, storage/access/retention and permitted use remain outstanding. Historical focus P4/P7 private real-data readiness and P8 release after gates; current owner-directed P0 closure supersedes it. [Checkpoint](CHECKPOINT.md) is sole current task handoff. All phase gates and estimates unchanged.

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
| P0 | Product discovery, supported buyer/market, feasibility | 6% | 94% | 5.6 pts |
| P1 | Reproducible ingestion, cleaning, historical joins, provenance | 12% | 98% | 11.8 pts |
| P2 | Explainable comparable-selection and evaluation | 14% | 75% | 10.5 pts |
| P3 | Product contracts, domain model, architecture decisions | 10% | 96% | 9.6 pts |
| P4 | Database, ingestion-to-storage, backend API | 16% | 95% | 15.2 pts |
| P5 | Browser property investigation experience | 16% | 89% | 14.2 pts |
| P6 | Saved investigations, shortlist, side-by-side comparison | 12% | 95% | 11.4 pts |
| P7 | Integrated quality, rights, security and operational readiness | 8% | 83% | 6.6 pts |
| P8 | Deployment, credible demo, documentation and portfolio handoff | 6% | 35% | 2.1 pts |
| **Total** | **Bounded flagship MVP** | **100%** | **87.1% weighted** | **87.1 pts** |

## Historical milestone assessments

The [delivery milestone history](archive/DELIVERY_MILESTONE_HISTORY_2026-11-26.md) preserves the full dated 24 November assessment chain, test and research evidence, rejected estimates and rationale through the owner-approved 87.1% baseline. [Exact pre-audit roadmap](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/a90a10113bec2aaf2f4ae137537045484de1c16b/docs/P_PHASE_ROADMAP.md). All P0–P8 weights, estimates, work-package IDs, progress vocabulary, acceptance criteria and exit gates below remain governing. No new percentage approval is inferred.

## Single-phase closure directive (26 November 2026)

Owner directed P0 as the single active phase after review of concurrent delivery. Existing later-phase implementations are preserved, not restarted. Use the existing exit criteria as the definition of done; only a bounded dependency tied to a named active-phase requirement may interrupt focus. Keep optional improvements parked. A blocked requirement remains blocked; do not switch phases or inflate progress. Obtain applicable owner acceptance before closure and advance in dependency order. The [P0 Discovery and Feasibility Directive](engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md) is the active subordinate research/analysis/planning/implementation strategy, with traceability from P0-A to P0-G to P0.1-P0.7. Begin P0-A.1, not the prior P0.4-first order. Subsequent 26 November [P0-G conditional audit](engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md#26-november-2026--p0-g-independent-conditional-acceptance-audit) delivered; formal exit blocked, P0.4/6 partial and P0.5/7 blocked. Await material external evidence or applicable route decision, no P1 transition. Original criteria and estimates retained. The historical vertical-slice policy below records why prior work overlapped, not authority to continue unrelated work during P0.

## Phase-governed, vertical-slice delivery directive (23 November 2026; historical)

Apply the [eight-step engineering lifecycle](engineering/LEAN_ENGINEERING_DIRECTIVE.md) proportionately to meaningful work. **Keep P0-P8 stage meanings, weights, acceptance and progress independent from implementation order.**

- **P3 is the immediate gate:** Review the current synthetic **address-candidate/PIN, parcel-only** domain and v0.3 HTTP/SQL/API contract, errors, v1–v3 migrations and hosted browser journey. Passing fixture CI alone is not design, rights or production contract acceptance.
- **P4/P5 cross-layer slices are already synthetically implemented and verified, but P3 acceptance remains pending:** Assess browser -> HTTP -> service -> curated SQLite -> unchanged matcher, including supported/insufficient/unknown cases. Any further production-oriented P4/P5 work still requires scoped approval. Backend P4 and browser P5 retain **distinct exit tests and completion credit**.
- **P6 synthetic journey is integrated and verified, but not phase-accepted:** Two or three fictitious properties, mutable notes, immutable evidence and opt-in restart recovery now pass browser/SQLite tests. Real access/retention, final owner UX, authorised data and full P6 acceptance remain open.
- **P0-P2 unresolved gates run in parallel:** Source rights, joins, historical publication time, leakage and independent comparable evaluation remain open while synthetic software is built.
- **P7 independently accepts integrated readiness; P8 requires authorised release.** Error handling, safe coding, privacy and security start with architecture and continue at every stage rather than being deferred until P7.

Classify each deliverable explicitly as **implemented, verified, integrated, accepted or released**. High-risk multi-layer changes should use compatible expansion, reproducible migration, controlled switching and recovery checks. Partial phase credit requires demonstrable, verified meaningful deliverables and an evidence-backed milestone review, not code quantity, test count or a documentation update. Full phase acceptance requires its exit gate.

## Granular deliverable and acceptance matrix (planning proposal, 23 November 2026)

**Purpose:** This is the task-level execution map for the existing P0–P8 stages, not a second roadmap, a new phase system or permission to change acceptance percentages. It is based on the [product brief](product/PRODUCT_BRIEF.md), [source register](research/SOURCE_REGISTER.md), [research audits](research/PHASE2_CLOUD_AUDIT_RESULTS.md), [P3 application contract](engineering/P3_APPLICATION_CONTRACT.md), [decisions](DECISIONS.md) and the current [development checkpoint](CHECKPOINT.md). The current stage summary and **87.1%** weighted assessment remain authoritative until the next evidence-backed milestone review. Each ID can be tracked independently as implementation advances.

**Progress vocabulary for this matrix:**

- **RESEARCH:** Documentary evidence, pilot analysis or a source survey exists. It is **not** a signed-off product deliverable.
- **VERIFIED:** Working implementation has relevant automated evidence on the **development** branch, generally synthetic only. This does **not** imply production readiness or owner acceptance.
- **PARTIAL:** Some design, code or evidence exists, but the deliverable described in its acceptance column is incomplete.
- **OPEN:** No completed delivery evidence yet.
- **BLOCKED:** Cannot be responsibly accepted before a named external decision, data permission or independent proof.

**Every item must eventually be accompanied by:** concrete output or code reference, the exact tested commit/CI or dated research evidence, owner review where necessary, and its resulting state: *proposed → implemented → verified → integrated → accepted → released*. For future progress reviews, record both **candidate implementation** and **accepted phase credit**. A long checklist is not itself evidence of completion. The historical Phase 0–2 audits remain distinct from delivery stages P0–P2.

### P0 | Buyer, market and product feasibility | Weight 6% | Approved planning estimate 94%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P0.1 | Define buyer decision and narrow value proposition | RESEARCH | Owner accepts Investigate → Compare → Decide for a single buyer comparing two or three homes, not a listings marketplace |
| P0.2 | Define explicit first-MVP inclusion/exclusion list | PARTIAL | Owner approves flagship features and non-goals, including conditional-only ML and no unverified live listings |
| P0.3 | Research one candidate geography and property segment | RESEARCH | Official class 203 definition confirmed; canonical correction and fixed holdout verified 142 eligible 2024-2025 sales, 59 later subjects; candidate retained |
| P0.4 | Validate source availability and property-entry feasibility | PARTIAL | Cook 262/262 nonblank address candidates retained; Pinelands 409/420 unique erf-based sale-row candidates, zero verified identities; historical continuity and entry qualification open |
| P0.5 | Review field-by-field data rights, privacy and attribution | BLOCKED | Cook licences unspecified; Pinelands scoped private research approved, portal-specific reuse and buyer/hosted/commercial display, protection and disposal qualification open |
| P0.6 | Approve final first-market/class and intended buyer scenario | PARTIAL | Geography-flexible data-first selection restored; Cook historical benchmark, NYC and England/Wales leads; SA mission terminated, final locality/class and buyer scope not accepted |
| P0.7 | Issue bounded feasibility and release-path decision | BLOCKED | Conditional technical research GO; no real buyer activation/release until identity, transaction semantics, rights/protection and final scope acceptance |

**P0 exit:** Approved scope, first supported market/class, source register, field policy and a clear permitted release approach. Cook historical benchmark and Pinelands candidate study are research evidence, not final geography or public-display approval. See [owner direction](DECISIONS.md#owner-decision-end-south-african-first-mission-27-november-2026) and [current checkpoint](CHECKPOINT.md).

**26 November initial P0 closure audit (preserved baseline; execution order superseded by the comprehensive P0 directive):** P0.1 and P0.2 supported by prior owner-approved Investigate/Compare/Decide scope and explicit product non-goals; P0.3 candidate-market research sufficient at discovery level. P0.4 partial: prior 262/262 one-nonblank address result and later [four-source rehearsal](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45375702613) (142 eligible sales, 137 parcel-year keys, 59/59 later unique-token reviews) support bounded address-to-parcel resolution, not every current address or verified building. Proposed first market: Evanston township 17, historical Class 203; sales 2024-2025 and prior-year assessment 2023-2024; one owner, two or three investigated properties, USD exact completed sales distinct from asking prices; explicitly retrospective current-source data, abstain outside eligible cohort or ambiguous/missing address. No new geographic or public-display approval inferred. P0.5 blocked by field-use scope; see [source register](research/SOURCE_REGISTER.md) and [FR2 field matrix](engineering/FULL_RELEASE_QUALIFICATION_V1.md). P0.6 pending final owner market/class decision. P0.7 technical GO for candidate research; operational NO-GO for durable real intake/display/release until the existing rights and protection requirements pass. No formal closure, score change or new extraction. Resolve P0.4-7 in the relevant P0-A to P0-G workstreams; do not begin P1 while P0 remains open. The earlier narrow discovery evidence for P0.1-P0.3 remains valid; deeper customer/differentiation research is needed, not a reversal of the verified evidence.

### P1 | Source extraction, cleaning and historical data | Weight 12% | Approved planning estimate 98%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P1.1 | Source inventory and schema/field register | RESEARCH | Dataset IDs, field definitions, source URLs, licence status and schema metadata captured |
| P1.2 | Deterministic bounded extraction in CI | PARTIAL | Four-source bounded private live collection passed independent counts, terminal pages, scope and revision checks in 45375702613; one authorised collection consumed; refresh/release process open |
| P1.3 | Data type, null, duplicate and exclusion policies | PARTIAL | Actual bounded intake and exact-cent canonical persistence passed on 142 eligible sales; 59 later subjects, no change to screening or matcher; production refresh review open |
| P1.4 | Preserve transaction, parcel, building and card grain | PARTIAL | 137 actual parcel-year records persisted, 59 unique address-token reviews verified; real building identity remains unverified |
| P1.5 | Historical as-of availability and late/backfilled changes | BLOCKED | Archived snapshot/publication evidence or an explicitly conservative non-as-of policy is reviewed and implemented |
| P1.6 | Versioned source manifest, drift/re-run comparison | PARTIAL | Four actual stable revisions, external relational seal and idempotence verified in private rehearsal; multi-revision real refresh/drift history remains open |
| P1.7 | Idempotent curated application-ready import | PARTIAL | Actual private PostgreSQL import of 142 sales, 137 parcel-year keys and 4 snapshots passed with idempotence/seal; production durable import and source-time validation open |
| P1.8 | Publisher-safe output and operational reproducibility | PARTIAL | FR aggregate-only funnel and four metadata snapshots verified; no raw output; reuse rights remain open |

**P1 exit:** Reproducible ingestion, stable keys, explained exclusions, source lineage and legally safe curated storage. Research pilot counts include 3,539 sales, 39,401 building records and 1,285 accepted historical joins; those alone do not prove complete historical or legal validity.

### P2 | Explainable comparable-sales intelligence | Weight 14% | Approved planning estimate 75%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P2.1 | Deterministic eligibility and exclusion rules | RESEARCH | Earlier-only sales, correct class/township, area tolerance, valid window and excluded shared transactions tested |
| P2.2 | Prevent duplicate property/document comparables | RESEARCH | Each selected comparable is unique under defined PIN/document/source grain and explainable |
| P2.3 | Same-neighbourhood selection and stable ranking | RESEARCH | Rank and explain relevant previous sales without using sale price as a ranking input |
| P2.4 | Evaluate bounded geographic fallback | PARTIAL | Fixed 2025 comparison completed: 18 fallback subjects, 28.10% MdAPE; 1 km not better on paired cases; retain exploratory label pending acceptance |
| P2.5 | Validate insufficiency and abstention policy | PARTIAL | Canonical matcher abstention and zero-evidence states verified across SQLite/React and PostgreSQL candidate; 59/59 eligible 2025 subjects supported under fixed policy; broader market/generalisation not established |
| P2.6 | Test better similarity and sale-quality factors | PARTIAL | Fixed 1 km ablation completed, no paired improvement and two fewer supported subjects; no policy change; other factors untested |
| P2.7 | Independent later chronological holdout | PARTIAL | Fixed 2025 retrospective completed at 3bd6232 on 59 eligible subjects; publication-time/as-of evidence and owner acceptance remain open |
| P2.8 | Prove time-valid source provenance and interpretability | BLOCKED | Every displayed sale has a traceable, permitted record and appropriate as-of/revision limitation |
| P2.9 | Accept evidence-only versus price-estimation boundary | BLOCKED | Owner approves when fallback may be displayed and how unsupported predictions/weak evidence are labelled |

**P2 exit:** Reliable, explainable comparable selection with a justified fallback and independent assessment. **Known limitation:** on the 17 fallback cases, exploratory 2 km retrospective MAE was about $209,471, worse than township comparison at about $192,153. Do **not** present the sample median as a validated house-price prediction.

### P3 | Domain model, service contracts and architecture | Weight 10% | Approved planning estimate 96%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P3.1 | Define inquiry, sale, parcel, building, assessment and evidence entities | VERIFIED | Owner accepted provisional synthetic ERD and grain; real source grain remains open |
| P3.2 | Define address resolution and ambiguous identity | VERIFIED | Owner accepted provisional synthetic parcel-only identity; real address/building resolver remains open |
| P3.3 | Define buyer input and server-owned fields | VERIFIED | Owner accepted provisional synthetic input/validation contract; real input provenance remains open |
| P3.4 | Define status/error/abstention contract | VERIFIED | Canonical status/error/abstention contract also runs on fictional PostgreSQL HTTP; production acceptance remains open |
| P3.5 | Define provenance, snapshots and frozen evidence | VERIFIED | Owner accepted provisional synthetic frozen evidence contract; historical availability remains open |
| P3.6 | Define exact-money and currency representation | VERIFIED | Owner accepted provisional synthetic integer cents and decimal USD contract; production limits remain open |
| P3.7 | Define schema evolution and recovery method | VERIFIED | Owner accepted provisional synthetic migration contract; SQLite restart and PostgreSQL candidate migration/restore verified; production plan open |
| P3.8 | Select application stack, hosting and access approach | PARTIAL | Offline loopback HTTPS OIDC/CSRF and persistent session candidate verified; actual provider, production session/security and hosting open |
| P3.9 | Define secure, permission-aware buyer experience | PARTIAL | Axe four views zero detected violations and offline TLS buyer isolation verified; manual accessibility/privacy/owner review open |
| P3.10 | Decide real geography/identity/as-of/field-rights boundaries | BLOCKED | Exact cohort address coverage measured, synthetic parcel-only resolver and default-deny field policy tested; real identity/field rights/as-of remain unapproved |
| P3.11 | Run formal P3 contract and design acceptance review | BLOCKED | Owner signs off ERD, migration, API, errors, evidence states, UX and threat/privacy plan with unresolved issues recorded |

**P3 exit:** A **signed-off**, test-backed domain, data, API, error, security and first-journey specification. A good synthetic CI run is important evidence, but does not mean real identity, usage rights or production migration has been accepted.

### P4 | Database, curated ingestion and backend APIs | Weight 16% | Approved planning estimate 95%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P4.1 | Implement relational constraints and migration runner | VERIFIED | Synthetic SQLite v1–v3 and PostgreSQL constraints, checksum history and transaction rollback passed; separate checksum-tracked historical extension rehearsed in disposable PostgreSQL, production migration open |
| P4.2 | Implement versioned and validated investigation HTTP contract | VERIFIED | Synthetic same-origin API accepts permitted input and rejects malformed/conflicting/unauthorised requests |
| P4.3 | Join the existing pure matcher to curated SQL records | VERIFIED | End-to-end fixture run returns actual stored synthetic transactions, not hand-entered output totals |
| P4.4 | Store, check and reopen frozen comparable evidence | VERIFIED | Fixture JSON, transaction IDs, snapshot IDs and exact cents remain consistent in memory **and in opt-in trusted local SQLite files** after restart |
| P4.5 | Implement production-appropriate durable database | PARTIAL | PostgreSQL runtime consolidated; actual Neon invented persistence and independent encrypted Drive restore verified; full protected storage and production infrastructure open |
| P4.6 | Implement idempotent source-to-curated import | PARTIAL | Actual bounded private import, exact cents, idempotence and seal passed; V4 fictional runtime remains; production migration and durable real import open |
| P4.7 | Resolve real buyer properties without unsupported guesses | PARTIAL | 137/137 actual historical cohort keys had nonblank unique labels; 59/59 restricted-reader address-token reviews matched PIN reviews; private acceptance only, public buyer resolver not activated |
| P4.8 | Implement time-valid evidence and source refresh handling | PARTIAL | Atomic reviewed build activation/rollback, cross-build saved evidence and revision-specific addresses verified; real refresh/as-of blocked |
| P4.9 | Finalise API stability, error safety and operational boundaries | PARTIAL | Offline HTTPS session adapter and canonical runtime requests verified; production rate, provider, storage and network review open |
| P4.10 | Run persistent database/API acceptance | PARTIAL | Actual private sealed reader reviewed 59/59 subjects with canonical parity; persistent invented Neon browser journey and independent restore passed; actual identity-to-buyer and real HTTP/browser acceptance open |

**P4 exit:** A durable, safe, source-aware backend supporting real permitted data or a clearly scoped synthetic-only publicly labelled mode. In-memory fixture storage alone does not satisfy the phase.

### P5 | Browser investigation experience | Weight 16% | Approved planning estimate 89%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P5.1 | Establish workspace/navigation and buyer entry flow | PARTIAL | Readable fictional address, buyer-friendly labels and compact mobile navigation verified; Atlas owner-approved, final real-buyer acceptance open |
| P5.2 | Address search, ambiguous candidate selection and validation | VERIFIED | Synthetic browser asks for explicit parcel choice and prevents accidental previous-property submission |
| P5.3 | Investigation result and comparable evidence cards | VERIFIED | Exact cents preserved from source-shaped intake to PostgreSQL HTTP and actual V4 Chromium; existing server-owned evidence and keyboard details preserved |
| P5.4 | Buyer-reported asking price and source attribution | PARTIAL | Dossier separates asking price, sale cents and provenance; real-source permitted display not established |
| P5.5 | Differences and comparison-quality explanations | PARTIAL | Varied prices, dates and areas with linked V3 virtual map verified; no real geography or independent accuracy proof |
| P5.6 | Complete supported, exploratory, unknown and error states | PARTIAL | Synthetic ambiguity, abstention, network and optional map failure recovery verified; V4 no-reviewed-map response verified in actual Chromium; real release-like coverage remains |
| P5.7 | Responsive, accessible browser acceptance | PARTIAL | 14-view axe audit zero detected violations; incomplete checks, manual AT/device/zoom and final acceptance open; keyboard/mobile tests passed |
| P5.8 | Real-permitted market coverage and source explanation | BLOCKED | UI accurately states supported geography, as-of caveats and field-level reuse restrictions |
| P5.9 | Approve final buyer workflow, styling and information hierarchy | BLOCKED | Atlas approved and fictional supported/insufficient journeys verified; owner final real-buyer task acceptance still required; real basemap optional/deferred |

**P5 exit:** A buyer can independently select a property, investigate eligible historical sales, understand why results are available or unavailable and act on the limitations, on the actual backend.

### P6 | Save, shortlist, compare and decide | Weight 12% | Approved planning estimate 95%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P6.1 | Save/reopen one synthetic investigation | VERIFIED | Frozen UUID-backed investigation reopens in memory and across restart with explicit `--fixture-db`; default memory-only demo remains temporary |
| P6.2 | Define shortlist and membership schema | PARTIAL | Integrated fictional two-owner HTTP and RLS with transaction-local identity verified; real provider and retention remain |
| P6.3 | Build durable save and restore across restarts | VERIFIED | Both SQLite and fictional PostgreSQL application process restart preserve saved evidence/shortlists; no production guarantee |
| P6.4 | Add and remove shortlist entries with notes | VERIFIED | Fixture-only add/remove and note editing preserve frozen response hash, original sale cents and comparable links |
| P6.5 | Build two- or three-property side-by-side view | VERIFIED | Aligned semantic comparison preserves asking prices, evidence, source builds and no valuation; owner review open |
| P6.6 | Preserve weak-evidence and excluded properties in shortlist | VERIFIED | At least one insufficient-data fictional property (0 eligible sales) remains visible alongside a three-sale property; broader real-market coverage not accepted |
| P6.7 | Keep immutable evidence/provenance alongside mutable notes | VERIFIED | Frozen evidence and mutable notes survive activation/rollback; mixed reviewed builds re-open through own source membership |
| P6.8 | Decide safe access and optional export/report rules | PARTIAL | Fictional HTTP Basic access and database isolation verified; real provider, retention and export policy blocked |
| P6.9 | Full returning-buyer comparison acceptance | PARTIAL | Actual TLS cookie-authenticated React investigation, shortlist and note writes verified; final owner/access acceptance remains |

**P6 exit:** An owner-accepted, responsible **Investigate → Compare → Decide** buyer workflow with two or three reopenable properties, notes, defensible evidence and appropriate data/access/retention and UX gates. The **implemented fictional-only P6 workflow** is verified, but it is not a production or formal P6 acceptance.

### P7 | Cross-layer correctness, privacy and readiness | Weight 8% | Approved planning estimate 83%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P7.1 | Automated regression across Python, SQL, HTTP and browser | VERIFIED | a90a101 10/10 CI, 206 backend, 40 React and 47 PostgreSQL runtime passed; prior marker 1290a1d 8/8 verified bounded real rehearsal, now consumed; no new live collection authority |
| P7.2 | Validate hostile/invalid/unsupported requests | PARTIAL | Offline HTTPS session/CSRF/owner denial retained; restricted historical reader denies writes, buyer tables, DDL/temp and table/column grant drift; public security remains open |
| P7.3 | Prove evidence integrity and migration rollback | PARTIAL | Inactive historical late-write conflict rollback, source tamper denial and old evidence reopen verified alongside fixture activation/rollback; actual invented Neon backup restored independently with source seal and owner denial; real-data operational protection open |
| P7.4 | Test historical leakage, duplicate sales and source revision | PARTIAL | 2025 fixed retrospective holdout evaluated 59 eligible subjects; source-shaped intake revision/duplicate checks verified; historical publication-time availability proof remains open |
| P7.5 | Accessibility, responsiveness and buyer failure recovery | PARTIAL | 14-view axe audit zero detected violations; keyboard/mobile and fictional map failure recovery tested; incomplete findings and manual accessibility review open |
| P7.6 | Authentication/privacy/retention and secrets review | PARTIAL | Offline OIDC HTTP, private persisted sessions and browser CSRF writes/logout verified; actual isolated Auth0 login/restart/logout and combined invented buyer journey demonstrated; combined-cloud restart, old-cookie/cross-owner probes, distributed store, retention and real-data acceptance open |
| P7.7 | Load, rate, recovery and operational monitoring checks | PARTIAL | Independent Drive retrieval and isolated PostgreSQL restoration verified for invented data; local rekey tests passed, owner key action and production rate/monitoring/retention remain |
| P7.8 | Licence, attribution and source-time release audit | BLOCKED | Publisher intended comparable-property use and metadata reviewed; four licence IDs unspecified; private durable retention/field scope, public redistribution and as-of proof open |
| P7.9 | Full user journey and release-readiness sign-off | BLOCKED | Separate P7 acceptance suite passes against release-like storage, APIs and browser; owner approves readiness |

**P7 exit:** A reproducible and verified **release candidate**, with privacy/security/rights gates satisfied. CI-verified synthetic fixtures are not the same thing as a release security review.

### P8 | Deployment, credible demonstration and recruiter handoff | Weight 6% | Approved planning estimate 35%

| ID | Work package | State | Measurable acceptance |
| --- | --- | --- | --- |
| P8.1 | Decide public demonstration mode and data | PARTIAL | Owner selects full real-property product; candidate market retained, licensed field display decision still open |
| P8.2 | Provide reproducible clean setup and deployment config | PARTIAL | Reproducible local release runbook, dependency/accessibility CI gates; Python/npm known-advisory gates passed; production hosting config, OS/native libraries, full dependency lock and actual environment review remain; optional one-click fictional fallback |
| P8.3 | Configure authorised hosting and safe endpoints | OPEN | Deployment uses reviewed network/auth/configuration; no localhost-only fixture WSGI accidentally exposed publicly |
| P8.4 | Demonstrate the complete buyer decision journey | PARTIAL | Richer V3 actual PostgreSQL screenshot and complete fictional buyer journey verified; public demo scope not accepted; browser-only end-to-end acceptance required |
| P8.5 | Publish clear architecture, data dictionary and evidence lineage | PARTIAL | Recruiter walkthrough includes architecture and SQL source lineage; full release review remains |
| P8.6 | Prepare technical recruiter walkthrough and failure demonstration | PARTIAL | Recruiter walkthrough and actual richer screenshot ready for owner review; recording, public scope and isolated recruiter access remain |
| P8.7 | Final project README, portfolio links and demo recording | PARTIAL | Release runbook, actual CI screenshot, reproducible local setup; final recording/portfolio link/release open |
| P8.8 | Owner acceptance, integration and release handoff | BLOCKED | Approved P7 readiness, reviewed \`main\` merge, correct demo URL/artifacts, browser-only acceptance and final handoff record |

**P8 exit:** A recruiter can try or watch the completed **Investigate → Compare → Decide** application and independently inspect a truthful code/test/evidence story. No deployment or release has yet been authorised.

### Critical path and workable parallel tracks

1. **Decisions first (P0/P3):** Accept exact MVP buyer journey, real pilot coverage, source rights/display approach, address→parcel→building handling, v0.3 contract boundaries, production storage and security assumptions. A synthetic-only portfolio demonstration is a legitimate *proposal* if rights block real property display, but its release still needs approval.
2. **Research/data risk in parallel (P1/P2):** Quantify exclusions/drift, investigate as-of availability and defensible sales, evaluate fallback honestly, and establish the permitted input/output dataset. These external-evidence tasks may block public real-data claims even when software is ready.
3. **Build cohesive P4/P5 slices:** A durable curated property record → server investigation → evidence/abstention UI; migrate/version safely and verify each slice in both backend and Chromium. P4 and P5 keep **separate gates**, even though implementation overlaps.
4. **Review integrated P6 for owner acceptance before calling this a flagship product:** Two/three fictional enquiries, notes, side-by-side evidence and frozen-restart reopening are code-verified. Complete missing UX, access, retention, approved source display and release-like cases.
5. **Treat P7 and P8 as independent release gates:** Security, rights, accessibility, performance, safe deployment and portfolio walkthrough. A green development build is not public release authorisation.

**Owner release direction:** full original real-property product selected. Canonical exact-year correction and fixed 2025 holdout verified; next source-specific rights, evidence-only/fallback disclosure and production gates. No further live extraction, contact, provisioning, real display or deployment without scoped approval.

**Scoring rule:** Existing P0–P8 stage weights and exit gates remain fixed. The latest owner-authorised 24 November reassessment is **87.1%** (85.7% was the preceding milestone); change estimates only at meaningful milestone reviews, not from this breakdown alone. Subitem statuses are *not numeric percentages*. At each milestone review, revisit the phase's exit gate, inspect exact commit/CI and dated research/owner evidence, then update both this roadmap and [CHECKPOINT.md](CHECKPOINT.md) with a defensible completion estimate and any remaining blocked items. Do not add a second spreadsheet or independent score ledger unless explicitly approved.

## Full process and phase exit gates

### P0: Discovery and feasibility — 6% weight; 94% estimated complete

**Goal:** Define a credible buyer decision, one supported geography and housing segment, a useful first product scope and viability boundaries.

**Evidence:** Product brief/pinnacle concept; historical Cook County Class 203 pilot; [Pinelands candidate feasibility](research/DATA_FEASIBILITY.md#27-november-2026--pinelands-candidate-feasibility); scoped official-source investigation and actual local reference evidence.

**Remaining:** Explicit owner sign-off on pilot geography/segment; source display/reuse rights, privacy and redistribution constraints; establish where user-entered properties can realistically be supported.

**Exit gate:** Approved bounded product brief, source register, class/geography decisions, permitted field display policy and a documented go/no-go decision. No claim of live listings or commercial appraisals.

### P1: Data engineering — 12% weight; 98% estimated complete

**Goal:** A repeatable extraction-to-cleaned-data pipeline with credible record grain, stable IDs and source/version lineage.

**Evidence:** GitHub Actions Phase 0/1 extraction, 3,539 recorded sales, 39,401 historical improvement records, 1,285 accepted joins and 273 Class 203 sales; numeric parser regression fixed; privacy-conscious aggregate report artifacts.

**Remaining:** Snapshot/version integrity, reproducible refresh and drift checks; schema and data dictionary review; policy for late-reported sales, historical backfills and ambiguous property identities; curated application-ready storage.

**Exit gate:** Reproducible dataset build with explicit inclusion/exclusion logs, validated grain and keys, provenance, tests for schema change and stable re-runs; raw records excluded from public repository/artifacts.

### P2: Comparable-sales intelligence — 14% weight; 75% estimated complete

**Goal:** Explainable, conservative same-market historical comparables, ranking, evidence and abstention.

**Evidence:** Phase 2 matcher, 42 offline tests across the pipeline, actual cloud evaluation: 83 Class 203 historical 2024 subjects; 66 with >=3 same-neighbourhood sales and 17 recovered by 2 km fallback.

**Remaining:** Fallback's retrospective price error is worse than township baseline on those 17 cases. More property similarity features, source-time limitations, untouched later holdout, error/coverage/abstention calibration and safe output evidence contract remain unresolved.

**Exit gate:** Deterministic eligibility and no-future-sale rules, one-property-one-comparable accounting, complete explanation/provenance, independent evaluation, justified fallback rules and truthful insufficiency response. Do not promote experimental median to a validated price estimate.

### P3: Product architecture and contracts — 10% weight; 96% estimated complete

**Goal:** Translate the research engine into explicit, testable business objects and contracts for a real application.

**Evidence:** P3.1–P3.7 provisionally accepted for synthetic scope, React and geographic evidence integrated, workspace tested, PostgreSQL candidate approved and verified. See [production readiness](engineering/PRODUCTION_READINESS_V1.md).

**Remaining:** Real address/building identity, source rights and historical availability; production authentication, pooling, concurrency, hosting and owner UX/security sign-off.

**Exit gate:** Accepted database ERD and migration plan, endpoint/request/response contract, error and unsupported states, first end-to-end journey specification, security/privacy rules and contract-test fixtures.

### P4: Backend API and database — 16% weight; 95% estimated complete

**Goal:** Running server and durable application storage connecting curated data to enquiries and evidence.

**Planned:** SQL schema and constraints; migrations; idempotent curated-data import; safe data access; validated property investigation endpoints; matcher service integration; source/version lineage; correctness integration tests.

**Exit gate:** A client can submit a supported subject, retrieve ranked and explained earlier comparable sales, retrieve truthful insufficient-data results, and recover an investigation from persisted storage. Tests demonstrate these behaviours without handwritten fake totals.

### P5: Property investigation frontend — 16% weight; 89% estimated complete

**Goal:** A usable browser experience rather than a notebook or audit dashboard.

**Planned:** Market coverage explanation, property entry/validation, asking-price field clearly user-reported, comparable cards/evidence, ranked differences and dates, transparent neighbourhood vs exploratory radius, loading/empty/failure states, responsive and accessible UX.

**Exit gate:** User completes add property -> inspect relevant historical comps -> understand why selected or why unavailable, in the browser, against the actual backend. No unsupported price claims.

### P6: Saved buyer decision workflow — 12% weight; 95% estimated complete

**Goal:** The distinctive complete micro-application experience.

**Planned:** Save and reopen at least two enquiries; per-property notes and shortlist; side-by-side comparison; recorded sale evidence linked to source/version and rule revision; simple decision report/export only where field rights permit. Authentication only if the product requires accounts.

**Exit gate:** A returning buyer can open two saved properties, compare supported evidence and notes, and reopen identical source/rule-referenced results. An insufficient-data home is still savable.

### P7: Integrated QA and readiness — 8% weight; 83% estimated complete

**Goal:** Prove the complete system is reliable, secure and honest.

**Planned:** API/database/browser end-to-end tests; malformed property submissions, duplicate/revised sales, date leakage, ambiguous joins, migration backup/recovery, accessibility, resource performance and source rights; verify no raw private records or credentials leak to Git or artifacts; monitor pipeline failures and source changes.

**Exit gate:** Accepted integration/demo journeys, reproducible clean build, documented limitations, suitable rate/resource controls and permission to expose chosen fields. Public exposure blocked if source reuse rights remain unresolved.

### P8: Release and portfolio demonstration — 6% weight; 35% estimated complete

**Goal:** Ship a coherent portfolio-quality application and explain technical decisions to recruiters.

**Planned:** Deploy only after P7; representative allowed data or unmistakably labelled synthetic/demo fixtures where public display rights are unresolved; README, architecture diagram, clean setup, demo walkthrough/video, source and QA evidence, explanation of matching/risk trade-offs; working app URL if deployment is authorized.

**Exit gate:** Reproducible installation and deployed/demo functionality: add two properties -> inspect ranked comps -> demonstrate fallback warning/abstention -> save/reopen -> compare -> explain test-backed joins and provenance.

**Owner-approved browser-only release acceptance (25 November 2026; required, not yet verified):** On an ordinary supported browser with no project-specific setup, open one authorised HTTPS application URL, sign in through the integrated identity flow, complete the buyer journey, refresh/reopen saved work and sign out. Neither presenter nor recruiter needs CMD, PowerShell, WSL, CLI commands, manual service startup, database connection, certificate installation or Auth0 dashboard configuration. Hosting manages service startup and TLS; secrets remain server-side. Provide a dedicated least-privilege recruiter demonstration account or equally isolated approved demo access, preconfigured safe data and repeatable scenarios, with no access to private buyer records or operator privileges. Use only expressly permitted real fields or clearly labelled synthetic fixtures for the demo; this does not replace the original real-property MVP. Verify from a fresh browser with no developer session and retain redacted evidence of the complete journey, including insufficient evidence, persistence and logout. Hosting, access mode, data rights, R0 sustainability, deployment and main integration retain separate approval gates.

**Optional resilience enhancement:** If proportionate, offer a one-click local fallback using prepared dependencies and isolated fictional data. No external login or cloud database should be required for an explicitly offline fallback; label its limitations. It is not a substitute for the browser-only hosted acceptance gate, and must not become a mandatory installer project.

## Conditional post-MVP branch, excluded from 100%

**M1: statistical pricing / machine learning.** Requires a credible later chronological holdout, fully time-appropriate features, strong baseline comparisons, useful accuracy and defensible uncertainty calibration. If it fails, ship without a predicted price. No forced "AI" feature.

**Deferred:** Global listing search, property photos, mortgages, multi-market expansion, notification infrastructure and professional-appraisal claims.

## Near-term execution, complexity last

1. Execute the [P0 directive](engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md) in sequence, beginning P0-A.1. Close against the seven existing work packages; P0.4-P0.7 remain open, and earlier buyer/market evidence is retained but refined through P0-A/B.
2. Retain P1-P8 implementation and evidence without unrelated changes; named dependencies only if required to close P0.
3. On verified P0 closure and applicable owner acceptance, select the next phase in dependency order. Existing protection, rights, data, cost, deployment and main-integration boundaries remain binding.
4. Reassess only at meaningful accepted milestones; no automatic score or phase exit.

## Evidence and reporting policy

**Verified as of 22 November 2026:** GitHub Actions [run 45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782); [Phase 2 retrospective results](research/PHASE2_CLOUD_AUDIT_RESULTS.md); [project checkpoint](CHECKPOINT.md).

**Progress tracking:** On every meaningful verified milestone review, update this file's stage figures, explain evidence and changed assumptions, and update `docs/CHECKPOINT.md`. Document rejected experiments rather than reporting them as successful features. No automatic %-increase per commit or test count. The original House Price Intelligence exploratory roadmap is preserved at [docs/archive/INITIAL_ROADMAP_2026-11-22.md](archive/INITIAL_ROADMAP_2026-11-22.md).


