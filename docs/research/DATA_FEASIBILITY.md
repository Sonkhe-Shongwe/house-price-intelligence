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
