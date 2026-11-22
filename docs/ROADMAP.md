# House Price Intelligence: execution roadmap

**Current governing roadmap:** [P0–P8 phase-gated delivery plan](P_PHASE_ROADMAP.md).

**Status as of 22 November 2026:** approximately **22.8%** weighted progress towards a bounded *property investigation and shortlist MVP*. This is an engineering planning estimate, not measured completion. The research audit's Phase 0/1/2 names are separate from the new P0–P8 project management stages.

| Phase | Focus | Weight | Estimated completion |
| --- | --- | ---: | ---: |
| P0 | Discovery, market and source viability | 6% | 85% |
| P1 | Data quality, ingestion and provenance | 12% | 75% |
| P2 | Explainable historical comparables | 14% | 55% |
| P3 | Domain, architecture and API contracts | 10% | 10% |
| P4 | Backend API and database | 16% | 0% |
| P5 | Buyer-facing browser investigation | 16% | 0% |
| P6 | Save/reopen, shortlist and compare | 12% | 0% |
| P7 | Integrated QA, privacy, rights, readiness | 8% | 0% |
| P8 | Release, demo and portfolio handoff | 6% | 0% |

**Next engineering milestone:** P3 domain design and acceptance of the subject -> ranked historical comparables -> evidence/warning/abstention API contract, followed by a P4 vertical slice against curated SQL storage.

**Critical boundaries:** Do not equate the 42 passing tests and historical audits with a finished app. Only 83 historical 2024 Class 203 subjects were evaluated; a 2 km fallback recovered 17 previously unsupported subjects but produced worse retrospective median-price MAE than the township baseline on those cases. No current-market valuation or trained ML model is authorized. Historical availability and public display rights remain unresolved.

The [earlier preliminary roadmap](archive/INITIAL_ROADMAP_2026-11-22.md) is retained for history. Original target remains a portfolio-grade application by late December 2026 or January 2027, with ShiftForge competing for time; it is aspirational, not an acceptance commitment.
