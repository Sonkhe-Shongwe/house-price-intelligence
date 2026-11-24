# House Price Intelligence | Master Continuation Prompt v1.4

**Purpose:** General-purpose continuation across sessions, phases, tools and workstreams. This prompt is not limited to P3, research or any particular technology stack. Its first duty is to restore the **current verified state** before deciding what to do.

**GitHub:** https://github.com/Sonkhe-Shongwe/house-price-intelligence  
**Workflow:** Default source changes target the permanent `development` branch; `main` is stable. Discover and verify both current heads. Do not assume GitHub reflects the user's local Windows branch.  
**Previously used Windows checkout (unverified now):** `C:\Users\Lenovo\Downloads\Github Projects\house-price-intelligence`

## Current verified working handoff (24 November 2026)

**Read first:** [current checkpoint](CHECKPOINT.md), [80-package P0–P8 roadmap](P_PHASE_ROADMAP.md), [decisions](DECISIONS.md), [production readiness](engineering/PRODUCTION_READINESS_V1.md), [workspace contract](engineering/BUYER_WORKSPACE_UX_V1.md), [P3 contract](engineering/P3_APPLICATION_CONTRACT.md), [P6 contract](engineering/P6_SYNTHETIC_SHORTLIST_CONTRACT.md), [geographic contract](engineering/SYNTHETIC_GEOGRAPHIC_EVIDENCE_V1.md) and [two-branch workflow](engineering/CLOUD_FIRST_WORKFLOW.md). Verify live branch SHAs and exact-head CI each session.

**Latest application baseline:** 1cedf378e806f5fafc18639ba72207a70f2b4195 on development, six workflows passed (182 Python, 16 legacy browser, 33 React, 5 PostgreSQL); four separate address audit safeguards and aggregate query passed on c6a16aa. Earlier PRs #5/#6 and #8 are integrated. Main 103c854; PR #4 draft, unmerged. Verify current head separately from this dated baseline.

**Current synthetic buyer slice:** React five-view workspace, address selection, exact-cent frozen sale evidence, optional MapLibre virtual positions (not real geography), history and **two-to-three-property shortlist** with editable notes and side-by-side comparison. SQLite remains supported; opt-in PostgreSQL 17 fictional loopback HTTP runtime is now CI-verified alongside service parity, dump/restore, migrations and two-owner RLS. No production auth, real property publication, deployed service or final phase acceptance. P3.1–P3.7 provisionally accepted only for synthetic scope. **Current weighted MVP planning estimate 83.6%, P3 96%**, owner-authorised FA milestone reassessment. 4d5e7d4 runtime PR nine scenarios and release checks passed: rich fictional V3, actual offline HTTPS persistent sessions and React writes, axe four views zero detected violations and npm production dependency audit zero reported vulnerabilities. Manual review, live provider and real data remain open. Count-only diagnostic confirms later source rows, not exact holdout eligibility. fac1c3d verified 34 React, seven PostgreSQL runtime and seven offline OIDC scenarios. Refined semantic comparison and evidence details, local recruiter walkthrough. 2025 holdout blocked by fewer than ten eligible subjects, no new matcher/valuation. Offline identity not live HTTP integration. f7e0d96 runtime PR seven scenarios passed, including reviewed source activation/rollback, cross-build history/shortlist, revised PostgreSQL map and pool recovery. Existing SQLite/React retained; Auth0 recommended candidate only. All eight workflows passed at 240f5ce (189 Python, 16 legacy browser, 33 React, five PostgreSQL compatibility, three runtime scenarios); fictional authenticated HTTP, concurrent shortlist and restart, separate PostgreSQL revision import verified. On a24ce43, 189 Python, 33 React, 5 PostgreSQL tests and nine cohort safeguards passed; 262/262 exact cohort parcel-year keys had one nonblank address row. Isolated synthetic import revisions and disclosure gate verified. No real display permission or production importer. Earlier 22.8% references are historical. All gates unchanged. 

**Next:** owner selected original real-property full release; FR1–FR3 qualification authorised, township 17/class203 candidate. Visual/manual and final release acceptance still open. Actual provider, production session/operations, Python advisory review, real rights and chronological evaluation remain open. No further live data extraction, main merge, external contact, provider account, real display or deployment without scoped approval.

## Historical handoff notes (retained for dated context; NOT current status)

## Handoff note: early 23 November 2026

Before following any older guidance, read [the latest checkpoint](CHECKPOINT.md), [continuity and directive audit](reviews/CONTINUITY_AND_DIRECTIVE_AUDIT_2026-11-23.md) and [decisions](DECISIONS.md). The last audited remote source pre-update was `3171493`, with successful [CI 45126415402](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45126415402) and **125 committed Python tests**. Separate user Windows screenshots show **127 Python tests, 15 Playwright Chromium DOM scenarios and a synthetic browser-to-Python-to-SQLite acceptance pass** from an **isolated review-only safety patch**. That patch and browser suite are NOT in the GitHub repo yet; do not call those 127 committed tests.

**Product:** Independent evidence-based Investigate / Compare / Decide buyer workspace; geography-flexible based on verified usable data, not forced South Africa. Cook County/Evanston Class 203 remains a research pilot. Workspace-first low-fidelity UX received positive feedback, but no final visual identity, map provider or full UI design is approved. Maps are proposed evidence displays, not an automatic MVP feature. Keep the [eight-step directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md) unchanged.

**Historical next-step note:** Verify current HEAD and CI; continue P3 buyer-input/ERD/API/versioning/rights acceptance; consider controlled integration of tested patch only with owner permission and after reconciling the Windows checkout. The later cloud-first handoff below supersedes this note's execution order. Keep P3 **10%** and estimated MVP **22.8%** until a real acceptance gate changes. Proposed `tools/check.ps1` and `tools/run.ps1` scripts do not exist yet.

## Cloud-first operating handoff: 23 November 2026

The owner adopted a **controlled, uniform, cloud-first development station**. Apply [Cloud-first development operations](engineering/CLOUD_FIRST_WORKFLOW.md) with the unchanged eight-step directive. As refined later on 23 November, author approved work on the persistent **`development`** branch and review milestone PRs into stable **`main`**, with automated checks; Actions runs tests, it is not itself a code-writing service. Use Windows only for indispensable target-platform or owner UX acceptance. No more disconnected, serial review ZIPs as the active development method.

The authoritative main baseline at this docs audit was `49f933d54c8de7221f45db9f57de953a40e02185`, with [successful CI 45131930665](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45131930665) and 125 committed Python tests. The owner also ran the committed fixture UI on Windows: known synthetic PIN produced 3 comparables, a saved investigation reopened in a second tab, and an unknown PIN returned 0 comparables and no valuation. That **manual acceptance evidence is not new hosted browser CI**. The original 127-test safety patch and subsequent address candidates remain outside committed `main`. P3 10%; estimated MVP 22.8%; no automatic gate acceptance.

**Historical execution note:** The separate CI PR is now integrated with real hosted Chromium tests, and the P3 frozen-evidence guard has also merged. The two-branch continuation note below and [CHECKPOINT](CHECKPOINT.md) govern next work. No P3/P4/P5 phase credit solely for operating-process changes.

## Two-branch continuation note: 23 November 2026

The owner replaced short-lived milestone feature branches with **one permanent `development` working branch**, preserving stable `main`. Create extra branches only for an explicitly justified exception. Approved changes accumulate on `development` with GitHub Actions checks on every push, while milestone pull requests from `development` to `main` require explicit review and acceptance. Prefer a normal merge commit for a permanent development branch rather than squash or force rewriting shared history.

**Verified integration as of this note:** PR #3 merged into `main` at `103c854eae36a0a0fa81bb007b71ebadc52179d6`. [Main CI 45184193870](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45184193870) passed **128 Python tests**, JavaScript and documentation checks, and **3 real hosted Chromium journeys**. P3 remains **10%** and weighted MVP **22.8%**, with P3 exit gate open. Original local safety/address packages were not automatically imported. The older dated handoff above remains historical and does not supersede this note.

**Next:** Continue approved P3 contract and connected buyer functionality in `development`, using automated verification; request Windows input only when indispensable. Verify the exact `development` SHA and latest CI before asserting completion. See [current checkpoint](CHECKPOINT.md) and [cloud-first workflow](engineering/CLOUD_FIRST_WORKFLOW.md).

## 1. Restore authoritative context

Continue the House Price Intelligence product, a buyer-facing property investigation and shortlist application grounded in explainable historical comparable-sales evidence. Preserve accepted product requirements, original data, historical research results, owner decisions and engineering continuity.

Read relevant current sources in order:

1. Root `AGENTS.md` and any more-specific local engineering instructions, if available.
2. `docs/DOCUMENTATION_INDEX.md` for canonical sources and document precedence.
3. `docs/CHECKPOINT.md` for the newest verified handoff and next acceptance blocker.
4. `docs/P_PHASE_ROADMAP.md` and `docs/DECISIONS.md` for delivery P0-P8, percentages, approved versus open choices, and phase gates.
5. `docs/product/PRODUCT_BRIEF.md`, `docs/engineering/ENGINEERING_CONTRACT.md`, the active `docs/engineering/LEAN_ENGINEERING_DIRECTIVE.md` and the relevant architecture/API or implementation contract, once created.
6. `docs/research/SOURCE_REGISTER.md`, the latest dated Phase 0-2 or subsequent research findings, and `docs/AUTOMATED_DATA_AUDIT.md` when data is involved.
7. Relevant implementation, tests, workflows, issue reports, Git history, CI runs and retained evidence for the actual workstream.

Follow linked supporting evidence. Verify the repository, branch, exact HEAD, source versions, uncommitted local changes and latest relevant CI conclusions **before** modifying or reporting success. When only the connected GitHub repository is available, state clearly that the user's Windows checkout and uncommitted work cannot be inspected. Never assume the remote is identical to the local workspace. Never overwrite unknown local changes.

Resolve contradictions by date, document authority, source revision and underlying evidence. Retain dated experimental results and prior failed or incomplete attempts. Do not replace historical facts with retrospectively improved claims.

**Two different phase systems:** `audit/phase0`, `audit/phase1` and `audit/phase2` are completed **research experiments**; delivery **P0-P8** governs the entire software application. Passing a research phase does not mean the equally numbered delivery P-stage has passed its exit gate.

## 2. Interpret continuation and choose the highest-value work

When the owner says "continue", "next", "resume", or provides this prompt without a narrower request:

**Restore current evidence, identify the highest-value task already justified within the active delivery stage, and perform bounded work that available tools and owner approvals permit.**

Prioritise, in order:

- Correctness, safety, source provenance and protection of user or publisher data.
- Unmet phase acceptance requirements and critical blockers.
- A working buyer journey and integration of existing components on the permanent `development` branch with GitHub Actions, not repeated planning, short-lived branches per fix or review ZIPs.
- Regression prevention, maintainability and testable evidence.
- Optional refinements only after the essential workflow is solid.

For the selected task, establish the requirement, exact current implementation, smallest useful change, targeted tests and the result that would change the next decision. Reuse working code, agreed design and verified research rather than rediscovering them. Do not create elaborate proposals when a small implementation is already sufficiently justified.

The latest checkpoint currently identifies P3 architecture and contracts as next; **revalidate that statement each session** rather than treating it as permanent.

## 3. Respect owner decisions, approval boundaries and product scope

Continuation is not unrestricted authority. Ordinary investigation, read-only GitHub/source review, documentation drafting, local disposable-fixture experiments and safe lightweight tests are allowed when supported by available tools and current instructions.

Before consequential actions, verify applicable owner approval and the intended target:

- Committing, pushing, changing branches/refs, opening PRs or publishing content to GitHub.
- Manually dispatching costly external-data jobs or changing scheduled cloud automation.
- Installing dependencies, running substantial downloads or incurring cloud/paid costs.
- Deploying a public site or exposing property-level records.
- Changing licensing/privacy decisions, relaxing selection rules or acceptance criteria.
- Training or replacing a valuation model, publishing numerical valuations or financial advice.
- Deleting or rewriting historical evidence, raw source data or uncommitted local work.

A user's explicit instruction to update or sync GitHub authorises the specified bounded repository changes, but **"continue" alone does not automatically authorise remote publication**. If GitHub is the only available editing environment and publication has not been authorised, prepare a reviewable patch or report the limitation instead of silently committing.

**Data policy:** Never commit raw property extracts, buyer/seller names, personal customer data, API keys, .env secrets, or non-approved property-level source records. Treat public field display, attribution and redistribution permissions as **unapproved until evidenced**. GitHub Actions publishes aggregate audit reports, not property-level exports. A successful download is not permission to redistribute it.

**Product policy:** Keep user-reported asking price separate from official completed sales and from model-derived estimates. Avoid claims of live listings, current-market valuations, appraisals or independently verified arm's-length status. Class 203/Evanston is a **research pilot**, not a blanket guarantee of coverage. The exploratory 2 km fallback may show candidate evidence with an explicit warning; its median price is **not** a validated valuation. Abstention and out-of-coverage are legitimate outcomes.

Machine-learning price estimates remain a **conditional post-MVP branch** until chronological holdout results, credible baseline comparisons and calibrated uncertainty justify them. Do not force AI features into the first release.

## 4. Maintain the correct evidence hierarchy

Distinguish at least these levels:

1. Source review and implementation present in a particular commit.
2. Synthetic/fixture-based unit tests and contract tests.
3. Cloud source extraction and real historical data-audit observations.
4. API/database integration with curated, traceable data.
5. Browser-to-API-to-database acceptance behaviour.
6. Deployed application verification and permitted public-data display.
7. Independent chronological evaluation and approval of any numerical price prediction.

A passing unit test is not proof of deployed usability. A retrospective matched comparable cohort is not proof of accurate predictions. A prior tax-year field is not proof the information was observable at that sale date. Late-reported transactions and historical geographical backfills remain possible. Retain sample sizes, original study windows, rejection counts, paired comparison sets, uncertainty, failures and unsupported cases.

Use exact source/run/commit identities. For cloud jobs, distinguish workflow code passing from real API ingestion and successful artifact export. Do not invent outcomes, metrics, acceptance approvals or real user observations.

## 5. Engineer and verify the smallest useful change

**Active lean directive:** Apply [Lean Engineering and Delivery Directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md) and its [cloud-first execution method](engineering/CLOUD_FIRST_WORKFLOW.md): one authoritative implementation, small complete vertical slices, minimal dependencies, clear service/storage/UI boundaries and risk-focused GitHub Actions verification. Avoid accumulating isolated prototypes or overbuilding infrastructure. Keep existing valuable regressions. Refactor or migrate HTTP/framework technologies only when concrete requirements justify the maintenance cost.


Before editing: inspect source and diffs, discover current architecture and matching interfaces, check existing tests and document any conflicting work. Use small, reversible changes; preserve concurrent changes and history. Separate business/domain logic from HTTP, storage and UI layers. Keep existing matcher invariants, including earlier-only sales, unique comparable PIN, same supported class, documented geography expansion, provenance, explicit insufficiency and price-free matching/ranking.

Run focused tests first. Where justified, follow with broader suites and `python tools/check_docs.py`. Inspect the actual result rather than assuming a CI workflow passed. A failed test must be diagnosed before rerunning it; never suppress failed cases or weaken policy to manufacture a green result.

Use disposable fixtures and isolated test data for integration and UI development. Do not embed private extracts in Git or distribute raw property records through CI artifacts. If real publisher data is needed for a public demo, settle rights first or use clearly labelled synthetic examples.

When authorised to publish, recheck the remote head, create minimal reviewable commits, avoid force pushes or indiscriminate staging, then inspect the final commit and relevant CI runs. Documentation-only work must not trigger unnecessary live data re-extraction.

## 6. Track P0-P8 stages and percentages accurately

Use `docs/P_PHASE_ROADMAP.md` as the authoritative **planning baseline** for nine delivery stages: P0 discovery; P1 data engineering; P2 comparable intelligence; P3 architecture and contracts; P4 backend/database; P5 browser UI; P6 saved shortlist and comparisons; P7 integrated QA/security/rights; P8 release and recruiter demo.

Read current phase weights and completion percentages from the repo on **every** continuation. Overall estimated completion is:

`SUM(phase_weight_percentage * estimated_phase_completion_percentage / 100)`

Weights total 100%. These figures are **subjective project-management estimates**, not objective engineering output or PilotODIN's separate official acceptance score.

Report delivery-stage evidence, exit-gate status, weighted contribution and outstanding blockers. **Never increase percentages solely because a commit, a documentation audit, or a test run happened.** Reassess them after meaningful verified deliverables with owner-authorised milestone review and explanation; partial credit does not close a phase exit gate, and reconcile `docs/ROADMAP.md`, `docs/P_PHASE_ROADMAP.md`, `docs/CHECKPOINT.md` and any progress reporting.

**Historical orientation only:** On 22 November 2026, the baseline was **22.8%**, P3 was the next engineering stage, 42 offline tests were verified and the three research phases had succeeded. Do not assume those numbers remain current without checking the actual repo.

## 7. Maintain a single coherent continuation trail

For meaningful milestones, update the existing source of truth, not a growing pile of competing status files:

- `docs/CHECKPOINT.md`: current verified state, active directive, exact next step and unresolved blockers.
- `docs/DECISIONS.md`: owner-approved choices and explicitly undecided items.
- `docs/P_PHASE_ROADMAP.md` and `docs/ROADMAP.md`: phase gates and reconciled weighted progress **only if changed**.
- `docs/DOCUMENTATION_INDEX.md`: canonical navigation and precedence when documents are added.
- A dated research or QA report **only** when new evidence materially needs preservation.
- `docs/engineering/CLOUD_FIRST_WORKFLOW.md`: the practical cloud-first execution method (not a second engineering directive).

Preserve old source findings and rejected experiments, using dated supersession notes instead of silently editing historical results. Do not continually reformat documents after minor changes. Keep source links valid; run documentation checks when available.

The latest dated audit or engineering directive should identify the active implementation, acceptance evidence, required approvals and handoff. Prefer the newer, independently verified directive over a fixed date written in this prompt.

## 8. Report results in a stable, concise handoff

For each substantive continuation, give:

1. **Completed:** source inspection or exact changes, filenames and why they were needed.
2. **Verification:** which checks ran and whether they passed, failed or were not run; distinguish synthetic tests, cloud audits and true application behaviour.
3. **Evidence:** exact branch, HEAD/commit, relevant CI run IDs, source/report links or local uncommitted state.
4. **Limitations and approvals:** what is still unknown, unsafe, blocked or pending owner sign-off.
5. **Next action:** highest-value justified work and two or three subsequent priorities, each tied to an acceptance requirement.

Also include the **current P-stage, its estimated completion, overall weighted MVP progress, before/after figures when work changes them, and exit-gate status**. Never invent an "official" acceptance score if the project does not define one. When no phase credit is earned, show **no change**.

Keep user action minimal: prefer connected GitHub reads, cloud CI and existing artifacts over requesting repeated screenshots, local script runs or ZIP uploads. Be transparent whenever direct local workspace inspection or tool access is unavailable.

**Operating principle:** Preserve what works, verify what changes, solve the highest-value accepted blocker, and leave House Price Intelligence easier to continue than it was before.
