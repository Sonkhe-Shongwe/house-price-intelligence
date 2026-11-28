# P0-A.4 | Evidence-informed buyer personas

**Date:** 26 November 2026. **Status:** provisional behavioural personas synthesised from prior secondary research; not interviewed participants, validated archetypes or approved customer/market decisions. **Authority:** [P0 directive](../engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md), P0.1/P0.2/P0.6. Retain [product brief](PRODUCT_BRIEF.md), [industry research](RESIDENTIAL_PROPERTY_INDUSTRY_RESEARCH_2026-11-26.md), [buyer problem research](HOMEBUYER_PROBLEM_RESEARCH_2026-11-26.md) and [segmentation](CUSTOMER_SEGMENTATION_2026-11-26.md). No new external research needed for this synthesis; prior source limitations apply.

## 1. Method and evidence levels

Use a single behavioural primary persona plus one meaningful overlapping variant. Define by purpose, decision stage and need, not demographic proxies. A first-time/occasional purchase is a useful discovery lens, not an eligibility rule; experienced repeat buyers can have the same job. No invented names, ages, occupations, incomes, household composition, technical competence, location, purchase budgets or direct customer quotations. Illustrative first-person statements below are authored scenario prompts, not testimony. Distinguish established product scope (S), published population-level evidence (E), and provisional design hypothesis (H). Evidence references refer to exact preceding research records, not independently re-queried survey microdata.

## 2. HPI-01 | The evidence-seeking homebuyer (primary)

| Dimension | Provisional profile and rationale |
| --- | --- |
| Context (S/H) | Individual prospective owner-occupier, already considering two or three homes in a demonstrably supported class/geography; pre-offer investigation or comparison, not property discovery. |
| Goal (H) | Understand meaningful differences and historical sale evidence before deciding what to investigate next or which questions to ask. |
| Trigger (H) | Multiple plausible homes, user-reported asking prices, uncertainty about relevance of previous completed sales or conflicting information from existing sources. |
| Potential frustrations (H) | Interpreting transaction terminology, comparing differently presented evidence, understanding whether past sales are relevant, uncertainty under time pressure. Prevalence of these precise frustrations is unmeasured. |
| Existing alternatives (E/H) | Agents and online property resources widely used in prior research; notes, spreadsheets and assessor searches plausible but usage unmeasured. Assistance may already be sufficient. |
| Information needs (S/H) | Sale date, reported completed consideration, permitted attributes, reason selected, differences, coverage and provenance; distinct buyer-reported asking price; visible insufficiency and caveats. |
| Interaction preference (H) | Plain language and accessible default explanations with optional methodological detail; no assumption of low technical skill or disability. |
| Successful outcome (H) | Can explain what the evidence supports and does not support, compare shortlisted homes and identify next questions without confusing HPI evidence with valuation or recommendation. |
| Out of scope (S) | Affordability, lending, live listings, inspection, negotiation/offer execution, appraisal, guaranteed price advice, investment returns. |

Illustrative motivation: "I have found homes that I like. I want to understand the evidence before making a commitment." This is not a participant quotation.

## 3. HPI-02 | The unfamiliar-market buyer (included overlapping variant)

| Dimension | Provisional profile and rationale |
| --- | --- |
| Context (S/H) | Same owner-occupier shortlist job; may be first-time or repeat, but lacks familiarity with the candidate local market. No inferred relocation reason, residency, demographic or income. |
| Goal (H) | Understand why previous local sales are relevant and where the available evidence is too limited. |
| Trigger and friction (H) | Unfamiliar local patterns, differing locations, difficulty judging geographic relevance; prior purchase experience may not transfer. Historical nonlocal premium study suggests a plausible information-gap mechanism, not local prevalence or causal HPI benefit. |
| Alternatives (E/H) | Local agent and online sources; property visits and personal contacts plausible, not measured here. |
| Information needs (S/H) | Market/class boundary, geographic matching explanation, selected evidence tier and location limitations, clear historical dates and no false location precision. |
| Interaction preference (H) | Optional depth on location and matching rules; same interface and data policy as HPI-01. |
| Successful outcome (H) | Can distinguish supported neighbourhood evidence, exploratory fallback and insufficient evidence; can identify questions requiring current local sources or professional advice. |

Illustrative motivation: "I understand how buying a house works, but I don't know this particular market well enough." This is a scenario for a possible repeat-buyer variant, not an assumption applicable to all unfamiliar-market buyers or a participant quotation.

No separate account type, interface, map service, live data or new feature is implied. A locally familiar experienced repeat buyer who shares HPI-01's job remains included. No third persona is necessary: additional experience or location variations can be tested within the same behavioural target.

## 4. Evidence-to-persona traceability

| Evidence inherited from P0-A.1-A.3 | Design implication / inference | Limitation |
| --- | --- | --- |
| A.2 S1: NAR 2026 national successful-purchaser survey, 39% first-time vs 8% repeat report process difficulty | Plain-language explanations for both profiles; first-time lens useful | Broad process difficulty, not comp-specific; nonresponse, recall and successful-purchase bias |
| A.2 S1: 37% very useful and 41% somewhat useful recent-sale website information | Evidence relevance supports investigating the core need | Combined rating is population-level, not persona-specific unmet demand |
| A.2 S1: 90% agent-assisted purchases; 92% process satisfaction | Complement agents and current tools; compare incremental benefit | Does not prove a separate workspace is needed |
| A.2 S2: retrospective commercial survey reports doubts and perceived overpayment alongside 81% happy with purchase | Non-coercive clarity, limitations, preserve buyer control | Not objective overpayment or causal benefit, no segment-specific rates |
| A.3 S3: historic Miami-Dade condo study on nonlocal premium | Unfamiliar-market variant merits testing | Different property class/market/era, abstract only, not transferable |
| A.1 S5/S7: transfer complexities, publication lag and historical availability uncertainty | Explicit price semantics, coverage, snapshot dates, supported/insufficient states | Current-source retrospective 2024-2025 cohort is not a current-market or historical-as-of guarantee |
| Product brief and verified fictional workflow | Two-to-three homes, evidence, shortlist and saved notes are existing scope; no new requirements accepted | Synthetic behaviour does not establish real buyer usefulness or data rights |

## 5. Counter-personas and counterevidence

Exclude professional valuation/lending and agent-client workflows, investor return analysis, seller pricing and broad live listing discovery as MVP target jobs, per A.3. Do not exclude a person by age, income, nationality, protected traits, first-time status, financing method or use of an agent. Unsupported property identity, geography/class, stale evidence or lack of eligible comparables should trigger existing truthful coverage/insufficiency behaviour rather than silently expand the audience or make unsupported claims. Recruiter demonstration audience and owner-only private beta operator are operating contexts, not buyer personas.

Counterexample: an otherwise suitable buyer already receives clear, sufficient current evidence from their agent or portal; HPI may add no value. If contemporary sale evidence is indispensable and historical cohort is inadequate, neither persona can support a viable current purchase use case yet. Do not disguise that gap with persuasive visuals or overconfident wording. The existing retrospective source rights, storage, identity, freshness and release blockers remain.

## 6. Validation questions (proposed, not executed)

For later approved research, use neutral prompts and observed tasks rather than suggestively asking whether HPI would be useful. Compare current workflow before introducing HPI. Ask participants to describe the most recent shortlist decision and evidence sources; show how they distinguish asking vs completed price, what a comparable means, how they judge date/location relevance, and what they do when evidence is missing. Use clearly fictional or otherwise expressly permitted scenarios; ask them to explain limitations, identify next questions, and say when existing tools already suffice. Include first-time and repeat/unfamiliar-market lenses if feasible, distinguish no need from poor usability, and record actual observed evidence before updating the personas. No fabricated responses, sample size, performance thresholds, or claimed improvement. No recruitment/contact is authorised here. P0-A.5 maps the journey; P0-A.6 prioritises jobs; P0-A.9 defines proposed success criteria; P0-B evaluates alternatives. Persona revisions and applicable approval at P0-A.10.

## 7. Stopping criterion

A.4 requires an evidence-informed provisional primary persona and relevant secondary audience only, without fictional demographics presented as facts. Both profiles, meaningful overlap, evidence provenance, assumption labels, alternatives, disconfirming conditions, exclusions and validation questions documented. Desk-synthesis stopping criterion satisfied; actual persona validity, customer demand, local market and owner acceptance remain open. A.1-A.4 verified bounded research/synthesis only; P0-A and original P0.1/P0.2/P0.6 acceptance remain open. Next P0-A.5 customer journey mapping only. No new product feature, scope, dataset, account, external contact, deployment, rights, cost or score change.
