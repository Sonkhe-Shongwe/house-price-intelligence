# House Price Intelligence: current checkpoint

**Verified development snapshot:** 23 November 2026, commit [`5e0a7f3`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/5e0a7f382c13d82b8640f63f18b5d981ff967e99). [Development push CI 45208709369](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45208709369) and [draft PR CI 45208727239](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45208727239) both passed: **148 Python tests, 7 hosted Chromium browser tests**, JavaScript syntax and documentation checks. Always verify current branch HEAD and its CI rather than treating this dated record as a live indicator.

**Repository:** [Sonkhe-Shongwe/house-price-intelligence](https://github.com/Sonkhe-Shongwe/house-price-intelligence). Permanent working branch: `development`. Stable `main`: [`103c854`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/103c854eae36a0a0fa81bb007b71ebadc52179d6), [main CI 45184193870](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45184193870) passed. [PR #4](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/4) is **draft and not merged**. Changes to `development` do not imply a release or owner acceptance.

**Official planning baseline:** **P3 10%**, **weighted P0–P8 MVP 22.8%**; P3 exit gate **open**. The detailed [80-package P0–P8 plan](P_PHASE_ROADMAP.md) tracks research, verified synthetic implementation, incomplete work and blocked approvals separately. No percentage increase for commits, CI or documentation cleanup alone.

## Current verified implementation on development

- **Research:** Cook County township 17, Class 203 remains an experimental *research pilot*, not the approved public first market. Bounded Phase 0–2 audits and the explainable neighbourhood-first matcher are tested; exploratory 2 km fallback had worse retrospective price error than the township baseline on its 17 tested cases. No independently validated current-home prediction, historical as-of guarantee or real-property display rights.
- **API + browser:** Loopback-only Python WSGI, plain HTML/CSS/JavaScript and invented SQLite fixtures. `POST /v1/addresses/search` returns distinct parcel candidate IDs even when two fictional parcels have the same invented street address. Explicit `GET /v1/addresses/{address_id}` selection resolves one synthetic parcel. A buyer may alternatively use an internal synthetic PIN. Browser validates and renders the resulting source-backed fictional sales, warnings and zero-evidence states; no numeric valuation.
- **Identity:** `POST /v1/investigations` accepts a bounded `subject.address_id`. SQLite, not the browser, binds it to the selected parcel; an unknown or conflicting PIN/ID returns HTTP 422 without saving an invented investigation. A chosen address is `parcel_only` and `building_identity_verified=false`. Saved results refuse reopening if that candidate's parcel mapping changes.
- **Money and evidence:** Synthetic HTTP contract `p3-draft-v0.3` returns sale prices as canonical fixed-two-decimal `sale_price_usd` **strings derived from integer cents**, not JSON float sale-price fields. The user-entered asking price is distinct from completed sales. Saved comparables track original sale cents, source snapshot/role, transaction, identity and response hash. The research matcher retains its historical numerical adapter for its separate tests.
- **Schema:** Frozen fixture-only `schema_draft.sql` v1 has 16 domain/fixture tables. v2 adds query indexes; v3 adds `synthetic_address_candidates` (17th domain/fixture table), allowing multiple parcels per invented address and aliases per parcel. `schema_migrations` is a separate control table (18 total at v3). Controlled migration checksums, foreign keys, rollback and saved-investigation survival are tested. The server uses in-memory SQLite; saved investigations **do not survive a restart**.
- **Not implemented/accepted:** durable database, account access, approved real-data curated import and address resolver, property-level publisher display, final visual UX/accessibility acceptance, persistent buyer shortlist/notes/comparison, operational monitoring, public deployment or ML price prediction.

## Evidence versus acceptance

| Evidence level | Established | Not established |
| --- | --- | --- |
| Original research | Dated Phase 0–2 source counts, exclusions, retrospective matching and caveats | Stable repeated extracts, complete as-of history, rights for public per-property display |
| `main` integration | PR #3 frozen comparable sale-price/snapshot guard; original fixture-only app | Later address candidates, v3 migrations and v0.3 HTTP contract on `main` |
| `development` tested candidate | 148 Python + 7 real browser scenarios on `5e0a7f3`, documented P3 ERD and 80 package matrix | P3 owner acceptance, production identity/database/security, P4–P8 release gates |
| Earlier Windows work | Dated owner demonstrations and independent review patches, separate from GitHub | Uninspected local Windows working tree, automatic inclusion of every old local change |

The earlier 127-Python/15-browser Windows checkout is a **historical isolated candidate**. Do not call all of that patch merged. The relevant frozen-sale guard was independently integrated in PR #3; other unverified local changes are **not** assumed present.

## Priority decisions and execution

1. **P3 acceptance review, P3.1–P3.11:** Review the [current proposed domain model and synthetic HTTP contract](engineering/P3_APPLICATION_CONTRACT.md), explicit ambiguity/identity, money and source evidence, schema/migration boundaries, threat/privacy and buyer UX. Record each item as *accepted for synthetic scope*, *accepted for production*, *deferred* or *rejected* in [DECISIONS.md](DECISIONS.md). A fixture API is not proof of real public identity.
2. **P0–P2 research risks in parallel:** Choose the first supported geography/class and verify source rights, permissible fields, historical availability, comparable eligibility and later independent evaluation. If these block real public display, consider a separately approved, conspicuously fictional-only portfolio demo.
3. **P4/P5 connected slices on `development`:** Agree a durable storage and safe import model; extend complete browser → API → SQL journeys with negative cases and acceptance. The source code may progress in parallel, but each phase has its own sign-off.
4. **P6 distinctive buyer value:** Durable two-to-three-property shortlist with editable notes, side-by-side evidence and consistent reopening. P7 security/readiness and P8 deployment remain separate gates.
5. **Release control:** Continue using the one `development` branch, CI on each relevant push and the single draft integration PR. Do not merge to `main` or deploy without explicit owner review and approval.

**Commands from repository root:** `python tools/dev_check.py` and `python -m backend.run_synthetic_api --fixture-only --port 8765`. This is a local fixture-only demonstration. No `tools/bootstrap.ps1`, `tools/check.ps1` or `tools/run.ps1` scripts are currently established.

**Windows state:** The repository's GitHub connection cannot see an uninspected Windows checkout or uncommitted files. Never overwrite, delete or force-reset those files.

**Source-of-truth rule:** This checkpoint is the *current-state* document, [P_PHASE_ROADMAP.md](P_PHASE_ROADMAP.md) defines work packages, phase weights and gates, [DECISIONS.md](DECISIONS.md) records owner decisions, and dated research/review reports retain their historical findings. Future updates replace obsolete checkpoint status here rather than appending another conflicting current-status section.
