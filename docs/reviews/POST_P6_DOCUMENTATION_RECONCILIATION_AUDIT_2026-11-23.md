# House Price Intelligence: post-P6 documentation reconciliation audit

**Performed:** 23 November 2026. **Status:** Dated audit, NOT a replacement for the [live checkpoint](../CHECKPOINT.md), [decision register](../DECISIONS.md), or [P0–P8 roadmap](../P_PHASE_ROADMAP.md).

**Authority:** Documentation repair and checker updates on permanent development only. No app feature, frontend rewrite, branch deletion, merge to main, deployment, map/data-service integration, new rights approval or phase-score adjustment.

## 1. Scope, evidence and limits

- Inventoried **38 Markdown documents** (29 under docs/) in the development repository tree. This is a complete filename inventory, NOT a claim that every historical research document was semantically revalidated line by line.
- Inspected the active root README, frontend and backend guides, checkpoint, detailed and short roadmaps, master continuation prompt, decisions, product brief, engineering contracts, P3 and P6 contracts, UX/map research and the existing documentation checker.
- Compared those claims with the current backend and schema migrations, fictional parcel coordinates, GitHub branches, merged PRs and CI.
- [PR #5](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/5) and [PR #6](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/6) were owner-approved merges into development. The [application merge commit 44e278f](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/44e278f5ff68475616d889d2c7fafd0b5b3c6304) passed [172 Python and 9 real Chromium checks](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45254283750), JavaScript and docs. The subsequent [map-research documentation push](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45259478988) also passed. This audit's latest documentation commits need their own exact-HEAD checks.
- Historical source counts, provider terms and external web references were NOT independently re-verified as part of this internal-document audit. Prior dated studies remain dated research.

## 2. Corrected conflicts

| Severity | Outdated or misleading active guidance | Action |
| --- | --- | --- |
| High | Root README described only a P3 investigation and no durable shortlist | Described integrated fictional P3–P6 buyer workflow, optional local SQLite persistence and open owner gates |
| High | Frontend guide said all saved evidence disappears on shutdown, and notes/comparison were not implemented | Distinguished default in-memory from opt-in on-disk demo, documented shortlist, notes and side-by-side; updated actual 9 Chromium result |
| High | Roadmap treated already-implemented P6.3–P6.7 as OPEN, and P7.1 referenced 148/7 | Updated narrowly to VERIFIED in **fictional scope**, P6.9 and P4.10 PARTIAL, and 172/9; numerical stage scores unchanged |
| High | Active master handoff and decisions described older 5e0a7f3 / 148+7 review as current | Updated active v1.4 continuation and decision register to integrated 44e278f / 172+9; retained dated historical sections |
| High | P3 current contract asserted no restart persistence or completed P6 shortlist | Reconciled with trusted fixture-file mode, existing shortlist schema and integrated API, leaving production gates open |
| Medium | P3 migration caveat asserted foreign-key checks happened after committing | Verified current migration runner checks foreign keys before commit and rolls back on failure; no production recovery claim |
| Medium | Product brief called all acceptance criteria not implemented | Distinguished working fictional features from still unchecked owner/product criteria |
| Medium | Engineering guidance could be read as binding the project to vanilla JS | Recorded owner desire for exceptional design and stack-neutral, evidence-based technology evaluation |
| Medium | Proposed map could be mistaken for real geographic capability | Explicitly recorded the six identical fictional parcel coordinates and lack of approved source-owned map response |
| Medium | Link/percentage checker did not prevent specific obsolete active phrases returning | Extended narrow required/forbidden text checks; checker remains a limited regression tool |

## 3. Canonical ownership after cleanup

| Subject | Authoritative file |
| --- | --- |
| Current verified branches, tests, capabilities and next gate | [Checkpoint](../CHECKPOINT.md) |
| Decisions and approvals | [Decisions](../DECISIONS.md) |
| Stage weights, percentages, individual packages and exit requirements | [P0–P8 roadmap](../P_PHASE_ROADMAP.md) |
| Cross-session working instructions | [Continuation prompt](../MASTER_CONTINUATION_PROMPT.md) and [AGENTS](../../AGENTS.md) |
| Product and source interpretation | [Product brief](../product/PRODUCT_BRIEF.md), [P3 contract](../engineering/P3_APPLICATION_CONTRACT.md), [P6 contract](../engineering/P6_SYNTHETIC_SHORTLIST_CONTRACT.md) |
| Pending visual and mapping choice | [Visual Foundation V1](../design/VISUAL_FOUNDATION_V1_IMPLEMENTATION_PROPOSAL_2026-11-23.md), [mapping research](../design/PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md) |
| Dated research evidence | [Source register](../research/SOURCE_REGISTER.md) and original [Phase 0](../research/PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1](../research/PHASE1_CLOUD_AUDIT_RESULTS.md), [Phase 2](../research/PHASE2_CLOUD_AUDIT_RESULTS.md) |

Historical audits and prior implementation-stage paragraphs remain preserved as historical, not competing current handoffs. The check_docs script verifies links and arithmetic plus narrow handoff phrases; it does not independently validate every external URL, research claim, source licence or usability requirement.

## 4. Outstanding substantive decisions, not documentation defects

1. **Stage scoring and acceptance:** P3 remains 10%, weighted P0–P8 MVP 22.8%. These are recorded acceptance estimates, not an accurate count of implemented code. Formal owner P3/P4/P5/P6 review is still required.
2. **Geospatial integrity:** All six original fictional parcels have coincident dummy latitude/longitude; geographic map feature response, coordinate accuracy, parcel-vs-building semantics, snapshots and map provider permissions have not been approved. First map proof should be explicitly schematic and non-geographic.
3. **Real market and source rights:** Select defensible first geography/class, permitted property-level fields and publication-time/as-of treatment before any real property display.
4. **Professional design:** User wants exceptional visuals, without frontend framework restrictions. No React/Vue/Svelte/MapLibre selection, final aesthetic, high-fidelity connected map or accessibility acceptance is approved yet.
5. **Security/operations:** Local fictional note storage has no accounts, authentication, privacy isolation or production recovery. External tile requests add billing, privacy, CSP and attribution decisions.
6. **GitHub housekeeping:** Four merged-PR branches (#1/#2/#3/#5) still need authorised deletion through the GitHub UI because the connected toolset has no ref-delete action. PR #6 branch is separate and was not included in the four-branch deletion approval. Main remains stable; PR #4 remains draft and unmerged.
7. **Historical content:** Previous research counts, study illustrations, dated CI test counts and source reviews are left intact, not silently overwritten as if they were current.

## 5. Change ledger and next decision

**Updated:** root README, frontend guide, brief roadmap, detailed P0–P8 work-package states, active P3 contract, master continuation v1.4, current decisions, product brief, AGENTS, engineering contract, documentation checker, checkpoint and documentation index.

**Added:** this audit report. **Unchanged:** source/application code, data, backend API, stage weights, completion percentages, archived research, main, draft PR #4 and deployment state.

**Suggested next decision:** Review at least two high-fidelity desktop/mobile directions and an honestly fictional map/list interaction proof before choosing a renderer, tile vendor or frontend migration. Separately schedule an owner acceptance audit of the already-tested fictional P3–P6 implementation and source/rights blockers. Those steps are recommendations, not authorisations to implement or merge.
