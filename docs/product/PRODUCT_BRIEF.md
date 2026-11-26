# Product brief: House Price Intelligence

**Source:** The pre-existing Project 2 brief in `Sonkhe-Shongwe/sa-tech-grad-playbook.` at `docs/portfolio/house-price-intelligence.md` (reviewed 22 November 2026). This is a standalone adapted copy retaining the prior requirements and unresolved decisions. The original source remains intact.

**Owner decision (24 November 2026):** pursue the original full real-property release. Evanston Township/Class 203 remains the initial candidate pending qualification and source-specific rights. Fictional fixtures remain development/test data; no production display or deployment approved. See [FR1–FR3](../engineering/FULL_RELEASE_QUALIFICATION_V1.md).

## Problem and buyer

A prospective homebuyer has shortlisted houses whose asking prices are visible, but needs evidence of recorded completed sales, relevant physical characteristics, differences among candidate homes and the limits of available information. The product should help a buyer understand which recently sold properties offer a defensible comparison and why.

**First buyer:** One individual inspecting two or three homes in one demonstrably supported local market and property class. A user may manually enter an asking price and supported property attributes. The system must not claim to provide live listing discovery, verified listing images or a current market feed until independently integrated and validated.

**P0-A.8 strategic synthesis (26 November):** [Vision and positioning](PINNACLE_VISION.md#p0-a8--product-vision-and-positioning-synthesis-26-november-2026) proposes the residential property decision intelligence identity and preserves Investigate / Compare / Decide, the narrow flagship and separate future pinnacle. Proposed language awaits applicable owner review; the existing scope and acceptance checklist below are unchanged. Historical evidence must not be represented as current market coverage or a current valuation.

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

## Scope boundaries

**No v1 commitment:** Multi-market listing search, professional appraisal accuracy, live property photographs, mortgages, AI assistant, property alerts, investor portfolio management or a global valuation model.

**Recruitment walkthrough:** Reopen two previously saved homes, inspect a traced comparable and its matching rule, show an unsupported property, then explain a database join, exclusion rule and test failure that the system prevents.
