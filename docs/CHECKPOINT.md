# House Price Intelligence: current checkpoint

Reviewed 26 November 2026. Sole live routing ledger. Progress and acceptance criteria: [P0-P8 roadmap](P_PHASE_ROADMAP.md); authority: [decisions](DECISIONS.md). Structured state routes work, not grants permission. All full phase gates remain open at this handoff.

## Continuation state

```json
{
  "schema_version": 1,
  "active_phase": "P0",
  "phase_gate": "blocked",
  "task": {
    "id": "P0-DATA-COMPLEMENT",
    "status": "ready",
    "objective": "Qualify complementary official geographic identifiers and legitimate direct-access D02 cadastral / D01 completed-sale sources.",
    "scope": "Read-only metadata, terms, schema, access and feasibility research; no new intake or material joins.",
    "acceptance": "Record publisher/source/version, access route, rights, join keys, scope and limitations; classify each lead qualified, conditional or blocked with evidence.",
    "read": [
      "docs/engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md",
      "docs/research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md",
      "docs/DECISIONS.md",
      "docs/P_PHASE_ROADMAP.md"
    ],
    "evidence": [
      "docs/reviews/DATA_FIRST_REPOSITORY_AUDIT_2026-11-26.md",
      "docs/engineering/DATA_MANAGER_V1.md"
    ],
    "stop": "Stop before acquisition, contact, material integration or market/scope change, or when no independently useful lawful R0 discovery remains. Do not advance P1."
  },
  "blockers": [
    "No lawful R0 individual completed-sale source or qualified cadastral/property join; official geography codes outstanding.",
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
| HPI-DATA-003 | 52 valid district features, 2020 geography | Official code crosswalk, topology and accuracy pending |
| HPI-DATA-004 | 289,864 usable of 289,867 footprint records | All height/confidence missing; 673 outside tile centroids |

002/003/004 private registration and null-deadline migration owner-observed; actual file bytes not independently inspected. D03/D07/D09 partial; twelve other families lack retained qualified data. Open repertoire source terms/law prevail; restricted real-property beta retains separate 30-day maximum and approval-controlled disposal. No automatic deletion, raw/derived private data in public Git/CI or real buyer activation. [Acquisition register](research/SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md), [Data Manager](engineering/DATA_MANAGER_V1.md), [prior audit](reviews/DATA_FIRST_REPOSITORY_AUDIT_2026-11-26.md). Permanent Windows Downloads/HPI-Project sibling checkout and HPI-Data-Workspace; local HEAD, uncommitted changes, actual file integrity and local audit execution not independently verified.

## Repository and verification

Requery exact `development` and stable `main` heads and Actions on every restoration. Migration baseline [9577b9f](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/9577b9f7ce5712001106bc0c94da3927aacd5abc) had 7/7 successful triggered runs, including [audit push](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45879683114). Newer heads require independent checks. Main baseline 103c854; integration PR #4 historically draft, verify before authorised integration. No new product credit.

## Current verified implementation on development

Integrated fictional React/TypeScript buyer journey, exact-cent evidence, two-to-three-property shortlist, comparison/notes, SQLite and disposable PostgreSQL. Direct restricted Neon TLS and persistent invented journey qualified. Actual isolated Auth0 login/restart/logout and combined invented save/compare/reopen/sign-out observed; combined restart, notes and cross-owner/old-cookie live probes not independently demonstrated. FE1-FE7 core qualified, Atlas owner-approved; generated contextual PMTiles qualified, no real tiles acquired. Automated accessibility and known-advisory gates passed on recorded application revisions, not final manual or production qualification. [Frontend directive](engineering/PROFESSIONAL_FRONTEND_EXCELLENCE_DIRECTIVE.md), [engineering evidence archive](archive/CHECKPOINT_EVIDENCE_2026-11-26.md).

## Actual Auth0 identity qualification: local milestone verified

See [historical checkpoint](archive/CONTINUATION_CHECKPOINT_2026-11-26.md) and [private beta contract](engineering/PRIVATE_REAL_DATA_BETA_V1.md). Temporary certificate cleanup not owner-confirmed; no replay of consumed login windows or collection of secrets.

## Recovery, storage and access gates

Independent invented-only encrypted recovery demonstrated; key non-exposure not accepted, owner deferred rekey after refusal. Both restricted roles NOLOGIN and zero sessions at last independent observation; no new connection necessary. Free provider storage/network/recovery limitations, direct-grant inventory and permitted use open. Owner 2FA attestation not independent per-provider evidence; consolidate final rundown, no repetitive checks. [Neon contract](engineering/NEON_CLOUD_INTEGRATION_V1.md), [beta](engineering/PRIVATE_REAL_DATA_BETA_V1.md).

## Research and data-use boundary

South Africa preferred, not approved final market. Cook County Class 203/Evanston retained measured research benchmark, not blanket coverage/valuation. Asking price, completed sales and estimates distinct. Exploratory 2 km candidate evidence not valuation. No property-level publication, model training or price prediction approval. [Feasibility](research/DATA_FEASIBILITY.md), [SA mission](engineering/SOUTH_AFRICAN_MISSION_DIRECTIVE.md).

## Active work and next acceptance task

Use structured state above. P0-A accepted, P0-B bounded research complete, P0-C/D/E conditional desk reviews complete; P0-F specification and P0-G audit delivered but not formally accepted. SA0-SA3 desk work and IR1/IR3 complete; IR2 not required now; SA4 blocked. Existing private drafts not submitted. Direct access first, existing enquiries parallel; exact recipient, subject, body and attachments require approval before EVERY email. No inbox observation in optimisation. No acquisition, contact, material integration, spend, deployment, provider mutation, main merge or phase acceptance authorised.

## Detailed engineering evidence and audit trail

[Complete historical checkpoint](archive/CONTINUATION_CHECKPOINT_2026-11-26.md) retains original dated evidence, failures, consumed approvals and old task sequences. [Original master](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/9577b9f7ce5712001106bc0c94da3927aacd5abc/docs/MASTER_CONTINUATION_PROMPT.md), [original checkpoint](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/9577b9f7ce5712001106bc0c94da3927aacd5abc/docs/CHECKPOINT.md), [decision history](archive/DECISION_HISTORY_2026-11-26.md), [delivery history](archive/DELIVERY_MILESTONE_HISTORY_2026-11-26.md). Retrieve by heading or exact run rather than wholesale.

## Actual combined fictional provider milestone (retained)

See complete historical checkpoint; no replay or real-data acceptance.

## Continuation boundaries

[Master protocol](MASTER_CONTINUATION_PROMPT.md), [decisions](DECISIONS.md) and [P0 directive](engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md) govern autonomy and R0. Current phase does not waive rights or safety gates.

## Evidence versus acceptance

No phase credit from continuation optimisation. Read roadmap for approved figures; historical estimates are not data readiness or an official acceptance score.

## Historical continuity and audit record

[Continuation optimisation audit](reviews/CONTINUATION_SYSTEM_AUDIT_2026-11-26.md). Original snapshots and archives are retained, not treated as active tasks.
