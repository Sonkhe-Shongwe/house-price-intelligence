# House Price Intelligence

**Status reviewed 23 November 2026: research engines verified; synthetic-only P3 application integrated for review, not yet accepted or deployed.** Current planning stage: **P3, product architecture and API contracts**. The bounded portfolio-MVP progress baseline is **22.8%**, a subjective weighted estimate, not a measurement of code completion.

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
| [UX research and product direction](docs/design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md) | Design research, competitor references, visual studies, screen IA and open design decisions; **not approved UI** |
| [Engineering contract](docs/engineering/ENGINEERING_CONTRACT.md) | Data and application correctness |
| [Lean engineering directive](docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md) | Eight-step feature lifecycle, risk-based tests, safe large changes and phase-governed integration |
| [P3 application contract](docs/engineering/P3_APPLICATION_CONTRACT.md) | Current synthetic-only investigation and API boundary; acceptance still pending |
| [Source register](docs/research/SOURCE_REGISTER.md) | Publisher IDs, provenance and reuse checks |
| [Latest continuity/directive audit](docs/reviews/CONTINUITY_AND_DIRECTIVE_AUDIT_2026-11-23.md) | Verified versus isolated evidence, grey areas, product scope, maps and new-tab handoff |
| [Earlier process audit](docs/reviews/ENGINEERING_DIRECTIVE_AUDIT_2026-11-23.md) | Dated engineering directive adoption and prior status review |
| [Previous documentation audit](docs/reviews/DOCUMENTATION_AUDIT_2026-11-22.md) | Retained historical cleanup findings |

The repository also retains the original [pinnacle vision](docs/product/PINNACLE_VISION.md), [data-feasibility research](docs/research/DATA_FEASIBILITY.md) and [migration history](docs/MIGRATION_MANIFEST.md). The older Phase 0–2 **audit experiment names are distinct from the overall P0–P8 delivery stages**.

## Run and development workflows

**Routine audits are cloud-first.** The [GitHub Actions data-audit workflow](.github/workflows/data-audit.yml) runs the three research phases and uploads aggregate, privacy-conscious summaries; [operating instructions](docs/AUTOMATED_DATA_AUDIT.md). The [offline unit-test workflow](.github/workflows/audit-tests.yml) checks the four research suites and the P3 synthetic application suite on pushes and pull requests. Audits are not on a recurring time schedule.

**Fixture-only demo:** `python -m backend.run_synthetic_api --fixture-only --port 8765` from the repo root, then open `http://127.0.0.1:8765/`. Run `python tools/dev_check.py` for no-dependency checks. This is an in-memory local demonstration, not an authorised public service. A separate **isolated patched checkout** has passed owner-reported Windows Chromium and browser-to-Python-to-SQLite synthetic acceptance, but that patch and its tests have not been committed, and P3 production/design acceptance is still outstanding. See [checkpoint](docs/CHECKPOINT.md).

Manual local runs are optional for debugging; see [Phase 0](audit/phase0/README.md), [Phase 1](audit/phase1/README.md), [Phase 2](audit/phase2/README.md) and [Windows Git setup](docs/GITHUB_SETUP.md). Never commit extracted datasets, private user data, personal names, API tokens or generated property-level output. See [data handling](data/README.md).

## Scope and next milestone

**Bounded flagship:** One supported geography and property class, user-entered property enquiry, transparently selected historical comparables, insufficient-evidence handling, saved investigations and side-by-side shortlist comparison.

**Next (P3):** Review and accept the domain/API/evidence contract and PIN-first internal journey; reconcile the already completed local-only graphical fixture acceptance against the eventual committed patch and CI. The [post-integration 125-test CI](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45059455620) passed, but does not certify browser or contract acceptance. Then develop P4/P5 together in tested slices while accepting each stage separately. The existing SQLite/HTTP/UI slice demonstrates feasibility but does not satisfy production P4/P5 or source-rights gates. Final public input/stack/deployment decisions remain open.

**Conditional only:** Price prediction requires independent, chronology-respecting evaluation with defensible uncertainty; do not add a model merely to advertise AI. Live listing search, real-time valuations, mortgages, alerts and multi-market expansion are outside the first MVP.

The [SA Tech Graduate Playbook](https://github.com/Sonkhe-Shongwe/sa-tech-grad-playbook.) is a separate, preserved source of graduate recruitment research. This repository is the standalone software project.
