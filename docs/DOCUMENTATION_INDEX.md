# Documentation index and source-of-truth rules

**Reviewed:** 23 November 2026. **Purpose:** Reduce documentation drift across research experiments, P0–P8 delivery planning and application implementation.

## What to read first

| Need | Canonical document | Status |
| --- | --- | --- |
| Start a new AI/code session | [Master continuation prompt](MASTER_CONTINUATION_PROMPT.md) and [repository instructions](../AGENTS.md) | **Current operating protocol**, defer to verified status and approvals |
| Pick up active work | [Current checkpoint](CHECKPOINT.md) | **Current**, factual snapshot and next acceptance/design gate |
| Inspect latest documentation cleanup | [Post-P6 documentation reconciliation audit](reviews/POST_P6_DOCUMENTATION_RECONCILIATION_AUDIT_2026-11-23.md) | **Dated audit**, current-source corrections, unchanged phase scores, unresolved mapping and release gates; not another current checkpoint |
| Understand percentages and phase gates | [P0–P8 roadmap](P_PHASE_ROADMAP.md) | **Current planning baseline**, 22.8% estimated |
| Check open choices | [Decision register](DECISIONS.md) | **Current**, confirmed vs unapproved |
| Understand the buyer experience | [Product brief](product/PRODUCT_BRIEF.md) | **Current product intent**, not implemented functionality |
| Review UX research and visual concepts | [UX research and product direction, 23 Nov](design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md) | **Exploratory, not approved**; inspiration, palettes, screen architecture, accessibility and design decisions |
| Review professional UI baseline proposal | [Visual Foundation V1 implementation proposal](design/VISUAL_FOUNDATION_V1_IMPLEMENTATION_PROPOSAL_2026-11-23.md) | **Owner review pending**; proposes screen hierarchy, prototype tokens, staged frontend work and acceptance tests; no UI changes approved |
| Review interactive visual-map concepts | [Map-linked Visual Study V1 review](design/MAP_LINKED_VISUAL_STUDY_V1_REVIEW_2026-11-23.md) and [offline HTML prototype](../design-prototypes/map-evidence-studio.html) | **Review-ready standalone fiction-only study**; two visual directions, linked diagram/card selection, responsive UI and shortlist; no integration, accurate geography or style approval |
| Review map and professional-UI grey areas | [Professional UI and mapping research](design/PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md) | **Research only**; map data coordinate blocker, renderer/provider/legal/CSP separations, linked-map buyer UX, frontend choices, cost/security/a11y/performance gates |
| Review tested MapLibre v6 frontend feasibility | [React/MapLibre compatibility spike](design/REACT_MAPLIBRE_V6_COMPATIBILITY_SPIKE_2026-11-23.md) | **Passing small Vite/TypeScript/Chromium WebGL proof** with bundle measurements; not a source/property map acceptance |
| Review full React ESM hosted validation | [24 Nov exact-source WebGL verification](design/REACT_FULL_ESM_HOSTED_VALIDATION_2026-11-24.md) and [23 Nov preliminary offline study](design/REACT_FULL_UI_SOURCE_VALIDATION_2026-11-23.md) | **6/6 real Chrome/Vite ESM UI tests including MapLibre WebGL ready, clean npm ci, 320px/375px and bundle measurements** on isolated feature branch; **no framework adoption, geographic-map permission or merge approval** |
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

## Terminology: two separate kinds of phases

- **Data research experiments:** `audit/phase0` = sales/buildings data feasibility; `audit/phase1` = Class 203 neighbourhood enrichment; `audit/phase2` = explainable comparable matcher. All three were executed in the cloud on 22 November 2026.
- **Portfolio delivery phases:** **P0–P8**, covering discovery through deployed application. The official recorded weighted baseline remains **22.8%**. P3 contract acceptance is open, while P4/P5/P6 *synthetic implementations* are CI-verified and integrated into `development`, not phase-accepted. Passing the Phase 0–2 data experiments does not mean delivery P0/P1/P2 are accepted or finished.

## Document precedence and maintenance

1. **Raw historical experiment figures:** cite the original dated findings and GitHub run. Do not overwrite numbers to fit a new narrative; publish a new run report if data or code changes.
2. **Current project position:** use `CHECKPOINT.md` for the latest verified status, `DECISIONS.md` for decisions requiring owner approval and `P_PHASE_ROADMAP.md` for phase weights/gates.
3. **Original proposals and old checkpoints:** retain their original wording with a clear dated **historical snapshot** banner, or archive them. Never leave an old "not run" statement presented as current after the run succeeds.
4. **Changes:** update checklist/status only when evidence supports it. Document changed assumptions, a rejected result and next gate. Do not inflate progress for docs edits. UX concepts, palettes and wireframes are proposals until expressly accepted.
5. **Public data and privacy:** do not publish raw extracts, property-level records, owner names, API secrets or personal client information. Research artifacts are aggregate-only. Source-specific public display/reuse is unapproved.
6. **External source documents:** the PilotODIN P0–P8 framing is an **adaptation** of its complexity-last phase-gating method, not a copy of PilotODIN's Windows/AI release requirements. See the [P-stage roadmap](P_PHASE_ROADMAP.md) for methodology and provenance.

## Active engineering handoff

**Canonical snapshot:** [CHECKPOINT.md](CHECKPOINT.md), with exact `development` SHA and verified CI. Use [DECISIONS.md](DECISIONS.md) for owner-approved versus blocked choices and the [80-package P0–P8 roadmap](P_PHASE_ROADMAP.md) for individual acceptance tests. Do not use dated review reports as the current action list.

**Working method:** The single permanent `development` branch receives authorised code/docs and hosted checks. Stable `main` receives milestone changes only through explicitly approved integration PRs. [Workflow](engineering/CLOUD_FIRST_WORKFLOW.md). No routine direct-to-main commits.

**Current capability boundary:** Synthetic local address search, explicit same-street parcel choice, source-bound investigation, exact-decimal comparable prices, v1–v3 versioned SQLite fixtures, opt-in restart-safe frozen investigations, and two-to-three-property shortlist with notes/comparison are CI-tested on `development` after approved PRs #5 and #6. This is **not owner-accepted P3–P6 or a released application**. There is no verified map UI/coordinate contract: all six original fictional parcel positions overlap. There is no real-address resolver, real property display permission, production database, accepted visual UX or deployment. See the [current P3 contract](engineering/P3_APPLICATION_CONTRACT.md). The original locally tested Windows safety patch was separate historical work; PR #3 independently merged the frozen comparable integrity safeguard.

**Phase scores:** P3 **10%**, weighted MVP **22.8%**, unchanged until relevant owner acceptance. Earlier 23 November test counts and staged commits are retained in Git history, [dated audits](reviews/) and [checkpoint references](CHECKPOINT.md), not duplicated as multiple competing current handoffs.
