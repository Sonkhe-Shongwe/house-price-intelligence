# House Price Intelligence

**Status reviewed 24 November 2026:** Owner-authorised PRs #5 and #6 integrated the fictional buyer workflow and PR #8 integrated React. The latest verified application baseline [1cedf37](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/1cedf378e806f5fafc18639ba72207a70f2b4195) passed six push/PR workflows: 182 Python, 16 legacy browser, 33 React and 5 PostgreSQL tests; the separate bounded address audit passed four safeguards. React workspace, fictional map, SQLite persistence and shortlist comparison are integrated; PostgreSQL is a verified candidate, not the deployed runtime. Latest RD candidate a24ce43 passed 189 Python, 33 React and 5 PostgreSQL tests; bounded cohort audit verified 262/262 nonblank single-row parcel-year keys. Runtime commit 240f5ce passed all eight workflows (fictional PostgreSQL HTTP, owner isolation, concurrency/restart, React and separate PostgreSQL revision import). **71.4%** is the current owner-authorised weighted planning estimate, not measured code completion or production readiness. All full phase exit gates remain open. See [current checkpoint](docs/CHECKPOINT.md) and [roadmap](docs/P_PHASE_ROADMAP.md). No release or real data display approved.

House Price Intelligence aims to help a prospective homebuyer examine historical completed sales, understand why properties are comparable, and save and compare a shortlist. It is an original Investigate / Compare / Decide workspace, not a copied property listings marketplace; the supported geography should be selected by verified data quality and rights, not nationality. Any asking price will be user-reported, not presented as a verified listing. **No current-market appraisal, trained price model, production API/database, approved public-data frontend or deployed service exists.** A local, invented-data HTTP/SQLite/browser investigation slice is included for engineering review.

## Verified evidence, not product claims

The historical research pilot uses Cook County township 17 (Evanston, Illinois), 2022–2024 recorded sales and a Class 203 one-story residence segment.

| Measurement | Verified result |
| --- | ---: |
| Downloaded sale rows / historical building rows | 3,539 / 39,401 |
| Sales passing experimental screens / accepted historical joins | 2,583 / 1,285 |
| Class 203 joined sales / distinct PIN-year lookup keys | 273 / 262 |
| Historical 2024 Class 203 subjects evaluated | 83 |
| Subjects with at least 3 same-neighbourhood comparisons | 66 |
| Subjects requiring the exploratory 2 km fallback | 17 |
| Automated offline tests in the last audited pipeline | 42 |

In retrospective testing, the 2 km fallback covered all 17 thin-neighbourhood subjects but produced **worse** median-based price errors than the township baseline on those same 17. Fallback sales are **exploratory evidence, not validated valuation estimates**. The underlying historical fields may have been reported, revised or backfilled after the recorded sale dates. Source-specific public display rights remain unresolved.

Evidence: [Phase 0](docs/research/PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1](docs/research/PHASE1_CLOUD_AUDIT_RESULTS.md), [Phase 2](docs/research/PHASE2_CLOUD_AUDIT_RESULTS.md) and the [successful cloud audit](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782).

## Start here

| Document | Role |
| --- | --- |
| [Documentation index](docs/DOCUMENTATION_INDEX.md) | Which document to trust; current versus historical material |
| [Current checkpoint](docs/CHECKPOINT.md) | Verified status, blockers and next engineering task |
| [Master continuation prompt](docs/MASTER_CONTINUATION_PROMPT.md) | Reusable instructions for resuming this project in a new session |
| [P0–P8 roadmap](docs/P_PHASE_ROADMAP.md) | Phase acceptance gates, weights and progress rules |
| [Roadmap summary](docs/ROADMAP.md) | Concise percentage table |
| [Decisions and open questions](docs/DECISIONS.md) | Agreed direction versus pending approval |
| [Product brief](docs/product/PRODUCT_BRIEF.md) | Buyer journey and functional acceptance |
| [UX research and product direction](docs/design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md) | Exploratory screen hierarchy and visual concepts; **not approved UI** |
| [Visual Foundation V1 proposal](docs/design/VISUAL_FOUNDATION_V1_IMPLEMENTATION_PROPOSAL_2026-11-23.md) | Proposed professional visual foundation and open frontend stack choices; no redesign authorised |
| [Professional UI and mapping research](docs/design/PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md) | Map renderer, geometry integrity, tile rights/CSP/cost, premium interface risks and test gates |
| [P6 shortlist contract](docs/engineering/P6_SYNTHETIC_SHORTLIST_CONTRACT.md) | Integrated fictional-only shortlist, notes and side-by-side comparison; phase acceptance pending |
| [Engineering contract](docs/engineering/ENGINEERING_CONTRACT.md) | Data and application correctness |
| [Lean engineering directive](docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md) | Eight-step feature lifecycle, risk-based tests, safe large changes and phase-governed integration |
| [Cloud-first development operations](docs/engineering/CLOUD_FIRST_WORKFLOW.md) | Permanent `development`, stable `main`, automated versus manual acceptance and controlled milestone merges |
| [Cloud-first documentation audit](docs/reviews/CLOUD_FIRST_DELIVERY_DOCUMENTATION_AUDIT_2026-11-23.md) | Dated audit of the new operating model; not a second checkpoint |
| [P3 application contract](docs/engineering/P3_APPLICATION_CONTRACT.md) | Current synthetic-only investigation and API boundary; acceptance still pending |
| [Source register](docs/research/SOURCE_REGISTER.md) | Publisher IDs, provenance and reuse checks |
| [Earlier continuity/directive audit](docs/reviews/CONTINUITY_AND_DIRECTIVE_AUDIT_2026-11-23.md) | Historical risk review, partially superseded by later integration and mapping research |
| [Earlier process audit](docs/reviews/ENGINEERING_DIRECTIVE_AUDIT_2026-11-23.md) | Dated engineering directive adoption and prior status review |
| [Previous documentation audit](docs/reviews/DOCUMENTATION_AUDIT_2026-11-22.md) | Retained historical cleanup findings |

The repository also retains the original [pinnacle vision](docs/product/PINNACLE_VISION.md), [data-feasibility research](docs/research/DATA_FEASIBILITY.md) and [migration history](docs/MIGRATION_MANIFEST.md). The older Phase 0–2 **audit experiment names are distinct from the overall P0–P8 delivery stages**.

## Run and development workflows

**Owner-approved two-branch cloud-first execution (23 November 2026):** Implement approved work on permanent `development`; reserve `main` for owner-reviewed integration milestones. GitHub Actions verifies each exact commit; it does not write source independently. Keep one draft integration PR rather than a new feature branch per minor change, and use Windows only when necessary for real UX/platform acceptance. See [cloud-first operations](docs/engineering/CLOUD_FIRST_WORKFLOW.md) and [current test evidence](docs/CHECKPOINT.md); do not copy fixed CI counts into a second live handoff. `main` branch protection remains unconfigured.

**Routine audits are cloud-first.** The [GitHub Actions data-audit workflow](.github/workflows/data-audit.yml) runs the three research phases and uploads aggregate, privacy-conscious summaries; [operating instructions](docs/AUTOMATED_DATA_AUDIT.md). The [offline application CI workflow](.github/workflows/audit-tests.yml) checks research and synthetic application tests, JavaScript, docs and genuine Chromium against the fixture-only local API on `development` and `main` pushes and PRs targeting `main`. Costly real-data audits remain separately restricted.

**Fixture-only demo:** Run `python -m backend.run_synthetic_api --fixture-only --port 8765` from the repo root, then open `http://127.0.0.1:8765/`. Run `python tools/dev_check.py` for dependency-free checks. The browser supports fictional address search, explicit ambiguous parcel choice, frozen investigations, saved **two-to-three-property shortlists, editable notes and side-by-side evidence**. The default database is **in-memory and temporary**. For opt-in restart persistence on this machine only, add `--fixture-db ./local-fictional-demo.sqlite` to the server command. No accounts, encryption or public access are provided. Do not enter personal or real property information. [Backend setup](backend/README.md), [frontend workflow](frontend/README.md) and [current checkpoint](docs/CHECKPOINT.md).

Manual local runs are optional for debugging; see [Phase 0](audit/phase0/README.md), [Phase 1](audit/phase1/README.md), [Phase 2](audit/phase2/README.md) and [Windows Git setup](docs/GITHUB_SETUP.md). Never commit extracted datasets, private user data, personal names, API tokens or generated property-level output. See [data handling](data/README.md).

## Scope and next milestone

**Bounded flagship:** One supported geography and property class, user-entered property enquiry, transparently selected historical comparables, insufficient-evidence handling, saved investigations and side-by-side shortlist comparison.

**Next:** Resolve source rights and permitted release route; close controlled source-build switching and production security/operational gaps. SQLite and fictional PostgreSQL HTTP are CI-verified, but all phase exits remain open. No real-data display, provider, hosting or deployment authorised. Stable `main` requires owner merge approval.

**Conditional only:** Price prediction requires independent, chronology-respecting evaluation with defensible uncertainty; do not add a model merely to advertise AI. Live listing search, real-time valuations, mortgages, alerts and multi-market expansion are outside the first MVP.

The [SA Tech Graduate Playbook](https://github.com/Sonkhe-Shongwe/sa-tech-grad-playbook.) is a separate, preserved source of graduate recruitment research. This repository is the standalone software project.
