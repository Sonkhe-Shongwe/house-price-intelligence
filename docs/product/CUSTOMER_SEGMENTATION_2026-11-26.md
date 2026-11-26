# P0-A.3 | Customer segmentation and provisional audience selection

**Date:** 26 November 2026. **Method:** bounded secondary research and qualitative product-fit analysis; no direct customer interviews, market sizing, recruitment, property rows or application experiments. **Status:** research recommendation, not market or customer acceptance. [P0 directive](../engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md), P0.1/P0.2/P0.6; [industry research](RESIDENTIAL_PROPERTY_INDUSTRY_RESEARCH_2026-11-26.md), [buyer problem research](HOMEBUYER_PROBLEM_RESEARCH_2026-11-26.md), [product brief](PRODUCT_BRIEF.md) retained.

## 1. Decision and segmentation dimensions

Select the audience whose actual decision fits the approved one-market, one-class, historical evidence-only, two-to-three-home shortlist. Distinguish customer need, product fit, access to the audience, and actual commercial demand. Primary residence versus investment/professional use is a purpose distinction; first-time versus repeat purchase is experience; local familiarity is an overlapping dimension, not a mutually exclusive market share. Current decision stage (after discovery, before commitment) and willingness to use traceable historical evidence are behavioural qualifiers. No age, income, nationality, race, household type or financing method restriction inferred.

## 2. Evidence register

All reviewed 26 November. NAR releases available through search excerpts; main release direct open returned cache miss. No new PDF analysis; detailed NAR figures and limitations inherited from the A.2 record, not independently re-extracted.

| ID | Source | Date / method / finding | Limit |
| --- | --- | --- | --- |
| S1 | [NAR 2026 release](https://www.nar.realtor/newsroom/first-time-home-buyer-share-inches-up-to-22-median-age-remains-at-record-high-of-40), [Top 10 takeaways](https://www.nar.realtor/news/economists-outlook/top-10-takeaways-from-nars-2026-profile-of-home-buyers-and-sellers), [research update](https://www.nar.realtor/research-and-statistics/research-reports/research-update) | Nov 2026, US successful primary-residence purchases July 2025-June 2026; first-time 22%, repeat remainder 78%; median ages 40 and 62; agent use 90%. Prior A.2 recorded 7,125 responses, low adjusted response rate; understanding buying process difficult for 39% first-time vs 8% repeat, finding right property 55% vs 57%. | Not local Evanston, not all searchers, not investor population; general difficulties not proof of comparable-evidence need. Trade association, retrospective/nonresponse bias. No demographic inference for individuals. |
| S2 | [NAR 2025 profile summary](https://www.nar.realtor/news/real-estate-news/nar-2025-profile-of-home-buyers-sellers-reveals-market-extremes) | Nov 2025; preceding successful-buyer cohort, 76% of first-time buyers credited agents with explaining process. | Separate year; not proof HPI replaces agents or unmet need. |
| S3 | [Kandlbinder, Miller and Sklarz 2019](https://doi.org/10.1108/IJHMA-02-2018-0017) | Publisher abstract rechecked, Miami-Dade condo sales 2005/2015, hedonic regression and matching checks; historical nonlocal premium consistent with search costs and anchoring; search-cost component declined. | Paywalled full text, different asset/time/market; no transferable effect or causal HPI benefit. |
| S4 | [CFPB Find the right home](https://www.consumerfinance.gov/owning-a-home/explore/find-the-right-home/), [Buying a house](https://www.consumerfinance.gov/owning-a-home/) | US federal consumer guidance, 2024 onward; home search, agents, finance and inspections are distinct tasks. | Guidance, not demand survey; financing hurdles not solvable by HPI. |
| S5 | [IRS Publication 527 (2025)](https://www.irs.gov/publications/p527), [rental income and expenses](https://www.irs.gov/businesses/small-businesses-self-employed/rental-income-and-expenses-real-estate-tax-tips) | US official rental-property tax guidance, 2025 edition; rental activity involves income, expenses and asset accounting. | Not investor preference survey; infer broader investment evaluation needs, not actual willingness to pay. |
| S6 | [Fannie Mae Selling Guide B4-1.3-08](https://selling-guide.fanniemae.com/sel/b4-1.3-08/comparable-sales), [B4-1.3-07](https://selling-guide.fanniemae.com/sel/b4-1.3-07/sales-comparison-approach-section-appraisal-report), [March 2026 update](https://singlefamily.fanniemae.com/originating-underwriting/appraisers/appraiser-update-march-2026) | Professional mortgage-appraisal guidance, 2025/2026; selection, independent data verification and market-condition adjustments. | Specific lending/appraisal context, not blanket requirements for consumer education or all professional work; HPI not an appraisal. |
| S7 | [P0-A.2 research](HOMEBUYER_PROBLEM_RESEARCH_2026-11-26.md) and [P0-A.1 industry](RESIDENTIAL_PROPERTY_INDUSTRY_RESEARCH_2026-11-26.md) | 78% combined very/somewhat useful rating for recent-sale details in NAR 2026; overall high satisfaction and agent use; source lag, retrospective cohort and price semantics. | No segment-specific usefulness estimate, no local adoption, no observed HPI advantage; data age and use rights constrain every segment. |

## 3. Segment profiles and alternatives

| Segment | Relevant need (evidence or hypothesis) | Alternatives and scope gap |
| --- | --- | --- |
| First-time owner-occupier | Greater process difficulty (S1); hypothesis of need for clear evidence interpretation, questions and comparison | Agent, portals, education and financing guidance; S2 counters replacement claim; affordability and process complexity extend beyond HPI |
| Repeat/occasional owner-occupier | Similar broad search difficulty (S1); may need to refresh local knowledge and compare shortlisted homes after long interval | Agent/portals, past purchase experience, manual research; no evidence all repeat buyers need another tool |
| Unfamiliar-market owner-occupier (overlap) | Historical evidence of information disadvantage (S3); plausible local-context need | Local agent, online evidence, visits; historic condo study not local proof; current geographic/condition data gaps particularly important |
| Investor | Inferred return, income, cost and risk evaluation (S5); sale evidence only one input | Investment calculators, rent data, professional analysis; no rental yields, operating costs, portfolio or tax tools in MVP |
| Agent/broker | Inferred client advice and comparative market research; professional help is already widespread (S1/S2) | Existing broker/MLS workflows, current market evidence and client-facing outputs; no licensed live listings or professional workflow/permissions |
| Appraiser/lender | Formal comparable selection, verification, time adjustment and reporting (S6) | Professional data and appraisal procedures; HPI's retrospective limited evidence cannot satisfy these as a substitute |

## 4. Qualitative selection matrix

Use mandatory scope fit as gate; compare surviving candidates by evidence of pain, relevance to historical comparison, cost/complexity of serving needs and risks. No invented numeric ratings, segment sizes, reach or adoption forecasts. Reachability is untested for every external audience; existing owner-only beta is an operating constraint, not a consumer segment. A public recruiter demo is a separate portfolio audience, not the primary buyer.

| Segment | Relevant pain evidence | Core workflow fit | Additional needs / risk | Recommendation |
| --- | --- | --- | --- | --- |
| First-time owner-occupier, shortlisted | Moderate for broad process difficulty; comp-specific unmeasured | High conditional | Plain language, not finance or offer advice; stale evidence risk | Priority discovery lens |
| Repeat/occasional owner-occupier, shortlisted | Moderate for broad search; comp-specific unmeasured | High conditional | Local knowledge varies; may already have sufficient help | Include in same behavioural segment |
| Unfamiliar-market owner-occupier | Directional historical study only | High conditional if cohort fits | Need current local context; avoid generalising premium | Cross-cutting priority lens, not separate exclusive segment |
| Investor | No direct preference evidence in this study | Low for investment decision as a whole | Rent, yield, cost, tax and risk models missing | Exclude as MVP target |
| Agent/broker | No direct professional demand evidence | Partial for evidence lookup only | Fresh data, licensed workflows, client access and support | Defer professional product |
| Appraiser/lender | Professional standards establish distinct job | Low for required professional outcome | Verification, time adjustments, professional responsibility | Exclude professional appraisal/lending use |

Conditional means the current historical cohort is not a live/current market feed, identity, rights and freshness remain unresolved; there is no validated contemporary consumer use yet. Need cannot offset an unsupported market/class or unapproved data use. Underlying HPI feasibility and no-go boundaries remain unchanged.

## 5. Recommended audience and boundaries

**Provisional primary segment:** an individual prospective owner-occupier evaluating two or three already shortlisted residential properties within one demonstrably supported geography/class, seeking understandable traceable historical sales evidence and differences before deciding whether to pursue a property or ask more questions. First-time/occasional and unfamiliar-market buyers are priority research lenses because of plausible learning/context needs, not eligibility requirements or independently verified HPI demand. Repeat experienced buyers remain in scope when they have the same job. Do not require age, income, first-time status, nationality, mortgage eligibility or a lack of professional assistance. No inference of a final Cook County market or data permission.

**Secondary future research:** a repeat buyer with the same shortlist task is an included variant, not a separate product; professional helpers may be stakeholders but not the account/customer target. Recruiter audience remains separate. **Explicitly excluded as MVP target:** property investors seeking returns, agents seeking professional client tools, appraisers/lenders seeking regulated professional outputs; also sellers seeking listing-price advice, speculative buyers, broad browsing and buyers needing unsupported locations, property types, current valuations or real-time listing feeds. Exclusions concern product jobs and evidence coverage, not protected traits. Existing out-of-coverage abstention remains required.

Counterfactual: if first-time buyers already receive sufficient evidence from agents, or need only affordability support, targeting first-time status alone would be poorly justified. If current-market evidence is essential and historical coverage cannot support the decision, none of the buyer segments is yet a viable real-product audience. P0-C/D/E/G must resolve scope, rights and feasibility before real product release; no private real-intake waiver. Do not pivot to investors or professionals to bypass a blocker.

## 6. Validation questions and stopping criterion

P0-A.4 should develop a provisional primary behavioural persona (no invented demographics presented as facts) and only a meaningful included repeat/unfamiliar-market variant if needed. P0-A.5/A.6 identify concrete decision jobs and evidence gaps; P0-B test existing alternatives. Later approved task research should compare understanding of dates/provenance/limitations, evidence comprehension, effort and appropriate refusal against existing workflow; measure actual adoption or willingness separately. No recruitment/contact authorised by this work. No persona or journey work begun here.

All required candidate segments compared, alternatives, scope fit, reachability unknowns, risks, recommended primary and excluded audiences documented. P0-A.3 meets desk-research stopping criterion; P0-A.1-A.3 verified research only, customer demand and applicable owner acceptance pending at P0-A.10. Next P0-A.4 buyer personas only. No new code, data, rights, scope, service, cost or score change.
