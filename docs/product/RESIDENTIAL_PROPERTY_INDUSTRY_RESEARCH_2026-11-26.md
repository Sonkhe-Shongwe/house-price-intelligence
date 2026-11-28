# P0-A.1 | US residential property industry and transaction lifecycle

**Research date:** 26 November 2026. **Method:** bounded desk research, official public guidance and catalogue descriptions only; no property rows, interviews, accounts, publisher contact or new application experiments. **Scope:** US owner-occupier home purchase, with Cook County/Evanston as the existing candidate historical market; not a universal transaction model or final geographic approval. **Authority:** [P0 directive](../engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md), P0.1/P0.2/P0.6. Product and customer demand remain hypotheses where unvalidated.

## Research question and existing evidence

Where, in a real residential purchase process, can HPI's evidence-only property investigation and comparison workspace assist an individual considering two or three homes, and which activities should remain outside the product? The [product brief](PRODUCT_BRIEF.md), [pinnacle vision](PINNACLE_VISION.md), [existing UX research](../design/UX_RESEARCH_AND_PRODUCT_DIRECTION_2026-11-23.md) and [data feasibility](../research/DATA_FEASIBILITY.md) establish the prior scope, prototype and source constraints. They do not establish the industry workflow or actual buyer demand. Use those foundations rather than replace them.

## Evidence register

All sources accessed/reviewed 26 November; guidance and administrative descriptions, not representative consumer surveys. Source dates below are publication/update dates where visible, not guaranteed current-source extraction times.

| ID | Source | Method / geography / date | Finding and limitation |
| --- | --- | --- | --- |
| S1 | [CFPB, Find the right home](https://www.consumerfinance.gov/owning-a-home/explore/find-the-right-home/) | US federal consumer guidance; last modified 12 Dec 2024 | Buyer may use agents or property websites, should understand representation and contingencies and consider budget/risks. Guidance, not observation of buyer habits or agent misconduct. |
| S2 | [CFPB, Closing on your new home](https://www.consumerfinance.gov/owning-a-home/close/) | US federal mortgage guidance; modified 3 Nov 2025 | After accepted offer and lender selection, inspection, underwriting, insurance, settlement and closing documents are relevant. Applies to typical mortgage transactions; cash and local practices may differ. |
| S3 | [CFPB, Schedule a home inspection](https://www.consumerfinance.gov/owning-a-home/close/schedule-a-home-inspection/) | US federal consumer guidance; retrieved 26 Nov | Inspection addresses condition; appraisal is separate and generally required in financed transactions. Inspection findings may affect repair negotiations or contractual options. No app can establish physical condition from assessor class. |
| S4 | [CFPB, What happens at mortgage closing?](https://www.consumerfinance.gov/ask-cfpb/im-about-to-close-on-a-real-estate-purchase-transaction-with-a-mortgage-what-can-expect-in-the-mortgage-closing-process-en-1905/) | US federal guidance; search excerpt reviewed | Closing involves transfer documents and recording by settlement/closing parties. Not a guarantee of local sequencing or that every transfer is recorded on closing day. |
| S5 | [Illinois Department of Revenue, PTAX-203 instructions](https://tax.illinois.gov/localgovernments/property/general-information/ptax-203_instructions.html) | Illinois administrative form instructions; retrieved 26 Nov, sections on special circumstances and consideration | Transfers may involve court orders, partial interests, short sales, options, exchanges and non-real-estate consideration. Declaration consideration has a defined accounting meaning, not an independent market valuation. Not proof of a specific source field's transformation or completeness. |
| S6 | [Illinois Department of Revenue, MyDec](https://tax.illinois.gov/localgovernments/property/mydec.html) | Illinois electronic transfer-tax declaration guidance; retrieved 26 Nov | System supports electronic declarations and corrections through recording; counties/settlement parties participate. Not a live listing service or proof every record appears promptly. |
| S7 | [Cook County Assessor - Parcel Sales catalogue](https://catalog.data.gov/dataset/assessor-parcel-sales) | Official catalogue mirror, modified 1 Aug 2026 in retrieved metadata; 31 Oct 2023 filter update noted | Document number links to clerk recording; PIN should preserve 14 digits; many records arrive months after recording. The 2023 update removed default deed/price/recency filters, yet older description also calls sales filtered: use explicit flags, not blanket assurances. No new rows queried, no freshness SLA or rights granted. |
| S8 | [Cook County Assessor, Evanston Township Residential Valuations](https://www.cookcountyassessoril.gov/valuation/evanston-township-residential-valuations) | Local publisher guidance; search excerpt only (full page returned 403) | Assessor receives MyDec sales and estimates property values using modelling. Corroborates data lineage; not used to claim model accuracy or exact valuation timing. |
| S9 | [Cook County Assessor, Property Tax System](https://www.cookcountyassessoril.gov/cook-county-property-tax-system) | Local publisher description; search excerpt reviewed | Assessment serves tax purposes and emphasises uniformity. Distinguish assessed value and estimated market value from sale consideration. Not an individual appraisal. |
| S10 | [HUD, Buying a Home](https://www.hud.gov/helping-americans/buying-a-home/) | US federal overview; search excerpt reviewed; full retrieval cache miss | Corroborates inspection/settlement/financing steps; not relied on for unique claims. |

## 1. Industry lifecycle and roles

Illustrative sequence, not a mandatory linear order. Financing and diligence may start earlier or overlap; cash purchases have different requirements. Existing HPI direction deliberately enters after discovery, before an offer, with possible evidence review during negotiation.

| Step | Buyer decision / evidence | Participants | HPI boundary |
| --- | --- | --- | --- |
| Preparation | Needs, affordability, financing and risk tolerance | Buyer, lender, housing adviser | Outside MVP; asking price alone does not establish affordability |
| Discovery | Locate available homes; listing facts, asking price, tours | Seller, listing broker, buyer broker, listing services | External entry point; HPI does not verify live availability or listing claims |
| Shortlist | Select plausible alternatives | Buyer, broker, household | Primary proposed intervention; two or three homes |
| Investigate | Examine earlier eligible completed transfers, attributes and evidence limitations | Buyer, broker, public data publishers | Primary proposed intervention: traceable evidence and abstention |
| Compare / prepare offer | Compare alternatives and questions, decide whether to proceed | Buyer, broker, seller | Primary proposed intervention: organise evidence, not recommend a binding price |
| Offer / contract | Price, terms and contingencies negotiated | Buyer, seller, brokers, attorneys where engaged | External; HPI is not an agent, legal adviser or negotiation platform |
| Due diligence / financing | Inspection, appraisal, title, underwriting and insurance | Inspector, appraiser, lender, attorney, title/settlement providers | External; not substitute for inspection, appraisal, financing or legal review |
| Closing / recording | Funds, title transfer, deed and recording | Parties and settlement/title/recording offices | External; creates potential future historical evidence, not live feed |

Buyer and seller have distinct interests; listing information and representation can vary. A buyer's broker may supply relevant sales comparisons and explain the local market; HPI supplements rather than replaces professional expertise. Listing sites, assessor records and manual research are existing alternatives. Do not claim competitors lack these capabilities or brokers are biased as a class. Validate actual workarounds and unmet needs separately in P0-A.2 and P0-B.

## 2. Price semantics

| Concept | Meaning | Product implication |
| --- | --- | --- |
| Asking price | Seller's proposed price, reported by buyer in HPI | Label buyer-reported; not a completed transaction or independently verified listing |
| Offer / agreed contract price | Proposed or negotiated terms; transaction may still fail or change | Not historical closed-sale evidence; no offer automation |
| Recorded sale price | Publisher-reported consideration for an earlier transfer; may include unusual terms | Preserve source/date; apply screened eligibility, exact cents and known limitations |
| Appraisal | Professional opinion of value, often used by lender | HPI makes no appraisal claim |
| Assessor estimated market value / assessed value | Mass assessment estimates and tax base, distinct from one sale | Do not substitute for comparable sale facts or equate tax assessment to market price |
| HPI comparable evidence | Selected earlier recorded sales under explicit rules, not a prediction | Explain selection and differences; no fair-price verdict, model estimate or guaranteed outcome |

S5 and S7 are important disconfirming evidence against the assumption every recorded transfer is a normal single-property sale. Transfer accounting can include exchanges, retained mortgages, personal property and exceptional circumstances. S7 describes filter changes and lag; preserve canonical screened candidate policy, do not alter it in P0-A.1. Data quality and field-level semantics belong to P0-C/P1.

## 3. Data lifecycle: source of historical evidence

Seller/buyer transaction -> settlement/transfer declaration (Illinois PTAX-203/MyDec where applicable) and deed recording -> assessor receives/processes data -> public catalogue revision -> authorised HPI snapshot (future, gates pending) -> screened comparable evidence. These are conceptual stages, not a claim every row follows an identical sequence. Distinguish contract date, recorded sale date, recording date, source publication/update date, extraction timestamp and analysis date. A past sale date or prior assessment year does not establish that the record was observable at that time.

S7 specifically notes that many sales arrive months after recording, despite periodic publication. Therefore the existing retrospective 2024-2025 sales / 2023-2024 assessment evidence supports a bounded historical research cohort, not contemporaneous 2026 market coverage. Show historical coverage and extraction date; make retrospective limitations visible; withhold claims of as-of verification. No guarantee of completeness/current availability or property identity. The four-source prior rehearsal is retained in [FR1-FR3](../engineering/FULL_RELEASE_QUALIFICATION_V1.md) and [private rehearsal](../engineering/PRIVATE_REAL_REHEARSAL_V1.md); no new intake or licence conclusion.

## 4. Product implications, hypotheses and next validation

| Evidence | Inference for HPI (not new approval) | Next validation |
| --- | --- | --- |
| S1-S3: distinct discovery, offer and diligence activities | Pre-offer shortlisted-home investigation is a plausible bounded decision point; repeat access during negotiation may help | P0-A.2 consumer evidence for actual pain and workarounds |
| S1: users can already use agents and property sites | Incremental value must be transparency, traceability and organisation rather than mere availability of sale data | P0-A.2, P0-A.6, P0-B |
| S5/S7: exceptional transfers, late arrivals and filter drift | Explicit price semantics, provenance, uncertainty and abstention are necessary safeguards | P0-C, P1/P2 at their own closure |
| S3/S9: distinct condition, appraisal and tax assessment roles | Avoid buy/sell advice, inspection, appraisal and affordability claims | P0-F requirements and acceptance |
| Existing brief: two or three properties, saved evidence | Retain Investigate / Compare / Decide, test whether the bounded workflow solves a meaningful buyer job | P0-A.5-A.10 |

Provisional industry positioning: a property-evidence workspace for an individual comparing shortlisted homes using transparent historical completed-sale context, without replacing a listing marketplace or professional transaction advice. This is aligned with prior approved scope, not a new final positioning or proof of demand. The hypothesis that information is fragmented or difficult to interpret is plausible but not established by this workflow research; research its severity, prevalence, counterexamples, buyer segmentation and existing workarounds in later named tasks.

## 5. Stopping criterion and review

P0-A.1 required industry map, roles, listing versus completed-sale evidence, jurisdiction/timing and decision point. All five are documented with source-backed findings and explicit limits. Desk-research task verified against its defined scope; **P0-A workstream and P0.1/P0.2/P0.6 acceptance remain open**. No direct consumer research, competitor benchmark, final geography, licence opinion, real data access or product change. The scope remains the prior owner-selected real-property product; R0, retention, protected-storage and permitted-use gates unchanged. Next: P0-A.2 homebuyer problem research, using credible published consumer surveys and studies to test hypotheses, distinguish populations/methods and counterevidence; no recruitment/contact without approval. No score change.
