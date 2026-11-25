# Documentation index and source-of-truth rules

**Reviewed:** 25 November 2026. **Purpose:** Reduce documentation drift across research experiments, P0–P8 delivery planning and application implementation.

## What to read first

| Need | Canonical document | Status |
| --- | --- | --- |
| Start a new AI/code session | [Master continuation prompt](MASTER_CONTINUATION_PROMPT.md) and [repository instructions](../AGENTS.md) | **Current operating protocol**, defer to verified status and approvals |
| Pick up active work | [Current checkpoint](CHECKPOINT.md) | **Current**, factual snapshot and next acceptance/design gate |
| Inspect latest documentation cleanup | [Current checkpoint](CHECKPOINT.md) | 25 November status-ledger consolidation; older [Post-P6 audit](reviews/POST_P6_DOCUMENTATION_RECONCILIATION_AUDIT_2026-11-23.md) remains historical |
| Active database workstream | [Neon Cloud Integration V1](engineering/NEON_CLOUD_INTEGRATION_V1.md) | Restricted TLS, persistent invented buyer journey and disposable encrypted recovery accepted; protected storage open |
| Active private beta boundary | [Private Real-Data Beta V1](engineering/PRIVATE_REAL_DATA_BETA_V1.md) | Conditional extraction unused; actual identity blocked on token timing; no deployment or real buyer route |
| Understand percentages and phase gates | [P0–P8 roadmap](P_PHASE_ROADMAP.md) | **Current planning baseline**, 87.1% estimated |
| Check open choices | [Decision register](DECISIONS.md) | **Current**, confirmed vs unapproved |
| Understand the buyer experience | [Product brief](product/PRODUCT_BRIEF.md) | **Current product intent**, not implemented functionality |
| Review UX research and visual concepts | [UX research and product direction, 23 Nov](design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md) | **Exploratory, not approved**; inspiration, palettes, screen architecture, accessibility and design decisions |
| Review professional UI baseline proposal | [Visual Foundation V1 implementation proposal](design/VISUAL_FOUNDATION_V1_IMPLEMENTATION_PROPOSAL_2026-11-23.md) | **Owner review pending**; proposes screen hierarchy, prototype tokens, staged frontend work and acceptance tests; no UI changes approved |
| Review interactive visual-map concepts | [Map-linked Visual Study V1 review](design/MAP_LINKED_VISUAL_STUDY_V1_REVIEW_2026-11-23.md) and [offline HTML prototype](../design-prototypes/map-evidence-studio.html) | **Review-ready standalone fiction-only study**; two visual directions, linked diagram/card selection, responsive UI and shortlist; no integration, accurate geography or style approval |
| Review map and professional-UI grey areas | [Professional UI and mapping research](design/PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md) | **Research only**; map data coordinate blocker, renderer/provider/legal/CSP separations, linked-map buyer UX, frontend choices, cost/security/a11y/performance gates |
| Review tested MapLibre v6 frontend feasibility | [React/MapLibre compatibility spike](design/REACT_MAPLIBRE_V6_COMPATIBILITY_SPIKE_2026-11-23.md) | **Passing small Vite/TypeScript/Chromium WebGL proof** with bundle measurements; not a source/property map acceptance |
| Review full React ESM hosted validation | [24 Nov exact-source WebGL verification](design/REACT_FULL_ESM_HOSTED_VALIDATION_2026-11-24.md) and [23 Nov preliminary offline study](design/REACT_FULL_UI_SOURCE_VALIDATION_2026-11-23.md) | **6/6 real Chrome/Vite ESM UI tests including MapLibre WebGL ready, clean npm ci, 320px/375px and bundle measurements** on isolated feature branch; **no framework adoption, geographic-map permission or merge approval** |
| Review integrated synthetic map | [Synthetic Geographic Evidence V1](engineering/SYNTHETIC_GEOGRAPHIC_EVIDENCE_V1.md) | Owner-authorised implementation; verify exact-head CI, no real geography or release |
| Review workspace consolidation | [Buyer Workspace and UX V1](engineering/BUYER_WORKSPACE_UX_V1.md) | Owner-authorised implementation; P3.1–P3.7 provisional synthetic acceptance, verify CI |
| Review production/data readiness | [Production Architecture and Data Readiness V1](engineering/PRODUCTION_READINESS_V1.md) | PostgreSQL candidate, synthetic CI and bounded aggregate research authorised; no deployment |
| Apply quality/invariants | [Engineering contract](engineering/ENGINEERING_CONTRACT.md) | **Binding engineering guardrails** |
| Develop efficiently and consistently | [Lean engineering directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md) | **Active eight-step engineering process**, approved 23 Nov |
| Run the two-branch development station | [Cloud-first development operations](engineering/CLOUD_FIRST_WORKFLOW.md) | **Current operating method:** ongoing `development`, accepted `main`, hosted CI implemented |
| Inspect integrated P3 app | [P3 application contract](engineering/P3_APPLICATION_CONTRACT.md) | **Synthetic-only code/HTTP/SQL/UI review candidate; acceptance pending** |
| Review integrated P6 shortlist | [P6 synthetic shortlist contract](engineering/P6_SYNTHETIC_SHORTLIST_CONTRACT.md) | **Merged to `development` as PR #6**, synthetic-only; phase exit and access/privacy decisions still open |
| Interpret source use | [Source register](research/SOURCE_REGISTER.md) | **Current research provenance**, rights still pending |
| Find verified counts | [Phase 0](research/PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1](research/PHASE1_CLOUD_AUDIT_RESULTS.md), [Phase 2](research/PHASE2_CLOUD_AUDIT_RESULTS.md) | **Dated immutable experiment summaries** |
| Re-run research | [Cloud audit operations](AUTOMATED_DATA_AUDIT.md) | **Current operating guide** |
| See the original 11 grey areas | [23 Nov continuity/directive audit](reviews/CONTINUITY_AND_DIRECTIVE_AUDIT_2026-11-23.md) | **Dated risk review**, some implementation findings superseded by current code; unresolved rights/identity risks still relevant |
| See the new development-process audit | [23 Nov cloud-first documentation audit](reviews/CLOUD_FIRST_DELIVERY_DOCUMENTATION_AUDIT_2026-11-23.md) | **Dated workflow audit**; does not supersede technical P3 evidence or phase estimates |
| See earlier process adoption | [23 Nov directive audit](reviews/ENGINEERING_DIRECTIVE_AUDIT_2026-11-23.md) | Historical dated process change, not latest implementation state |
| See earlier cleanup | [22 Nov documentation audit](reviews/DOCUMENTATION_AUDIT_2026-11-22.md) | **Retained historical audit** |
| Review old scope/origins | [Pinnacle vision](product/PINNACLE_VISION.md), [Migration manifest](MIGRATION_MANIFEST.md), [archived roadmap](archive/INITIAL_ROADMAP_2026-11-22.md) | **Historical/reference**, not current status |

**Earlier RD1–RD7 contract:** [Real Data Integration Readiness V1](engineering/REAL_DATA_READINESS_V1.md), bounded cohort audit and synthetic-only ingestion/guard.

**Earlier runtime contract:** [Production Runtime Integration V1](engineering/PRODUCTION_RUNTIME_V1.md), fictional accounts, PostgreSQL HTTP and revision candidate.

**Consolidation contract:** [Production Consolidation V1](engineering/PRODUCTION_CONSOLIDATION_V1.md).

**Product intelligence contract:** [PI1–PI8](engineering/PRODUCT_INTELLIGENCE_V1.md); [recruiter walkthrough](product/RECRUITER_WALKTHROUGH_V1.md).

**Final acceptance contract:** [FA1–FA8](engineering/FINAL_ACCEPTANCE_V1.md); [local release runbook](engineering/RELEASE_RUNBOOK_V1.md).

**Full product qualification:** [FR1–FR3](engineering/FULL_RELEASE_QUALIFICATION_V1.md).

## Terminology: two separate kinds of phases

- **Data research experiments:** `audit/phase0` = sales/buildings data feasibility; `audit/phase1` = Class 203 neighbourhood enrichment; `audit/phase2` = explainable comparable matcher. All three were executed in the cloud on 22 November 2026.
- **Portfolio delivery phases:** **P0–P8**, covering discovery through deployed application. The current owner-authorised planning estimate is **87.1%** (24 November 2026); prior baselines 85.7%, 84.0%, 83.6%, 79.2%, 76.1%, 71.4%, 66.5%, 62.9% and 22.8%. P3 contract acceptance is open, while P4/P5/P6 *synthetic implementations* are CI-verified and integrated into `development`, not phase-accepted. Passing the Phase 0–2 data experiments does not mean delivery P0/P1/P2 are accepted or finished.

## Document precedence and maintenance

1. **Raw historical experiment figures:** cite the original dated findings and GitHub run. Do not overwrite numbers to fit a new narrative; publish a new run report if data or code changes.
2. **Current project position:** use `CHECKPOINT.md` for the latest verified status, `DECISIONS.md` for decisions requiring owner approval and `P_PHASE_ROADMAP.md` for phase weights/gates.
3. **Original proposals and old checkpoints:** retain their original wording with a clear dated **historical snapshot** banner, or archive them. Never leave an old "not run" statement presented as current after the run succeeds.
4. **Changes:** update checklist/status only when evidence supports it. Document changed assumptions, a rejected result and next gate. Do not inflate progress for docs edits. UX concepts, palettes and wireframes are proposals until expressly accepted.
5. **Public data and privacy:** do not publish raw extracts, property-level records, owner names, API secrets or personal client information. Research artifacts are aggregate-only. Source-specific public display/reuse is unapproved.
6. **External source documents:** the PilotODIN P0–P8 framing is an **adaptation** of its complexity-last phase-gating method, not a copy of PilotODIN's Windows/AI release requirements. See the [P-stage roadmap](P_PHASE_ROADMAP.md) for methodology and provenance.

## Active engineering handoff

Use [CHECKPOINT.md](CHECKPOINT.md) as the only current state/next-task ledger; [DECISIONS.md](DECISIONS.md) for authority and [P_PHASE_ROADMAP.md](P_PHASE_ROADMAP.md) for phase gates. [Master prompt](MASTER_CONTINUATION_PROMPT.md) and [cloud-first workflow](engineering/CLOUD_FIRST_WORKFLOW.md) define standing autonomy, one permanent development branch and stable main. Earlier design and engineering contracts describe their dated scope, not the latest project status.

Active: [Neon Cloud Integration V1](engineering/NEON_CLOUD_INTEGRATION_V1.md) within [Private Real-Data Beta V1](engineering/PRIVATE_REAL_DATA_BETA_V1.md). See checkpoint for the actual identity timing diagnostic and next action. Disposable encrypted recovery verified; managed recovery and protected storage open. P4 95%, P7 83%, P8 35%; **87.1%** weighted, all gates open. [Pre-cleanup index](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/1dbcb6aba082af909ee3fe79d5b0a1cfec8cc867/docs/DOCUMENTATION_INDEX.md).
