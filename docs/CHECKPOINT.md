# House Price Intelligence: current checkpoint

27 November 2026. Sole live routing ledger. [Roadmap](P_PHASE_ROADMAP.md) governs gates/progress; [decisions](DECISIONS.md) governs authority. Schema v2: verify inclusive ranges at HEAD. No inferred permission; phase gates open.

## Continuation state

```json
{"schema_version":2,"active_phase":"P0","phase_gate":"blocked","task":{"id":"P0-C-MARKET-GATE-REVIEW","status":"ready","objective":"Restore geography-flexible first-market qualification and identify the smallest unresolved evidence path.","scope":"Read-only public terms, metadata and existing evidence; Cook reference, NYC and England/Wales challengers; no SA work, intake, contact or migration.","acceptance":"Compare mandatory transaction, identity, dated attributes, entry/coverage, permitted operations and R0 protection gates; distinguish resolved evidence, remaining gaps and one justified next decision.","read":["docs/DECISIONS.md","docs/P_PHASE_ROADMAP.md","docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md","docs/engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md","docs/research/DATA_FEASIBILITY.md","docs/research/SOURCE_REGISTER.md","docs/product/PRODUCT_BRIEF.md"],"evidence":["docs/research/DATA_FEASIBILITY.md","docs/research/SOURCE_REGISTER.md","docs/product/COMPETITIVE_INTELLIGENCE_2026-11-26.md","docs/engineering/PRIVATE_REAL_DATA_BETA_V1.md","docs/engineering/PRODUCTION_READINESS_V1.md"],"stop":"Stop at bounded comparative review or indispensable approval/protection blocker; no phase acceptance or automatic market choice.","read_ranges":{"docs/DECISIONS.md":[[13,16,"| Engineering process (approved 23 Nov) | Eight-step requirement","| Research-driven evolution (26 Nov, owner clarification) | Exis"],[24,29,"| Single active phase (26 Nov, owner direction) | Begin P0 closu","| Dedicated HPI-SA mission (26 Nov, historical; terminated 27 No"],[176,178,"## Proportionate public-data research (27 November 2026)","Owner direction: do not be excessively strict about licences and"],[236,238,"## Owner decision: end South African-first mission (27 November ","Owner directs: abandon and abolish the South African narrative. "]],"docs/P_PHASE_ROADMAP.md":[[13,32,"### Progress methodology","| **Total** | **Bounded flagship MVP** | **100%** | **87.1% weig"],[68,82,"### P0 | Buyer, market and product feasibility | Weight 6% | App","**26 November initial P0 closure audit (preserved baseline; exec"],[227,235,"### P0: Discovery and feasibility — 6% weight; 94% estimated com","**Exit gate:** Approved bounded product brief, source register, "]],"docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md":[[110,131,"## 6. Eight-step feature engineering lifecycle (approved 23 Nove","Each substantial change should identify its outcome, affected bo"],[162,169,"## 9. Safe large changes, migrations and CI controls","- Apply the same review to AI-assisted and human code. No LLM ou"]],"docs/engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md":[[5,33,"**27 November owner direction:** HPI-SA mission terminated; resu","Do not turn optional methods (SWOT, persona variants, full comme"]],"docs/research/DATA_FEASIBILITY.md":[[172,211,"## 26 November 2026 | P0-C alternative-market gaps and minimum v","**Stopping criterion:** incumbent/challenger/secondary critical "]],"docs/research/SOURCE_REGISTER.md":[[114,165,"## 26 November 2026 | P0-D.1 source-specific permitted-use recon","**P0-D.1 complete as documentary reconciliation. P0.5/P0.7 remai"]],"docs/product/PRODUCT_BRIEF.md":[[63,72,"### 2. Supported-market contract: explicit conditional boundary","Use [P0-C conditional review](../research/DATA_FEASIBILITY.md#26"]]}},"blockers":["P0.4/6 partial: no qualified contemporary subject entry, transaction/temporal semantics or final market/class.","P0.5/7 blocked: exact permitted operations, protection and R0 release path unresolved; Cook publisher contact/rekey deferred."],"parked":["HPI-SA mission terminated; City submission historical, no active grant dependency or further SA-specific work","P1-P8 except indispensable named P0 dependencies","Real basemap attempt unused/deferred on upstream extractor security","Cook publisher contact and recovery rekey owner-deferred","Wikidata pilot consumed; owner parked","GHSL attempts closed pending material evidence","D02-P1/P2 exact API pilot closed; no replay","Windows Security repair and local protection verification owner-deferred"],"authority":["docs/DECISIONS.md","docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md","docs/engineering/CLOUD_FIRST_WORKFLOW.md"],"history":["docs/archive/CONTINUATION_CHECKPOINT_2026-11-26.md","docs/archive/CHECKPOINT_EVIDENCE_2026-11-26.md","docs/archive/DECISION_HISTORY_2026-11-26.md","docs/archive/DELIVERY_MILESTONE_HISTORY_2026-11-26.md"]}
```

## Historical South African data repertoire

| Dataset | Owner-observed outcome | Qualification limit |
| --- | --- | --- |
| HPI-DATA-001 | 49 usable OSM ways; closed, no raw retained | No maintained source |
| HPI-DATA-002 | 19 RPPI series, 157 months, 2,983 observations | Aggregate historical indices only |
| HPI-DATA-003 | 52 valid district features, 2020 geography | 52/52 name candidates; identity/topology unverified |
| HPI-DATA-004 | 289,864 usable of 289,867 footprint records | All height/confidence missing; 673 outside tile centroids |
| HPI-DATA-005 | 52 official district/metro codes, visual match confirmed | Census 2022; 0 unmatched, noncommercial |
| HPI-DATA-006 | Two metros, six RPPI observations, four growth checks | June 2026 fixed release, no merge or valuation |
| HPI-DATA-008 | 16 household service percentages, two metros | 2011/2022 aggregate, no property reliability inference |
| HPI-DATA-009 | 25,505 institutions; 19,412 plausible mapped candidates | Q3 2023; 6,093 unmapped; no verified locations |
| HPI-DATA-010 | 3,442 retained; 3,421 spatial candidates; audit passed | Pinelands only; private; review by 27 Dec 2026 |
| HPI-DATA-011 | 839 sales; 340 candidate sales, 330 parcels | Audit passed; review by 27 Dec 2026 |

002-006, 008/009 registered with null deadlines; 010/011 registered and audited; fixed deadlines; 005/006/008 private noncommercial. 007 parked. 006/008 integrity/re-extraction and 009 owner-observed integrity passed; private bytes not inspected. D01/D02/D03/D07/D08/D09/D11 partial; other families unresolved. Open repertoire source terms/law prevail; restricted real-property beta retains separate 30-day maximum and approval-controlled disposal. No automatic deletion, raw/derived private data in public Git/CI or real buyer activation. [Acquisition register](research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md), [Data Manager](engineering/DATA_MANAGER_V1.md), [prior audit](reviews/DATA_FIRST_REPOSITORY_AUDIT_2026-11-26.md). Windows sibling workspace; private bytes not independently verified.

## Repository and verification

Requery `development` and `main` heads and exact CI. 185c78e 10/10 exact runs passed; [53 browser tests](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/46026557508/job/140599330388). Main 103c854; PR #4 historically draft. No phase credit.

## Current verified implementation on development

Integrated fictional React/TypeScript buyer journey, exact-cent evidence, two-to-three-property shortlist, comparison/notes, SQLite and disposable PostgreSQL. Direct restricted Neon TLS and persistent invented journey qualified. Actual isolated Auth0 and combined invented save/compare/reopen/sign-out observed; combined restart, notes, cross-owner/old-cookie probes unverified. FE1-FE7 core qualified, Atlas owner-approved; generated contextual PMTiles qualified, no real tiles acquired. Automated accessibility and known-advisory gates passed on recorded application revisions, not final manual or production qualification. [Frontend directive](engineering/PROFESSIONAL_FRONTEND_EXCELLENCE_DIRECTIVE.md), [engineering evidence archive](archive/CHECKPOINT_EVIDENCE_2026-11-26.md).

## Actual Auth0 identity qualification: local milestone verified

See [historical checkpoint](archive/CONTINUATION_CHECKPOINT_2026-11-26.md) and [private beta contract](engineering/PRIVATE_REAL_DATA_BETA_V1.md). Temporary certificate cleanup not owner-confirmed; no replay of consumed login windows or collection of secrets.

## Recovery, storage and access gates

Independent invented-only encrypted recovery demonstrated; key non-exposure not accepted, owner deferred rekey after refusal. Both restricted roles NOLOGIN and zero sessions at last independent observation; no new connection necessary. Free provider storage/network/recovery limitations, direct-grant inventory and permitted use open. Owner 2FA attestation not independent per-provider evidence; consolidate final rundown, no repetitive checks. [Neon contract](engineering/NEON_CLOUD_INTEGRATION_V1.md), [beta](engineering/PRIVATE_REAL_DATA_BETA_V1.md).

## Research and data-use boundary

SA-first mission terminated by owner; no SA-specific development or City dependency remains active. Geography-flexible, data-first P0-C restored; no final market approved. Cook County Class 203/Evanston retained measured research benchmark, not blanket coverage/valuation. Asking price, completed sales and estimates distinct. Exploratory 2 km candidate evidence not valuation. No property-level publication, model training or price prediction approval. [Feasibility](research/DATA_FEASIBILITY.md), [SA mission](engineering/SOUTH_AFRICAN_MISSION_DIRECTIVE.md).

## Active work and next acceptance task

P0-A accepted; B complete; C/D/E conditional; F/G not accepted. Resume ordinary P0-C comparative gate review: retain the completed Cook empirical boundary, NYC and England/Wales desk comparison and P0-D field matrix; identify only material unresolved source terms, event/entry/time and R0 protection evidence. Prefer public publisher-wide terms and authoritative metadata; no new records, joins, contact or speculative implementation. If the desk path cannot settle a mandatory gate, present one narrowly scoped next decision rather than restart prior studies. SA mission and optional fictional SA work terminated; City submission remains historical, grant unconfirmed. [Previous exact checkpoint](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/120618c70435790c1ba3d04f2dbb530ec7d92f3f/docs/CHECKPOINT.md) preserves complete SA milestones, approvals and prior blockers. 010/011 review deadlines unchanged; no automatic disposal/renewal. Cook contact/rekey remain deferred. P0 remains blocked at exit, but the read-only review task is ready.

## Detailed engineering evidence and audit trail

[Historical checkpoint](archive/CONTINUATION_CHECKPOINT_2026-11-26.md), [engineering evidence](archive/CHECKPOINT_EVIDENCE_2026-11-26.md), [decision history](archive/DECISION_HISTORY_2026-11-26.md), [delivery history](archive/DELIVERY_MILESTONE_HISTORY_2026-11-26.md). 

## Continuation boundaries

[Master protocol](MASTER_CONTINUATION_PROMPT.md), [decisions](DECISIONS.md) and [P0 directive](engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md) govern autonomy and R0. Current phase does not waive rights or safety gates.

## Evidence versus acceptance

Roadmap estimates are not acceptance scores; no phase credit.

## Historical continuity and audit record

[Continuation optimisation audit](reviews/CONTINUATION_SYSTEM_AUDIT_2026-11-26.md). Historical snapshots retained.
