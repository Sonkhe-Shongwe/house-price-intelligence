# House Price Intelligence: Lean Engineering and Delivery Directive

**Adopted:** 22 November 2026; **engineering lifecycle extended by owner:** 23 November 2026  
**Status:** Active engineering process directive for future work. It does **not** approve a framework, override data/rights restrictions, accept an unintegrated prototype or award a delivery milestone.  
**Scope:** All delivery stages (P0–P8), including research, database, Python services, browser UI, testing, CI, documentation and handoffs.  
**Authority:** Complements the [engineering contract](ENGINEERING_CONTRACT.md), [P-stage roadmap](../P_PHASE_ROADMAP.md) and [master continuation instructions](../MASTER_CONTINUATION_PROMPT.md). Correctness, owner approvals and source-data protections take precedence over speed.

**Execution addendum (23 November 2026):** The owner adopted a [cloud-first development station](CLOUD_FIRST_WORKFLOW.md), later refined to one continuing `development` branch plus stable `main`, with GitHub Actions for routine tests and Windows only for indispensable human/platform checks. This implements the existing lifecycle without changing its eight steps, approvals or phase gates.

## 1. Core operating principle

**Build the simplest correct solution that demonstrably solves the current user problem. Prevent defects through clear interfaces, explicit domain rules, maintainable architecture and database constraints, then verify the remaining high-value risks with lightweight automation.**

- **KISS:** Prefer an understandable implementation and small number of moving parts.
- **YAGNI:** Implement only capabilities justified by the present buyer workflow or an accepted next-stage requirement.
- **DRY with judgment:** Avoid duplicated *business rules*. UI validation may duplicate a server-side check for usability, but the backend must remain authoritative.
- **Separation of concerns:** Distinguish UI, HTTP validation, application workflow, pure matching logic, SQL persistence and data ingestion.
- **Small-batch delivery:** Prefer finished, integrated vertical slices over long-lived isolated prototypes, expansive platform scaffolding or repeated architecture rewrites.
- **Fail safely:** Invalid, ambiguous, stale, unsupported or insufficient property evidence yields an explicit truthful outcome, never a guessed price.
- **Readability:** Clear domain names, functions with focused responsibilities, predictable data types, error contracts and minimal comments that explain important reasons.

**Good architecture reduces defect opportunities. Automated tests verify assumptions that good architecture cannot guarantee.** Do not treat test count, coverage percentage, line count or passing fixtures alone as proof of a strong product.

## 2. One authoritative implementation, not successive disconnected prototypes

**Historical risk at initial adoption (22 November):** The P3 v0.1-v0.5 candidates had not yet been integrated. This remains dated historical context, not the latest source state.

**Verified remote on 23 November:** The fixture-only P3 application was integrated at [`e8b8f70`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/e8b8f70de2bb10fd61b9cec9cc1d12aabdc6cfef). [Post-integration CI run 45059455620](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45059455620) passed 125 research/application tests and documentation checks on Python 3.12. The graphical browser, P3 contract, production database, public-data rights and deployment are **not** accepted. The owner's Windows branch and uncommitted files were inaccessible.

**Required approach going forward:**

1. Inspect the latest remote repository **and** the actual local working tree when accessible; never assume they match.
2. Stop making indefinitely numbered copies of the same app. Develop approved work in the permanent `development` branch, preserving `main` for stable accepted releases. Preserve earlier work as history/patches and reconcile exact changes carefully. Create exceptional branches only when specifically justified and approved.
3. Keep the Phase 2 matching engine's documented selection invariants unchanged unless a separate acceptance decision requires and verifies a change.
4. Before extracting abstractions, establish at least two real uses or a measured need. Avoid speculative plugin systems, provider adapters, event queues or service layers that do not simplify the current feature.
5. Preserve a single current handoff and existing phase-gate records; do not grow a parallel family of authoritative progress files.

**Integration is not permission-free:** "continue" alone is not blanket authorisation to commit, push, install dependencies, deploy or publish sensitive data. An explicit request to update GitHub permits the requested bounded change, subject to preserving concurrent work.

## 3. Proposed architecture and technology selection

For the bounded property-investigation MVP, **prefer a Python modular monolith** with clear, light boundaries:

```text
Browser (HTML/CSS/JavaScript)
    -> API input and response contract
       -> Investigation service
          -> Existing pure Python comparable matcher
          -> Relational persistence and historical evidence repository
             -> Curated dataset + saved enquiry/evidence records
```

The matcher does not import HTTP, SQL, frontend code or source-download utilities. The service owns workflow decisions. Storage owns transactions and constraints. The API validates and exposes supported evidence states. Browser code handles input usability and presentation, not eligibility truth.

### Technology decisions: defaults for evaluation, not irrevocable commitments

| Layer | Lean candidate | Selection trigger |
| --- | --- | --- |
| Python | Existing compatible Python standard | Keep current source/tests working; avoid upgrades solely for novelty |
| HTTP validation | Keep the current minimal WSGI adapter **or** evaluate FastAPI/Pydantic | Adopt only if it removes meaningful handwritten parsing/security/contract burden without large migration risk |
| Database | SQLite and explicit parameterised SQL first | Consider PostgreSQL if real concurrency/deployment needs justify it |
| Persistence layer | Thin Python data-access functions; foreign keys, unique constraints and transactions | Consider an ORM/migration tool only when schema changes and query maintenance justify it |
| Frontend | Existing HTML, CSS and plain JavaScript | Adopt a framework only when UI state/complexity measurably demands it |
| Quality tools | Existing `unittest`, optional Ruff formatter/linter | Add tools if they simplify maintenance and provide fast deterministic checks; avoid unrelated mass formatting |
| Browser acceptance | One or two meaningful Playwright scenarios when browser execution is permitted | Do not claim graphical acceptance from HTTP asset retrieval alone |
| Dependencies | Minimal reviewed additions; pin and lock if adopted | Require a specific payoff, compatibility review and approval for installation |

**Avoid by default:** microservices, Kubernetes, mandatory Docker, Redis, Celery, message brokers, elaborate frontend state frameworks, generic AI agents and premature ML valuation training. No blanket prohibition if a later measured requirement changes the decision.

## 4. Practical code-quality rules

- Use business-specific names and short, cohesive functions. Do not split code into dozens of nearly empty wrappers for aesthetic reasons.
- Define typed input/output contracts at layer boundaries. Preserve **PIN as a zero-padded string** and use `Decimal` or integer cents for persisted money; avoid unnecessary conversion to floats.
- Keep recorded sale date, analysis date, data-extraction timestamp and source-publication availability distinct. Unknown availability remains unknown.
- Parameterise SQL. Enforce relevant primary/foreign keys, uniqueness and transactional rollback in the database; verify SQLite foreign-key enforcement per connection.
- Explicitly separate a user-reported asking price, recorded sale prices, descriptive historical calculations and any eventual approved prediction.
- Avoid N+1 queries when observed or obvious in a hot path; profile or measure before introducing caches.
- Keep error responses deterministic and actionable. Valid `insufficient_data` or `out_of_coverage` outcomes are different from bad input, unavailable evidence and infrastructure failure; never silently fall back to township median or guessed property facts.
- Log useful failures, correlation context and source-build identifiers where safe, without exposing protected personal or per-property records. Handle expected errors at their relevant boundary; return safe external errors for unexpected failures and retain protected diagnostics.
- Avoid broad catches, permissive defaults, hardcoded real property details, hidden mutation and magic numbers without documented domain justification.
- Refactor only when there is actual duplication, complexity, changing requirements or maintainability pain; do not rewrite successful components for fashion.

## 5. Minimal, risk-based automated verification

**Default fast loop:** format/lint changed Python (where configured), run relevant unit/contract tests, then the existing quick integration smoke. Repeat broader checks when shared code, SQL schema, API contracts or release pathways change.

| Change | Minimum appropriate evidence |
| --- | --- |
| Pure matching or eligibility rule | Focused deterministic examples for valid selection, no future sale, duplicate PIN, explicit abstention; then existing matching regressions |
| Database schema or persistence | Foreign keys, duplicate/ambiguous links, transaction rollback, save/reopen and build-provenance isolation |
| API contract | Input validation, supported/unsupported statuses, structured failures and same-origin protections |
| Browser workflow | One supported investigation journey plus a meaningful failure/insufficient-data case in a real browser when available |
| Documentation only | Internal Markdown links and P0–P8 arithmetic; do **not** run a live data extraction |
| Public deployment | Rights/privacy approval, security and user-data checks, integrated user journey, permitted real-environment smoke |

- Keep the current fast tests. **Do not delete existing valuable regressions just to reduce a test count.**
- Do not add trivial tests for getters, internal variable names or behaviour already protected at a lower level.
- Test at the lowest reasonable layer; reserve graphical/end-to-end tests for real user journeys and cross-layer risks.
- Diagnose a failed check before rerunning it. Do not suppress evidence, rewrite a failing test to match bad code, or equate the absence of errors with full acceptance.
- The reported 83 passing local P3 v0.5 tests are fixture/HTTP evidence **only**. A prior Chromium graphical check was blocked by the environment; browser acceptance stays open.

**Feedback-time targets (aspirations, not verified SLAs):** coding checks in seconds, focused suite plus contract checks approximately under one minute on a normal runner, few browser tests only when pertinent. Measure actual times, and only optimise meaningful bottlenecks.

## 6. Eight-step feature engineering lifecycle (approved 23 November 2026)

Apply this **proportionately**: a tiny fix needs a concise outcome and a focused regression; a change affecting a schema, trust boundary, public-data handling or multiple components needs explicit contract, migration and recovery review. This replaces the old seven-step sequence, without removing its protections.

1. **Problem and requirements:** Define buyer outcome, inputs/outputs, invariants and at least one success and meaningful failure/abstention example.
2. **Architecture and contract:** Assign ownership across browser, HTTP, service, matcher and storage; specify key identity, dates, money, source versions, API responses and expensive-to-reverse decisions.
3. **Risk and failure analysis:** Check bad joins, duplicate PIN, future or backfilled evidence, source drift, privacy, interruption, permission and rollback.
4. **Implementation:** Build the smallest complete vertical slice; preserve accepted behaviour and retain compatible paths.
5. **Automated verification:** Run risk-focused unit, domain, SQL, API and security checks. Protect each genuine defect with a meaningful regression test.
6. **Integrated user acceptance:** Where relevant, actually run browser-to-HTTP-to-database success, insufficiency, unsupported and infrastructure failure flows. HTTP asset loading alone is not a graphical browser pass.
7. **Review and controlled integration:** Check source/HEAD and available local diffs, inspect the change, obtain publication approval, and verify CI on the precise source revision.
8. **Documentation and continuity:** Update only the one authoritative checkpoint, decisions and milestone records affected by accepted evidence. Preserve historical findings and do not award progress for docs or test counts alone.

### Evidence and Definition of Done

- **Implemented:** Code exists at an identified source revision.
- **Verified:** Appropriate named checks passed on that revision and environment; untested levels remain explicit.
- **Integrated:** Reviewed work is in the intended branch with local/remote divergence reconciled where available.
- **Accepted:** Applicable contract, buyer, evidence and owner gates have passed.
- **Released:** Operational, security, data-rights and authorised deployment gates have passed.

Each substantial change should identify its outcome, affected boundaries, unchanged invariants, success/abstention/error cases, test evidence, exact source/CI, blockers, approval and progress decision. Do not create extensive paperwork for trivial changes.

## 7. Quality and delivery metrics

Track useful signals rather than code volume:

- Cycle time from feature start to **accepted integration**; reduce it over successive features.
- Number and age of unintegrated candidate branches/workspaces; aim for one active coherent implementation.
- Coding-check feedback time; aim for fast checks that do not disrupt iteration.
- Escaped/repeated regressions and their root causes; protect fixes with focused tests.
- Completed browser-to-database user journeys and working acceptance gates, not just unit-test totals.
- Rework due to unstable contracts; decrease through clearer, narrower boundaries.

No arbitrary 100% test coverage requirement, 100% lint cleanliness on untouched historical code, forced test-count reduction, or KPI used to justify weakening safety checks.

## 8. Current priorities and boundaries (23 November 2026)

1. **Accept P3 before expanding:** Review the already-integrated synthetic PIN-first API, 15-table draft ERD, error/abstention states and genuine graphical browser journey. CI is verified but P3 acceptance remains open.
2. **Review-only evidence integrity guard:** A separate sale-price/sales-snapshot reopen-guard patch exists outside GitHub. Do not claim it is integrated or tested by the 125-test CI. Reconcile the Windows checkout and rerun the full suite before any authorised integration.
3. **P4/P5 connected slices after P3:** Implement curated-build storage/reader, investigation API and matching browser behaviour together on safe fixtures. **P4 and P5 still have separate completion scores and exit gates**.
4. **P6 buyer workflow:** Saved two-property shortlist, notes, reopen and comparison with frozen provenance.
5. **Continuous protection; independent readiness:** Validate security, errors, provenance, privacy and migrations during every stage. P7 independently checks readiness, while P8 remains authorised deployment and portfolio handoff.

**Unresolved:** final buyer entry/market scope, public field rights, historical as-of availability, later holdout, approved production framework/hosting, graphical acceptance, shortlist and deployment. No automated valuation model is approved.

**Historical baseline:** The original 22 Nov adoption referred to `708239eb2451e379981767136186ab5010057fed`, 42 published research tests and 83 local isolated P3 tests. This was a dated baseline and remains preserved for continuity.

**Planning estimate unchanged:** P3 **10%**; weighted MVP **22.8%**.

## 9. Safe large changes, migrations and CI controls

Use **baseline -> explicit contract -> compatible expansion -> tested migration/comparison -> controlled switch -> monitoring/recovery -> retirement** rather than one large destructive replacement.

- Test database migrations on verified copies; keep snapshot/transaction provenance, idempotency and recovery controls. A Git rollback is not automatically a safe database rollback.
- Preserve price-free comparable ranking, earlier-only sales, unique PIN, sale/building/parcel grain, exact cents, leading-zero IDs and distinct analysis/publication/extraction dates. Reject inconsistent evidence rather than manufacture a value.
- Maintain least-privilege CI and separate cheap offline checks from costly live data extraction. Workflow, branch protection, dependency pinning and hosted services require separately reviewed implementation and permissions.
- Apply the same review to AI-assisted and human code. No LLM output authorises data publication, protected writes or unsupported valuation claims. Do not rewrite the framework unless measured needs justify it.
