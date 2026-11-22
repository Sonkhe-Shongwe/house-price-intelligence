# Decisions and open questions

**Reviewed:** 22 November 2026. **Authority:** Active product choices and documented user direction; research observations alone do not approve public product claims.

## Confirmed direction

| Topic | Current decision | Evidence or boundary |
| --- | --- | --- |
| Product | Build House Price Intelligence as a property investigation and shortlist application | [Product brief](product/PRODUCT_BRIEF.md) |
| Method | Product-first, verifiable foundations before advanced prediction | [Engineering contract](engineering/ENGINEERING_CONTRACT.md) |
| Delivery control | Adopt a House Price Intelligence-specific P0–P8 complexity-last framework | [P-stage roadmap](P_PHASE_ROADMAP.md); 22.8% subjective baseline |
| Research geography | Use Cook County township 17 / Evanston as the **research pilot** | Phase 0–2 verified cloud runs; not approval of permanent market |
| Research segment | Investigate assessor Class 203, a one-story residence category | 273 historical matched sale records; individual building form/condition not verified |
| Data strategy | Preserve transaction, parcel, building and assessment-year grain separately; reject inappropriate joins | [Phase 0 findings](research/PHASE0_LIVE_AUDIT_RESULTS.md) |
| Comparison policy | Test neighbourhood-first with bounded spatial fallback, distinct PINs and abstention | [Phase 2 findings](research/PHASE2_CLOUD_AUDIT_RESULTS.md); **exploratory only** |
| Processing | Use GitHub Actions for source research audits and publish **aggregate-only** report artifacts | [Automated audit](AUTOMATED_DATA_AUDIT.md) |
| Security | No raw property extracts, seller/buyer names, secrets or user records in public repository | [Data policy](../data/README.md) |
| Boundaries | Do not claim current price prediction, live listings or app deployment | No such accepted implementation exists |
| Repository | Keep this codebase separate from the [SA Tech Graduate Playbook](https://github.com/Sonkhe-Shongwe/sa-tech-grad-playbook.) | Original graduate research untouched |

## Open decisions, with next acceptance point

| Question | Needed evidence or approval | Gate |
| --- | --- | --- |
| Will Evanston/Class 203 be the final MVP boundary? | Buyer use case, coverage, field rights and explicit scope decision | P0/P3 |
| Which property-level fields may be publicly stored/displayed? | Dataset-specific licence, attribution, privacy and redistribution review | P0/P7 |
| What counts as a defensible completed sale? | Filter definitions, parcel/document grain and representative exclusions | P1/P2 |
| How do we guarantee evidence available as of analysis date? | Historical snapshots or an explicitly honest policy; later holdout validation | P1/P2 |
| Should exploratory 2 km fallback be included in UI? | Evidence-only warning design and independent testing; current price errors are poor | P2/P3 |
| Which subject inputs, geographic entry and map behaviour? | First supported buyer workflow and inputs realistically available in source | P3 |
| Backend framework, database, frontend and hosting? | Reviewed P3 contract and deployment constraints; no precommitment | P3 |
| How are saved investigations versioned and accessed? | Identity/security, snapshot and persistence design | P3/P6 |
| Can price prediction be shipped? | Untouched chronological holdout, acceptable baseline comparisons, uncertainty | Post-MVP, conditional |
| Should repository remain public? | Repository risk review and owner choice; currently reported public | P7 |

## Non-negotiable interpretation rules

- Historical audit "Phase 0/1/2" is **not** equivalent to delivery "P0/P1/P2".
- A prior tax year is **not proof** that a building record was available at that sale date.
- A township or Class 203 match is **not proof** of a detached-house sale or arm's-length transaction.
- An asking price entered by a buyer is not a verified sale/listing; recorded sale prices are not model predictions.
- A 2 km match is explanatory **candidate evidence**, not a validated valuation.
- Missing evidence requires an explicit abstention/unsupported status; never fabricate results or silently switch data sources.
