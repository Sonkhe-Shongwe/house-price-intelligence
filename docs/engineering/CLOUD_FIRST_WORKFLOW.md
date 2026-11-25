# Cloud-first development operations

**Adopted:** 23 November 2026; **two-branch model approved:** 23 November 2026.  
**Authority:** Implements the unchanged [eight-step Lean Engineering and Delivery Directive](LEAN_ENGINEERING_DIRECTIVE.md) and [P0–P8 acceptance gates](../P_PHASE_ROADMAP.md). It is not permission to deploy, disclose publisher data, change source rights, or accept an incomplete delivery phase.

## Authoritative working arrangement

- **Connected Neon administration:** Use the authenticated integration for non-destructive development-only inspection and scoped database preparation. Never substitute a public repository for a secret store, retrieve elevated credentials unnecessarily, or confuse administrative access with direct application runtime connectivity. See [Neon contract](NEON_CLOUD_INTEGRATION_V1.md). Use the existing protected environment and v4 exact-parent marker for temporary direct-connection acceptance; avoid repeated manual SHA updates. Do not confuse a runner with permanent hosting.

- **One GitHub repository:** [house-price-intelligence](https://github.com/Sonkhe-Shongwe/house-price-intelligence). No competing source checkouts, numbered review ZIPs or parallel status ledgers.
- **`development` is our single continuing working branch.** Build approved application features, fixes, tests and documentation on it. Do **not** create another feature branch for each task. Additional branches require a demonstrated reason, such as an urgent release hotfix, incompatible experiment or concurrent risky migration, and explicit approval.
- **`main` is the stable integrated branch.** Keep the last tested and owner-accepted milestone here. Never use `main` for routine incremental development.
- **GitHub-connected source tools author code; GitHub Actions runs verification.** Actions is not an independent coding agent. Only the exact commit that passed its relevant checks is verified.
- **Windows is the manual acceptance station only when necessary:** Windows-only compatibility, actual UX/visual judgment or owner sign-off. Never treat Windows's unknown uncommitted changes as automatically represented by GitHub.

## Standing engineering autonomy (25 November 2026)

Routine engineering within the approved scope is delegated: independently select and implement the next integrated task, commit to development, run and diagnose CI, correct regressions and continue toward a meaningful milestone in the available execution session. No separate owner approval for ordinary scoped edits or synthetic verification. Ask only for indispensable owner action or a genuine cost, credential/access, data-rights, live-data, destructive-operation, release or main-integration boundary. Preserve the eight-step directive, exact-head evidence and phase gates. Do not claim unattended execution after the session ends. Prefer working software to new process documents.

## Continuous development and integration loop

1. Restore the canonical [checkpoint](../CHECKPOINT.md), actual repository heads, [decisions](../DECISIONS.md), approval scope and current acceptance gate. Inspect relevant implementation and tests before changing it.
2. Develop authorised work directly on **`development`** in coherent, connected buyer slices. Keep each commit reversible, read-only with respect to real publisher data and small enough to diagnose. Implement the complete backend/SQL/frontend/test path when required.
3. Push reviewed commits to **`development`** only when owner-authorised for the scope. The existing offline GitHub Actions workflow runs automatically on every `development` push and every `main` push, plus PRs targeting `main`. A failed check must be corrected on `development`; do not hide failures.
4. At a **meaningful owner-review milestone**, use one pull request from `development` to `main` to inspect the accumulated changes, recheck CI and seek explicit integration approval. There is **no PR required for each ordinary commit or fix**. A continuously open milestone PR is acceptable; it should be updated, not duplicated, while the milestone remains unmerged.
5. Merge only after relevant checks and owner acceptance. **Prefer a normal merge commit, not a squash merge or force-push, for this permanent working branch**, so shared history stays understandable and the branch survives for the next cycle. Confirm merged `main` CI; reconcile any changes made to `main` back into `development` before continuing.
6. Update the existing checkpoint and decisions after meaningful accepted work. Change P0–P8 percentages only on justified phase deliverables, not merely because a branch, test or commit exists.

The development branch is not a staging copy of real property datasets or a public deployment. No real property-level source records, owner/seller names, credentials or secrets may enter commits or CI logs.

## Test responsibility and historical two-branch adoption baseline

| Evidence or test | Default location | Verified status at two-branch adoption |
| --- | --- | --- |
| 12 Phase 0 + 12 Phase 1 + 14 Phase 2 + 4 exporter Python tests | GitHub Actions | Implemented, passing |
| 86 P3 synthetic Python/database/HTTP tests | GitHub Actions | Implemented, passing |
| JavaScript syntax and documentation/phase arithmetic | GitHub Actions | Implemented, passing |
| Supported, unknown-property, reopen and invalid-price Chromium browser scenarios | GitHub Actions | **3 real browser tests passing** against actual local fixture API and SQLite |
| Browser visual quality, device/Windows-specific behaviour and final UX acceptance | Owner where necessary | Not replaced by headless CI |
| Dataset-specific field display rights, historical availability and public release acceptance | Evidence review / owner | Not approved |

**Verified historical integration checkpoint:** `main` commit `103c854eae36a0a0fa81bb007b71ebadc52179d6`, [passing CI 45184193870](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45184193870), 128 Python tests and 3 hosted Chromium cases. The documentation update that establishes `development` is not itself a product deliverable. The current exact branch heads and CI must be checked again on every later session.

The [offline CI workflow](../../.github/workflows/audit-tests.yml) runs on `main` and `development` pushes and PRs into `main`. The [real-data audit workflow](../../.github/workflows/data-audit.yml) **stays separate** and is restricted to its configured paths/manual dispatch. Do not trigger external extraction for ordinary frontend or documentation work.

## Priorities and safeguards

- **Product:** Complete P3 contract acceptance (property identity, exact-money response, domain/ERD, source versions, rights/privacy) before granting P3 gate completion. Then progress through the already-agreed integrated P4/P5 browser-to-service-to-SQL slices and P6 comparison features.
- **Evidence:** Mark changes as proposed, implemented, verified, integrated, accepted or released. A green CI run does not automatically accept a product feature.
- **Earlier Windows patches:** The original isolated 127-test safety patch and address-search candidates are historical inputs. Some safeguards were independently implemented on GitHub; do not assume every original local change is merged. Obtain their exact source diff before incorporating any unmerged element; preserve all local files.
- **Release control:** The repository's `main` protection was not enabled at adoption. Required branch rules remain a separately reviewed configuration decision. Until then, use the documented PR + explicit approval discipline.
- **Progress baseline:** 22.8% was historical at adoption. The current owner-approved estimate is 87.1%; consult [roadmap](../P_PHASE_ROADMAP.md) and [checkpoint](../CHECKPOINT.md), not historical workflow test counts. Workflow-only changes do not award phase credit.

**Operating principle:** One working branch, automated cloud verification, one stable integration branch, milestone approvals rather than a PR for each small step.
