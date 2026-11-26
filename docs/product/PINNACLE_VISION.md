# Pinnacle vision and flagship separation

**Status:** Product exploration, not a promise of functionality by January 2027.

## Pinnacle product

House Price Intelligence could mature into an evidence-based property decision workspace answering: What is this home worth? Why? Which alternatives are stronger? What does ownership cost? Where is the evidence weak?

Potential pillars:

1. Property dossiers combining publisher-sourced historical facts, user-entered details and legitimately licensed listings.
2. Explainable comparable-sales analysis with inspectable eligibility, similarity and exclusions.
3. Time-tested price estimates and validated uncertainty, with abstention outside supported cases.
4. Neighbourhood and market intelligence using properly licensed spatial and contextual data.
5. Saved property shortlists and adjustable side-by-side scenarios.
6. Explicit financial assumptions and purchase/ownership-cost scenarios.
7. Versioned decision reports and future monitoring where ongoing source data permits it.

These capabilities are *future-state*, not part of the Phase 0 deliverable. Commercial market differentiation and user demand remain unvalidated.

## First flagship

One local market, one tested property class and one buyer workflow: manually enter a property and asking price, find and explain traceable earlier completed sales, compare a small shortlist and save/reopen the result. Include honest insufficient-data behaviour. Add ML only if data quality and chronological model evaluation meet documented acceptance thresholds.

## First implementation slice

Verify a bounded source extraction; resolve transaction/parcel/building grain and class codes; produce valid comparable examples; then create a narrow UI-to-database workflow. Do not begin by committing to a frontend or database brand.

## Product-first engineering rule

Define data coverage, record grain, user flows, reliability expectations and testable constraints first. Select API, spatial, persistence, UI and ML tools according to these measured needs. Python in Phase 0 is a disposable audit instrument, not the mandatory production stack.

## P0-A.8 | Product vision and positioning synthesis (26 November 2026)

**Status:** internal strategic direction accepted at P0-A.10 on 26 November 2026, subject to documented limitations; not a new owner-approved scope, commercial positioning, market approval, brand redesign, public release or proof of customer demand. The original pinnacle exploration above remains aspirational; its first implementation slice describes the historical approach, not today's active task. Follow the [P0 directive](../engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md) and [checkpoint](../CHECKPOINT.md).

### Purpose, vision and mission

- **Purpose:** Help buyers understand the available property evidence, including what that evidence cannot establish.
- **Vision:** A property-buying experience where people can make informed decisions supported by understandable, transparent and reliable evidence.
- **Mission:** Transform relevant property data into explainable historical evidence and meaningful comparisons that support the buyer's own judgement.
- **Product identity:** House Price Intelligence (HPI), a residential property decision intelligence workspace. Keep the established expression **Investigate. Compare. Decide.** The category descriptor and mission/vision are proposals, not a rename or approved marketing claims.

The first release is not principally a house-price prediction application. A future independently validated estimate can serve the broader decision purpose, but is not a prerequisite for the evidence-only flagship. Current valuation output remains absent.

### Positioning hypothesis

For an individual prospective owner-occupier evaluating two or three already shortlisted residential properties in a demonstrably supported local market and class, HPI is an evidence-based property decision workspace designed to organise eligible historical completed sales, explain their relevance and limitations, and preserve a consistent comparison and the buyer's own questions. It complements existing property discovery, current research and professional advice. It does not provide a current valuation, live listings or a purchase recommendation.

First-time/occasional buyers and unfamiliar-market buyers are priority research lenses, not eligibility restrictions. Experienced buyers with the same decision job remain included. The consumer problem, actual incremental value and market reach remain unvalidated. Portfolio/recruiter demonstration is a separate audience and operating scenario, not the primary customer.

| Product expression | Buyer outcome hypothesis | Existing commitment |
| --- | --- | --- |
| Investigate | Understand which property and historical evidence is relevant, and what is not known | Validated entry, permitted earlier-sale context, matching explanation, coverage and provenance; JT1-JT3 / VP1-VP3 |
| Compare | Understand meaningful differences between shortlisted alternatives, including uneven evidence | Two-to-three distinct homes, aligned comparisons, no forced winner or missing-data imputation; JT4 / VP4 |
| Decide | Prepare the buyer's own next action, questions or appropriate abstention | Personal notes and authorised frozen save/reopen; seek current/professional advice where necessary; JT5-JT6 / VP5-VP6 |

The candidate value pillars are evidence, explainability, comparability, transparency and continuity. JT7/JT8 emotional/social benefits are secondary hypotheses; no guaranteed confidence, financial savings, reduced regret or new sharing capability.

### Flagship versus pinnacle: explicit scope reconciliation

| Dimension | First flagship (existing scope; final acceptance pending) | Aspirational pinnacle (not a delivery commitment) |
| --- | --- | --- |
| Customer and market | Individual buyer, one qualified local geography and class, two or three shortlisted properties | Potential broader validated markets and use cases only after separate approval and evidence |
| Property dossier | Manual user-reported asking price and supported attributes, bounded parcel identity, permitted historical facts | Richer licensed listing/attribute/context integration and independently verified identity |
| Comparable analysis | Earlier eligible recorded sales, selection and differences, explicit insufficiency and exploratory fallback limitations | Further validated comparable methods and more comprehensive permitted data |
| Estimates | No committed numerical valuation; ML strictly conditional under existing product brief, chronological baseline and interval acceptance | Time-tested estimates with calibrated uncertainty and abstention, only if independently justified |
| Geography | Bounded evidence relevance and matching explanation; retain existing qualified fictional contextual map work | Richer properly licensed neighbourhood/market intelligence, no automatic real map-data approval |
| Decision workspace | Two-to-three-property shortlist, notes, comparison, verified reopen within authorised lifetime | Adjustable scenarios and versioned reports where justified; no automatic sharing/export or broader accounts |
| Finance and monitoring | Not committed | Explicit purchase/ownership-cost scenarios, future monitoring only with lawful timely sources |
| Release | Real-property flagship remains the owner-selected objective, with fictional fixtures for development and testing | No commercial product, pricing, acquisition, multi-market expansion or delivery date committed |

No v1 scope expansion to marketplace discovery, listing photos, real-time feeds, mortgages, agent-client systems, investor portfolios, professional appraisal, AI assistant, offers, negotiation, alerts or global valuation. Preserve the existing [product brief](PRODUCT_BRIEF.md) and all its acceptance criteria, conditional prediction clause, existing verified engineering and scope boundaries.

### Positioning alternatives and falsification

| Candidate identity | Assessment |
| --- | --- |
| House-price predictor | Reject as primary category: narrows the purpose to an unqualified estimate and risks unsupported current price claims. Conditional future prediction retained. |
| Listings marketplace | Reject for flagship: discovery is external; no licensed current inventory or validated discovery differentiation. |
| Professional valuation / investor platform | Reject for flagship: different user jobs and materially different evidence, risk and professional requirements. |
| Historical property evidence and decision workspace | Recommended provisional positioning: matches existing product scope, buyer job and evidence-first approach; incremental benefit and differentiation must be tested. |

The plausible differentiation is the combination of transparent historical evidence, comparable selection, uncertainty, and persistent personal comparison. Do not claim this combination is unique or better than agents, portals, official records or manual workflows until P0-B benchmarks actual alternatives and later evaluation supports the claim.

A.2 research supports relevance of recent-sale information (37% very useful and 41% somewhat useful in the NAR 2026 respondent sample), not unmet demand. High agent assistance and satisfaction are counterevidence; the sample is national, retrospective and successful-purchaser-selected. A.3-A.7 are derived hypotheses, not independent surveys. Historical source lag and current-source retrospective analysis limit contemporary relevance. A buyer who needs fresh data, or already has adequate understandable evidence, may gain no value from HPI. If evidence cannot support the intended decision or be lawfully and safely supplied, narrow the proposition with owner approval or record no-go; do not disguise infeasibility through branding or synthetic substitution.

### Boundaries and handoff

The existing candidate is Evanston township 17 / historical Class 203, 2024-2025 sales and 2023-2024 prior-year assessments, not an approved final market or current/as-of feed. Do not imply verified building identity, completeness, live pricing or unconditional provenance display. P0.4 property-entry, P0.5 field-use rights, P0.6 final market and P0.7 release feasibility remain open. Protected storage, narrow private projection, 30-day maximum authorised intake retention and confidential recovery boundaries remain binding; no new extraction, publisher contact, rekey, service window, provider operations, payment, deployment or main merge. Current fictional/actual invented-data technical evidence is not proof of real consumer utility. P0-A.10 review may approve the direction while explicitly leaving later workstreams' gates open; no P0 closure or P1 transition implied.

**Traceability:** [A.1 industry](RESIDENTIAL_PROPERTY_INDUSTRY_RESEARCH_2026-11-26.md), [A.2 problem research](HOMEBUYER_PROBLEM_RESEARCH_2026-11-26.md), [A.3 segmentation](CUSTOMER_SEGMENTATION_2026-11-26.md), [A.4 personas](BUYER_PERSONAS_2026-11-26.md), [A.5 journey](CUSTOMER_JOURNEY_MAP_2026-11-26.md), [A.6 jobs](JOBS_TO_BE_DONE_2026-11-26.md), [A.7 value proposition](VALUE_PROPOSITION_2026-11-26.md), [product brief](PRODUCT_BRIEF.md), [dated UX research](../design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md). P0.1 buyer decision and value, P0.2 scope, P0.6 intended scenario: evidence for review, not acceptance. No new external research is necessary for this internal synthesis; source limitations inherited.

**Stopping criterion:** A.8 requires reconciliation of Investigate / Compare / Decide, narrow flagship versus future pinnacle and a defensible positioning hypothesis. Proposed vision/mission, category rationale, scope comparison, claim boundaries and falsification conditions meet that bounded synthesis criterion. A.1-A.8 research/synthesis verified against task stopping criteria only. Next A.9 product principles and success definition: propose measurable task outcomes, guardrails and validation protocol, without inventing results or implying approval. P0-A and P0 remain open; no new feature, phase credit or score change.
