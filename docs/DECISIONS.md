# Decisions and open questions

**Reviewed:** 23 November 2026. **Authority:** Active product choices and documented user direction; research observations alone do not approve public product claims.

## Confirmed direction

| Topic | Current decision | Evidence or boundary |
| --- | --- | --- |
| Product | Build House Price Intelligence as a property investigation and shortlist application | [Product brief](product/PRODUCT_BRIEF.md) |
| Method | Product-first, verifiable foundations before advanced prediction | [Engineering contract](engineering/ENGINEERING_CONTRACT.md) |
| Delivery control | Retain House Price Intelligence P0-P8 stages, weights and gates | [P-stage roadmap](P_PHASE_ROADMAP.md); 22.8% subjective baseline |
| Engineering process (approved 23 Nov) | Eight-step requirements/architecture/risk/implementation/tests/integration/review/handoff; safe migrations and explicit evidence levels | [Lean engineering directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md); process approval, not feature/stack approval |
| Development station (approved 23 Nov; refined 23 Nov) | **One ongoing `development` working branch** for connected P3–P6 feature work, **stable `main`** for reviewed and owner-accepted milestones; GitHub Actions on development pushes and integration PRs; local Windows pulls only for indispensable owner/platform acceptance | [Cloud-first workflow](engineering/CLOUD_FIRST_WORKFLOW.md). Additional branches only for exceptional needs. Avoid squash/force rewrites of permanent branch; no blanket permission to merge or deploy |
| Delivery evidence (23 Nov) | Original owner manual fixture journey, now followed by real hosted synthetic browser and API tests on `development` | [Current checkpoint](CHECKPOINT.md) identifies the latest verified run; earlier 125-test main and isolated 127-test Windows results are historical snapshots, not the active CI counts |
| Development sequencing (approved 23 Nov) | P4 backend and P5 browser implementation can overlap after P3 acceptance via complete vertical slices; each phase retains its own exit gate and progress | [P-stage roadmap](P_PHASE_ROADMAP.md) |
| Market choice (23 Nov) | **Data-first, geography-flexible**. Do not force South African coverage if sources, identity, attributes, usage rights or reliability limit the product. Cook County township 17 / Evanston remains the **research pilot**, not final permanent coverage | Phase 0–2 research and owner direction |
| Research segment | Investigate assessor Class 203, a one-story residence category | 273 historical matched sale records; individual building form/condition not verified |
| Data strategy | Preserve transaction, parcel, building and assessment-year grain separately; reject inappropriate joins | [Phase 0 findings](research/PHASE0_LIVE_AUDIT_RESULTS.md) |
| Comparison policy | Test neighbourhood-first with bounded spatial fallback, distinct PINs and abstention | [Phase 2 findings](research/PHASE2_CLOUD_AUDIT_RESULTS.md); **exploratory only** |
| Processing | Use GitHub Actions for source research audits and publish **aggregate-only** report artifacts | [Automated audit](AUTOMATED_DATA_AUDIT.md) |
| Security | No raw property extracts, seller/buyer names, secrets or user records in public repository | [Data policy](../data/README.md) |
| Boundaries | Do not claim current price prediction, live listings or app deployment | No such accepted implementation exists |
| UX design authority (23 Nov) | Current teal interface is provisional; owner liked the **workspace-first low-fidelity study** for exploration, not as final branding/navigation approval | [23 Nov UX research](design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md) |
| Independent product (23 Nov) | Investigate / Compare / Decide, not a Property24 clone or listings marketplace; external platforms are UX inspiration only | [Product brief](product/PRODUCT_BRIEF.md) and [pinnacle vision](product/PINNACLE_VISION.md) |
| Map direction (23 Nov) | Explore a map-linked evidence view with reliable coordinates and a synced evidence table; **not implemented, provider-approved or required MVP scope yet** | [Continuity audit](reviews/CONTINUITY_AND_DIRECTIVE_AUDIT_2026-11-23.md) |
| Directive (confirmed 23 Nov) | Retain existing eight-step lean lifecycle unchanged; apply UX sign-off and geospatial/source integrity within it | [Lean directive](engineering/LEAN_ENGINEERING_DIRECTIVE.md) |
| Repository | Keep this codebase separate from the [SA Tech Graduate Playbook](https://github.com/Sonkhe-Shongwe/sa-tech-grad-playbook.) | Original graduate research untouched |

## Current development candidate (not accepted on `main`)

**Latest verified position (23 Nov):** [`development` at `5e0a7f3`](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/5e0a7f382c13d82b8640f63f18b5d981ff967e99), [green PR CI 45208727239](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45208727239): **148 Python and 7 hosted Chromium** cases. The synthetic v3 parcel-candidate index supports multiple parcels per invented street label and candidate aliases, keeps an explicit parcel-only/building-unverified scope and refuses changed saved identity. The v0.3 money and v1–v3 migration candidates remain fixture-only. **These are verified implementations, not owner approvals** for real address mapping, source rights, production storage, final UX or release. PR #4 remains draft; P3 10% and weighted MVP 22.8% unchanged.

## Historical implementation milestones (dated development changes, not current acceptance)

- **23 November 2026, `development` `07f637b`:** Four invented address rows were added to the P3 disposable SQLite demo, with a bounded search endpoint, explicit candidate selection and existing synthetic comparable investigation/reopen. CI [45193537292](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45193537292) passed 132 Python and 5 hosted Chromium tests. This demonstrates an original, connected buyer interaction on the approved technology stack; it **does not settle the real address/parcel/building identity decision**, rights, historical availability, migrations, branding or production scope. Remains in the [draft development integration PR #4](https://github.com/Sonkhe-Shongwe/house-price-intelligence/pull/4), not accepted on `main`.

- **23 November 2026, `development` `79a7c4d`:** Candidate synthetic investigation contract `p3-draft-v0.3` now carries an optional fictional-address ID which the server binds to a trusted synthetic parcel, with 422 on mismatch; comparable HTTP prices are fixed-scale USD text derived from exact SQLite cents, not JSON floats. [Push CI 45196929621](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45196929621) passed 137 Python + 6 hosted Chromium cases. This **does not settle real address identity, real-data source rights, approved commercial pricing or production migrations**. Provisional until owner P3 acceptance. Still in draft PR #4.

- **23 November 2026, `development` `8ed4269`:** Candidate v1/v2 synthetic SQLite migration runner added with hash and version checks, rollback, no unversioned adoption and populated-database upgrade tests. The [P3 application contract](engineering/P3_APPLICATION_CONTRACT.md) contains the proposed domain ERD and distinct identity grains. [Push CI 45200038440](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45200038440) and [PR CI 45200054027](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45200054027) passed 144 Python and 6 Chromium tests. No production database, backup, real address identity or P3 gate acceptance has been approved.

- **23 November 2026, `development` `3793b81`:** A new v3 **fictional-only** parcel-candidate table permits two parcels to share a visible address or one parcel to have multiple aliases. Search shows separate parcel options, the server binds the exact chosen candidate, the UI labels building identity unverified, and saved investigations fail closed if the selected mapping changes. This is a testable identity-risk model, **not an approved real-source address, building or title-identity solution**. [Current P3 contract and ERD](engineering/P3_APPLICATION_CONTRACT.md). No P3 completion credit.

## Open decisions, with next acceptance point

| Question | Needed evidence or approval | Gate |
| --- | --- | --- |
| Will Evanston/Class 203 be the final MVP boundary? | Buyer use case, coverage, field rights and explicit scope decision | P0/P3 |
| Which property-level fields may be publicly stored/displayed? | Dataset-specific licence, attribution, privacy and redistribution review | P0/P7 |
| What counts as a defensible completed sale? | Filter definitions, parcel/document grain and representative exclusions | P1/P2 |
| How do we guarantee evidence available as of analysis date? | Historical snapshots or an explicitly honest policy; later holdout validation | P1/P2 |
| Should exploratory 2 km fallback be included in UI? | Evidence-only warning design and independent testing; current price errors are poor | P2/P3 |
| Which buyer entry and property identity? | Address/parcel/building resolution and real supported market; technical 14-digit PIN is not final consumer entry | P3 |
| What would a responsible map require? | Coordinate source/accuracy, provider/tile rights, attribution, restrictive CSP/referrer compatibility, keyboard/table alternative | P3/P5 |
| Backend framework, database, frontend and hosting? | Reviewed P3 contract and deployment constraints; no precommitment | P3 |
| How are saved investigations versioned and accessed? | Identity/security, snapshot and persistence design; fixture-only schema upgrade is tested, but user access is undecided | P3/P6 |
| Which production database migration, recovery and retention policy? | Synthetic SQLite migration runner and rollback are verified only for disposable fixtures; production DB, backup/restore, retention, access and historical source identity remain to be selected and approved | P3/P4/P7 |
| Can price prediction be shipped? | Untouched chronological holdout, acceptable baseline comparisons, uncertainty | Post-MVP, conditional |
| Should repository remain public? | Repository risk review and owner choice; currently reported public | P7 |
| What should the application look and feel like? | Refine promising workspace-first idea, compare visual directions, accessibility, responsive information density and buyer tasks; **no palette or final style approved** | [Exploratory UX study](design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md); P3/P5 |
| When can the 127-test patch be committed? | Review exact local/remote diff, protect untracked work, obtain bounded owner code-integration authority, commit tested guard and browser regressions, verify CI | P3 |
| Should protected-`main` required checks be enabled? | Enforced JavaScript syntax, 128 Python tests and three actual Chromium acceptance scenarios now pass on integrated `main`; owner-approved repository rules are still needed. Review stable checks and branch permission changes separately | Engineering operations / P3 |
| What exact money representation is required? | Synthetic v0.3 fixture HTTP response now uses fixed two-decimal sale-price strings derived from SQLite integer cents; confirm cross-market currency, scale, limits and versioning before approving any real-data/production contract | P3/P4 |

## Non-negotiable interpretation rules

- Historical audit "Phase 0/1/2" is **not** equivalent to delivery "P0/P1/P2".
- A prior tax year is **not proof** that a building record was available at that sale date.
- A township or Class 203 match is **not proof** of a detached-house sale or arm's-length transaction.
- An asking price entered by a buyer is not a verified sale/listing; recorded sale prices are not model predictions.
- A 2 km match is explanatory **candidate evidence**, not a validated valuation.
- Missing evidence requires an explicit abstention/unsupported status; never fabricate results or silently switch data sources.
