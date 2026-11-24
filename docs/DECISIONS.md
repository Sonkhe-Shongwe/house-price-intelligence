# Decisions and open questions

**Reviewed:** 23 November 2026. **Authority:** Active product choices and documented user direction; research observations alone do not approve public product claims.

## Confirmed direction

| Topic | Current decision | Evidence or boundary |
| --- | --- | --- |
| Product | Build House Price Intelligence as a property investigation and shortlist application | [Product brief](product/PRODUCT_BRIEF.md) |
| Method | Product-first, verifiable foundations before advanced prediction | [Engineering contract](engineering/ENGINEERING_CONTRACT.md) |
| Delivery control | Retain House Price Intelligence P0-P8 stages, weights and gates | [P-stage roadmap](P_PHASE_ROADMAP.md); 84.0% owner-authorised planning estimate (24 Nov) |
| Engineering process (approved 23 Nov) | Eight-step requirements/architecture/risk/implementation/tests/integration/review/handoff; safe migrations and explicit evidence levels | [Lean engineering directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md); process approval, not feature/stack approval |
| Development station (approved 23 Nov; refined 23 Nov) | **One ongoing `development` working branch** for connected P3–P6 feature work, **stable `main`** for reviewed and owner-accepted milestones; GitHub Actions on development pushes and integration PRs; local Windows pulls only for indispensable owner/platform acceptance | [Cloud-first workflow](engineering/CLOUD_FIRST_WORKFLOW.md). Additional branches only for exceptional needs. Avoid squash/force rewrites of permanent branch; no blanket permission to merge or deploy |
| Delivery evidence (23 Nov) | Original owner manual fixture journey, now followed by real hosted synthetic browser and API tests on `development` | [Current checkpoint](CHECKPOINT.md) identifies the latest verified run; earlier 125-test main and isolated 127-test Windows results are historical snapshots, not the active CI counts |
| Development sequencing (approved 23 Nov) | P4 backend and P5 browser implementation can overlap after P3 acceptance via complete vertical slices; each phase retains its own exit gate and progress | [P-stage roadmap](P_PHASE_ROADMAP.md) |
| Market choice (23 Nov) | **Data-first, geography-flexible**. Do not force South African coverage if sources, identity, attributes, usage rights or reliability limit the product. Cook County township 17 / Evanston remains the **research pilot**, not final permanent coverage | Phase 0–2 research and owner direction |
| Research segment | Investigate assessor Class 203, a one-story residence category | 273 historical matched sale records; individual building form/condition not verified |
| Data strategy | Preserve transaction, parcel, building and assessment-year grain separately; reject inappropriate joins | [Phase 0 findings](research/PHASE0_LIVE_AUDIT_RESULTS.md) |
| Comparison policy | Test neighbourhood-first with bounded spatial fallback, distinct PINs and abstention | [Phase 2 findings](research/PHASE2_CLOUD_AUDIT_RESULTS.md); **exploratory only** |
| Processing | Use GitHub Actions for source research audits and publish **aggregate-only** report artifacts | [Automated audit](AUTOMATED_DATA_AUDIT.md) |
| Security | No raw property extracts, seller/buyer names, secrets or user records in public repository | [Data policy](../data/README.md) |
| Boundaries | Do not claim current price prediction, live listings or app deployment | No such accepted implementation exists |
| UX design authority (23 Nov) | Current teal interface is provisional; owner liked the **workspace-first low-fidelity study** for exploration, not as final branding/navigation approval | [23 Nov UX research](design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md) |
| Visual quality and frontend freedom (23 Nov, owner clarification) | **Target an exceptional, commercially credible visual and interaction experience; do not constrain the frontend to vanilla JS, a specified framework or today’s CSS.** Select UI technology only after contrasting tangible high-fidelity visual candidates, component/state needs, accessibility, integration risk and real-browser evidence. **No framework, visual identity, migration or release is approved by this instruction alone.** | [Visual Foundation V1 proposal](design/VISUAL_FOUNDATION_V1_IMPLEMENTATION_PROPOSAL_2026-11-23.md); preserve existing Python/SQLite source-of-truth and stage gates |
| Independent product (23 Nov) | Investigate / Compare / Decide, not a Property24 clone or listings marketplace; external platforms are UX inspiration only | [Product brief](product/PRODUCT_BRIEF.md) and [pinnacle vision](product/PINNACLE_VISION.md) |
| Map direction (23 Nov) | Explore an **investigation-centred, synchronized map and evidence list**, with optional map view for shortlist locations. **No map renderer, tile provider, geocoder, geographic source, map API or visual style is approved.** Today's six synthetic parcels share one dummy coordinate: never plot them as distinct real positions. Start with an explicitly **schematic fictional map proof** until safe, versioned geometry is agreed. | [Professional UI and mapping research](design/PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md) |
| Directive (confirmed 23 Nov) | Retain existing eight-step lean lifecycle unchanged; apply UX sign-off and geospatial/source integrity within it | [Lean directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md) |
| Repository | Keep this codebase separate from the [SA Tech Graduate Playbook](https://github.com/Sonkhe-Shongwe/sa-tech-grad-playbook.) | Original graduate research untouched |

## P3.1–P3.11: contract readiness and owner acceptance review (23 November 2026)

**Review status:** **Technical assessment recorded; owner acceptance not yet granted.** Evaluated against `development` [`79c77cc`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/79c77cc29d6b4e0e7e93261710b6f74ae54d4888), [successful push CI 45214449443](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45214449443) and [successful PR CI 45214464051](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45214464051): **148 Python tests, 7 real Chromium browser journeys**, JavaScript and docs checks. This is a *source-backed acceptance proposal* under the existing [P0–P8 roadmap](P_PHASE_ROADMAP.md), **not a production approval, real-data licence opinion, deployment authority or automatic phase-score increase**.

**Recommended operating split:** Accept the *tested shape* of the fictional-data demonstrator as a **provisional design baseline**, rather than demanding all real-market evidence before building more buyer features. Every production-facing version of these contracts remains subject to a later review of real source identity, historical availability, privacy/security, persistence and display rights. Do not confuse "technically verified on fixtures" with "owner accepted" or "ready to expose on the internet."

| Package | Review finding and existing evidence | Proposed disposition, not yet owner accepted | Required follow-up |
| --- | --- | --- | --- |
| **P3.1 Domain entities and ERD** | v1–v3 relational fixtures distinguish sale transaction, parcel, optional building, tax-year assessment, source snapshot/build and frozen investigation. Tested constraints and [candidate ERD](engineering/P3_APPLICATION_CONTRACT.md) exist. | **Eligible for fixture-only approval** | Owner reviews source grain, optional building/card relationships and multi-parcel exclusion before treating model as canonical for any real source |
| **P3.2 Address/parcel/building identity** | Same invented street label can map to two distinctly selected parcels; server binds candidate ID; building remains explicitly unverified; changed selected mapping fails reopening. | **Eligible for fixture-only approval** | Specify the licensed real address source, match/ambiguity policy and building-versus-parcel semantics; no assumption of one address = one building |
| **P3.3 Buyer input and source-controlled fields** | `validate_request` allows bounded PIN, optional candidate ID, area, label, date and asking-price text; prevents browser-supplied trusted coordinates, neighbourhood, source/build and comparable data. HTTP rejects missing/conflicting IDs. | **Eligible for fixture-only approval** | Confirm real buyer input and provenance of area/asking price before live entry; reconcile client-assisted identity with source permissions |
| **P3.4 Response, errors and abstention** | Four statuses are implemented, with 422 validation, 404 missing IDs, 503 unavailable evidence and no numeric valuation; browser tests demonstrate supported, insufficient and no-match safety. | **Eligible for fixture-only approval** | Approve published field/code meanings, failure/retry UX, unsupported-class cases and compatibility/versioning strategy for any durable service |
| **P3.5 Provenance and frozen evidence** | Selected transaction, original integer cents, source snapshot/role, curated-build membership, response hash and candidate-to-parcel mapping are checked on saved reopening. | **Eligible for fixture-only approval** | Historical publication-time provenance remains unproved; select archival source and snapshot revision policy before showing live record facts |
| **P3.6 Money and currency** | Synthetic HTTP v0.3 serializes USD sale amounts from SQLite cents as fixed two-decimal strings; buyer asking price is a separate user report. Research adapter uses older numeric shape only in its own boundary. | **Eligible for fixture-only approval** | Approve currency/precision, limits, null/negative rules, market-specific formatting and contract migration before production or multi-market support |
| **P3.7 Schema migration and recovery** | Fixture v1–v3 scripts have checksums, controlled version history, rollback-on-SQL-error, duplicate/unknown version refusal and data-preserving in-memory upgrade tests. | **Eligible for fixture-only approval** | Choose durable DB and backup/restore strategy; test migrations against a real persistent file/backup. The current post-commit FK check is not a substitute for a tested production recovery plan |
| **P3.8 Runtime stack, access and hosting** | Modular Python standard library, SQLite, loopback WSGI and plain HTML/CSS/JS run as one testable local slice. | **PARTIAL: technical stack candidate only** | Decide whether first release is accountless/single-user or authenticated/multi-user, its durable database, hosting model and responsible service boundary; localhost WSGI must not be publicly exposed unchanged |
| **P3.9 Secure and usable buyer UX** | Existing browser journey is tested; missing selection does not guess, errors are surfaced and source/evidence caveats are present. Provisional interface is not an owner-approved visual or accessibility baseline. | **PARTIAL: UX/security acceptance not ready** | Review 2–3 representative buyer tasks, keyboard/screen-reader/reflow checks, long/empty/error states, privacy and access controls; accept or revise information architecture |
| **P3.10 Market, data rights and as-of** | Evanston/township 17 Class 203 real-data research exists, but current app contains only invented records. Source-specific field reuse, real address identity and publication-time historic availability are unresolved. | **BLOCKED for real-property display** | Approve candidate first market and field-level source-use/attribution rights, prove or disclose time validity, and document a conservative synthetic-only release mode if real display is not permitted |
| **P3.11 Formal contract and design sign-off** | This review names the 10 preceding packages and outstanding gaps. No owner has approved an end-to-end architecture, migrations, UI, security or source-rights package yet. | **PENDING OWNER DECISION; P3 exit remains open** | Accept or revise the seven *fixture-only* candidates explicitly, select the first release/data path, assign open P3.8–P3.10 decisions, and record dated evidence and sign-off |

**Proposed owner decision bundle, requiring explicit approval:** (A) adopt P3.1–P3.7 *only as a provisional synthetic-fixture contract*, with no change to formal P3 completion; (B) continue a cohesive P4/P5/P6 **fictional-data** buyer application while doing P0–P2 rights and historical research separately; (C) keep the real-property/production contract and P3 exit unaccepted until P3.8–P3.11 are resolved. A public synthetic demo would still need security, operational and release review. This bundle is **a recommendation, not an approved decision**.

**Prioritised unresolved decisions:** (1) Data/release mode: fictional-only portfolio demonstration or later rights-approved first-market data. (2) Storage/access: initial single-user durable mode versus accounts, retention and authentication. (3) First buyer UX acceptance, including accessible navigation and shortlist-first flow. (4) Production migration/backup and historical source-time contract. Evaluate these without silently installing frameworks, distributing records or merging PR #4 into `main`.

**Phase accounting:** P3 **10%**, weighted MVP **22.8%**, unchanged. Current roadmap P3.1–P3.7 remain technically `VERIFIED`, P3.8/P3.9 `PARTIAL`, P3.10/P3.11 `BLOCKED` until owner review. Technical evidence is distinct from product acceptance.

## Current integrated development candidate (not accepted on `main`)

**Application verification, 23 Nov:** Owner-authorised [PR #5](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/5) and [PR #6](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/6) merged into permanent `development` at [`44e278f`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/44e278f5ff68475616d889d2c7fafd0b5b3c6304). [Integration CI 45254283750](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45254283750) passed **172 Python and 9 real Chromium** tests, JavaScript/docs. Fictional address/parcel identity, v0.3 money, v1–v3 schema, opt-in locally durable SQLite and **two-to-three-property shortlist, notes and side-by-side comparison** are integrated; final visual identity, interactive map, real/source-verified property data, production access/retention and release remain unapproved. The [current checkpoint](CHECKPOINT.md) records later docs-only updates. [PR #4](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/4) remains draft, no `main` merge; **P3 10% and weighted MVP 22.8% are unchanged**, pending owner phase exit acceptance.

**Additional owner direction, 23 Nov:** Exceptional visual polish is required, but **no specific frontend stack is mandatory**. The map is proposed as a central evidence view, but rendering library, tile rights and versioned geographic evidence contract are **independent decisions**, not implicit implementation permission. Refer to [Visual Foundation V1](design/VISUAL_FOUNDATION_V1_IMPLEMENTATION_PROPOSAL_2026-11-23.md) and the [map/UX grey-area research](design/PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md).

## Historical implementation milestones (dated development changes, not current acceptance)

- **23 November 2026, `development` `07f637b`:** Four invented address rows were added to the P3 disposable SQLite demo, with a bounded search endpoint, explicit candidate selection and existing synthetic comparable investigation/reopen. CI [45193537292](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45193537292) passed 132 Python and 5 hosted Chromium tests. This demonstrates an original, connected buyer interaction on the approved technology stack; it **does not settle the real address/parcel/building identity decision**, rights, historical availability, migrations, branding or production scope. Remains in the [draft development integration PR #4](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/4), not accepted on `main`.

- **23 November 2026, `development` `79a7c4d`:** Candidate synthetic investigation contract `p3-draft-v0.3` now carries an optional fictional-address ID which the server binds to a trusted synthetic parcel, with 422 on mismatch; comparable HTTP prices are fixed-scale USD text derived from exact SQLite cents, not JSON floats. [Push CI 45196929621](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45196929621) passed 137 Python + 6 hosted Chromium cases. This **does not settle real address identity, real-data source rights, approved commercial pricing or production migrations**. Provisional until owner P3 acceptance. Still in draft PR #4.

- **23 November 2026, `development` `8ed4269`:** Candidate v1/v2 synthetic SQLite migration runner added with hash and version checks, rollback, no unversioned adoption and populated-database upgrade tests. The [P3 application contract](engineering/P3_APPLICATION_CONTRACT.md) contains the proposed domain ERD and distinct identity grains. [Push CI 45200038440](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45200038440) and [PR CI 45200054027](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45200054027) passed 144 Python and 6 Chromium tests. No production database, backup, real address identity or P3 gate acceptance has been approved.

- **23 November 2026, `development` `3793b81`:** A new v3 **fictional-only** parcel-candidate table permits two parcels to share a visible address or one parcel to have multiple aliases. Search shows separate parcel options, the server binds the exact chosen candidate, the UI labels building identity unverified, and saved investigations fail closed if the selected mapping changes. This is a testable identity-risk model, **not an approved real-source address, building or title-identity solution**. [Current P3 contract and ERD](engineering/P3_APPLICATION_CONTRACT.md). No P3 completion credit.

## Open decisions, with next acceptance point

| Question | Needed evidence or approval | Gate |
| --- | --- | --- |
| Will Evanston/Class 203 be the final MVP boundary? | Buyer use case, coverage, field rights and explicit scope decision | P0/P3 |
| Which property-level fields may be publicly stored/displayed? | Dataset-specific licence, attribution, privacy and redistribution review | P0/P7 |
| What counts as a defensible completed sale? | Filter definitions, parcel/document grain and representative exclusions | P1/P2 |
| How do we guarantee evidence available as of analysis date? | Historical snapshots or an explicitly honest policy; later holdout validation | P1/P2 |
| Should exploratory 2 km fallback be included in UI? | Evidence-only warning design and independent testing; current price errors are poor | P2/P3 |
| Which buyer entry and property identity? | Address/parcel/building resolution and real supported market; technical 14-digit PIN is not final consumer entry | P3 |
| What would a responsible map require? | Coordinate source/accuracy, provider/tile rights, attribution, restrictive CSP/referrer compatibility, keyboard/table alternative | P3/P5 |
| Backend framework, database, frontend and hosting? | Reviewed P3 contract and deployment constraints; no precommitment | P3 |
| How are saved investigations versioned and accessed? | Identity/security, snapshot and persistence design; fixture-only schema upgrade is tested, but user access is undecided | P3/P6 |
| Which production database migration, recovery and retention policy? | Synthetic SQLite migration runner and rollback are verified only for disposable fixtures; production DB, backup/restore, retention, access and historical source identity remain to be selected and approved | P3/P4/P7 |
| Can price prediction be shipped? | Untouched chronological holdout, acceptable baseline comparisons, uncertainty | Post-MVP, conditional |
| Should repository remain public? | Repository risk review and owner choice; currently reported public | P7 |
| What should the application look and feel like? | Refine promising workspace-first idea, compare visual directions, accessibility, responsive information density and buyer tasks; **no palette or final style approved** | [Exploratory UX study](design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md); P3/P5 |
| When can the 127-test patch be committed? | Review exact local/remote diff, protect untracked work, obtain bounded owner code-integration authority, commit tested guard and browser regressions, verify CI | P3 |
| Should protected-`main` required checks be enabled? | Enforced JavaScript syntax, 128 Python tests and three actual Chromium acceptance scenarios now pass on integrated `main`; owner-approved repository rules are still needed. Review stable checks and branch permission changes separately | Engineering operations / P3 |
| What exact money representation is required? | Synthetic v0.3 fixture HTTP response now uses fixed two-decimal sale-price strings derived from SQLite integer cents; confirm cross-market currency, scale, limits and versioning before approving any real-data/production contract | P3/P4 |

## Non-negotiable interpretation rules

- Historical audit "Phase 0/1/2" is **not** equivalent to delivery "P0/P1/P2".
- A prior tax year is **not proof** that a building record was available at that sale date.
- A township or Class 203 match is **not proof** of a detached-house sale or arm's-length transaction.
- An asking price entered by a buyer is not a verified sale/listing; recorded sale prices are not model predictions.
- A 2 km match is explanatory **candidate evidence**, not a validated valuation.
- Missing evidence requires an explicit abstention/unsupported status; never fabricate results or silently switch data sources.

### 24 November: React integration review authorisation

Owner approved React Application Integration V1 implementation, commits on a short-lived branch based on development, canonical persistence reuse, feature parity, CI and a review PR. See [PR #8](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/8). This is bounded fictional integration approval only: no merge, deployment, legacy retirement, real property data, map adoption or phase acceptance authorised. Final UI/stack acceptance remains subject to review and applicable security/rights gates.


## 24 November 2026 owner authorisation

PR #8 synthetic React accepted and merged to development after exact-head CI success. Synthetic Geographic Evidence Integration V1 authorised on development, using versioned read-only virtual display positions, separate from the original matcher and frozen SQLite records. See [contract](engineering/SYNTHETIC_GEOGRAPHIC_EVIDENCE_V1.md). No approval of real geography, external providers, main merge, deployment or publication. P3 10%, weighted MVP 22.8% unchanged.


## 24 November 2026: provisional P3 contract and UX approval
Owner explicitly approved P3.1–P3.7 as the provisional synthetic application contract, and authorised UX1–UX7 commits and CI on development. This supersedes the pending synthetic approval entries in the dated review, not the production gaps. P3.8–P3.11 and real data rights remain open. See [workspace contract](engineering/BUYER_WORKSPACE_UX_V1.md). No main merge, deployment or real property publication. P3 10%, weighted MVP 22.8% pending formal phase reconciliation.


## 24 November 2026: PostgreSQL and source-readiness authorisation
Owner approved PostgreSQL as a production database candidate and authorised PA1–PA4 synthetic implementation/CI and PA5–PA7 bounded aggregate-only research/documentation. Existing SQLite runtime preserved; no provider, deployment, real market, production authentication or publication rights approved. See [readiness contract](engineering/PRODUCTION_READINESS_V1.md). Formal P3 exit open, P3 10% and weighted MVP 22.8% unchanged.


## 24 November 2026: milestone progress reassessment
Owner authorised formal review and updating the recorded estimate after meaningful verified milestones. Current weighted estimate 62.9%, previous 22.8%, +40.1 percentage points. Original weights, product scope and phase exit gates retained. Evidence and remaining blockers are recorded in [P0–P8 roadmap](P_PHASE_ROADMAP.md) and [checkpoint](CHECKPOINT.md). Partial credit recognises verified integrated deliverables; this is not production approval, whole-phase acceptance, permission to deploy or a new code implementation instruction. Earlier scores in dated decisions are historical.


## 24 November 2026: real-data integration readiness authorisation
Owner approved RD1–RD7 bounded live cohort research, synthetic curated ingestion/disclosure and verification on development. No real property publication, paid infrastructure, main merge or deployment. No source reuse grant or production runtime switch. See [readiness contract](engineering/REAL_DATA_READINESS_V1.md).


## 24 November 2026: RD milestone progress review
Owner-authorised RD1–RD7 verification supports 66.5% weighted planning progress (previous 62.9%, +3.6 points). Same weights and gates. Exact cohort address audit passed; synthetic idempotent ingestion, source revision retention and guard verified. Real-data rights and production runtime remain blocked. See [RD contract](engineering/REAL_DATA_READINESS_V1.md) and [roadmap](P_PHASE_ROADMAP.md). No release approval.


## 24 November 2026: production runtime candidate authorisation
Owner approved PR1–PR8 on development, actual PostgreSQL HTTP and fictional authentication/ownership/concurrency tests, synthetic revision import and CI. No provider, public deployment, real-data display or main merge. See [runtime contract](engineering/PRODUCTION_RUNTIME_V1.md).


## 24 November 2026: runtime milestone progress review
Owner-authorised PR1–PR8 verified all eight workflows at 240f5ce. Weighted estimate 71.4% (66.5% prior, +4.9 points); unchanged phase weights and open exit gates. Fictional loopback Basic authentication is not a production provider; PostgreSQL revision importer remains separate from HTTP runtime. No production hosting, real-data rights or release approval. See [runtime contract](engineering/PRODUCTION_RUNTIME_V1.md) and [roadmap](P_PHASE_ROADMAP.md).


## 24 November 2026: consolidation authorisation
Owner approved PC1–PC8 fictional runtime integration and bounded public-source research. No real data, external contact, provider provisioning, main merge or deployment. See [consolidation](engineering/PRODUCTION_CONSOLIDATION_V1.md).


## 24 November 2026: consolidation milestone progress review
PC1–PC8 verified same-database reviewed fictional source lifecycle, cross-build reopen and rollback, revised PostgreSQL map and bounded recovery checks; weighted estimate 76.1% (71.4% prior, +4.7 points). Auth0 is recommended first OIDC candidate, not selected/provisioned; real property disclosure remains unapproved. All weights and exit gates unchanged. See [consolidation](engineering/PRODUCTION_CONSOLIDATION_V1.md) and [roadmap](P_PHASE_ROADMAP.md). No release scope change, provider account, deployment or contact authorised.


## 24 November 2026: PI1–PI8 authorisation
Owner approved bounded 2025 holdout and fixed research ablation, UI refinement, offline OIDC/session, accessibility/security checks, recruiter preparation and scoped development commits/CI. No live provider, contact, real records, valuation, deployment or main merge. See [PI contract](engineering/PRODUCT_INTELLIGENCE_V1.md).


## 24 November 2026: PI milestone review
79.2% weighted estimate (76.1% prior, +3.1 points); fixed weights and open gates. 2025 independent holdout blocked by insufficient eligible subjects, no policy or valuation adopted. Refined comparison/keyboard UI and offline OIDC session tests passed; recruiter walkthrough documented. No live provider integration, real publication, external contact or deployment. See [PI contract](engineering/PRODUCT_INTELLIGENCE_V1.md).


## 24 November 2026: FA authorisation
Owner approved FA1–FA8 bounded fictional development/CI, aggregate coverage diagnostics, offline OIDC HTTP and persistent sessions, accessibility/release preparation. No provider account, real records, valuation, external contact, deployment or main merge. See [FA contract](engineering/FINAL_ACCEPTANCE_V1.md).


## 24 November 2026: FA milestone review
83.6% weighted estimate (79.2% prior, +4.4 points), fixed weights and open full phase gates. Rich V3 and offline HTTPS persisted sessions/React writes verified; axe four views zero detected violations, manual review pending; npm production audit zero reported vulnerabilities. Count-only diagnostic does not resolve holdout eligibility. No actual provider, real record release, contact, hosting, deployment or main merge. See [FA contract](engineering/FINAL_ACCEPTANCE_V1.md).


## 24 November 2026: Full product release selected
Owner selects original real-property product, with Evanston Township/Class 203 as candidate. Authorised FR1–FR3 bounded eligibility diagnostics, fixed chronological validation, source rights research and development CI. No real display, provider, contact, hosting, deployment or main merge. [Qualification](engineering/FULL_RELEASE_QUALIFICATION_V1.md).


## 24 November 2026: FR qualification result
84.0% weighted estimate (83.6% prior, +0.4 points). All eight workflows at 0381780 passed. Legacy year parser rejects all 13,151 assessment-year 2024 rows; exact-year diagnostic recovers 59 later subjects, without adopting a correction or evaluating outcomes. Four licence IDs null, rights not approved. No further live extraction, release or deployment under FR1–FR3. Next separately authorise correction and unchanged holdout. See [qualification](engineering/FULL_RELEASE_QUALIFICATION_V1.md).


## 24 November 2026: Canonical Year Correction and Chronological Qualification V1 authorisation
Owner authorises scoped source changes, offline regressions, hosted CI and exactly one bounded live 2025 holdout under the existing fixed policy and source windows/caps. Reuse exact-integral parsing at the canonical building lookup and geographic response boundary; keep ambiguity, screening, matching and all historical results. No main merge, deployment, real-property publication or valuation approval. Progress remains 84.0% pending verified evidence and milestone review. The historical FR qualification is not rerun; the existing holdout workflow is the single authorised extraction path.


## 24 November 2026: Canonical Year Correction and Chronological Qualification V1 verified result
[Code 3bd6232](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/3bd623262da29b56b74a2af1272a4870e7c25767) and [holdout 45368763925](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45368763925) passed; 59 later eligible subjects recovered and evaluated under the unchanged policy. Current matcher beats township MAE on the same 59; 1 km alternative does not improve the paired result. No policy change adopted, no valuation approved, no source publication-time guarantee, no rights grant. Single authorised extraction consumed. Retain exploratory spatial-fallback warning. 84.0% recorded estimate unchanged pending owner milestone review. Next: owner review evidence-only release/explicit spatial-fallback limitation and source-specific display, caching and reuse rights; resolve conservative historical-availability disclosure and real-data/production readiness gates. No further live extraction, real-property publication, external contact, provider provisioning, deployment or main merge without scoped approval. See [checkpoint](CHECKPOINT.md).


## 24 November 2026: Real-Data Integration V1 approval
Owner approved Real-Data Integration V1 and the 85.7% milestone reassessment, with P1 95% and P2 75%; all other phase scores and exit gates unchanged. No additional live extraction, valuation, main merge or public deployment. External contact is not a prerequisite for controlled non-commercial development; public availability is not proof of unrestricted redistribution. [Integration contract](engineering/REAL_DATA_INTEGRATION_V1.md).


## 24 November 2026: Real-Data Integration V1 verified result
[Code 91d8872](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/91d8872342b10ba673c067a83d6fe6f1b0177871) verified: [runtime push 45372187493](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45372187493) passed 11 scenarios, including private historical PostgreSQL import, exact cents, idempotency, revision isolation, late relational-conflict rollback, scoped exact address tokens, ambiguity and cross-build denial; actual authenticated V4 React browser displayed $487,500.01, $542,750.02 and $519,900.03, previous frozen evidence reopened, unavailable map correctly abstained with null display-source metadata. [Regression push 45372187271](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45372187271) passed 204 Python tests across five suites (15/12/14/4/159) and documentation validation, plus legacy Chromium acceptance. [React push 45372187465](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45372187465), [PostgreSQL compatibility 45372187430](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45372187430), [release checks 45372187694](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45372187694) and [identity PR 45372200203](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45372200203) passed. 11/11 triggered workflows successful at review. Earlier [8f84b59](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/8f84b594c012ac8e97be776501df5e4af2736d7a) passed 10/10 workflows. V4 initial [runtime PR 45371776832](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45371776832) and [push 45371767269](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45371767269) failed on unknown-map contract; preserved and corrected rather than suppressing.

All input records invented; no additional live extraction, no real data persisted or publicly served, no deployment or main merge, no valuation or matcher change. Historical operator-side functions remain in disposable loopback PostgreSQL ingestion DB; source completeness/authenticity, production migration/least-privilege service, actual real-source import, approved field projection and public activation remain open. V4 is the existing fictional HTTP/React runtime, not a public historical-data endpoint. External contact not a prerequisite for controlled development; public release still separate.

Recorded owner-approved 85.7% remains unchanged; proposed next evidence-based milestone review 86.5% (P1 97%, P4 93%, P5 89%, P7 81%, other stages unchanged), no full phase exit. See [checkpoint](CHECKPOINT.md) and [integration contract](engineering/REAL_DATA_INTEGRATION_V1.md).


## 24 November 2026: Production Data Activation Preparation V1
Owner directs continuation of the offline workstream. Scope: versioned historical migration, dedicated restricted read role, external relational seal and private read-only service, synthetic verification and development commits. No live extraction, public release, valuation, provider provisioning or main merge. See [contract](engineering/PRODUCTION_DATA_ACTIVATION_V1.md).


## 24 November 2026: Production Data Activation Preparation V1 verified result
[Migration and reader 624fa9b](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/624fa9bff6f8e7ee57920017e5f7e0be0ea73b2c) passed 10/10 triggered workflows, including [runtime 45374000414](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45374000414) with 12 PostgreSQL scenarios. [Collection and privilege hardening 2310a2e](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/2310a2e519b3a55d5ba167b1ab7ea58fcce0ee59): [regression 45374209927](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45374209927) passed 208 Python tests (15/12/14/4/163), documentation checks and legacy Chromium; [runtime 45374209975](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45374209975) passed 12 scenarios, including historical migration checksum/re-entry, externally held relational seal, repeatable-read private search/review without re-supplying extracts, write/DDL/temp/buyer-table denial, table and column grant drift, cross-build seal rejection, row tamper denial and preserved V4 Chromium. Four new Python regressions cover counts, short/extra/capped pages, revisions, unexpected keys/fields and omitted nulls. 10/10 exact-head workflows successful at review.

All tests used invented inputs. No additional live extraction, provider provisioning, real-property persistence/publication, deployment, valuation, matcher change or main merge. Historical reader is a trusted internal role with source-table SELECT, not a buyer account or public field-level security boundary. Only disposable loopback PostgreSQL was tested; real production credentials, protected seal configuration, existing installation migration/restore, public display rights and field projection are not accepted. External contact not a prerequisite for development.

Owner-authorised estimate remains **85.7%**. Prior 86.5% proposal not adopted. Combined proposed evidence-based reassessment 87.1% (P1 98%, P4 95%, P5 89%, P7 83%; other scores and fixed weights unchanged), pending owner score review. All full gates open.

Next highest-value gate: separately authorised single bounded private real-data rehearsal, using existing township 17/class203 scope, sales 2024–2025, assessments 2023–2024, four datasets, fixed selected fields and existing caps (sales 5,000, assessments 40,000, max 500 distinct keys, 35/key batch, enrichment count <500/batch and aggregate <7,500/role). Reconcile counts, terminal pages and source revisions; import into disposable PostgreSQL, verify source membership, exact cents, seal and restricted-reader redacted outcomes. No row-level output, artifacts, raw query URLs, seal values or sensitive logs; aggregate counts/status only. No workflow dispatch under existing authority. Do not equate a successful rehearsal with durable production storage, real property release or as-of proof. See [activation contract](engineering/PRODUCTION_DATA_ACTIVATION_V1.md).


## 24 November 2026: Private Real-Data Integration Rehearsal V1 authorisation
Owner approved 87.1% weighted milestone reassessment (P0 94%, P1 98%, P2 75%, P3 96%, P4 95%, P5 89%, P6 95%, P7 83%, P8 35%) and one bounded private live rehearsal. All full gates remain open. No public property publication, permanent hosting, deployment, valuation or main merge. [Contract](engineering/PRIVATE_REAL_REHEARSAL_V1.md). One marker addition only, after offline verification. No rerun of live extraction.


## 24 November 2026: Private Real-Data Integration Rehearsal V1 verified outcome
[Preparation bfb640d](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/bfb640d2da56655bfa9998a30c97ba11efab9e15) passed all 10 triggered workflows, 208 Python tests, documentation checks and 13 hosted PostgreSQL/HTTP/browser scenarios, including the full invented-data rehearsal. [TCP readiness 270e977](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/270e9776fbd851f6d9902449e030817c38da4ff9) adjusted only the container readiness probe. [One-time marker 1290a1d](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/1290a1da25b1117d3c0ff9afe2799bd838ec733d) triggered [private live rehearsal 45375702613](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45375702613), attempt 1, job 138381304147, successful. All 8 workflows triggered on marker commit passed. Focused offline collection/intake suite passed 16 tests before live collection; full invented PostgreSQL rehearsal also passed. No uploaded artifacts.

Aggregate source collection at 2026-11-24T10:32:36.930897+00:00: sales 2,107, assessment 26,296, geography 137, address 137. Source epochs unchanged: sales wvhk-k5uv 1794745762, assessment x54s-btds 1794760638, geography nj4t-kc8j 1794758349, address 3723-97qp 1794745694. Eligible Class 203 sales 142 (83 in 2024, 59 in 2025); 137 distinct prior parcel-year keys, all 137 nonblank single address rows, neighbourhood and coordinate pairs; zero shared labels, ambiguous/missing/blank address states. Canonical PostgreSQL stored 142 sales, 137 parcel-year assessments, four source snapshots; exact-cent row verification, idempotent reimport, external relational seal and four restricted-role permission denials passed. All 59 eligible 2025 subjects reviewed by restricted reader, and all 59 by unique address token with equal redacted result. Canonical pure-matcher parity on status, tier, reason and selected count for 59/59: 41 supported neighbourhood, 18 exploratory spatial fallback, zero insufficient; 261 selected comparables in total (not distinct transactions). No valuations, saved investigations or row-level disclosure. Disposable database and role removed. This is real-source intake-to-private-reader acceptance, not real HTTP/React or production acceptance.

The single authorised live collection is consumed. Preserve marker and run history; no rerun, new extraction, durable real data storage, provider provisioning, public property display, deployment, valuation or main merge under this authority. Historical availability, physical building identity, public display terms and actual production security/recovery remain unverified. All full phase exits remain open. Owner-approved weighted progress remains 87.1%; do not assign additional credit without score review.

Next highest-value work: production release contract and buyer evidence field projection, then separately approved controlled durable real-data ingestion and real buyer API/browser acceptance (with public release as a distinct decision). Prepare offline using existing V4 synthetic source-shaped records and the verified historical reader; avoid another speculative architecture or unapproved extraction. Real property data were removed after rehearsal, so there is no live database to activate now.


## 24 November 2026: Buyer Product Release Preparation V1
Continue offline release preparation after verified private rehearsal. Correct client comparable cardinality without changing matcher or shortlist capacity; verify five source-shaped invented comparables through existing buyer runtime. Proposed field display contract, no actual release grant. See [contract](engineering/BUYER_PRODUCT_RELEASE_PREPARATION_V1.md).


## Buyer evidence preview continuation
Five-sale correction 55d6799 passed 11/11. Implement an explicit minimised read-only fixture projection from verified frozen evidence under existing owner boundary; reject historical source and approval flags. No real route, extra collection, release or matcher change. See [contract](engineering/BUYER_PRODUCT_RELEASE_PREPARATION_V1.md).
