# Documentation audit and cleanup: 22 November 2026

**Repository:** `Sonkhe-Shongwe/house-price-intelligence` (`main`). **Review basis:** repository Markdown and GitHub Actions workflow files at initial commit [`7bf3266`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/7bf326624d4d9f4b4eb67b8d53c27173f4b10c4e), compared with verified [Phase 0](../research/PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1](../research/PHASE1_CLOUD_AUDIT_RESULTS.md) and [Phase 2](../research/PHASE2_CLOUD_AUDIT_RESULTS.md) results. The PilotODIN October 24 source was inspected for the original complexity-last P0–P8 phase order; House Price Intelligence's delivery stages remain a clearly labelled adaptation, not PilotODIN's Windows feature requirements.

## Objective and scope

Audit **repository documentation**, not new property data: look for outdated status, contradicting claims, unclear sources of truth, duplicated handoffs, broken local navigation, omitted source IDs, stale execution instructions, incorrect stage terminology and unsupported completion claims. Preserve the genuine historical results, original migration trail and approved scope boundaries. Do not fabricate model performance or treat documentation maintenance as feature delivery.

## Findings and resolutions

| Severity | Finding before cleanup | Treatment |
| --- | --- | --- |
| **High** | [Data feasibility](../research/DATA_FEASIBILITY.md) said the live join had not been completed and referred to only seven fabricated-data tests. | Replaced stale status with verified cloud metrics and 42-test pipeline evidence; retained original feasibility questions. |
| **High** | [GitHub setup](../GITHUB_SETUP.md) said live extraction was unverified and instructed Windows execution as the default. | Made GitHub Actions the default, documented the verified run, optional Windows workflow and 14-day artifact retention. |
| **High** | [Phase 0 README](../../audit/phase0/README.md) claimed no data had been downloaded, and referenced an old standalone directory. | Added current cloud result banner, corrected repo-relative commands and v2 reanalysis; retained experimental policy warning. |
| **High** | [Initial Phase 0 checkpoint](../../audit/phase0/PROJECT_CHECKPOINT.md) still read as the live handoff, saying GitHub was unchanged and seven tests passed. | Marked as a **historical pre-extraction snapshot** and linked to the live [checkpoint](../CHECKPOINT.md). Its original facts remain preserved in context. |
| **Medium** | [Source register](../research/SOURCE_REGISTER.md) omitted the Historical Parcel Universe used in Phase 1 and did not distinguish queried feeds from research leads. | Added dataset `nj4t-kc8j`, relevant metadata/classification URLs, observed source use, and outstanding source-rights/as-of checks. |
| **Medium** | [Engineering contract](../engineering/ENGINEERING_CONTRACT.md) had a pre-run checklist with all gates unchecked and no distinction between verified tests and unresolved source quality. | Separated demonstrated gates from outstanding source-validation and P3–P8 product gates, preserving strict evidence rules. |
| **Medium** | [Phase 0 report](../research/PHASE0_LIVE_AUDIT_RESULTS.md) and [Phase 1 report](../research/PHASE1_CLOUD_AUDIT_RESULTS.md) described already-completed follow-on experiments as future tasks. | Updated **follow-up commentary only** to reference completed subsequent phases. Historical counts, methodology and error results were not restated or replaced. |
| **Medium** | The [Phase 1 instructions](../../audit/phase1/README.md) and [backend placeholder](../../backend/README.md) treated subsequent completed phases or the initial evidence gate as pending. | Cross-linked verified research and put P3 contracts before implementing the production backend; frontend placeholder clarified the intended real workflow. |
| **Medium** | [README](../../README.md), [checkpoint](../CHECKPOINT.md) and [decision register](../DECISIONS.md) mixed dated research labels and P0–P8 delivery statuses. | Established one consistent current handoff, unambiguous phase naming and canonical [documentation index](../DOCUMENTATION_INDEX.md). |
| **Preventive** | No automated guard against broken local documentation links and divergent P-stage percentages. | Added `tools/check_docs.py` to the offline GitHub Actions test workflow. It checks Markdown local links, nine P-stage rows, total phase weights and cross-roadmap estimates. |
| **Preventive** | A Markdown-only edit under `audit/` also triggered an expensive live data extraction through an overly broad path filter. | Limited the live GitHub Actions trigger to Python research files or its own workflow. Documentation-only edits still receive offline link and progress checks. |

## Invariants preserved

- **3,539** sales rows, **39,401** building rows, **2,583** screened sales, **1,285** accepted joins and **273** Class 203 matched sale records are still the documented 22 November 2026 source run.
- The Phase 1 and Phase 2 historical test cohort remains **83** 2024 Class 203 subjects; **66** had neighbourhood support and **17** required exploratory 2 km fallback.
- The fallback's historical price MAE was **worse** than the township baseline on those 17. We did not turn it into an approved price estimate or claim a valid present-day price.
- **42 offline tests** is the last verified cloud audit suite count prior to the documentation checker; do not count the docs check as a new unit test.
- The **22.8% weighted MVP estimate is unchanged**, because documentation cleaning is not delivery of backend, UI, shortlist or deployment features.
- No raw records or personally identifying transaction examples were added to Git. Existing research output policy stays aggregate-only.

## Outstanding work, not "cleaned away"

1. **P0/P7:** Dataset-specific public reuse, field display and attribution permission remains unapproved.
2. **P1/P2:** Historical as-of data validity, late reports, geography backfills, join semantics and independent later evaluation remain unresolved.
3. **P3:** Domain/SQL schema, buyer input contract, evidence statuses, saved-investigation provenance and technical stack decisions need review and acceptance.
4. **P4–P8:** No production API/database, browser UI, shortlist persistence, integrated user journey or released app exists.
5. **External source availability:** This cleanup checked **repo-local links and documented evidence**. It is not a fresh audit of every external source URL, licence, source publication semantics or data completeness.

## Documentation operating rules

The [index](../DOCUMENTATION_INDEX.md) identifies current, historic and research-result documents. A new development milestone should update [CHECKPOINT](../CHECKPOINT.md), [DECISIONS](../DECISIONS.md) where relevant, and [P0–P8 roadmap](../P_PHASE_ROADMAP.md) only with accepted evidence. Dates and old findings remain intact; new data requires a new named experiment or dated result file.

For audit results, use a GitHub run link, exact sample/screen and documented limitations. Do not present expired artifacts as guaranteed available. Source approval and user-facing value claims are separate gates.

## Verification status

- Repository-document updates were staged as a single coherent documentation cleanup change.
- The new Markdown link and roadmap consistency check runs via [Property audit unit tests](../../.github/workflows/audit-tests.yml) on pushes and pull requests.
- **Acceptance requires a green GitHub Actions run after commit.** A successful documentation lint checks internal links and arithmetic only; it does not verify factual truth of every sentence.
