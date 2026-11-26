# HPI-SA | SA3.3 research proposal and permission packet

**Prepared:** 26 November 2026. **Status: INITIAL METADATA ENQUIRY SENT 26 November; FORMAL APPLICATION UNSENT.** Original draft below preserved as historical; shorter owner-authorised enquiry actually sent, see D. No application, account, payment, request for individual property rows or transfer of property rows has occurred. This document contains no personal CV, personal contact details, signature, confidential source data or assertion of academic affiliation. It is not a grant, legal opinion, ethics approval, final pilot design or permission to start research.

Basis: [SA2 acquisition review](SOUTH_AFRICAN_DATA_ACQUISITION_2026-11-26.md), [SA3 legal/field/operation review](SOUTH_AFRICAN_LEGAL_AND_DATA_RIGHTS_2026-11-26.md), [local buyer research](../product/SOUTH_AFRICAN_ECOSYSTEM_AND_BUYER_RESEARCH_2026-11-26.md), [mission directive](../engineering/SOUTH_AFRICAN_MISSION_DIRECTIVE.md) and [private beta](../engineering/PRIVATE_REAL_DATA_BETA_V1.md). Official [City research page](https://www.capetown.gov.za/city-connect/access-information/submit-a-research-request) and [document requirements](https://resource.capetown.gov.za/documentcentre/Documents/Procedures%2C%20guidelines%20and%20regulations/Submit%20_Research_Request_Guidelines.pdf) rechecked 26 November: confirmed Organisational Research contact and independent-applicant route, application through official portal and supporting documents. PDF text pp.1–2 recovered, screenshot attempts failed (cache miss); City HTML independently corroborates core requirements. The institution ethics committee letter appears under academic-purpose requirements in the detailed guideline, while the general ethics document requirement also applies; ask what applies to an independent applicant. No exemption asserted. The guideline requests at least one month (20 working days) before commencement; this is a submission lead time, not promised response or approval.

## A. First contact: metadata-only clarification (draft email)

**To:** researchrequest@capetown.gov.za

**Subject:** Independent research enquiry: residential property sales data availability

Dear Organisational Research Team,

I am developing House Price Intelligence, an independent, non-commercial software portfolio project investigating how historical residential property sales can help prospective homebuyers compare properties using transparent evidence.

I came across the City's GV2025 property sales guidance and would like to establish whether a small, authorised research study could be feasible before submitting a formal application.

Could you please advise:

1. Whether the City maintains a residential sales dataset containing transaction dates and prices, property identifiers, dwelling and land area, property category and sale-validity information, and whether a data dictionary or aggregate coverage information is available.
2. Whether an independent researcher could apply for access to a minimised extract for one locality, excluding owner names, identity numbers, contact details, account information and financing information, at no cost.
3. Which department or data custodian would be responsible, what source and use restrictions apply, and whether private research and a later redacted portfolio demonstration would require separate approvals.
4. What ethics documentation and CV requirements apply to a solo independent researcher whose project is not part of a university qualification.

At this stage I am requesting guidance and non-personal metadata only. Please do not send individual property records. Any later research would be subject to the City's approval, applicable data protection requirements and agreed security, retention and publication conditions. A future buyer-facing application would require separate permission and is not part of this initial enquiry.

Thank you for your time and guidance.

Kind regards,

[Applicant's name]

**Send boundary:** one email, to the confirmed official Organisational Research address, no attachments, no CV/ID, no personal-data or property-row request, no acceptance of terms, no payment and no portal submission. Applicant reviews and supplies name privately before transmission. If user asks for a different sender or changes message, review exact final content. No authority for follow-up messages or accepting an offer of data implied. If unsolicited records arrive, do not ingest or redistribute them; seek safe handling instructions and appropriate approval without logging contents.

## B. Research proposal outline (for later formal application, not an attachment to A)

### Title
Feasibility of transparent residential comparable-sales evidence for prospective homebuyers in a South African municipal market: a bounded Cape Town study.

### Applicant, collaborators and purpose
Independent software portfolio project, currently non-commercial. One applicant; no external research partners, confirmed supervisor, institutional sponsorship, municipal endorsement or ethics clearance claimed. Applicant identity and contact details to be supplied privately. This phase investigates whether lawful, appropriately minimised municipal data can support a transparent comparison workflow, not a property valuation service. No direct participants, surveys, interviews or personal profiling proposed. Future user research, buyer-facing distribution, public demonstration with real data or commercial use are separate potential activities requiring applicable permissions and approvals. A fictional-data demonstration is distinct from actual municipal data use.

### Background and research questions
The City's [GV2025 sales guide](https://www.capetown.gov.za/media/qujmn5mx/propertysalessearchguidegv2025.pdf) describes nearby-sales information and dwelling/erf extent. A [2018 CAHF Cape Town market report](https://documents1.worldbank.org/curated/en/949651559538607449/pdf/Cape-Town-s-Residential-Property-Market-Size-Activity-Performance-Size-Activity-Performance.pdf), p.77, reports historical use of the City's transaction file. The [2026 Stats SA RPPI methods](https://www.statssa.gov.za/publications/Report%2001-60-00/Report%2001-60-002026.pdf) describe reporting/registration lag and a different aggregate statistical purpose. These motivate research, not proof of current access, permission, data quality or demand. Relevant standard: [SACPVP municipal valuation specification](https://www.sacpvp.co.za/standards/SAVS-02_Municipal%20Valuation%20Standard_sMVPR%20v2021_2024.11b.pdf) Template D; no assumption City's actual file implements it. Prior documentary retrieval limitations retained in SA2.

- Can the source identify distinct eligible single-property transactions and historically dated dwelling attributes without ambiguous links?
- Can earlier comparable sales be selected on documented, price-independent physical, temporal and local geographic criteria, with explicit abstention for insufficient evidence?
- Can the data's availability dates, provenance, permitted use and disclosure constraints support honest buyer-facing interpretation in a later separately approved product? Is contemporary unsold-subject entry demonstrable rather than inferred from retrospective sales?

### Design and scope (provisional, no data requested now)
First obtain dictionary, existing aggregate availability counts and conditions only. If a lawful route exists, preregister one locality in agreement with the City, freehold single-dwelling residential property as candidate class, and a bounded retrospective cohort before viewing outcomes. Proposed sale window 1 January 2024 inclusive to 1 January 2026 exclusive; later 2025 subjects, earlier-only reference sales within a provisional 365-day window, conditional on available prior attributes and dates. A separate contemporary independent unsold-subject frame, actual cutoff and freshness assessment would be required for current buyer claims; not included automatically. No selected suburb, source, accepted policy or validated cohort.

Provisional ceilings for discussion at SA4, not approval or an assertion the dataset fits: at most 5,000 sale rows, 500 distinct scoped property keys for linked attributes/subject entry, 40,000 total auxiliary rows, one authorised bounded attempt and no citywide archive. Custodian-filtered structured export preferred (CSV or Parquet, dictionary and revision metadata), or expressly approved controlled environment. No silent truncation, expansions after results, repeated scraping or live API assumption. Before acquisition agree exact rows/keys/bytes/request/time limits, approved transport and environment, selection policy, retention/cleanup and stop conditions; if caps would produce biased/incomplete sample, revise proposal before intake or decline. Aim 20 or more later eligible subjects where feasible, diagnostic floor 10, no population representativeness or acceptance inferred; final sample plan determined independently before intake. No actual property rows, counts or subject selections yet.

### Minimum candidate data dictionary (availability enquiry only)
| Field family | Need and handling |
| --- | --- |
| Stable custodian transaction token and property token | Essential distinct transaction and property linkage; preferably source-generated pseudonymous tokens; preserve cardinality, grouping and repeat detection. SG21/deed reference only if indispensable, separately permitted, internal only. |
| Tenure, category, locality/neighbourhood and effective version | Essential supported scope and geographic relevance; no raw comparable addresses or geometry. |
| Recorded sale consideration, currency, agreement/sale date and registration date | Essential distinct meanings; exact ZAR cents, recorded consideration not asking price or municipal assessment. Registration date where necessary to establish availability; no assumed equality of dates. |
| Observation, effective, capture/publication and revision dates | Essential to temporal integrity, actual as-of capability and reporting lag; document unknowns explicitly, no leakage claim. |
| Dated dwelling area/GBA definition and eligibility | Essential physical comparison, same measurement definition; one dwelling or defensible restriction. No footprint or land substitution. |
| Land/erf extent | Conditional if needed, distinct from dwelling area. |
| Multiple/grouped/partial transfer, valid sale, deed/transaction type, repeat and inspection eligibility flags | Essential sufficient audited exclusion logic, particular flags conditional; no free-text notes. Custodian-screened export acceptable only with documented rule and aggregate funnel. |
| Subject-only lookup key or permitted address label | Required for later independent unsold-entry qualification; separate approved source/use. No owner-based search. |
| Source revision, field definitions and licence/permission | Essential provenance, explicit disclosure authority, permitted operations and correction path. |
| Exact centroid/geometry or optional contextual attributes | Not requested by default; only if indispensable, separately permitted and approved. |
| Owner/tenant names, ID/contact, tax/account, financing, objection/inspection narratives, special personal information | Excluded altogether. No record containing these requested. |

No collection of research participant details or City staff participant time. Initial administrative routing and optional existing metadata response only; no bespoke analysis or uncompensated staff commitment assumed. If preparation requires a fee or substantial work, ask whether an existing approved no-cost alternative exists; otherwise stop under R0.

### Analysis and interpretation
Reconcile source rows to unique screened sales, dated eligible attributes, assigned later subjects and supported/exploratory/insufficient/out-of-coverage outcomes. Report disjoint exclusion reasons and denominators, duplicates/grouping, missing dated joins, ambiguity, and reporting lag. Provisional criteria for SA4 review: three to five unique eligible earlier properties, same class and locality, consistent area definition and provisional ±25% dwelling size, no use of prices to rank comps, no same-property/future/same-day leaks. Separate spatial exploratory status only if justified and authorised. Use all assigned subjects including failures; never present conditional coverage as market-wide. No appraisal, price prediction or recommended offer. Earlier-only and actual information-availability chronology distinct. No user study or demand proof in this phase.

### Ethics, data management and publication
Before any real intake, confirm relevant statutory and third-party disclosure authority (including Municipal Property Rates Act ss41–44 where applicable), POPIA purpose/basis, roles, applicable notice, prior-authorisation and cross-border assessment, ethics documentation and written operation-specific terms. This outline is not ethics clearance. Confirm whether independent applicant must obtain external ethics review and whether a solo project profile can replace organisation CV. No institutional endorsement claimed.

Proposed research processing only by authorised applicant in independently verified protected local/approved environment; no foreign hosting without specific assessment and approval; no public repository, CI, model prompts, unrestricted exports or personal records. Minimise inputs at custodian; keep access controlled, encrypted, audited, and restricted to defined purpose. No raw comparable identifiers, exact comparable addresses or coordinates in any public output. Risk-review exact prices/dates/area and small cells for reidentification; aggregate/suppress/withhold as needed. No real records supplied to reviewers or recruiters unless expressly permitted. Source attribution and terms recorded. Handle correction, access, incident response, and deletion with custodian-approved plan, including residual backups and logs. Real-data retention ceiling 30 calendar days from intake or shorter applicable requirement, no automatic extension; establish lawful timely disposal and approval before receiving data. No real-data storage environment is yet accepted; don't represent existing invented-data tests as proof.

Expected deliverable: internal methodology and feasibility report, with permission-reviewed aggregate findings where allowed, including negative results and limitations. Offer the City an approved report under agreed conditions. No publication venue/date committed, no public data release. Later public portfolio demo or private buyer display requires separate written permission and actual output/privacy qualification; disclose possible future product use now, no commercial exploitation in proposed research.

### Proposed work plan (relative, conditional)
Submit any complete formal application at least one month/20 working days before proposed start, only after route and requirements clarified. Actual start/completion dates to be agreed with City after approvals; no calendar commitment now. Indicative maximum 30-day intake-to-disposal research window, if terms permit:
- Days 1–5: approved bounded intake, schema/cardinality/provenance and integrity checks; stop on violations.
- Days 6–15: preregistered retrospective matching and full-denominator audit.
- Days 16–25: error review and internal report; permitted aggregates only.
- By applicable expiry, no later than day 30: approved cleanup, residual assessment and completion record. Shorter source conditions override plan; no intake unless timely compliant disposal feasible.
Administrative review, ethics and protection occur before intake, not within the retention clock. No promise of completion or provider response.

## C. Approval and response checklist

| Gate | Evidence necessary | Current state |
| --- | --- | --- |
| Owner authorises one metadata-only contact | Explicit decision to send concise metadata-only enquiry | Sent (Gmail SENT); exact shortened draft not shown beforehand, acknowledged error; future exact approval required |
| Appropriate official route and application requirements | Custodian/City confirmation of independent route, CVs, ethics and portal requirements | Public guideline documented; individual applicability unknown |
| Application material | Approved outline, actual applicant details, lead CV 2–3 pages, organisation CV 1–2 pages or City-confirmed alternative, relevant ethics document, partners, dates, planned outputs | Outline drafted; actual CV/identity/ethics/approved dates not supplied; do not place in Git |
| Field disclosure and lineage | Custodian and upstream authority, actual field definitions, MPRA s44 determination where applicable | Unresolved |
| Costs | Written no-cost acquisition/preparation/access and sustainable R0 terms | Unresolved |
| Operations | Written permitted acquisition, transformation, joins, internal research, retention, corrections and output; separate public/private/commercial rights | Unresolved |
| Protection | Purpose/basis, applicable POPIA approvals, ethics, hosting, roles, security, retention/disposal approved and verified | Unresolved |
| SA4 bounded study | Exact locality/class, windows/caps, one-attempt protocol, pre-registered acceptance and separate owner approval | Proposal only; blocked |
| Future product | Contemporary entry/freshness, applicable original P0 exit and P1–P8 gates, actual display rights, scope and release approval | Blocked |

### Historical owner decision and recovery path (initial contact resolved; see D)

At preparation, recommended **authorise one metadata-only Cape Town contact as drafted in A** (or send it personally). This initial-contact decision is superseded by D; do not send again. This does not authorise requesting actual records, submitting an application, sharing a CV, accepting terms, payment, follow-up contact, data acquisition, provider operations, market selection or implementation. Do not send anything on a generic continuation such as “next” after this checkpoint; obtain explicit contact authorisation or user confirmation of personal sending. If metadata reply confirms a credible no-cost route, review exact response and proposed formal application requirements before seeking any additional permission; no automatic step into SA4. If no qualifying route, consider Ekurhuleni then Johannesburg or a specific authorised partner as previously ranked, only with separate permission for contact. No response or deferred decision is BLOCKED, not proof of impossibility. If the owner elects to defer the mission rather than contact, preserve this packet and return to ordinary P0-C supported-property boundary review at the saved [49f7a53 checkpoint](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/49f7a5396792e8bf09bdc060e4bde1b78e8674e3/docs/CHECKPOINT.md); do not discard local findings or claim SA failed. If credible lawful R0 routes genuinely exhausted, document NO-GO and return there. No repetitive desk work while awaiting an indispensable decision.

**SA3 verdict:** SA3.1–3.3 bounded desk deliverables complete, including explicit outstanding permission gate; not legal compliance, approval or local empirical qualification. SA0–SA3 complete as research (4/10 unweighted workstreams); SA4 blocked before real data experiment. P0 94%, weighted MVP 87.1%, R0 and all full phase gates open. Ordinary P0-C paused pending owner direction.

## D. Actual contact event and process correction (26 November 2026)

Owner explicitly asked to send a concise version and selected their primary connected account. Gmail returned SENT for subject “Independent research enquiry: residential property sales data” to official Organisational Research contact. Shortened message asked about authorised no-cost limited municipal sales dataset, sale dates/prices/identifiers/dwelling area/validity, dictionary, research/portfolio use, application and ethics; requested nonpersonal metadata only and expressly asked not to send property records. No attachments. Exact sent text and personal sender identity remain in private email, not public Git. Delivery to recipient, response and permission not verified; response not checked in this slice. Original A was a longer draft, not what was sent. Assistant should have presented the shortened version before sending and acknowledged the mistake. Owner now requires exact draft review before every send, including recipient, subject, body and attachments, followed by explicit approval. No generic next or prior permission authorises future emails. The earlier owner-contact decision in C is resolved for this one send only; no formal application, CV, fee, property data, terms or follow-up authorised. [Independent readiness](../engineering/SOUTH_AFRICAN_INDEPENDENT_READINESS_2026-11-26.md) governs finite design while external gate remains blocked.

## E. Independent audit conditions for any later application (26 November 2026)

[IR critical audit](../engineering/SOUTH_AFRICAN_INDEPENDENT_READINESS_2026-11-26.md#5-owner-requested-independent-critical-audit-26-november-2026) found material event-history/attribute-time uncertainty. Before finalising any application, clarify whether requested window has all relevant events, finite previous sales or only latest sale, whether sales are a valuation-selected subset, and whether actual historical effective/observation/availability dates and auditable single-dwelling/group restrictions exist. If only current snapshots, do not pretend full historical coverage or run the original retrospective plan unchanged. Joint ceilings: 500 property keys includes all assigned subjects and retained reference candidates needing attributes; 5000 sale rows and 40000 auxiliary rows are outer ceilings, not target sample sizes. Preregister a jointly feasible bounded cohort and deterministic selection before observing outcomes; no post-hoc truncation or price-based selection; if constraints conflict or omit essential rows, revise prospectively under approval or decline. Diagnostic floor 10 and aim 20 do not establish population or user acceptance. No actual application submitted; clarify these points only in response review or future explicitly approved exact draft, not automatic follow-up.
