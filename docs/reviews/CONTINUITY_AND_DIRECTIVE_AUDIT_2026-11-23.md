# House Price Intelligence: Continuity and directive audit

**Audited:** 23 November 2026. **Scope:** Documentation and source-of-truth reconciliation only. **Starting GitHub main:** `317149392678646455a0eb6080c086d682bca293`. This is not a new engineering directive or release approval.

## Evidence inspected

Current GitHub repository, source tree and recent CI; [Lean Directive](../engineering/LEAN_ENGINEERING_DIRECTIVE.md), [Engineering Contract](../engineering/ENGINEERING_CONTRACT.md), [P3 Contract](../engineering/P3_APPLICATION_CONTRACT.md), [P0-P8 Roadmap](../P_PHASE_ROADMAP.md), [Product Brief](../product/PRODUCT_BRIEF.md), [Pinnacle Vision](../product/PINNACLE_VISION.md), [UX Research](../design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md), [Source Register](../research/SOURCE_REGISTER.md), [Phase 2 Report](../research/PHASE2_CLOUD_AUDIT_RESULTS.md), backend/SQLite/frontend files, tests and GitHub Actions. The real Windows worktree was **not** independently accessible.

### Test and implementation boundary

- **Live research evidence:** [Cloud audit 45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782). 3,539 sale rows; 39,401 historical building rows; 2,583 provisionally screened sales; 1,285 provisional joins; 273 class-203 joined sales. Of 83 evaluated 2024 subject sales, 66 had neighbourhood evidence and 17 used exploratory 2 km fallback. On those 17, fallback median-price MAE was **$209,470.65**, worse than township baseline **$192,153**. Not a validated valuation or proof of historical publication timing.
- **Committed application evidence:** Synthetic PIN-first Python/SQLite/WSGI/browser candidate, 15-table draft schema and local UUID reopen. **125 Python tests** (42 research/export + 83 application) passed on [GitHub CI 45059455620](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45059455620). [Documentation HEAD CI 45126415402](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45126415402) was also successful, but did not integrate patch/browser tests.
- **Separate local-only verification:** Owner Windows screenshots showed a disposable patched checkout with **127 Python tests**, **15 Playwright Chromium DOM scenarios** and a real **synthetic browser -> Python -> SQLite** success/insufficient/reopen/error journey all passing. The isolated runner reported the original Windows repository unchanged. The two extra backend regression tests and backend/frontend guard patch are **not committed to GitHub main**, and Playwright is **not in the committed CI workflow**.
- **Not shipped:** Authorised real-data public interface, verified consumer property/address lookup, permanent shortlist with notes and side-by-side UI, map, model valuation, production API, accounts or deployment.

## Drift identified and corrected

| Issue | Resolution |
| --- | --- |
| Historical docs claimed browser testing was still blocked or unverified | Preserve the dated blocked attempt, but state the **later isolated synthetic graphical pass** without falsely claiming committed CI coverage |
| Mixed 125 and 127 test counts | Label **125 committed** versus **127 isolated patched** everywhere updated |
| Product discussion introduced a map and Property24 comparisons | Clarify **original independent Investigate / Compare / Decide** product, not a listings marketplace; maps are **proposed evidence presentation**, not approved MVP feature |
| Ambiguous geography | Explicitly **data-first, geography-flexible**. Do not force South African coverage if unsupported; Cook County/Evanston Class 203 remains the research pilot, not the final market |
| Screen concept might be treated as final branding | Owner liked the shortlist/workspace-first *low-fidelity structure*; palettes, final routes, brand and aesthetics remain unapproved |
| Multiple source-of-truth status notes | The current [CHECKPOINT](../CHECKPOINT.md) supersedes earlier status claims; retain dated audits and research results without rewriting history |
| Proposed developer shortcuts sounded already implemented | `tools/bootstrap.ps1`, `tools/check.ps1`, `tools/run.ps1` **do not yet exist**. Existing check: `python tools/dev_check.py`; fixture app: `python -m backend.run_synthetic_api --fixture-only --port 8765` |

## 11 unresolved areas

| # | Area | Main gate |
| --- | --- | --- |
| 1 | Property-level display/reuse licensing, attribution and privacy | P0/P7 |
| 2 | Point-in-time record availability, late reporting and source backfills | P1/P2 |
| 3 | Valid property identity across address, PIN, parcel, building, sale transaction | P1/P3/P4 |
| 4 | Eligibility and similarity of selected historical sales; untouched later holdout | P2 |
| 5 | Consumer-friendly supported property enquiry versus technical PIN | P3 |
| 6 | Best first market/class selected by usable data, not nationality | P0/P3 |
| 7 | Persistence, buyer notes, frozen evidence and secure access policy | P3/P6/P7 |
| 8 | Reviewed safety patch, browser-test reproducibility, unified local checkout | P3 |
| 9 | Map coordinates, accuracy, provider permissions, CSP/referrer, accessible table | P3/P5 |
| 10 | Final UX identity, layout, navigation, design approval and usability | P3/P5 |
| 11 | Production schema, migrations, hosting, security and operational controls | P3/P7/P8 |

**Additional technical review item:** SQLite prices are stored in exact integer cents, but the synthetic candidate builds comparable price values via `cents / 100`. Review money serialization before extending financial claims; no implementation has changed.

## Directive verdict

**RETAIN the owner-approved eight-step directive unchanged.** It already covers buyer requirements, contracts, failure analysis, small vertical slices, risk-driven tests, real-browser acceptance, controlled integration and continuity. Apply product/UX approval, geospatial provenance and anti-scope-drift discipline *inside* the directive; do not add another governing process.

**Main risk:** Whether buyer-selected property identity can connect lawfully and accurately to time-appropriate, eligible recorded sales. A visual map or automated estimate is not a substitute.

## Exact new-tab handoff

1. Read [Master Continuation Prompt](../MASTER_CONTINUATION_PROMPT.md), [CHECKPOINT](../CHECKPOINT.md), [DECISIONS](../DECISIONS.md), [P3 Contract](../engineering/P3_APPLICATION_CONTRACT.md) and [UX Research](../design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md); verify GitHub main HEAD and latest CI again.
2. **Current P3:** Review and accept domain/ERD, true buyer input and market scope, four evidence statuses, source versioning, save/reopen, errors, privacy. Locally passed graphical fixture tests are important evidence but not P3 contract acceptance.
3. **Controlled engineering next:** With explicit owner permission to integrate code, inspect local Windows status and exact patch; add the two reopen-guard tests and backend/JS safety changes to main, establish reproducible browser acceptance and verify CI on that exact commit. Do **not** assume this documentation-only update authorised code integration.
4. Parallel research: permission, availability timing, join integrity, legitimate market/geography choice and coordinate provenance. Final look/feel and map provider remain open decisions.

**Windows details last observed:** Checkout `C:\Users\Lenovo\Downloads\Github Projects\house-price-intelligence`; review folder `C:\Users\Lenovo\Downloads\HPI-P3-review`. Three untracked research ZIP archives were previously present inside the real checkout; do not delete/overwrite them. GitHub reads cannot verify current Windows status.

**No progress change:** P3 **10%**, weighted MVP **22.8%**; P4-P8 exit gates remain open. No new feature, map, framework, model or deployment approved.
