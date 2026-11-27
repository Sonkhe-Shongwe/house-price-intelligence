# House Price Intelligence: current checkpoint

Reviewed 27 November 2026. Sole live routing ledger. [Roadmap](P_PHASE_ROADMAP.md) governs gates/progress; [decisions](DECISIONS.md) governs authority. Schema v2 ranges: inclusive bounds and markers; verify at HEAD. No permission inferred. All full phase gates open.

## Continuation state

```json
{"schema_version":2,"active_phase":"P0","phase_gate":"blocked","task":{"id":"P0-CORE-D01-D02-MISMATCH-DIAGNOSIS","status":"blocked","objective":"Diagnose address mismatches and unsupported formats without promoting candidates.","scope":"Proposed pinned 010/011 private aggregate diagnostic; separate approval required.","acceptance":"Reason counts or abstention; preserve 420/409/266 baseline.","read":["docs/engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md","docs/research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md","docs/DECISIONS.md","docs/P_PHASE_ROADMAP.md","docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md","docs/product/PRODUCT_BRIEF.md","docs/engineering/DATA_MANAGER_V1.md","docs/engineering/ACQUISITION_INTELLIGENCE_SIDE_DIRECTIVE.md"],"evidence":["docs/research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md","docs/product/PRODUCT_BRIEF.md","docs/engineering/DATA_MANAGER_V1.md","docs/engineering/ACQUISITION_INTELLIGENCE_SIDE_DIRECTIVE.md","docs/reviews/DATA_FIRST_REPOSITORY_AUDIT_2026-11-26.md"],"stop":"No additional private diagnostic without approval; no join, acquisition, model or app.","read_ranges":{"docs/engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md":[[11,31,"## 2. Research -> analysis -> planning -> implementation -> verif","Do not turn optional methods (SWOT, persona variants, full commer"],[109,160,"## 26 November 2026 | P0-G independent conditional acceptance aud","[Pinelands empirical evidence]"]],"docs/research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md":[[698,712,"## 27 November 2026 | D01-F1 approved local sales table export","Owner-observed 420 screened"],[714,727,"## 27 November 2026 | D01/D02 documentary cadastral corroboration","Documentary milestone complete;"]],"docs/DECISIONS.md":[[13,16,"| Engineering process (approved 23 Nov) | Eight-step requirements","| Research-driven evolution (26 Nov, owner clarification) | Exist"],[24,60,"| Single active phase (26 Nov, owner direction) | Begin P0 closur","| Boundaries | Do not claim current price prediction, live listin"],[74,87,"## Open decisions, with next acceptance point","| Which buyer entry and property identity? | Address/parcel/build"],[99,106,"## Non-negotiable interpretation rules","- Missing evidence requires an explicit abstention/unsupported st"],[176,202,"## Proportionate public-data research (27 November 2026)","Owner explicitly approves HPI-DATA-011 private offline"],[204,206,"## HPI-DATA-010/011 strict corroboration authority (27 November 2026)","Owner explicitly approves th"]],"docs/P_PHASE_ROADMAP.md":[[13,32,"### Progress methodology","| **Total** | **Bounded flagship MVP** | **100%** | **87.1% weigh"],[68,82,"### P0 | Buyer, market and product feasibility | Weight 6% | Appr","**26 November initial P0 closure audit (preserved baseline; execu"],[227,235,"### P0: Discovery and feasibility — 6% weight; 94% estimated comp","**Exit gate:** Approved bounded product brief"]],"docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md":[[110,131,"## 6. Eight-step feature engineering lifecycle (approved 23 Novem","Each substantial change should identify its outcome, affected bou"],[162,169,"## 9. Safe large changes, migrations and CI controls","- Apply the same review to AI-assisted and human code. No LLM out"]],"docs/product/PRODUCT_BRIEF.md":[[218,220,"### 27 November 2026 | Core comparable-sales feasibility update","The original Investigate"]],"docs/engineering/DATA_MANAGER_V1.md":[[340,348,"## HPI-DATA-011 approved registration","Next justified work:"],[350,354,"## HPI-DATA-010/011 approved strict corroboration implementation (27 November 2026)","Synthetic CI covers repeat s"],[356,362,"## HPI-DATA-010/011 actual strict corroboration milestone (27 November 2026)","Next proposed bounded task"]],"docs/engineering/ACQUISITION_INTELLIGENCE_SIDE_DIRECTIVE.md":[[294,298,"## 27 November 2026 | D11 HPI-DATA-009 actual","Next bounded task:"],[300,302,"## 27 November 2026 | D11 offline integrity milestone","Owner PowerShell screenshot shows"]]}},"blockers":["D01/D02 partial; 266/420 region/address corroborated, 138 mismatches and five unsupported; zero verified identities.","SA4 partial empirical evidence; full acceptance blocked; City/CSG replies unverified.","P0.4/6 partial; P0.5/7 blocked; rights, protected storage, final market and formal phase acceptance unresolved."],"parked":["P1-P8 except indispensable named P0 dependencies","Real basemap attempt unused/deferred on upstream extractor security","Cook publisher contact and recovery rekey owner-deferred","Wikidata pilot consumed; owner parked","GHSL attempts closed pending material evidence","D02-P1/P2 exact API pilot closed; no replay"],"authority":["docs/DECISIONS.md","docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md","docs/engineering/CLOUD_FIRST_WORKFLOW.md"],"history":["docs/archive/CONTINUATION_CHECKPOINT_2026-11-26.md","docs/archive/CHECKPOINT_EVIDENCE_2026-11-26.md","docs/archive/DECISION_HISTORY_2026-11-26.md","docs/archive/DELIVERY_MILESTONE_HISTORY_2026-11-26.md"]}
```

## Current South African data repertoire

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
| HPI-DATA-011 | 839 sales; 266/420 corroborated, 409 strict | Audit passed; review by 27 Dec 2026 |

002-006, 008/009 registered with null deadlines; 010/011 registered and audited; fixed deadlines; 005/006/008 private noncommercial. 007 parked. 006/008 integrity/re-extraction and 009 owner-observed integrity passed; private bytes not inspected. D01/D02/D03/D07/D08/D09/D11 partial; other families unresolved. Open repertoire source terms/law prevail; restricted real-property beta retains separate 30-day maximum and approval-controlled disposal. No automatic deletion, raw/derived private data in public Git/CI or real buyer activation. [Acquisition register](research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md), [Data Manager](engineering/DATA_MANAGER_V1.md), [prior audit](reviews/DATA_FIRST_REPOSITORY_AUDIT_2026-11-26.md). Windows sibling checkout/workspace; local state and file integrity not independently verified.

## Repository and verification

Requery `development` and `main` heads and exact CI. 32a6680 7/7 passed; requery exact CI. Main 103c854; PR #4 historically draft. No phase credit.

## Current verified implementation on development

Integrated fictional React/TypeScript buyer journey, exact-cent evidence, two-to-three-property shortlist, comparison/notes, SQLite and disposable PostgreSQL. Direct restricted Neon TLS and persistent invented journey qualified. Actual isolated Auth0 login/restart/logout and combined invented save/compare/reopen/sign-out observed; combined restart, notes and cross-owner/old-cookie live probes not independently demonstrated. FE1-FE7 core qualified, Atlas owner-approved; generated contextual PMTiles qualified, no real tiles acquired. Automated accessibility and known-advisory gates passed on recorded application revisions, not final manual or production qualification. [Frontend directive](engineering/PROFESSIONAL_FRONTEND_EXCELLENCE_DIRECTIVE.md), [engineering evidence archive](archive/CHECKPOINT_EVIDENCE_2026-11-26.md).

## Actual Auth0 identity qualification: local milestone verified

See [historical checkpoint](archive/CONTINUATION_CHECKPOINT_2026-11-26.md) and [private beta contract](engineering/PRIVATE_REAL_DATA_BETA_V1.md). Temporary certificate cleanup not owner-confirmed; no replay of consumed login windows or collection of secrets.

## Recovery, storage and access gates

Independent invented-only encrypted recovery demonstrated; key non-exposure not accepted, owner deferred rekey after refusal. Both restricted roles NOLOGIN and zero sessions at last independent observation; no new connection necessary. Free provider storage/network/recovery limitations, direct-grant inventory and permitted use open. Owner 2FA attestation not independent per-provider evidence; consolidate final rundown, no repetitive checks. [Neon contract](engineering/NEON_CLOUD_INTEGRATION_V1.md), [beta](engineering/PRIVATE_REAL_DATA_BETA_V1.md).

## Research and data-use boundary

South Africa preferred, not approved final market. Cook County Class 203/Evanston retained measured research benchmark, not blanket coverage/valuation. Asking price, completed sales and estimates distinct. Exploratory 2 km candidate evidence not valuation. No property-level publication, model training or price prediction approval. [Feasibility](research/DATA_FEASIBILITY.md), [SA mission](engineering/SOUTH_AFRICAN_MISSION_DIRECTIVE.md).

## Active work and next acceptance task

P0-A accepted; B complete; C/D/E conditional; F/G not accepted. SA4 partial empirical; acceptance blocked; 007 parked. [AE0 side directive](engineering/ACQUISITION_INTELLIGENCE_SIDE_DIRECTIVE.md): AE0 World Bank/NASA PASS, unregistered; Wikidata/GHSL STOP, parked. AE0 attempts closed. D01/D02 partial; DBE 009 integrity review complete. [Evidence](engineering/ACQUISITION_INTELLIGENCE_SIDE_DIRECTIVE.md#27-november-2026--d11-offline-integrity-milestone). Other workspace statuses unverified. D02-P1/P2 parked after SCHEMA/FIELDS refusals. D02-F1/010 registered and audited; 3,430 unique-key and 3,421 spatial candidates. 011 audit passed; 409/420 strict, 266 region/address agreement. [Documentary corroboration](research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md#27-november-2026--d01d02-documentary-cadastral-corroboration) complete; strict check complete, mismatch diagnosis proposed; [pre-migration audit](reviews/DATA_FIRST_REPOSITORY_AUDIT_2026-11-26.md#27-november-2026--south-african-pre-migration-readiness-audit): additive design proposed, real migration blocked. No new intake, persistent join, spend or release.

## Detailed engineering evidence and audit trail

[Historical checkpoint](archive/CONTINUATION_CHECKPOINT_2026-11-26.md), [engineering evidence](archive/CHECKPOINT_EVIDENCE_2026-11-26.md), [decision history](archive/DECISION_HISTORY_2026-11-26.md), [delivery history](archive/DELIVERY_MILESTONE_HISTORY_2026-11-26.md). 

## Continuation boundaries

[Master protocol](MASTER_CONTINUATION_PROMPT.md), [decisions](DECISIONS.md) and [P0 directive](engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md) govern autonomy and R0. Current phase does not waive rights or safety gates.

## Evidence versus acceptance

No phase credit from continuation optimisation. Read roadmap for approved figures; historical estimates are not data readiness or an official acceptance score.

## Historical continuity and audit record

[Continuation optimisation audit](reviews/CONTINUATION_SYSTEM_AUDIT_2026-11-26.md). Historical snapshots retained.
