# Product brief: House Price Intelligence

**Source:** The pre-existing Project 2 brief in `Sonkhe-Shongwe/sa-tech-grad-playbook.` at `docs/portfolio/house-price-intelligence.md` (reviewed 22 November 2026). This is a standalone adapted copy retaining the prior requirements and unresolved decisions. The original source remains intact.

**Owner decision (24 November 2026):** pursue the original full real-property release. Evanston Township/Class 203 is the measured research reference; geography-flexible, data-first market selection applies; final market/class not accepted. Fictional fixtures remain development/test data; no production display or deployment approved. See [FR1–FR3](../engineering/FULL_RELEASE_QUALIFICATION_V1.md).

## Problem and buyer

A prospective homebuyer has shortlisted houses whose asking prices are visible, but needs evidence of recorded completed sales, relevant physical characteristics, differences among candidate homes and the limits of available information. The product should help a buyer understand which recently sold properties offer a defensible comparison and why.

**First buyer:** One individual inspecting two or three homes in one demonstrably supported local market and property class. A user may manually enter an asking price and supported property attributes. The system must not claim to provide live listing discovery, verified listing images or a current market feed until independently integrated and validated.

**P0-A.8 strategic synthesis (26 November):** [Vision and positioning](PINNACLE_VISION.md#p0-a8--product-vision-and-positioning-synthesis-26-november-2026) proposes the residential property decision intelligence identity and preserves Investigate / Compare / Decide, the narrow flagship and separate future pinnacle. Internal strategic language accepted by owner on 26 November, subject to documented limitations; the existing scope and acceptance checklist below are unchanged. Historical evidence must not be represented as current market coverage or a current valuation.

## Proposed end-to-end user journey

1. **Add property:** Enter user-reported asking price, location, property type and supported features. Explain the covered market, data date and class restrictions.
2. **Inspect comparable sales:** Show eligible prior completed sales, transaction prices and dates, matched attributes, why each was selected and material differences.
3. **Shortlist:** Save two or three properties with notes, reopen the shortlist and compare the evidence side by side.
4. **Handle weak evidence:** If out of coverage or insufficiently supported, explicitly report *Insufficient data*, showing what was missing or excluded. Preserve the user's entry.
5. **Estimate only if justified:** Include predicted selling price and a tested prediction interval only if an earlier-held-out evaluation supports it. The interval is not the raw spread of observed comparables.

## Core properties of the data model

- **Sales transaction** is not the same entity as **parcel** or **building**. A recorded transaction may involve multiple parcels; a parcel may contain multiple buildings.
- Match historical characteristics to each specific sale at its valid point in time. A simple prior-tax-year join is only a pilot proxy, not a proof of source availability at the sale date.
- Comparable rules may consider area, property class, building size, recency and reliable distance; each expansion of the matching criteria must be visible and testable.
- Store source ID, source snapshot or source version, matching rules and analysis date to make saved comparisons reproducible.
- Preserve user-entered listing/asking-price observations separately from publisher-sourced completed sale facts and model estimates.
- Do not imply precision when sale evidence is too thin, inconsistent or outside the supported geography.

## Flagship acceptance criteria (synthetic features partly implemented; final acceptance open)

**Implementation note (23 Nov 2026):** `development` already demonstrates two-to-three-property fictional shortlists, editable notes, frozen source-linked comparables, insufficient evidence and restart recovery via opt-in fixture SQLite (PRs #5/#6). **The unchecked criteria below are still product/owner acceptance gates**, not claims that none of the related code exists. Approved market data rights, real property identity, visual UX and public release remain unresolved. See [P0–P8 roadmap](../P_PHASE_ROADMAP.md) and [P6 contract](../engineering/P6_SYNTHETIC_SHORTLIST_CONTRACT.md).

- [ ] Audited geography, property class, record count, join quality, comparable coverage and permitted display fields.
- [ ] User can add and save two properties, view side-by-side comparisons and reopen them.
- [ ] Every comparable links to an eligible sale before the analysis date and explains its selection.
- [ ] Insufficient-data behaviour is correct and visible.
- [ ] Tests cover future sales, excluded transactions, unsupported homes and stale/inconsistent snapshots.
- [ ] If prediction ships, compare with a comparable-sales baseline on a chronological holdout; report accuracy and interval coverage and width.

**P0-A.9 measurement proposal (26 November):** [Product principles and success definition](PRODUCT_PRINCIPLES_AND_SUCCESS_2026-11-26.md) defines proposed buyer-task measures and validation, distinct from the existing mandatory acceptance checklist above. Provisional validation plan accepted at A.10, with final study design and permission still required; no customer results or change to existing phase gates.

**P0-A.10 foundation review (26 November):** [Review and consolidated owner decision](../reviews/P0_A_PRODUCT_FOUNDATION_REVIEW_2026-11-26.md) reconciles the nine research tasks with existing intent and gates. Review complete, foundation direction explicitly accepted 26 November; no change to the original flagship checklist or approved scope.

## Scope boundaries

**No v1 commitment:** Multi-market listing search, professional appraisal accuracy, live property photographs, mortgages, AI assistant, property alerts, investor portfolio management or a global valuation model.

**Recruitment walkthrough:** Reopen two previously saved homes, inspect a traced comparable and its matching rule, show an unsupported property, then explain a database join, exclusion rule and test failure that the system prevents.

## 26 November 2026 | P0-F definitive MVP requirements and conditional scope

**Status:** canonical consolidation of the previously accepted product foundation and subsequent conditional discovery findings, ready for independent P0-G review; not final market, real-data, hosting, release or P0 acceptance. This addendum supersedes stale candidate-market framing above only as to research priority, not prior approvals or original six flagship acceptance items. No new product scope. Evidence restored at [943bdf2](https://github.com/Sonkhe-Shongwe/house-price-intelligence/commit/943bdf27a8f388d6b53f62da43c6a5e46b92b05b), seven of seven exact-head workflows passed: [audit push](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45844583087), [audit PR](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45844593304), [identity](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45844593328), [compatibility](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45844593316), [runtime](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45844593319), [React](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45844593555), [release checks](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45844593289). Prior application evidence is distinct from this documentation CI. No external data, new research participant, Windows inspection, provider operation or application test performed in this slice.

### 1. Product identity and outcome

House Price Intelligence is a residential property decision intelligence workspace for an individual prospective owner-occupier comparing two or three already shortlisted homes in one demonstrably supported market and property class. The job is to understand relevant earlier completed sales, material differences and evidence limitations before deciding the next action, including pausing or seeking appropriate professional advice. **Investigate / Compare / Decide** remains the accepted identity and workflow. Discovery occurs outside HPI; no marketplace, agent replacement, ranking of homes by investment attractiveness or recommended purchase/offer. HPI-01 and unfamiliar-market HPI-02 are overlapping provisional behavioural personas, not observed demographic segments. The perceived fragmentation/interpretation burden, willingness to adopt and incremental benefit over existing agents/portals/manual comparison are hypotheses, not demonstrated market fit.

Authority: [A.10 owner acceptance](../reviews/P0_A_PRODUCT_FOUNDATION_REVIEW_2026-11-26.md#8-formal-acceptance-26-november-2026-1356-sast), [JTBD](JOBS_TO_BE_DONE_2026-11-26.md), [value proposition](VALUE_PROPOSITION_2026-11-26.md), [competitive intelligence](COMPETITIVE_INTELLIGENCE_2026-11-26.md), [P0 directive](../engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md), [roadmap](../P_PHASE_ROADMAP.md) and [decisions](../DECISIONS.md).

### 2. Supported-market contract: explicit conditional boundary

| Scope | Required evidence and limits | Status |
| --- | --- | --- |
| Intended MVP | Exactly one qualified local market and eligible dwelling class, authorised subject entry including unsold homes, decision-relevant freshness, suitable recorded-sale population, lawful permitted display and durable storage. | Final geography/class/entry not accepted. |
| Cook County measured reference | Township 17 (Evanston Township, not city), Class 203 one-storey residence, 1,000-1,800 assessed sqft, 2024-2025 sales, applicable prior 2023-2024 assessment years. Distinct earlier events, 365 days, +/-25% area, 3-5 other properties; same neighbourhood or explicitly exploratory 2 km fallback. 142 eligible events, 59 later sold subjects, 41 neighbourhood/18 exploratory. | Retrospective measured cohort, selected sold-property entry only; not as-of availability, current unsold coverage, permanent market or approved valuation. Four source licences unspecified; rights and protection unresolved. |
| Alternatives | NYC priority challenger; England/Wales secondary lead; assess exact grain, historical availability, entry, rights and R0 if needed. | Documentary leads only; no automatic fallback, migration or additional data collection. |

Use [P0-C conditional review](../research/DATA_FEASIBILITY.md#26-november-2026--p0-c-supported-property-boundary-and-conditional-feasibility-review). The market-independent product contract below is determinate; market-specific numerical thresholds, semantics, currency, temporal rules, permissions and current-entry evidence are not. No substitution of fictional scope, stale cohort or aggregate-only report for the owner-selected real-property product without separate approval. If current buyer coverage cannot be supplied, abstain and reassess viability rather than relabel old evidence as current.

### 3. Mandatory functional requirements and traceability

IDs F1-F8 are trace references to existing flagship requirements and G1-G7 guardrails, not new P0 acceptance criteria, weights or features. JT/VP/M identifiers retain their meanings in the accepted foundation. Technical verification must use the applicable mode; fixtures are not evidence of real-data usability.

| ID / job and value | Required behaviour and binding rule | Observable acceptance / downstream owner |
| --- | --- | --- |
| F1 / JT1 VP1 M1: enter and identify | Show supported coverage/class/data date; accept separately labelled buyer-reported asking price and supported attributes, select a unique authorised subject. Never guess ambiguous identity, accept caller-selected source/build or conflate parcel, dwelling, sale. | Known unique, missing, ambiguous, conflicting and unsupported cases produce correct selection/refusal; conflicting invalid requests create no investigation; well-formed unsupported enquiries preserve entry. Independently audit unsold entry and coverage. P0.3/4/6, P1/P3/P4/P5, G1. |
| F2 / JT2 VP2 M2: investigate | Retrieve 3-5 distinct eligible earlier properties when approved policy allows; separate transaction and property identities, exact recorded consideration and buyer price, no future/same-day or subject sale, no multi-property price allocation, no duplicate property, rank independent of price. Apply compatible dated area/geography and source-specific eligibility. | Every displayed comparable traces internally to eligible event, source/build/rule/date, exact currency and attributes; exercise duplicate, future, excluded, conflicting, price-perturbed and wrong-version negatives. No assumed publication-time availability. P1/P2/P3/P4/P5, G1/G2. |
| F3 / JT2/JT3 VP2/VP3 M2/M3: explain | Show permitted completed-sale price/date, matching reason, material differences and caveats, provenance and analysis date. Use only applicable approved projection; no raw comparable identifiers/addresses/geometry or unsupported claims. | Verify response/UI parity against source evidence and field allowlist; buyer can distinguish recorded consideration, asking price and evidence age; unsafe disclosure withheld. P0.5, P2/P4/P5/P7, G2/G3/G5. |
| F4 / JT3 VP3 M3: abstain | Distinguish supported_neighbourhood, exploratory_spatial, insufficient_data and out_of_coverage according to qualified source/rules. Exploratory only if independently justified and approved; missing or ambiguous evidence never fabricated, absent price not zero, valuation null. | Test each applicable status, absent/weak/future/stale/conflicting source, map failure and unsupported entry; no false evidence or forced positive support. If a market cannot support spatial mode, do not invent it. P2/P3/P4/P5/P7, G3/G7. |
| F5 / JT5 VP5 M5: save and reopen | Save distinct investigations and buyer-scoped notes; freeze source version, matching rules, dates and evidence. Reopen the original, never silently refresh or rewrite; authorised source correction/revocation/expiry restricts access. | Save two distinct homes (including insufficient), restart/reopen authorised view and confirm evidence and note parity; deny tamper, cross-owner, expired and unapproved projection. P4/P6/P7, G4/G5. |
| F6 / JT4 VP4 M4: compare | Align two or three distinct homes side by side with comparable evidence, user asking prices, material differences, date/tier/limitations and editable notes; remove membership without silently deleting investigation. No forced winner. | Supported and unsupported pair visible together; three-home limit, duplicate refusal, note edit/remove and original evidence integrity. P5/P6/P7, G3/G4. |
| F7 / JT6 VP6 M6: decide | Present what evidence does and does not establish, allow an appropriate next action, revisit or seek professional advice; no prescriptive offer or financial/appraisal claim. | In applicable task scenario buyer identifies a justified next action and remaining uncertainty without critical misconception; abstention can be success. P5/P6/P7/P8, G3/G6/G7. |
| F8 / returning journey and recruiter access | Owner-only private real mode first, conditional on rights/protection; separate authorised demo access. Browser-only final release through one approved HTTPS URL, integrated sign-in, full journey, persisted reopen, sign-out, no shell/certificate/database setup by buyer or recruiter. | Fresh browser, permitted data, least privilege, isolation, persistence, correct failure recovery, sign-out and release review; no fixture adapter exposed publicly. P0.7/P3/P7/P8, G4/G5/G6. |

The underlying [P3 contract](../engineering/P3_APPLICATION_CONTRACT.md), [P6 shortlist contract](../engineering/P6_SYNTHETIC_SHORTLIST_CONTRACT.md) and [engineering contract](../engineering/ENGINEERING_CONTRACT.md) remain implementation references. Integrated fictional HTTP/SQL/React, actual invented provider journey and encrypted invented restore are substantial existing evidence, not new feature work. User input units and status names in any future local API change must be explicitly reconciled, not silently reused.

### 4. Non-functional requirements and test obligations

| Requirement | Acceptance boundary / accountable workstream |
| --- | --- |
| Correctness and reproducibility | G1-G4/G7 mandatory on every applicable audited/tested case; canonical exact-cent transactions, source grain, immutable versioned evidence, deterministic selection and exclusions; fail closed on invalid build or privilege drift. P1-P4/P6/P7. |
| Rights, privacy and security | G5; field/operation-specific permission, lawful purpose/roles, access inventory, permitted projection, no raw data in public Git/CI, least privilege, HTTPS and secure server-side session/CSRF/revocation, protected independent recovery. No real mode before applicable approvals. P0.5/P3/P4/P7. |
| Lifecycle | Owner-approved maximum 30 calendar days from earliest authorised intake, shorter terms/law prevail, no automatic deletion/renewal, no clock reset on restore; demonstrate source/derived/copy inventory, restriction/expiry across save/reopen/export/restore, incident/correction and authorised disposal including residual history. Existing read-only retention impact review not runtime enforcement. P0.5/P0.7/P4/P6/P7. |
| Availability and resource feasibility | Strict R0, one canonical development repository, existing stack retained conditionally; credible browser-only hosted route with durable session state, measured cold/warm start, request/connection limits, provider usage and fail-stop on quota/outage. Render/Vercel only candidates; no paid allowance or new infrastructure authorised. P0.4/7/P3/P7/P8. |
| Usability and accessibility | G6; keyboard and responsive core journey, explicit loading/empty/error/unsupported and recovery, readable caveats, equivalent non-map evidence. Existing 14-view automated accessibility result not full manual or hosted acceptance. P5/P7/P8. |
| Maintainability and verification | Lean modular monolith, versioned domain contracts, focused regression tests and exact-head CI, no duplicate application or speculative AI; Windows essential for owner/platform acceptance where applicable. P3-P8. |

See [D.3 rights/protection verdict](../engineering/PRIVATE_REAL_DATA_BETA_V1.md#26-november-2026--p0-d3-conditional-legal-and-privacy-feasibility-review), [P0-E feasibility](../engineering/PRODUCTION_READINESS_V1.md#26-november-2026--p0-e-conditional-technical-financial-and-operational-feasibility) and [release runbook](../engineering/RELEASE_RUNBOOK_V1.md). Do not introduce invented latency, availability, coverage, load or budget guarantees. Operational targets require actual relevant measurement and applicable review. No stack, policy or acceptance thresholds changed here.

### 5. Scope priorities and measurable success

- **Must:** F1-F8 and applicable G1-G7; original six flagship checklist items remain. Conditional estimation acceptance applies if later approved, not a feature required for evidence-only MVP.
- **Should, when useful and permitted:** retain existing linked map/Atlas and contextual renderer, accessible non-map evidence always available. Real basemap/geometry and export require their own source and disclosure approval, not a prerequisite added by this specification. Existing optional one-click fictional local fallback or recorded demo cannot satisfy browser-only release or replace real MVP.
- **Could / later proposal only:** additional markets, broader pinnacle features or prediction once original separate gates and a justified scope decision permit. No new feature commitments.
- **Won't in current flagship:** listing search/current feed, professional valuation/appraisal, prescribed offer, unverified price predictions/intervals, mortgages, photos, notifications, collaboration, investor portfolios, AI assistant, nationwide coverage, public raw-source download or unrestricted comparable API. Commercial licensing/demand not assumed.

North Star: evidence-informed decision task success. Reuse [M1-M8 and G1-G7](PRODUCT_PRINCIPLES_AND_SUCCESS_2026-11-26.md), not a second metric ledger. M1-M6 correspond to identity, price/evidence, limitation, comparison, continuity and next-action tasks; M7 composite; M8 paired comparison with existing workflow. Prior A.10 approval covers provisional 80% unassisted formative targets, zero observed critical misconceptions and proposed 6-8 participants, not achieved outcomes, recruitment authority or production thresholds. Use the existing denominator, failure and M8 complete-pair clarification (design proposal) at later applicable study approval; critical error or technical/data breach blocks affected claim. Existing evidence levels remain separate: technical fixture/provider qualification, customer value, real source/operational readiness. No participant data or market-fit result exists.

### 6. Material risks, responsibility and P0-G handoff

| Risk | Responsible evidence / decision | Fail-closed outcome |
| --- | --- | --- |
| Local source inaccessible, fee or incomplete event history | SA clarification, exact source grant/dictionary, SA4 bounded empirical evidence only after approval; owner selects final market/class after qualification | Keep SA preferred but blocked; no paid acquisition or automatic international fallback. |
| Unsupported current identity or stale evidence | P0.4 independent current unsold frame, freshness and applicable attribute/time evidence; P1/P2 quality and selection audits | Abstain, no current-market claims; revisit product feasibility. |
| Source restriction, linkage or statutory processing | P0.5/D actual permission/lawful processing/roles/transfer and output review; owner/custodian/legal authority as applicable | No intake, durable evidence, display or publication. |
| Unqualified real protection, storage, quota or recovery | D/E and P3/P4/P7 operational evidence; owner approval for material protection/service changes; preserve rekey deferral | No real-data operation or deployment; no paid workaround. |
| Demand or comparative advantage not demonstrated | P0-A/B evidence and later authorised M1-M8 study, customer/owner review | Treat as hypothesis; narrow/reconsider if disconfirmed, no unsupported superiority claim. |
| Scope/phase drift | P0-G independent review of all seven original criteria, applicable explicit owner decisions, separate P1-P8 exit gates | No P0 closure, P1 advance, new code, source collection, public deployment or main integration implied. |

**P0-F bounded specification consolidation delivered.** The accepted common buyer journey and safeguards have been made testable and traceable; final supported market, source rights, actual protection and real release path remain material blockers. No new owner decision or formal specification/phase acceptance inferred. Next P0-G independent **conditional audit** against original P0.1-P0.7, consolidate required decisions and evidence; stop at unresolved indispensable blockers rather than approve the real-property MVP or start P1. Applicable owner decisions and approvals remain required for full F/G acceptance; prior accepted foundation is not reopened. P0 94%, weighted MVP 87.1%, R0, all full gates open. No inbox check, contact, acquisition, code/schema, provider operation, new spending, deployment or main merge. No score change.

## Retired scope proposals and research

The contextual-only pivot was not adopted and is no longer an active product option. [Full historical product brief](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md) preserves its evaluation and experimental findings. The comparable-sales product and original requirements remain governing.

## 26 November 2026 | Direction B proposed contextual decision workspace (not adopted)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#26-november-2026--direction-b-proposed-contextual-decision-workspace-not-adopted). Not active instructions.

### B.1 Problem, alternatives and decision

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#b1-problem-alternatives-and-decision). Not active instructions.

### B.2 Proposed minimum viable contextual slice

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#b2-proposed-minimum-viable-contextual-slice). Not active instructions.

### B.3 Engineering and delivery decision

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#b3-engineering-and-delivery-decision). Not active instructions.

## 26 November 2026 | Direction B contextual evidence review and prototype decision

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#26-november-2026--direction-b-contextual-evidence-review-and-prototype-decision). Not active instructions.

### Evidence fitness and interpretation

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#evidence-fitness-and-interpretation). Not active instructions.

### Scenario review (authored hypothetical buyer cases, not participants or completed usability tests)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#scenario-review-authored-hypothetical-buyer-cases-not-participants-or-completed-usability-tests). Not active instructions.

### Proposed refinement to B requirements (not adopted)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#proposed-refinement-to-b-requirements-not-adopted). Not active instructions.

### Next decision: narrow private proof or stop

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#next-decision-narrow-private-proof-or-stop). Not active instructions.

### Approved bounded proof implementation (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#approved-bounded-proof-implementation-26-november-2026). Not active instructions.

### Actual contextual proof outcome and next research question (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#actual-contextual-proof-outcome-and-next-research-question-26-november-2026). Not active instructions.

### Finer-context research outcome (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#finer-context-research-outcome-26-november-2026). Not active instructions.

### Finer-context access decision (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#finer-context-access-decision-26-november-2026). Not active instructions.

### 27 November 2026 | Core comparable-sales feasibility update

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/product/PRODUCT_BRIEF.md#27-november-2026--core-comparable-sales-feasibility-update). Not active instructions.
