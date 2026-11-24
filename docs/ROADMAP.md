# House Price Intelligence: execution roadmap

**Current governing roadmap:** [P0–P8 phase-gated delivery plan](P_PHASE_ROADMAP.md).

**Status reviewed 24 November 2026:** approximately **83.6%** weighted progress towards a bounded *property investigation and shortlist MVP*. This is an engineering planning estimate, not measured completion. The research audit's Phase 0/1/2 names are separate from the new P0–P8 project management stages.

| Phase | Focus | Weight | Estimated completion |
| --- | --- | ---: | ---: |
| P0 | Discovery, market and source viability | 6% | 92% |
| P1 | Data quality, ingestion and provenance | 12% | 90% |
| P2 | Explainable historical comparables | 14% | 65% |
| P3 | Domain, architecture and API contracts | 10% | 96% |
| P4 | Backend API and database | 16% | 91% |
| P5 | Buyer-facing browser investigation | 16% | 88% |
| P6 | Save/reopen, shortlist and compare | 12% | 95% |
| P7 | Integrated QA, privacy, rights, readiness | 8% | 80% |
| P8 | Release, demo and portfolio handoff | 6% | 35% |

**Current delivery distinction:** Owner accepted P3.1–P3.7 provisionally for synthetic scope and PostgreSQL as a candidate. P3 contracts, synthetic P4 backend, P5 React workspace with history and optional fictional map, and P6 two-to-three-property shortlist/notes/comparison are integrated and verified on development. SQLite remains the local runtime; PostgreSQL candidate parity, dump/restore and ownership isolation passed. **No full P0–P8 phase exit is claimed.** The owner-authorised milestone reassessment recognises these partial deliverables, moving 22.8% to 62.9% without changing weights or exit gates. RD1–RD7 adds bounded exact-cohort address coverage (262/262 keys) and verified synthetic versioned import/disclosure, raising the estimate to 66.5%. PR1–PR8 verified actual fictional PostgreSQL HTTP, pooled identity, concurrent shortlist and restart, separate versioned importer and two-context Chromium, raising the estimate to 71.4%. PC1–PC8 verified same-runtime fictional build activation/rollback, mixed-build history and shortlists, revised browser map and connection recovery, raising progress to 76.1%. PI1–PI8 verified refined evidence/comparison, offline OIDC/session and recruiter walkthrough; 2025 holdout blocked by too few eligible subjects. Progress 79.2%. Real rights, actual provider, production operations and deployment remain open. See [detailed roadmap](P_PHASE_ROADMAP.md), [current checkpoint](CHECKPOINT.md) and [production readiness](engineering/PRODUCTION_READINESS_V1.md).

**Critical boundaries:** The **42 offline tests** refer to the dated research pipeline, not the current application CI; see the [checkpoint](CHECKPOINT.md) for current test counts. Do not equate those historical audits with a finished app. Only 83 historical 2024 Class 203 subjects were evaluated; a 2 km fallback recovered 17 previously unsupported subjects but produced worse retrospective median-price MAE than the township baseline on those cases. No current-market valuation or trained ML model is authorized. Historical availability and public display rights remain unresolved.

The [earlier preliminary roadmap](archive/INITIAL_ROADMAP_2026-11-22.md) is retained for history. Original target remains a portfolio-grade application by late December 2026 or January 2027, with ShiftForge competing for time; it is aspirational, not an acceptance commitment.


FA1–FA8 milestone: 83.6% (79.2% prior). V3 rich fictional revision, offline HTTPS persistent sessions, actual browser writes and zero detected axe violations across four views verified. Count-only coverage diagnostic did not resolve 2025 holdout. No live provider, publication or deployment. See [FA contract](engineering/FINAL_ACCEPTANCE_V1.md).
