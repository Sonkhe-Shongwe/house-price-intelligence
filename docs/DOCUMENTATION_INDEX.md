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
| Run the two-branch development station | [Cloud-first development operations](engineering/CLOUD_FIRST_WORKFLOW.md) | **Current operating method:** ongoing `development`, accepted `main`, hosted CI implemented |
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

**Execution model refined 23 November 2026:** One GitHub repository with a permanent `development` branch, stable `main`, GitHub Actions verification on both and reviewed PRs only at meaningful integration milestones. The committed CI now enforces JavaScript syntax and three real Chromium browser-to-HTTP-to-SQLite journeys, in addition to 128 Python tests and documentation checks. Windows remains for indispensable owner/platform acceptance. [Operating method](engineering/CLOUD_FIRST_WORKFLOW.md).

**Current work is P3 contract acceptance and review of the first synthetic buyer-search workflow on `development`:** [Main CI 45184193870](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45184193870) verifies 128 Python tests, enforced JavaScript and three hosted Chromium journeys. Frozen comparable price and source-snapshot guarding was integrated in PR #3. The later development-only address-selection candidate passed [132 Python and 5 browser checks](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45193537292) at `07f637b` and remains in draft PR #4, not accepted on `main`. Other historical local patch contents are not automatically integrated. Source rights, consumer identity, exact-money output contract, ERD approval, final UX and persistent shortlist remain open. See [checkpoint](CHECKPOINT.md) and [continuity audit](reviews/CONTINUITY_AND_DIRECTIVE_AUDIT_2026-11-23.md).

See [latest checkpoint](CHECKPOINT.md).
