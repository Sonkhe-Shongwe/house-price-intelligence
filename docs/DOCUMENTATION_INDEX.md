# Documentation index and source-of-truth rules

**Reviewed:** 23 November 2026. **Purpose:** Reduce documentation drift across research experiments, P0–P8 delivery planning and application implementation.

## What to read first

| Need | Canonical document | Status |
| --- | --- | --- |
| Start a new AI/code session | [Master continuation prompt](MASTER_CONTINUATION_PROMPT.md) and [repository instructions](../AGENTS.md) | **Current operating protocol**, defer to verified status and approvals |
| Pick up active work | [Current checkpoint](CHECKPOINT.md) | **Current**, factual snapshot and P3 next step |
| Understand percentages and phase gates | [P0–P8 roadmap](P_PHASE_ROADMAP.md) | **Current planning baseline**, 22.8% estimated |
| Check open choices | [Decision register](DECISIONS.md) | **Current**, confirmed vs unapproved |
| Understand the buyer experience | [Product brief](product/PRODUCT_BRIEF.md) | **Current product intent**, not implemented functionality |
| Review UX research and visual concepts | [UX research and product direction, 23 Nov](design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md) | **Exploratory, not approved**; inspiration, palettes, screen architecture, accessibility and design decisions |
| Apply quality/invariants | [Engineering contract](engineering/ENGINEERING_CONTRACT.md) | **Binding engineering guardrails** |
| Develop efficiently and consistently | [Lean engineering directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md) | **Active eight-step engineering process**, approved 23 Nov |
| Run the cloud-first development station | [Cloud-first development operations](engineering/CLOUD_FIRST_WORKFLOW.md) | **Owner-approved operating method**; CI enhancements staged, not yet implemented |
| Inspect integrated P3 app | [P3 application contract](engineering/P3_APPLICATION_CONTRACT.md) | **Synthetic-only code/HTTP/SQL/UI review candidate; acceptance pending** |
| Interpret source use | [Source register](research/SOURCE_REGISTER.md) | **Current research provenance**, rights still pending |
| Find verified counts | [Phase 0](research/PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1](research/PHASE1_CLOUD_AUDIT_RESULTS.md), [Phase 2](research/PHASE2_CLOUD_AUDIT_RESULTS.md) | **Dated immutable experiment summaries** |
| Re-run research | [Cloud audit operations](AUTOMATED_DATA_AUDIT.md) | **Current operating guide** |
| See continuity audit and 11 grey areas | [23 Nov continuity/directive audit](reviews/CONTINUITY_AND_DIRECTIVE_AUDIT_2026-11-23.md) | **Current P3 continuity review**, tested vs committed evidence and open technical risks |
| See the new development-process audit | [23 Nov cloud-first documentation audit](reviews/CLOUD_FIRST_DELIVERY_DOCUMENTATION_AUDIT_2026-11-23.md) | **Dated workflow audit**; does not supersede technical P3 evidence or phase estimates |
| See earlier process adoption | [23 Nov directive audit](reviews/ENGINEERING_DIRECTIVE_AUDIT_2026-11-23.md) | Historical dated process change, not latest implementation state |
| See earlier cleanup | [22 Nov documentation audit](reviews/DOCUMENTATION_AUDIT_2026-11-22.md) | **Retained historical audit** |
| Review old scope/origins | [Pinnacle vision](product/PINNACLE_VISION.md), [Migration manifest](MIGRATION_MANIFEST.md), [archived roadmap](archive/INITIAL_ROADMAP_2026-11-22.md) | **Historical/reference**, not current status |

## Terminology: two separate kinds of phases

- **Data research experiments:** `audit/phase0` = sales/buildings data feasibility; `audit/phase1` = Class 203 neighbourhood enrichment; `audit/phase2` = explainable comparable matcher. All three were executed in the cloud on 22 November 2026.
- **Portfolio delivery phases:** **P0–P8**, covering discovery through deployed application. The current overall weighted baseline is **22.8%**, with P3 integration review and acceptance next. Passing the three audit experiments does not mean delivery P0/P1/P2 are accepted or finished.

## Document precedence and maintenance

1. **Raw historical experiment figures:** cite the original dated findings and GitHub run. Do not overwrite numbers to fit a new narrative; publish a new run report if data or code changes.
2. **Current project position:** use `CHECKPOINT.md` for the latest verified status, `DECISIONS.md` for decisions requiring owner approval and `P_PHASE_ROADMAP.md` for phase weights/gates.
3. **Original proposals and old checkpoints:** retain their original wording with a clear dated **historical snapshot** banner, or archive them. Never leave an old "not run" statement presented as current after the run succeeds.
4. **Changes:** update checklist/status only when evidence supports it. Document changed assumptions, a rejected result and next gate. Do not inflate progress for docs edits. UX concepts, palettes and wireframes are proposals until expressly accepted.
5. **Public data and privacy:** do not publish raw extracts, property-level records, owner names, API secrets or personal client information. Research artifacts are aggregate-only. Source-specific public display/reuse is unapproved.
6. **External source documents:** the PilotODIN P0–P8 framing is an **adaptation** of its complexity-last phase-gating method, not a copy of PilotODIN's Windows/AI release requirements. See the [P-stage roadmap](P_PHASE_ROADMAP.md) for methodology and provenance.

## Active engineering handoff

**Execution model updated 23 November 2026:** One authoritative GitHub project, authorised short-lived branch and PR per milestone, GitHub Actions for most automated checks, Windows only when necessary for owner UX or platform acceptance. The current GitHub workflow still lacks enforced JavaScript and automated Chromium/SQLite graphical acceptance. [Operating method](engineering/CLOUD_FIRST_WORKFLOW.md). The owner's 23 November browser screenshots verify supported, reopen and safe unknown-PIN outcomes on the committed synthetic app; these are **manual evidence**, not new CI tests.

**Next work remains P3 product-contract acceptance and safety-patch integration review:** [Committed CI 45059455620](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45059455620) verifies **125** Python tests. Separate owner Windows screenshots establish **127 tests + 15 Chromium DOM cases + synthetic full browser/database flow** in an **isolated patched checkout**, not `main` CI. Source rights, legitimate consumer input, ERD, evidence versioning, final UX and permanent shortlist are outstanding. Do not mistake the map/colour studies for approved frontend. See [checkpoint](CHECKPOINT.md) and [continuity audit](reviews/CONTINUITY_AND_DIRECTIVE_AUDIT_2026-11-23.md).

See [latest checkpoint](CHECKPOINT.md).
