# Cloud-first delivery: documentation and CI readiness audit

**Audited:** 23 November 2026.  
**Scope:** Read-only repository/workflow audit followed by documentation-only operating updates. No implementation, workflow YAML, external data, branch rules, deployment or phase-credit changes.  
**Audited main:** `49f933d54c8de7221f45db9f57de953a40e02185`. Last known passing main run: [45131930665](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45131930665). The audit was prepared on a docs feature branch; `main` remains the baseline until explicitly reviewed and merged.

## Verified source and audit findings

| Area | Verified finding | Document action |
| --- | --- | --- |
| Repository organisation | One authoritative public GitHub repo exists; prior sessions accumulated disconnected review ZIP candidates | Adopt one GitHub branch / PR per bounded milestone; archives remain historical inputs |
| Offline CI | [`audit-tests.yml`](../../.github/workflows/audit-tests.yml) runs Phase 0, Phase 1, Phase 2, report-export and P3 synthetic Python suites plus docs on push/PR; **125 tests** in successful committed CI | Keep one fast offline test backbone, make other checks explicit future work |
| Research CI | [`data-audit.yml`](../../.github/workflows/data-audit.yml) performs external extraction on restricted main code paths or deliberate dispatch; summary artifacts only | Preserve expensive / rights-sensitive audit separation |
| Browser and JavaScript | Node syntax is an optional local diagnostic; no committed Playwright workflow or browser quality gate | Mark as proposed CI milestone, not complete |
| Branch merge control | `main` was observed **unprotected**; PR required checks are not enforced | Propose later review of branch rules after checks are verified, not claim enabled protection |
| User Windows test | Owner screenshots and server logs show loaded fixture UI, three selected comparables for known synthetic PIN, reopening in another tab, and unknown PIN returning zero comps with no valuation; POSTs returned 201 | Record **manual synthetic acceptance evidence** separately from CI and the still-unintegrated safety patch |
| Safety patch and address candidates | A 127-Python-test / 15-Chromium-case safety checkout and later address/identity packages were reviewed separately, not integrated in `main` | Require precise local diff/patch recovery; do not invent combined source or overwrite unknown local files |
| Product stage | P3 contract acceptance and all 11 prior grey areas remain open; no rights-approved property-level release | Retain P3 **10%** and weighted MVP **22.8%** |

## Approved operating decision

The owner requested a **controlled, uniform, cloud-first development station** on 23 November 2026: most routine development and automated verification happens through GitHub-connected authoring plus GitHub Actions; local Windows pulls are reserved for necessary physical or human acceptance. Actions executes workflows and tests; it does **not** autonomously author all code. Short-lived review branches, PRs, CI on exact revisions and explicit approval govern integration.

The practical method is in [Cloud-first development operations](../engineering/CLOUD_FIRST_WORKFLOW.md). It **applies**, but does not amend, the [approved eight-step directive](../engineering/LEAN_ENGINEERING_DIRECTIVE.md). This documentation audit is a dated evidence record, **not** a second roadmap or a competing status file. The canonical live state remains [CHECKPOINT](../CHECKPOINT.md).

## Exact next acceptance work

1. Review and merge this docs-only PR, after confirming docs checks. Do not award P-stage points.
2. In a separately authorised engineering PR, strengthen existing CI with enforced JS checks and a small safe synthetic browser acceptance suite; keep the live audit separate.
3. Reconcile the exact Windows safety patch once into the authoritative repo, protect untracked data and continue P3 contract acceptance. Restrict local Windows activity to genuine manual verification.

**Not established by this audit:** automated browser CI, protected main, safety-patch integration, publisher display rights, accepted production architecture, permanent shortlist, deployed service or numerical valuation.
