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
