# House Price Intelligence: Lean Engineering and Delivery Directive

**Adopted:** 22 November 2026  
**Status:** Active engineering process directive for future work. It does **not** approve a framework, override data/rights restrictions, accept an unintegrated prototype or award a delivery milestone.  
**Scope:** All delivery stages (P0–P8), including research, database, Python services, browser UI, testing, CI, documentation and handoffs.  
**Authority:** Complements the [engineering contract](ENGINEERING_CONTRACT.md), [P-stage roadmap](../P_PHASE_ROADMAP.md) and [master continuation instructions](../MASTER_CONTINUATION_PROMPT.md). Correctness, owner approvals and source-data protections take precedence over speed.

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

**Observed process risk (22 Nov 2026):** The GitHub main branch contains the verified research code, while isolated P3 v0.1–v0.5 candidates contain a synthetic property enquiry, SQLite storage, HTTP service and browser assets that have not been accepted or integrated. Their local test results must not be reported as GitHub CI or native browser acceptance.

**Required approach going forward:**

1. Inspect the latest remote repository **and** the actual local working tree when accessible; never assume they match.
2. Stop making indefinitely numbered copies of the same developing app. Select one reviewed source workspace or short-lived branch, preserve other work as history/patches, and integrate compatible changes in small units when publication is authorised.
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
- Keep error responses deterministic and actionable; no silent fallback to township median or guessed property facts.
- Log useful failures, correlation context and source-build identifiers where safe, without exposing protected personal or per-property records.
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

## 6. Seven-step feature workflow

1. **Outcome:** State the user-visible behaviour or data invariant and an explicit done condition.
2. **Inspect:** Read current relevant source, test evidence, diffs, outstanding approvals and compatibility boundaries.
3. **Design minimally:** Specify inputs, outputs, errors, affected data and one acceptance case. Do not write a substantial speculative proposal.
4. **Implement a vertical slice:** Reuse domain logic; connect only the necessary browser, service and database components.
5. **Verify proportionately:** Run focused checks, add only high-value regressions, and perform relevant integration/browser tests.
6. **Integrate when authorised:** Small, reviewable change; remote SHA lease; run CI and inspect real results. Do not accumulate another unsynchronised long-lived prototype.
7. **Handoff sparingly:** Update the current checkpoint and decisions only for a meaningful accepted change; preserve previous evidence and update P-stage percentages only when gates justify credit.

## 7. Quality and delivery metrics

Track useful signals rather than code volume:

- Cycle time from feature start to **accepted integration**; reduce it over successive features.
- Number and age of unintegrated candidate branches/workspaces; aim for one active coherent implementation.
- Coding-check feedback time; aim for fast checks that do not disrupt iteration.
- Escaped/repeated regressions and their root causes; protect fixes with focused tests.
- Completed browser-to-database user journeys and working acceptance gates, not just unit-test totals.
- Rework due to unstable contracts; decrease through clearer, narrower boundaries.

No arbitrary 100% test coverage requirement, 100% lint cleanliness on untouched historical code, forced test-count reduction, or KPI used to justify weakening safety checks.

## 8. Current execution priorities and boundaries

1. **Consolidate P3 v0.5:** Review the locally tested code, inspect compatibility with the GitHub research matcher, and integrate into one authoritative implementation when explicitly authorised. Avoid another disconnected v0.6 merely for organisation.
2. **One fast quality command:** Add minimal reproducible Python formatting/lint and existing unit/SQL/API regression checks, within practical dependency constraints. Avoid a project-wide rewrite.
3. **Review HTTP complexity:** Evaluate whether the current minimal HTTP implementation or a thin FastAPI adapter is simpler **based on actual maintenance and contract behaviour**. This is a technical decision, not automatic permission to install or migrate.
4. **Real browser journey:** Verify investigate, show evidence and warnings, save and reopen; retain the existing blocked-browser finding until a permitted browser succeeds.
5. **Deliver buyer value:** Resolve PIN versus trusted address discovery, then save/compare multiple properties and prepare the release gates.

**Always pending until independently verified:** Data rights and public display authorisation; historical source publication timing; chronological valuation evaluation; final consumer lookup contract; public deployment requirements.

**Baseline at adoption:** GitHub `main` at commit `708239eb2451e379981767136186ab5010057fed`, with 42 published offline tests; isolated P3 v0.5 reported 83 local fixture/HTTP tests. Delivery P3 remained **10% estimated** and overall MVP **22.8% estimated**. These historical figures are **not** permanent targets and must be rechecked every session. Document adoption does not itself earn phase credit.
