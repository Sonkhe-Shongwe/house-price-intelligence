# House Price Intelligence: execution roadmap

**Current governing roadmap:** [P0–P8 phase-gated delivery plan](P_PHASE_ROADMAP.md).

**Status reviewed 26 November 2026 (scores approved 24 November):** approximately **87.1%** weighted progress towards a bounded *property investigation and shortlist MVP*. This is an engineering planning estimate, not measured completion. The research audit's Phase 0/1/2 names are separate from the new P0–P8 project management stages.

| Phase | Focus | Weight | Estimated completion |
| --- | --- | ---: | ---: |
| P0 | Discovery, market and source viability | 6% | 94% |
| P1 | Data quality, ingestion and provenance | 12% | 98% |
| P2 | Explainable historical comparables | 14% | 75% |
| P3 | Domain, architecture and API contracts | 10% | 96% |
| P4 | Backend API and database | 16% | 95% |
| P5 | Buyer-facing browser investigation | 16% | 89% |
| P6 | Save/reopen, shortlist and compare | 12% | 95% |
| P7 | Integrated QA, privacy, rights, readiness | 8% | 83% |
| P8 | Release, demo and portfolio handoff | 6% | 35% |

**Current delivery distinction:** Provisional P3.1-P3.7 synthetic scope, integrated P4 backend, P5 React workspace and P6 two-to-three-property shortlist/notes/comparison; all full phase gates remain open. PostgreSQL fictional runtime, split-role historical persistence and authenticated browser rehearsal are verified in CI. Neon schema and restricted permissions are installed (25 tables, five RLS policies); direct restricted application connectivity and persistent invented buyer journey accepted (v3, 45627319372). Temporary service logins disabled after acceptance; independent encrypted Google Drive recovery verified on the invented database; key non-exposure, managed recovery and full protected real-data gates remain open. Actual isolated Auth0 login, restart and logout verified. Combined actual Auth0/Neon invented buyer save/compare and owner-observed reopen/sign-out completed; access window consumed, both restricted roles disabled and zero sessions independently verified. Actual combined restart, note persistence and cross-owner/old-cookie probes not independently demonstrated.

**Active priority:** owner-directed P0 data-first repertoire qualification; P0-G conditional audit delivered, formal P0 exit blocked at external/rights/protection dependencies; qualify contextual candidates independently of Cape Town per checkpoint, under the [P0 discovery directive](engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md) (owner direction 26 November); P1-P8 work parked except indispensable named dependencies. Prior P4/P7 protected-storage, retention and permitted-use gates remain open and must pass before real intake; P8 browser-only release downstream. FE1–FE7 core qualified, Atlas approved, generated PMTiles contextual render verified. Real basemap approval unused/deferred on extractor security. Python/npm known-advisory checks and 14-view automated accessibility gate passed; final manual and production qualification remain. [Checkpoint](CHECKPOINT.md) governs current evidence and next task; no phase score or gate change.

**Critical boundaries:** Historical source use, identity/as-of timing, protected storage and real buyer acceptance remain unresolved. Previous single live collection consumed; one additional conditional extraction authorised on 24 November, unused. No public release, paid resources, valuation or main merge. No change to stage weights, estimates or gate acceptance during documentation audit.

**Historical milestone sequence:** 22.8%, 62.9%, 66.5%, 71.4%, 76.1%, 79.2%, 83.6%, 84.0%, 85.7%, 87.1%. The [previous full roadmap summary](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/8e85c848c66f5c540e3730f8e93d87011d39ffcd/docs/ROADMAP.md) preserves the detailed rationale and private rehearsal figures. The [initial roadmap](archive/INITIAL_ROADMAP_2026-11-22.md) is historical. The original late December 2026/January 2027 target is aspirational, not acceptance evidence.
