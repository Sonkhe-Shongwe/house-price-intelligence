# House Price Intelligence

A buyer-facing historical comparable-sales investigation and shortlist workspace: **Investigate / Compare / Decide**. Not a listings marketplace, appraisal or trained price-prediction model. Asking price is user-reported, distinct from recorded sales.

**Status reviewed 25 November 2026:** `development` contains the integrated fictional React/SQLite buyer journey (PRs #5 and #6; React PR #8), verified split-role PostgreSQL persistence and authenticated historical-shape browser rehearsal. Neon development schema and restricted permissions installed (25 tables, five RLS policies, no application records); temporary service credentials configured, direct application-driver connectivity still pending. **87.1%** is the approved weighted MVP planning estimate, not measured completion. All full phase gates open. See [current checkpoint](docs/CHECKPOINT.md) for exact source/CI, current connection test and next task; [roadmap](docs/P_PHASE_ROADMAP.md) for gates. No public data display, valuation or deployment approved.

## Historical research evidence, not product claims

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
| [Current checkpoint](docs/CHECKPOINT.md) | Single current engineering handoff, CI and next task |
| [Master continuation prompt](docs/MASTER_CONTINUATION_PROMPT.md) | Standing engineering autonomy and cross-session workflow |
| [Documentation index](docs/DOCUMENTATION_INDEX.md) | Canonical navigation, historical evidence and contracts |
| [P0-P8 roadmap](docs/P_PHASE_ROADMAP.md) | Acceptance gates and weights |
| [Decisions](docs/DECISIONS.md) | Approved scope and open boundaries |
| [Neon integration](docs/engineering/NEON_CLOUD_INTEGRATION_V1.md) | Active cloud database workstream |
| [Private beta](docs/engineering/PRIVATE_REAL_DATA_BETA_V1.md) | Conditional real-data scope |
| [Product brief](docs/product/PRODUCT_BRIEF.md) | Buyer workflow |
| [Lean engineering directive](docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md) | Eight-step lifecycle and Definition of Done |

## Run and development workflows

**Cloud-first execution and standing autonomy (25 November 2026):** Implement approved work on permanent `development`; reserve `main` for owner-reviewed integration milestones. GitHub Actions verifies each exact commit; it does not write source independently. Keep one draft integration PR rather than a new feature branch per minor change, and use Windows only when necessary for real UX/platform acceptance. See [cloud-first operations](docs/engineering/CLOUD_FIRST_WORKFLOW.md) and [current test evidence](docs/CHECKPOINT.md); do not copy fixed CI counts into a second live handoff. See the checkpoint for observed branch configuration. Neon administration uses the connected integration, not passwords in source or chat.

**Routine audits are cloud-first.** The [GitHub Actions data-audit workflow](.github/workflows/data-audit.yml) runs the three research phases and uploads aggregate, privacy-conscious summaries; [operating instructions](docs/AUTOMATED_DATA_AUDIT.md). The [offline application CI workflow](.github/workflows/audit-tests.yml) checks research and synthetic application tests, JavaScript, docs and genuine Chromium against the fixture-only local API on `development` and `main` pushes and PRs targeting `main`. Costly real-data audits remain separately restricted.

**Fixture-only demo:** Run `python -m backend.run_synthetic_api --fixture-only --port 8765` from the repo root, then open `http://127.0.0.1:8765/`. Run `python tools/dev_check.py` for dependency-free checks. The browser supports fictional address search, explicit ambiguous parcel choice, frozen investigations, saved **two-to-three-property shortlists, editable notes and side-by-side evidence**. The default database is **in-memory and temporary**. For opt-in restart persistence on this machine only, add `--fixture-db ./local-fictional-demo.sqlite` to the server command. No accounts, encryption or public access are provided. Do not enter personal or real property information. [Backend setup](backend/README.md), [frontend workflow](frontend/README.md) and [current checkpoint](docs/CHECKPOINT.md).

Manual local runs are optional for debugging; see [Phase 0](audit/phase0/README.md), [Phase 1](audit/phase1/README.md), [Phase 2](audit/phase2/README.md) and [Windows Git setup](docs/GITHUB_SETUP.md). Never commit extracted datasets, private user data, personal names, API tokens or generated property-level output. See [data handling](data/README.md).

## Scope and next milestone

**Bounded flagship:** One supported geography and property class, user-entered enquiry, transparently selected historical comparables, insufficient-evidence handling, saved investigations and side-by-side shortlist comparison.

**Next:** Complete the simplified restricted direct-connection acceptance test, then verify cloud-connected application behaviour, persistent invented-data acceptance and storage/data-use protections. The prior private live rehearsal is historical; the new conditional extraction allowance is unused and cannot be exercised before the protected-storage and permitted-use gate. See [checkpoint](docs/CHECKPOINT.md).

**Conditional only:** Price prediction requires independent chronological evaluation and defensible uncertainty. Live listings, real-time valuations, mortgages, alerts and multi-market expansion are outside this MVP.

Earlier project status and run details remain in the [25 November pre-audit README snapshot](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/8e85c848c66f5c540e3730f8e93d87011d39ffcd/README.md) and the dated evidence linked in the [documentation index](docs/DOCUMENTATION_INDEX.md).
