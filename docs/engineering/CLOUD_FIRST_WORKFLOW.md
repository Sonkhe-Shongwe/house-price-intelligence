# Cloud-first development operations

**Adopted:** 23 November 2026, by owner direction.  
**Status:** Current operating method, not a claim that all proposed CI gates are implemented.  
**Authority:** Applies the existing [eight-step Lean Engineering and Delivery Directive](LEAN_ENGINEERING_DIRECTIVE.md), [P0-P8 phase gates](../P_PHASE_ROADMAP.md) and [decision register](../DECISIONS.md). It does not replace those documents or authorise code publication, production deployment, external source downloads or phase acceptance.

## 1. One authoritative implementation

- **Repository:** [Sonkhe-Shongwe/house-price-intelligence](https://github.com/Sonkhe-Shongwe/house-price-intelligence). `main` is the stable integration target; use a short-lived feature branch and pull request for an approved milestone. Avoid active standalone project clones, serial candidate ZIPs and competing checkpoints.
- **Cloud-first authoring and review:** Write and review source in this GitHub repository through authorised connected GitHub editing or cloud coding tools. **GitHub Actions runs jobs on commits; it is not, by itself, an autonomous code author.** Never claim a workflow developed or merged code merely because it passed tests.
- **GitHub Actions first:** Routine automated test, database, API, lint/syntax, documentation and eventual browser acceptance checks should run on the exact GitHub commit. Use existing commands locally only for fast diagnostics or a proven environment-specific gap.
- **Local Windows role:** Pull a reviewed revision **only when essential** for physical Windows compatibility, owner UX/visual judgment or final human acceptance. Give the owner the exact SHA, one command and a short scenario checklist. A local screenshot is evidence for that session, not a committed CI result.
- **Approvals:** An explicit bounded request to update GitHub can authorise the requested branch/PR change. Do not silently merge, deploy, force-push, change paid jobs, publish source property records or alter acceptance gates. A green check is not owner approval.
- **Preserve source:** Before incorporating earlier local work, inspect the real local status/diff or an exact exported patch. Keep untracked records. Never assume the isolated Windows safety patch is in `main`; do not replace it with a lookalike.

## 2. Controlled feature delivery loop

1. **Specify the next buyer outcome:** Identify its P-stage, acceptance criteria, abstention/failure case, data/privacy boundary and manual testing necessity; use one issue or PR description, not a new parallel roadmap.
2. **Create one feature branch** from verified `main`; check the actual current HEAD and known concurrent changes. Do not develop directly on `main` by default.
3. **Implement one coherent vertical slice** across necessary layers only. Use the existing matcher, synthetic fixtures and contracted evidence rules. Do not introduce speculative services or UI frameworks.
4. **Push reviewed commits** to the feature branch only when authorised. Trigger existing GitHub Actions and the additional CI gates as they are actually implemented. Do not download real publisher records for a UI/docs edit.
5. **Diagnose failing jobs on the same branch.** Run deterministic unit, SQLite, HTTP, safety and browser acceptance checks, with safe logs and precise commit SHA. Mark any missing test layer as unverified.
6. **Review the PR and owner acceptance requirements** before integration. Once required checks and applicable manual approval pass, merge through the agreed procedure, then confirm `main` CI on the merged SHA.
7. **Update canonical continuity:** Record accepted implementation in [CHECKPOINT](../CHECKPOINT.md), [DECISIONS](../DECISIONS.md) and the roadmap only when phase evidence actually changes. No automatic percent credit for commits, docs or CI infrastructure.

The approved eight-step engineering lifecycle still governs requirements, architecture, risk, implementation, verification, user acceptance, controlled integration and handoff. This loop only specifies **where and how** to execute it.

## 3. Test responsibility matrix

| Test / evidence | Default owner | Actual status at adoption |
| --- | --- | --- |
| Research unit tests and aggregate-report tests | GitHub Actions | **Implemented** in `audit-tests.yml` |
| Synthetic Python, SQLite, service/HTTP contract tests | GitHub Actions | **Implemented** in `audit-tests.yml`; 125 Python tests in total across suites |
| Documentation links and P0-P8 arithmetic | GitHub Actions | **Implemented** via `tools/check_docs.py` |
| JavaScript syntax | GitHub Actions | **Not enforced in CI**; optional Node diagnostic in `tools/dev_check.py` |
| Real Chromium browser-to-HTTP-to-SQLite user journeys | GitHub Actions | **Not in committed CI**; previously passed only in a separate isolated Windows patch |
| Negative paths: unknown property, malformed input, tampered evidence | GitHub Actions | Some Python tests already exist; expand actual browser checks only for meaningful risks |
| Windows compatibility, physical UI and owner visual acceptance | Owner, only as required | **Manual**; 23 November known/unknown/reopen synthetic demonstration observed |
| Final public source permissions, privacy and release decision | Owner + evidence review | **Open**; no deployment approval |

`audit-tests.yml` currently runs on pushes and pull requests. It does not enforce Node or Playwright. `data-audit.yml` is separate, performs external source extraction only on its restricted push paths or manual dispatch, and uploads aggregate-only summaries. **Do not merge these into one always-on expensive workflow.**

Reference: [offline test workflow](../../.github/workflows/audit-tests.yml), [live research audit workflow](../../.github/workflows/data-audit.yml) and [developer checks](../../tools/dev_check.py).

## 4. First GitHub Actions implementation milestone (not yet implemented)

1. Enhance the **existing** offline test workflow to enforce JavaScript syntax alongside Python and docs, with read-only `contents` permission, reasonable timeouts and a clear job summary. Confirm green PR CI before considering a branch rule.
2. Add the smallest synthetic Chromium acceptance check for a **supported** investigation, a truthful **insufficient-data** result and **reopen**, exercising browser -> HTTP -> SQLite. Keep fixtures invented; ensure browser and application tests run from the *same commit*. Do not claim acceptance from static asset GETs or mocked browser API alone.
3. Review and enable required PR checks / branch protection **only after** their jobs have stable names and pass. As audited on 23 November, `main` is not protected. This is a proposed configuration change requiring a separate owner-approved action.
4. Then reconcile the original local 127-test safety patch, exact money and address-search candidates through **one** reviewed integration branch. Exact local patch contents are required; previous review archives are inputs, not new active source trees.

No new workflow, dependency, repository rule, trigger, secret or cloud-hosted browser suite is created by adopting this document.

## 5. Safety, reporting and progress

- Use least-privilege GitHub Actions permissions. Never pass secrets or protected publisher records to untrusted pull-request jobs. Keep CI artifacts aggregate or synthetic and avoid logging person-level or property-level source records.
- Separate `implemented`, `verified`, `integrated`, `accepted` and `released`. State exact branch, SHA, workflow run, test scope and missing acceptance layers.
- Review outcomes in the single PR and [current checkpoint](../CHECKPOINT.md); do not produce serial ZIP handoff packages.
- Keep the [P0-P8 weighted roadmap](../P_PHASE_ROADMAP.md) unchanged until a substantive milestone meets its gate. **Baseline at adoption: P3 10%, weighted MVP 22.8%.**
