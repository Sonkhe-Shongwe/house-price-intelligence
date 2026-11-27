# Property data source register

**Updated:** 27 November 2026. Original pilot URLs, extraction evidence and dated rights reviews retained below; see [Pinelands source entries](#27-november-2026--pinelands-local-reference-sources) for the newest measured South African routes. Verified extraction or local audit does not establish time-correctness, legal identity, independent byte inspection or redistribution rights.

| Source | Identifier / URL | Current evidence | Outstanding review |
| --- | --- | --- | --- |
| Cook County parcel sales | `wvhk-k5uv`; https://datacatalog.cookcountyil.gov/d/wvhk-k5uv | **Queried:** 3,539 sale rows in township 17 for 2022–2024 | Sale flags, parcel/document grain, reporting lag, display rights |
| Historical residential building characteristics | `x54s-btds`; https://datacatalog.cookcountyil.gov/d/x54s-btds | **Queried:** 39,401 building rows; 1,285 accepted prior-year matches across classes | Historical publication timing, multi-card exclusions, data dictionary |
| Historical Parcel Universe | `nj4t-kc8j`; https://datacatalog.cookcountyil.gov/d/nj4t-kc8j | **Queried:** 262 matching PIN/prior-year records for Class 203 enrichment | Neighbourhood definitions, backfills, coordinates and usage terms |
| Sales metadata API | `/api/views/wvhk-k5uv.json`; https://datacatalog.cookcountyil.gov/api/views/wvhk-k5uv.json | Field inventory and update timestamp used in Phase 0 | Detect source schema/metadata drift per run |
| Building metadata API | `/api/views/x54s-btds.json`; https://datacatalog.cookcountyil.gov/api/views/x54s-btds.json | Field inventory and update timestamp used in Phase 0/1 | Track changed fields and definitions |
| Historical Parcel Universe metadata | `/api/views/nj4t-kc8j.json`; https://datacatalog.cookcountyil.gov/api/views/nj4t-kc8j.json | Queried by Phase 1 schema inspection | Historical coverage and missing/optional fields |
| Cook County Assessor real property classification | https://www.cookcountyassessoril.gov/classifications-real-property | Class 203 used as research category | Verify individual-record class use and final product eligibility |
| Cook County open-data policy | https://datacatalog.cookcountyil.gov/stories/s/About-Open-Data/pvqg-z4sc/ | General policy identified | Dataset-specific field display/reuse/attribution permission **not accepted** |
| Assessor research/AVM methodology | https://gitlab.com/ccao-data-science---modeling/models/ccao_res_avm | Methodology reference only | Not evidence that our MVP has complete model features or performance |
| NYC rolling property sales | https://www.nyc.gov/site/finance/property/property-rolling-sales-data.page | Research lead, not extracted for this MVP | Property types, comparable linkage, rights |
| HM Land Registry paid-price data | https://www.gov.uk/guidance/about-the-price-paid-data | Alternative source lead | Coverage, joinable attributes and reuse |
| England/Wales EPC data | https://get-energy-performance-data.communities.gov.uk/ | Potential attributes | Licence and linkage |
| South African DeedsWeb | https://www.gov.za/services/services-residents/place-live/subscribe-deedsweb | Potential local-market lead | Access, transaction granularity and rights |

**Current strategic direction (27 November 2026):** [owner decision](../DECISIONS.md#owner-decision-end-south-african-first-mission-27-november-2026) ends the SA-first mission. The source register retains dated research, permissions and lifecycle obligations; no SA grant or intake is an active project dependency. Restore geography-flexible source qualification.

## Provenance and control rules

- Pilot dates: sales from **2022-01-01 inclusive to 2025-01-01 exclusive**, Cook County township code `17`; characteristics and geography are linked to the **prior tax year as a proxy**.
- Verified source run: [22 Nov 2026 cloud audit](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782). See the detailed [Phase 0](PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1](PHASE1_CLOUD_AUDIT_RESULTS.md), and [Phase 2](PHASE2_CLOUD_AUDIT_RESULTS.md) findings for actual counts and limitations.
- Keep publisher URL, dataset ID, extraction timestamp, query, schema and source update timestamp in the internal research layer; raw records never go in Git or public audit artifacts.
- Review data rights **by source and by displayed field** before storing/distributing property-level records in the buyer-facing app. An open-data catalogue listing alone does not settle permitted use.
- Original fallback-source leads came from the separate SA Tech Graduate Playbook. No fallback dataset has been quietly substituted for Cook County.


## 24 November 2026: address candidate and reuse review
Parcel Addresses `3723-97qp`: https://catalog.data.gov/dataset/assessor-parcel-addresses; first published March 2026 according to catalogue. Contains sensitive-to-product owner/taxpayer/mailing fields; excluded from research queries. Only aggregate-only feasibility authorised. See [production readiness contract](../engineering/PRODUCTION_READINESS_V1.md) for field policy, publisher sources, separate bulk agreement caveat and temporal limitations. No property-level display approval.


## 24 November 2026: FR source-specific metadata and year representation
[Qualification run 45365766942](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45365766942) verified stable revision metadata: all four required source licence identifiers null (sales wvhk-k5uv, assessment x54s-btds, historical universe nj4t-kc8j, addresses 3723-97qp). Null is unspecified, not prohibition or a grant. Official [classification](https://www.cookcountyassessoril.gov/classifications-real-property) identifies Class 203 as one-storey residence, 1,000–1,800 sq ft. Legacy integer conversion rejected all 13,151 assessment-year 2024 rows; exact whole-year diagnostic recovered 59 eligible 2025 sales, no canonical correction yet. See [qualification and field-level proposed disclosure](../engineering/FULL_RELEASE_QUALIFICATION_V1.md). No real publication, as-of proof or external contact.

## 25 November 2026: publisher intended-use review and proposed beta boundary

Reviewed public publisher documentation, not property rows: [Cook County About Open Data](https://datacatalog.cookcountyil.gov/stories/s/About-Open-Data/pvqg-z4sc/), [Assessor Open Data SOP](https://github.com/ccao-data/wiki/blob/master/SOPs/Open-Data.md), [Assessor 2022 refresh and contact](https://datacatalog.cookcountyil.gov/stories/s/i22y-9sd2), and [separate database subscription agreement landing page](https://www.cookcountyassessoril.gov/form-document/database-subscription-agreement). The portal describes independent API/download analysis; the SOP identifies comparable-property matching with sales and characteristics, address linkage/geocoding and geographic joins as intended uses. This supports the research purpose, not a blanket licence. The prior four null licence IDs remain unresolved; do not apply a separate paid database agreement to the public API without evidence, or infer unrestricted reuse from the public listing.

Proposed narrow private beta: one owner/operator, noncommercial personal research and portfolio development, authenticated private access, source allowlists and sealed records only, minimum redacted evidence projection; no owner/taxpayer/mailing/contact fields, raw comparable identifiers or coordinates in browser output; no real data in GitHub/public CI or recruiter access. Public demo remains fictional unless explicit display rights are established. Obtain clarification of private durable cloud retention, derived field-level display and recruiter/public reuse from publisher if terms do not settle these. Published data department contact is Assessor.data@cookcountyil.gov. No contact sent, no response or rights grant asserted. Owner-only scope approved; remaining protection/access gates await acceptance; no data extracted, no conditional extraction allowance consumed.

## 26 November 2026: retention and permitted-use clarification preparation

Rechecked public [portal principles](https://datacatalog.cookcountyil.gov/stories/s/About-Open-Data/pvqg-z4sc/) and [Assessor SOP](https://github.com/ccao-data/wiki/blob/master/SOPs/Open-Data.md). Portal supports independent API/download analysis; general license-free principle qualified by reasonableness does not establish dataset-specific rights. Full portal text not retrievable in this review; SOP confirms public data publication and intended research. Four previously null licence identifiers remain unresolved; no property rows queried, no new metadata claims. Proposed owner-only 30-day private retention, minimum selected fields, derived display to sole operator; no public raw records or real-property recruiter demo. Seek clarification from published data department contact on public API licence/terms, private hosted retention and derived field display, attribution and disposal obligations, separate public demo rights. No contact sent; no approval inferred. Confidential backup gate separately open after owner declined rekey. No real extraction.

## 26 November 2026: public terms reconciliation and narrow clarification

Public publisher pages reviewed (no property rows): [About Open Data](https://datacatalog.cookcountyil.gov/stories/s/About-Open-Data/pvqg-z4sc/) describes independent analysis via download/API and a qualified licence-free principle; [County Terms of Use](https://www.cookcountyil.gov/terms-use) sections 2, 7 and 10 disclaim data accuracy/non-infringement, direct appropriate-use questions to the data originator, require compliance with applicable law and third-party rights, and distinguish copyright concerns for site imagery/graphics. [Assessor valuation release](https://datacatalog.cookcountyil.gov/stories/s/Cook-County-Assessor-Valuation-Data-Release/p2kt-hk36/) encourages local analysis of released data; AGPL applies to the Assessor's code and is not a data licence. [2023 refresh](https://datacatalog.cookcountyil.gov/stories/s/Assessor-2023-Open-Data-Refresh/9bqn-cfsv/) confirms research purposes, documents limitations and welcomes questions to the Data Department. These support legitimate private research but do not settle the four unspecified dataset licence identifiers or the exact proposed hosted retention/display scope. No general prohibition inferred. Do not copy publisher imagery or claim endorsement. This is a project-specific conservative acceptance boundary, not a legal finding that express permission is always required for open data.

**Proposed clarification (unsent; owner review required):** To Assessor.data@cookcountyil.gov, subject: Clarification of open-data reuse for a private research project. Ask whether public API data from parcel sales (wvhk-k5uv), historical residential characteristics (x54s-btds), historical parcel universe (nj4t-kc8j) and parcel addresses (3723-97qp) may be used in a sole-operator noncommercial comparable-sales research application, retained in an access-restricted cloud database for up to 30 days with encrypted recovery copies subject to the same disposal policy, and displayed privately as redacted historical comparable evidence (sale price/date, assessment-year building area, age, differences and location category; no owner/contact/mailing fields, raw comparable identifiers or coordinates). Ask about any applicable dataset-specific terms, attribution, retention/disposal or geographic hosting requirements. Public portfolio uses fictional examples and aggregate research results only; public property-level display is a separate question. No contact sent, no response claimed. Subsequently owner approved 30-day maximum and deferred publisher contact on 26 November. No response or data-use grant inferred; no new intake.

## 26 November P0 closure review: independent catalogue and reuse evidence

Rechecked public documentation only, not property rows or metadata API: four US public catalogue entries for [sales](https://catalog.data.gov/dataset/assessor-parcel-sales), [characteristics](https://catalog.data.gov/dataset/assessor-single-and-multi-family-improvement-characteristics), [historical universe](https://catalog.data.gov/dataset/assessor-parcel-universe) and [addresses](https://catalog.data.gov/dataset/assessor-parcel-addresses) identify the Assessor data and public access; no explicit licence text found in those entries. This corroborates, but does not re-query, four previously null licenseId values. [County portal principles](https://datacatalog.cookcountyil.gov/stories/s/About-Open-Data/pvqg-z4sc/) support free access and independent analysis; [Assessor class definition](https://www.cookcountyassessoril.gov/classifications-real-property) confirms Class 203, one-storey 1,000-1,800 sq ft. [County GIS open-data announcement](https://www.cookcountyil.gov/news/county-eliminates-charge-gis-data) supports reuse of open GIS information in combination with other data; it is not a blanket licence for the four Assessor datasets. [Illinois Counties Code section 5-1106.1](https://codes.findlaw.com/il/chapter-55-counties/il-st-sect-55-5-1106-1/) distinguishes public electronic access, bulk/compiled dissemination and fees; not specific approval of the proposed hosted retention/display. These are positive feasibility indications, not legal advice or an independent grant of permission.

P0.5 remains blocked for the intended durable real-property product. Keep existing [FR2 field matrix](../engineering/FULL_RELEASE_QUALIFICATION_V1.md): internal parcel/document/card identifiers and centroids only if necessary and permitted; minimum private redacted comparable sale cents/date, assessment year/area, age, relative size and location category; no names, taxpayer/mailing/contact fields, raw comparable IDs or coordinates in browser output. Candidate attribution: publisher, dataset title/link, snapshot/retrieval date, transformations/limitations, no endorsement. Owner-only noncommercial scope, 30-day limit and protected-storage prerequisites remain; no publisher contact (deferred), no new extraction, and no public real-property release. The existing one conditional extraction remains unused. No inferred data-use approval or waiver.

## 26 November P0-B.4: alternative source documentation (no extraction)

See [competitive intelligence B.4](../product/COMPETITIVE_INTELLIGENCE_2026-11-26.md#b4--bounded-geographic-market-assessment) for the evidence, limits and provisional market comparison. New documented leads only: NYC DOF rolling/annual sales and BBL/MapPLUTO; England/Wales Price Paid Data and prospective 28 August 2026 transaction-to-UPRN lookup, EPC non-address OGL and separate address restrictions; King County assessor schemas (GIS residential derivative nonpublic and nonauthoritative); SA official fee-based registry route. No alternate data rows, verified joins, rights acceptance, final market choice or approved extraction. P0-C/D to verify applicable field/coverage and use conditions; P0-E R0 sustainability. Retain Cook County historical source register and evidence unchanged.

## 26 November P0-C source and field inventory

[Data feasibility P0-C inventory](DATA_FEASIBILITY.md#26-november-2026--p0-c-source-field-and-grain-inventory) maps essential semantics and source grains to actual Cook County code and NYC official documentation. NYC documented leads only: rolling usep-8jbt; annual w2pb-icbu; ACRIS Master bnx9-e6tj and Legals 8h5j-fqxa; PLUTO 64uk-42ks; PAD bc8t-ecyu. Official catalogue/glossary evidence and retrieval limitations in linked inventory. No actual NYC rows, joins, document amounts as sale prices, single-lot eligibility, historical attributes, entry coverage or permission established. ACRIS document-to-sale reconciliation and four-borough/County Clerk distinction material; no use of Parties/owner fields. No new acquisition or license decision.

## 26 November South African-first source leads

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/research/SOURCE_REGISTER.md#26-november-south-african-first-source-leads). Not active instructions.

## 26 November HPI-SA initial permission and source routes

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/research/SOURCE_REGISTER.md#26-november-hpi-sa-initial-permission-and-source-routes). Not active instructions.

## SA2.1 national source evidence (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/research/SOURCE_REGISTER.md#sa21-national-source-evidence-26-november-2026). Not active instructions.

## SA2.2 municipal source evidence (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/research/SOURCE_REGISTER.md#sa22-municipal-source-evidence-26-november-2026). Not active instructions.

## SA2.3 alternative source evidence (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/research/SOURCE_REGISTER.md#sa23-alternative-source-evidence-26-november-2026). Not active instructions.

## SA2.4 consolidated acquisition disposition (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/research/SOURCE_REGISTER.md#sa24-consolidated-acquisition-disposition-26-november-2026). Not active instructions.

## SA3.1 legal framework evidence (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/research/SOURCE_REGISTER.md#sa31-legal-framework-evidence-26-november-2026). Not active instructions.

## SA3.2 source-specific rights evidence (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/research/SOURCE_REGISTER.md#sa32-source-specific-rights-evidence-26-november-2026). Not active instructions.

## SA3.3 permission packet (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/research/SOURCE_REGISTER.md#sa33-permission-packet-26-november-2026). Not active instructions.

## Post-contact status (26 November 2026)

[Archived evidence](https://github.com/Sonkhe-Shongwe/house-price-intelligence/blob/ff02c39e233c7181cd021337bff45c9e7348c5ed/docs/research/SOURCE_REGISTER.md#post-contact-status-26-november-2026). Not active instructions.

## Independent critical audit (26 November 2026)

[Audit evidence and findings](../engineering/SOUTH_AFRICAN_INDEPENDENT_READINESS_2026-11-26.md#5-owner-requested-independent-critical-audit-26-november-2026) reverified CAHF 2018 p.77 and Gazette pp.5–6 visually; sMVPR Template C/D extracted text and policy 7.2–7.7 with screenshot failures, research page and DataFirst excerpts, POPIA text, MPRA excerpt. CAHF last-sale field does not prove full event history; current property-data extracts not proof of historical attributes. New bounded countersearch found no qualified substitute; not exhaustive. Exact Stats SA lag not independently reverified. No reply, rows, contact or permission. IR1 delta design next.


## 26 November 2026 | P0-D.1 source-specific permitted-use reconciliation

**Scope:** bounded desk reconciliation of retained documentary evidence and actual prior qualification, no fresh external source retrieval, metadata API/property requests, legal opinion, permission, or source/owner contact. Reviewed [FR2](../engineering/FULL_RELEASE_QUALIFICATION_V1.md), [production readiness](../engineering/PRODUCTION_READINESS_V1.md), [private real beta](../engineering/PRIVATE_REAL_DATA_BETA_V1.md), [disposable four-source rehearsal](../engineering/PRIVATE_REAL_REHEARSAL_V1.md), [P0-C conditional boundary](DATA_FEASIBILITY.md#26-november-2026--p0-c-supported-property-boundary-and-conditional-feasibility-review), [SA3 field/operation matrix](SOUTH_AFRICAN_LEGAL_AND_DATA_RIGHTS_2026-11-26.md), and current decisions at exact development 79326aa (7/7 CI passed). Historical source retrieval limitations above remain; not a new certification that the terms remain unchanged. Distinguish publisher indications, contractual/legal terms, project acceptance and technical controls. P0.5/P0.7 remain blocked. The owner deferred Cook publisher clarification and rekey; do not treat this task or a generic continuation as reversal. 

### 1. Authority and evidence hierarchy

Four dataset catalogue entries identify the Assessor as publisher and public access; the last retained observed metadata run 45365766942 had four null licence identifiers. Null is unspecified, not a negative licence or a positive grant; a later published applicable policy or licence could settle reuse without bespoke permission. Retained [County portal principles](https://datacatalog.cookcountyil.gov/stories/s/About-Open-Data/pvqg-z4sc/), [Assessor SOP](https://github.com/ccao-data/wiki/blob/master/SOPs/Open-Data.md), [2023 refresh](https://datacatalog.cookcountyil.gov/stories/s/Assessor-2023-Open-Data-Refresh/9bqn-cfsv/) support public download/API analysis, property linkage and independent research. [County terms](https://www.cookcountyil.gov/terms-use) sections 2,7,10 as previously reviewed include accuracy/noninfringement disclaimers, appropriate-use enquiries to originator, lawful use/third-party rights; do not import site-image terms, developer documentation licences, AGPL for code, GIS announcements or the [separate subscription agreement](https://www.cookcountyassessoril.gov/form-document/database-subscription-agreement) as the four datasets' licence. Prior source register also records public-record access law as an access signal, not a conclusion about all downstream use. No fresh statutory interpretation, no claim express permission universally necessary. **Project-specific real-data acceptance requires adequate documented applicable rights and operational approval**, not merely publicly viewable records. Evidence of a prior approved temporary rehearsal and current code passing tests does not settle those rights.

### 2. Field-level minimum and output boundaries

| Dataset / retained licence status | Necessary internal fields and joins (proposed) | Narrow candidate private evidence (only if later approved) | Excluded from proposed disclosure |
| --- | --- | --- | --- |
| [Parcel Sales wvhk-k5uv](https://catalog.data.gov/dataset/assessor-parcel-sales), unspecified | PIN, internal document/transaction identity, recorded date, exact USD cents, qualifying transfer flags; exclude ambiguous multi-parcel/conflicting events | Selected sale date, recorded consideration, age; derived count and status | Raw PIN, document/transaction identifier, raw flags or excluded-sale details, full sales file |
| [Improvement Characteristics x54s-btds](https://catalog.data.gov/dataset/assessor-single-and-multi-family-improvement-characteristics), unspecified | PIN, tax year, assessment card, class203, assessed sqft and necessary single-card/area validation; prior-year proxy only | Selected assessed area, assessment year, relative area difference; truthful subject limitations | Internal card/PIN, unneeded building attributes, proof-of-building claim |
| [Historical Parcel Universe nj4t-kc8j](https://catalog.data.gov/dataset/assessor-parcel-universe), unspecified | PIN/year, township and neighbourhood, coordinates only for justified exploratory fallback; approximate parcel centroid | Match category, permitted coarse explanation; status and limits | Raw comparable PIN, centroid, exact location, geometry, neighbourhood code if identifying; no rooftop assertion |
| [Parcel Addresses 3723-97qp](https://catalog.data.gov/dataset/assessor-parcel-addresses), unspecified | PIN/year, minimum situs label to resolve explicitly selected subject, ambiguity handling; March 2026 publication not historical availability | Authorised subject-only selected address/label if essential and expressly within approved scope; no proof of title or current unsold coverage | Comparable addresses, owner/taxpayer/mail/contact fields, address-directory export, source lookup token exposed as identifier |

The earlier production readiness address status was aggregate-only; the later four-source disposable rehearsal qualified 137 selected keys and 59 historical subject lookups, not a durable resolver or blanket address permission. Never ingest names, contact, taxpayer/owner mailing fields, photos, financing or unnecessary identifiers. Browser fixtures are not publisher data; historical-shape rehearsal projection remains invented-only and redacted. The selected evidence combinations (sale price/date/area, geography, asking-price/subject label, note) can still facilitate linkage even after removing PINs, and tokens are not anonymity. Output risk review and suppression/withholding required; no public real-property recruiter demo or buyer accounts.

### 3. Operation-specific acceptance matrix

Each of the four sources is evaluated against each operation; the rows below apply individually, not a collective licence. C = conditional documentary research support, **not accepted future access**; U = unresolved permission or applicability, **blocked in this project**; X = excluded by current project scope (not a legal prohibition). Prior bounded temporary approvals were specific, not recurring authority.

| Operation | Sales | Characteristics | Universe | Addresses | Conditions / rationale |
| --- | --- | --- | --- | --- | --- | --- |
| Public catalogue/metadata research | C | C | C | C | Retained documentation only, no source API or row request in this slice |
| New bounded real acquisition and temporary analysis | C | C | C | C | Portal research signal; specific field/operation scope, applicable terms, independent approval/protection and limits before any attempt. Existing conditional Cook extraction not consumed or triggered. |
| Internal linkage/deduplication in approved temporary research | C | C | C | C | SOP analytical linkage signal; purpose/minimisation, scope, authorised keys, source provenance, correction and retention required; no new join executed |
| Durable owner-only cloud cache and frozen real investigation/shortlist | U | U | U | U | Documented right for storage and derived retention, encryption, actual operator/access/backup/disposal gates; existing invented acceptance does not transfer |
| Owner-only redacted individual evidence/subject lookup | U | U | U | U | Exact field combinations and identity/disclosure risk, authorised purpose, approved output boundary and provenance; address subject-only |
| Aggregate report/public portfolio statistics | U | U | U | U | Historical aggregate results already recorded; future external aggregate publication and disclosure review distinct, no new approval or reidentifiable small cells |
| Public real property-level demo, downloadable source/derived rows or unrestricted API | X | X | X | X | Not included in current private research scope; requires separate rights and owner release decision |
| Commercial reuse | X | X | X | X | No adopted commercial proposition or permissions |
| Attribution, refresh, correction, expiry and disposal | U | U | U | U | Proposed attribution/operational controls below; actual source terms and compatible protection/disposal not established |

Proposed minimum attribution: Cook County Assessor's Office, exact dataset title/link, revision/retrieval date, transformations, limitations (retrospective, not publication-as-of), non-endorsement. Preserve permission evidence, restrictions and expiry with build lineage. Corrected/revoked data must not be served merely because an old investigation was frozen; authorised restrictive access and approved disposal/correction path govern. Owner-approved real-data maximum 30 calendar days from intake (shorter applicable conditions prevail), no automatic extension or deletion; reconcile encrypted recovery copies, provider residual history and logs before accepting actual data. Do not take a deletion-disallowed snapshot under a shorter retention promise. P0-E owns demonstrated protected operation and retention feasibility, not this matrix. No rekey, provider call, infrastructure change or data deletion.

### 4. Other markets: reuse the existing work, do not duplicate it

| Route | Evidence retained | Permission boundary |
| --- | --- | --- |
| NYC challenger | [P0-C comparison](DATA_FEASIBILITY.md): general open-data policy reuse signal, documented DOF/ACRIS/PLUTO/PAD leads; agency-specific terms may apply. | Exact source/field joins, document-vs-sale grain, historical attributes, addresses, reuse/retention and safe output not established. No data experiment or final market. |
| England/Wales secondary | Retained PPD non-address OGL signal and separate address/lookup and EPC terms. | No inferred OGL for linked addresses, UPRN linkage, EPC or third-party intellectual property. Need specific rights, compatible dated coverage and entry before experimental proposal; no accounts or downloads. |

Apply the same noncompensatory operation gates but jurisdiction-specific law; do not transpose POPIA/MPRA to Cook publishers or assume foreign data is exempt from applicant-side privacy obligations. Later legal review must resolve applicable jurisdiction, responsible party/operator roles, cross-border/provider conditions and subject rights where relevant. No legal advice/clearance claimed.

### 5. Indispensable decisions and handoff

Unresolved Cook gate: applicable source-specific terms/licence or authoritative clarification covering minimal fields, research/joins, temporary vs owner-only durable hosted storage and protected recovery, exact redacted private evidence including subject lookup, permitted aggregate publication, attribution, correction/retention/disposal, hosting restrictions. Existing [unsent narrow clarification above](#26-november-2026-public-terms-reconciliation-and-narrow-clarification) retained, no new draft or contact, owner deferred. Do not assert all four require separate written permissions as a universal legal rule: a sufficiently applicable published grant can resolve an operation; unresolved or conflicting terms require review. If permission only supports temporary research, no persistent real application; if aggregate-only, no individual evidence; if source conditions contradict R0/protection/retention, do not ingest. No blanket acceptance via owner intent.

**P0-D.1 complete as documentary reconciliation. P0.5/P0.7 remain blocked.** Next bounded P0-D.2 privacy and ethical operational policy delta: reconcile existing SA3 and Cook proposed controls into one minimum purpose, access, minimisation, disclosure, correction, incident, retention and source revocation policy for the intended noncommercial single-owner research and fictional public demonstration; distinguish design from actual compliance and legal approval. Do not repeat rights/source research without new evidence; then P0-D conditional review and P0-E operational feasibility only if justified. This is a bounded continuation of original P0-D deliverable, not a new mandatory phase. No external contact, property acquisition, infrastructure, code, final market, deployment or phase credit. Original P0 94%, weighted 87.1%, R0; all full phase gates open.

## 27 November 2026 | Pinelands local reference sources

| Source | Access and measured evidence | Qualification / permitted scope |
| --- | --- | --- |
| HPI-DATA-010 [City Land Parcels](https://odp-cctegis.opendata.arcgis.com/datasets/cctegis::land-parcels/about) | R0 filtered portal GeoJSON; 3,442 features; 3,430 unique-key and 3,421 spatial candidates; registration/audit owner-observed | Private reference, not title, historical geometry or dwelling proof; review before 27 December or earlier terms |
| HPI-DATA-011 [GV2025](https://web1.capetown.gov.za/web1/gv2025/SearchProperty) | R0 client-side export of 839 already-loaded reported sales; 791 positive prices; 420 screened erf-style rows; 409 unique parcel candidates; registration/audits inferred from successful command return | Private noncommercial research; registration date, market-sale status, historical area, coverage and independent identity unresolved; review before 27 December or earlier terms |

[Data Manager evidence](../engineering/DATA_MANAGER_V1.md#hpi-data-011-actual-identity-feasibility-milestone-27-november-2026) and [owner authority](../DECISIONS.md#hpi-data-011-combined-registration-and-identity-feasibility-authority-27-november-2026). Exact portal-specific reuse terms not independently verified; no public/hosted buyer display, commercial redistribution, persistent join or valuation/model authority. Acquisition feasibility is no longer the only blocker; identity and event/temporal semantics plus rights/protection and final scope remain. Cook research and prior permissions unchanged.
