# Data feasibility: research state and audit contract

**Source:** Adapted from `docs/portfolio/house-price-data-feasibility.md` in `Sonkhe-Shongwe/sa-tech-grad-playbook.` (reviewed 22 November 2026). The original research note remains preserved. **Status updated 22 November 2026:** Phase 0, Phase 1 and Phase 2 live experiments **have been completed** in GitHub Actions. See [verified findings](PHASE2_CLOUD_AUDIT_RESULTS.md) and the [current checkpoint](../CHECKPOINT.md). This note retains the original research questions, not outdated claims about whether the API works.

## Working conclusion

**Cook County township 17 (Evanston), Class 203** is now the measured *research pilot* because the publisher offers parcel sales, historical residential characteristics and the Historical Parcel Universe. It is **not yet the approved public app geography or class boundary**. The official dataset queries have succeeded, but their rights and point-in-time semantics remain under review. **New York City** is the first alternative for a comparable-sales explorer; the UK Land Registry is another potential transaction source. A **South African** property-level product needs independently verified completed-sale data, attributes and reuse rights. Do not substitute municipal valuations, asking prices or aggregate indices for individual sale records.

## Primary sources

- Parcel sales: https://datacatalog.cookcountyil.gov/d/wvhk-k5uv
- Historical residential improvement characteristics: https://datacatalog.cookcountyil.gov/d/x54s-btds
- Historical Parcel Universe: https://datacatalog.cookcountyil.gov/d/nj4t-kc8j
- Assessor class definitions: https://www.cookcountyassessoril.gov/classifications-real-property
- Assessor modelling documentation: https://gitlab.com/ccao-data-science---modeling/models/ccao_res_avm
- NYC rolling/annual property sales: https://www.nyc.gov/site/finance/property/property-rolling-sales-data.page
- HM Land Registry price paid data: https://www.gov.uk/guidance/about-the-price-paid-data
- England/Wales EPC download service: https://get-energy-performance-data.communities.gov.uk/
- King County assessments: https://info.kingcounty.gov/assessor/datadownload/
- SA DeedsWeb: https://www.gov.za/services/services-residents/place-live/subscribe-deedsweb
- Stats SA Residential Property Price Index: https://www.statssa.gov.za/?PPN=P0160&SCH=74476&page_id=1854
- Lightstone comparable valuation description: https://www.lightstone.co.za/AVM/content/help/default.aspx

## Data-grain risks

The sales table records parcel-level references to transactions. One sale can reference multiple parcels. Historical characteristics records are by parcel, assessment year and individual building (card), so a parcel-year may have multiple rows. A naive join can duplicate a sale or attach an entire transaction price to one building. PIN must be preserved as a zero-padded 14-digit string.

The county's reporting pipeline is delayed, and data definitions and filtering have changed. Some past characteristic rows may have been revised after the sale date; an earlier tax year by itself is not proof against time leakage.

## Original feasibility experiment (now executed in phases)

The following eight steps describe the original feasibility contract. The extractor, Class 203 enrichment and baseline comparison **were executed** on 22 November 2026, but not all legal, identity/time or deployment gates are satisfied. Step 8 remains exploratory because no leakage-safe ML model has been accepted.

1. Download **bounded, dated source snapshots** and record the extraction parameters, schema, update timestamps, record counts and truncation.
2. Identify actual transaction grain; audit duplicates, multi-parcel and multi-building records separately. Keep each source row traceable.
3. Choose conservative eligibility rules for arm's-length candidate sales, documented exclusions and class-code verification from official definitions.
4. For each included sale, join to an appropriate historical characteristic row that is actually available when evaluated, or explicitly mark the pilot's time-validity limitation.
5. Select one submarket and one verified single-family class; test 20 representative historical properties for at least 3 eligible earlier comparables in an exploratory 12-month window, with explicit matching rules.
6. Inspect 2 or 3 traceable cases including weak-data and multi-parcel exclusion examples. Record why a candidate was included or excluded.
7. Verify dataset-specific reuse, attribution, storage and displayed-field terms before public deployment.
8. If the first segment passes, compare a simple comparable-based price baseline with any ML model on a later holdout. Evaluate error, interval coverage and width separately.

## Go/no-go

- **Proceed to a comparable explorer** only when the join, source rights, property classes and measurable comparable coverage support a useful buyer journey.
- **Include price prediction** only when chronological evaluation demonstrates benefits and interpretable limits relative to a baseline.
- **Narrow or pivot** if the data are sparse, joins are unstable or display rights cannot be established. Record the reason rather than fabricating sale evidence or pretending a synthetic dataset is a current property market.

## Verified findings (22 November 2026)

| Measurement | Live result |
| --- | ---: |
| Extracted historical sale and building rows | 3,539 and 39,401 |
| Sales passing provisional screens | 2,583 |
| Accepted prior-tax-year building joins | 1,285 |
| Enriched Class 203 matched sales | 273 |
| Historical 2024 Class 203 subjects analysed | 83 |
| Same-neighbourhood subjects with >=3 prior comparables | 66 |
| Additional subjects with >=3 comparables using exploratory 2 km fallback | 17 |

The three-phase source audit and **42 offline tests** passed in [GitHub Actions run 45046687782](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782). The fallback-only 17 produced worse retrospective median-price errors than the township-wide baseline on those same cases. Consult [Phase 0](PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1](PHASE1_CLOUD_AUDIT_RESULTS.md) and [Phase 2](PHASE2_CLOUD_AUDIT_RESULTS.md) before citing this experiment.

## Remaining limitations and gate

Historical source records may be late-reported or backfilled; the prior-tax-year join is not a verified as-of release snapshot. The sale screens are analyst proxies, not independent arm's-length certification. The Class 203 property type and individual homes' condition need careful eligibility review. **Source-specific reuse/display rights remain unresolved**. There is no production database import, buyer-facing app, trained ML price model or accepted current valuation.

**Current decision:** Continue controlled engineering work on a clearly labelled historical comparable explorer. Do not treat the research extraction or 83-subject results as approval to publish property-level facts or current-market valuations.

## 26 November 2026 | P0-C source, field and grain inventory

**Status:** first bounded P0-C task complete as source/code/documentation review; actual alternative coverage, temporal/entry feasibility, rights and final market remain open. Read [B.5 rationale](../product/COMPETITIVE_INTELLIGENCE_2026-11-26.md#b5--market-rationale-and-workstream-review), [product brief](../product/PRODUCT_BRIEF.md), [P0 directive](../engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md), [source register](SOURCE_REGISTER.md), [FR qualification](../engineering/FULL_RELEASE_QUALIFICATION_V1.md), [private beta](../engineering/PRIVATE_REAL_DATA_BETA_V1.md), [original audit implementation](../../audit/phase0/audit.py), [enrichment](../../audit/phase1/expand.py), [matcher](../../audit/phase2/matcher.py) at development 3238290. Previous 22 Nov record above is historical, not a claim that fictional application development is absent today. No change to approved two-to-three-home scope, selection policy, projection or data-use boundary. No property data queries/downloads, schema migration, contacts or new service resources.

### Minimum semantic data contract (requirements analysis, not an approved schema)

E = essential for the existing evidence workflow; C = conditional on approved matching/display policy; O = optional enhancement, not required for the present comparator. Distinguish internal identity/provenance from redacted buyer display. All real fields remain subject to P0-D permission, even if essential. Neither new provider metadata nor a nonempty field proves quality.

| Semantic requirement | Cook County: actual audited schema/code | NYC: documented candidate | Critical gap / treatment |
| --- | --- | --- | --- |
| E transaction identity and cardinality | wvhk-k5uv pin, doc_no, sale_date; reject multi-sale or parcel count !=1; dedupe PIN/document/date | DOF rolling usep-8jbt and annual w2pb-icbu BBL/date/price; ACRIS Master bnx9-e6tj and Legals 8h5j-fqxa document_id links candidate document and parcel evidence | Published sales-file glossary does not establish a transaction ID or one-lot-per-transfer rule. Positive price and one row do not prove standalone transaction; need verified reconciliation or fail closed. Never synthesize a unique transaction ID from price/date alone. |
| E recorded price/date and currency | sale_price, sale_date; research screen USD 20k–5m, exact cents required by later runtime | DOF sale price/date in USD; zero consideration documented as noncash transfer | Keep reported sale distinct from asking price and assessments; check cent parsing, date semantics, duplicates and exceptional sales. ACRIS document_amt is not generically a sale price; mortgages and other instruments excluded. |
| E sale eligibility | is_multisale, num_parcels_sale, sale_filter_less_than_10k, sale_filter_deed_type, sale_filter_same_sale_within_365; missing invalid required flags reject | Zero/positive consideration; ACRIS document type, full/partial lot and parcel cardinality candidate; code mapping catalogue | No verified equivalent to Cook screening flags. Validate document type, multi-lot/partial transfer, non-market and repeated-transfer screen; no independent arm's-length certification. Do not copy analyst price bounds unchanged. |
| E property identity/class | 14-digit normalized PIN; historical x54s-btds pin/year/card/class; one-storey 203 (1,000–1,800 sq ft) | Borough/block/lot (BBL), DOF class at sale and present; A2 one-storey permanent one-family dwelling is a candidate, not equivalent class; units and lot identity | Need fixed-width source-specific identity (BBL 1+5+4 digits), no silent coercion or cross-market reuse of PIN checks; confirm lot lifecycle, class drift and one-building eligibility, no final NYC area/class approved. |
| E physical similarity, units | char_bldg_sf, one prior tax-year building row, card/multicard checks; research 250–20,000 sq ft plausibility and ±25% match | DOF gross square feet, residential/commercial/total units, year built; PLUTO tax-lot data and versioned archive; candidate additional building count | Gross area is not necessarily comparable to Cook building-area definition or living area. Multiple buildings/units per lot can invalidate comparison even if one residential unit. Check measurement definitions, missing/zero, timing, cardinality and scope; never mix inconsistent area definitions. |
| E local geography | township_code and prior-year nj4t-kc8j nbhd_code; unique PIN/year join | DOF borough and assessor neighbourhood; published boundaries may differ from common neighbourhood names; PLUTO/MapPLUTO tax-lot context | Define candidate locality and stable, dated category; no township-to-borough policy transfer without evidence. |
| E source time and provenance | sale date, prior-year assessment/universe, dataset revision/extraction timestamp, rule/build identity | DOF sale date and at-sale class; other file attributes may not be at-sale; DCP catalogue documents previous PLUTO releases | Archive release availability is promising, not proof each input existed at that sale date. Record actual source publication/revision, observation and analysis dates; reject future information or label retrospective limitation. |
| E buyer property entry | 3723-97qp PIN/year and minimal situs fields (e.g. prop_address_full); bounded prior cohorts only; user selection required | NYC DCP Property Address Directory (PAD), ACRIS address/parcel lookup and BBL; DOF sale address/zip alone not an adequate current-property index | Need explicit candidate resolution and supported class/area verification for unsold subjects; no guessed address, no owner/mailing fields. Historical sale address != verified current building. |
| C geometry for exploratory fallback | nj4t-kc8j lat/lon, approximate parcel centroid; matcher bounds hard-coded Illinois, distance 2 km experimental | PLUTO/MapPLUTO lot geography candidate, coordinate provenance/accuracy untested | Not required for strict local match; necessary only for approved spatial policy. Never reuse hard-coded Illinois range for NYC or imply rooftop location. No raw comparable coordinates in private projection. |
| C/O explanatory attributes | optional char_yrblt, char_beds, char_fbath, char_hbath, char_rooms, char_land_sf; age in existing narrow private projection | year built, land area and unit counts documented; bedrooms/baths not established in core sales file | Age remains existing proposed display where available; no new matching requirement or silent removal. Keep unknown explicit; optional fields cannot compensate for missing essential ones. |
| E buyer context (not source) | user-reported asking price, analysis date, chosen property, notes, frozen comparison | same conceptual requirement if new market approved | Separate from publisher facts, retain exact source/build/rule linkage; approved max 30 days from real intake, no automatic deletion or renewal. No display of raw comparable PIN, document, address or geometry. |

### NYC source documentation (reviewed 26 November; no records)

- [DOF rolling sales](https://www.nyc.gov/site/finance/property/property-rolling-sales-data.page), [annual sales](https://www.nyc.gov/site/finance/property/property-annualized-sales-update.page), [glossary](https://www.nyc.gov/site/finance/property/glossary-property-sales.page) full text and [class codes](https://www.nyc.gov/assets/finance/jump/hlpbldgcode.html) full text. The official glossary distinguishes lot vs address, class at present vs at sale, unit counts, square feet, sale price/date and no-cash transfers. [Rolling catalogue](https://catalog.data.gov/dataset/nyc-citywide-rolling-calendar-sales) search excerpt only, full fetch failed; [annual catalogue](https://catalog.data.gov/dataset/nyc-citywide-annualized-calendar-sales-update) full text identifies w2pb-icbu. Public files/schema evidence, no completeness/actual record distribution or licence confirmation.
- ACRIS [City Register scope](https://www.nyc.gov/site/finance/taxes/property-recording-property-related-documents.page), [land records FAQ](https://www.nyc.gov/site/finance/property/land-records-faqs.page), [document detail](https://a836-acris.nyc.gov/AcrisHelp/docsearch/Documents/detailview.htm) and [property tab](https://a836-acris.nyc.gov/Acrishelp/coverpage/Documents/property_tab_referen.htm) search excerpts; detail/tab fetch failed. Official Master catalogue/schema search excerpt bnx9-e6tj and [Legals catalogue](https://data.cityofnewyork.us/City-Government/ACRIS-Real-Property-Legals/8h5j-fqxa/data), [document codes](https://catalog.data.gov/dataset/acris-document-control-codes) search excerpts. Master amount described as principal debt/obligation; documents can involve multiple properties. No assumed exact DOF-to-ACRIS join or comparable transaction amount. Staten Island County Clerk performs separate recording functions; do not assume four-borough ACRIS coverage extends to all NYC even though RPTT returns use ACRIS. Queens is a provisional source-compatibility lead only, not a chosen geography or measured cohort.
- [PLUTO catalogue](https://catalog.data.gov/dataset/primary-land-use-tax-lot-output-pluto) full text: tax-lot grain, previous versions advertised, catalogue snapshot May 2026 version 26v1, not a claim of latest. [MapPLUTO catalogue](https://catalog.data.gov/dataset/primary-land-use-tax-lot-output-map-mappluto) and [PAD catalogue](https://catalog.data.gov/dataset/property-address-directory) search excerpts. PLUTO 64uk-42ks; PAD bc8t-ecyu. Do not download archives or assume all dated files, joins, field definitions or terms verified. [City Council BBL methodology](https://council.nyc.gov/data/evictions/) retained from B.4.
- All official documentation observations are distinct from HPI data measurements. No real row, data API resource call, account or individual address lookup performed. Reuse general NYC policy evidence from B.4; P0-D must address every needed source/field, including ACRIS and PAD; no rights granted here.

### Architecture consequence and stopping criterion

NYC's sale-file attributes could reduce separate enrichment joins, but credible transaction and building identity may require more source reconciliation than Cook's explicit document/eligibility flags. It is not a demonstrably simpler stack yet. The existing matcher hard-codes class 203, township, PIN, Illinois coordinate bounds and pilot policies; if market change justified, first qualify source semantics and then refactor only affected contracts, preserving exact money, earlier-only/price-free matching, unique properties, source versions and abstention. No speculative multi-market framework or new tables now.

This source/field/grain task meets its bounded criterion: essential/conditional/optional field map, both candidates, source grain, identity, units, time, eligibility and gaps, existing code/actual evidence separated from documentation. Cook County remains only measured incumbent; NYC minimum contract is **plausible but not established** (transaction reconciliation, single-building identity, temporal attributes, entry, coverage and rights unproven). No migration, approval, new acquisition or phase credit. Next P0-C: consolidate actual Cook County cohort funnels, address/identity and timing evidence across historical experiments and later qualification, quantify supported vs exploratory vs unsupported and specify the exact retrospective boundary/abstention; do not repeat completed extracts. Then assess remaining alternative risks and indispensable empirical gaps, stop before unauthorised acquisition. P0 94%, overall 87.1%, R0.
