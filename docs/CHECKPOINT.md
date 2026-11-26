# House Price Intelligence: current checkpoint

Reviewed 26 November 2026. Sole live routing ledger. [Roadmap](P_PHASE_ROADMAP.md) governs gates/progress; [decisions](DECISIONS.md) governs authority. Schema v2 ranges: [first line, last line, first marker, last marker]; pin HEAD, verify markers, expand as needed and repair stale ranges. Hints do not grant permission. All full phase gates open.

## Continuation state

```json
{
  "schema_version": 2,
  "active_phase": "P0",
  "phase_gate": "blocked",
  "task": {
    "id": "P0-CONTEXTUAL-PROOF-LOCAL",
    "status": "blocked",
    "objective": "Run approved independent 006/008 proof locally and assess usefulness.",
    "scope": "No writes, network, intake, joins or app changes; terminal only.",
    "acceptance": "Both source integrity/re-extraction checks and five cases per source; share summary only.",
    "read": [
      "docs/engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md",
      "docs/research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md",
      "docs/DECISIONS.md",
      "docs/P_PHASE_ROADMAP.md",
      "docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md",
      "docs/product/PRODUCT_BRIEF.md",
      "docs/engineering/DATA_MANAGER_V1.md"
    ],
    "evidence": [
      "docs/reviews/DATA_FIRST_REPOSITORY_AUDIT_2026-11-26.md",
      "docs/engineering/DATA_MANAGER_V1.md"
    ],
    "stop": "Await local result; no scope adoption, app implementation, recruitment, intake or P1.",
    "read_ranges": {
      "docs/engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md": [[11,31,"## 2. Research -> analysis -> planning -> implementation -> verif","Do not turn optional methods (SWOT, persona variants, full commer"],[109,156,"## 26 November 2026 | P0-G independent conditional acceptance aud","The data-first correction has delivered three private local conte"]],
      "docs/research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md": [[621,625,"## 26 November 2026 | HPI-DATA-008 empirical registration and con","Next task: bounded desktop feasibility review of 006 and 008 as i"],[627,629,"## 26 November 2026 | Contextual evidence review delivered","006 and 008 local registration observations support two distinct "]],
      "docs/DECISIONS.md": [[13,16,"| Engineering process (approved 23 Nov) | Eight-step requirements","| Research-driven evolution (26 Nov, owner clarification) | Exist"],[24,60,"| Single active phase (26 Nov, owner direction) | Begin P0 closur","| Boundaries | Do not claim current price prediction, live listin"],[74,87,"## Open decisions, with next acceptance point","| Which buyer entry and property identity? | Address/parcel/build"],[99,106,"## Non-negotiable interpretation rules","- Missing evidence requires an explicit abstention/unsupported st"],[144,146,"## Independent contextual proof authority (26 November 2026)","Owner approves bounded private offline contextual intelligence pr"]],
      "docs/P_PHASE_ROADMAP.md": [[13,32,"### Progress methodology","| **Total** | **Bounded flagship MVP** | **100%** | **87.1% weigh"],[68,82,"### P0 | Buyer, market and product feasibility | Weight 6% | Appr","**26 November initial P0 closure audit (preserved baseline; execu"],[227,235,"### P0: Discovery and feasibility — 6% weight; 94% estimated comp","**Exit gate:** Approved bounded product brief, source register, c"]],
      "docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md": [[110,131,"## 6. Eight-step feature engineering lifecycle (approved 23 Novem","Each substantial change should identify its outcome, affected bou"],[162,169,"## 9. Safe large changes, migrations and CI controls","- Apply the same review to AI-assisted and human code. No LLM out"]],
      "docs/product/PRODUCT_BRIEF.md": [[166,198,"## 26 November 2026 | Direction B contextual evidence review and ","Proposed B proof requires explicit owner authority: extend existi"],[200,202,"### Approved bounded proof implementation (26 November 2026)","Owner approved independent private offline 006/008 reports, integ"]],
      "docs/engineering/DATA_MANAGER_V1.md": [[245,262,"## Approved independent contextual proof (26 November 2026)","For private inspection only, display `$proof.market_evidence | Co"]]
    }
  },
  "blockers": [
    "D01/D02 unresolved; 007 parked; approved 006/008 proof local run pending.",
    "SA4 empirical blocked; Cape Town clarification and CSG reply not verified this session.",
    "P0.4/6 partial; P0.5/7 blocked; rights, protected storage, final market and formal phase acceptance unresolved."
  ],
  "parked": [
    "P1-P8 except indispensable named P0 dependencies",
    "Real basemap attempt unused/deferred on upstream extractor security",
    "Cook publisher contact and recovery rekey owner-deferred"
  ],
  "authority": [
    "docs/DECISIONS.md",
    "docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md",
    "docs/engineering/CLOUD_FIRST_WORKFLOW.md"
  ],
  "history": [
    "docs/archive/CONTINUATION_CHECKPOINT_2026-11-26.md",
    "docs/archive/CHECKPOINT_EVIDENCE_2026-11-26.md",
    "docs/archive/DECISION_HISTORY_2026-11-26.md",
    "docs/archive/DELIVERY_MILESTONE_HISTORY_2026-11-26.md"
  ]
}
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

002-006 and 008 registered, null deadlines owner-observed; 005/006/008 private noncommercial. 007 parked. Bytes not independently inspected. D03/D07/D08/D09 partial; eleven other families lack retained qualified data. Open repertoire source terms/law prevail; restricted real-property beta retains separate 30-day maximum and approval-controlled disposal. No automatic deletion, raw/derived private data in public Git/CI or real buyer activation. [Acquisition register](research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md), [Data Manager](engineering/DATA_MANAGER_V1.md), [prior audit](reviews/DATA_FIRST_REPOSITORY_AUDIT_2026-11-26.md). Permanent Windows Downloads/HPI-Project sibling checkout and HPI-Data-Workspace; local HEAD, uncommitted changes, actual file integrity and local audit execution not independently verified.

## Repository and verification

Requery heads and exact CI at restoration. Prior continuation 5c6b957 10/10; RPPI/Census 7/7 each; evidence in Data Manager. Main 103c854; PR #4 historically draft. No phase credit.

## Current verified implementation on development

Integrated fictional React/TypeScript buyer journey, exact-cent evidence, two-to-three-property shortlist, comparison/notes, SQLite and disposable PostgreSQL. Direct restricted Neon TLS and persistent invented journey qualified. Actual isolated Auth0 login/restart/logout and combined invented save/compare/reopen/sign-out observed; combined restart, notes and cross-owner/old-cookie live probes not independently demonstrated. FE1-FE7 core qualified, Atlas owner-approved; generated contextual PMTiles qualified, no real tiles acquired. Automated accessibility and known-advisory gates passed on recorded application revisions, not final manual or production qualification. [Frontend directive](engineering/PROFESSIONAL_FRONTEND_EXCELLENCE_DIRECTIVE.md), [engineering evidence archive](archive/CHECKPOINT_EVIDENCE_2026-11-26.md).

## Actual Auth0 identity qualification: local milestone verified

See [historical checkpoint](archive/CONTINUATION_CHECKPOINT_2026-11-26.md) and [private beta contract](engineering/PRIVATE_REAL_DATA_BETA_V1.md). Temporary certificate cleanup not owner-confirmed; no replay of consumed login windows or collection of secrets.

## Recovery, storage and access gates

Independent invented-only encrypted recovery demonstrated; key non-exposure not accepted, owner deferred rekey after refusal. Both restricted roles NOLOGIN and zero sessions at last independent observation; no new connection necessary. Free provider storage/network/recovery limitations, direct-grant inventory and permitted use open. Owner 2FA attestation not independent per-provider evidence; consolidate final rundown, no repetitive checks. [Neon contract](engineering/NEON_CLOUD_INTEGRATION_V1.md), [beta](engineering/PRIVATE_REAL_DATA_BETA_V1.md).

## Research and data-use boundary

South Africa preferred, not approved final market. Cook County Class 203/Evanston retained measured research benchmark, not blanket coverage/valuation. Asking price, completed sales and estimates distinct. Exploratory 2 km candidate evidence not valuation. No property-level publication, model training or price prediction approval. [Feasibility](research/DATA_FEASIBILITY.md), [SA mission](engineering/SOUTH_AFRICAN_MISSION_DIRECTIVE.md).

## Active work and next acceptance task

[005 import evidence](research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md#26-november-2026--hpi-data-005-empirical-import-and-proposed-crosswalk): complete; 52/52 candidates; contextual source review delivered; 006 registered; [Contextual review delivered; proof local run next](product/PRODUCT_BRIEF.md#26-november-2026--direction-b-contextual-evidence-review-and-prototype-decision). P0-A accepted, B research complete, C/D/E conditional, F/G delivered not accepted. SA0-SA3 desk work and IR1/IR3 complete; IR2 not required now; SA4 blocked. Existing private drafts not submitted. Direct access first, existing enquiries parallel; exact recipient, subject, body and attachments require approval before EVERY email. No inbox observation in optimisation. 005 intake and both candidate experiments delivered; no downstream authority. 006/008 delivered; 007 consumed; approved read-only proof pending. No other intake, contact, joins, spend, provider changes, deployment, main merge or phase acceptance.

## Detailed engineering evidence and audit trail

[Complete historical checkpoint](archive/CONTINUATION_CHECKPOINT_2026-11-26.md) retains original dated evidence, failures, consumed approvals and old task sequences. [Original master](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/9577b9f7ce5712001106bc0c94da3927aacd5abc/docs/MASTER_CONTINUATION_PROMPT.md), [original checkpoint](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/9577b9f7ce5712001106bc0c94da3927aacd5abc/docs/CHECKPOINT.md), [decision history](archive/DECISION_HISTORY_2026-11-26.md), [delivery history](archive/DELIVERY_MILESTONE_HISTORY_2026-11-26.md). Retrieve by heading or exact run rather than wholesale.

## Continuation boundaries

[Master protocol](MASTER_CONTINUATION_PROMPT.md), [decisions](DECISIONS.md) and [P0 directive](engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md) govern autonomy and R0. Current phase does not waive rights or safety gates.

## Evidence versus acceptance

No phase credit from continuation optimisation. Read roadmap for approved figures; historical estimates are not data readiness or an official acceptance score.

## Historical continuity and audit record

[Continuation optimisation audit](reviews/CONTINUATION_SYSTEM_AUDIT_2026-11-26.md). Original snapshots and archives are retained, not treated as active tasks.
