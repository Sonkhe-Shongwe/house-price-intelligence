# Data feasibility: research state and audit contract

**Source:** Adapted from `docs/portfolio/house-price-data-feasibility.md` in `Sonkhe-Shongwe/sa-tech-grad-playbook.` (reviewed 22 November 2026). Original not deleted. The source catalog is independently accessible; the live joined audit **has not been completed**.

## Working conclusion

Try **Cook County, Illinois** first because the same publisher offers parcel sales and historical residential building characteristics. Choose the actual township and property class only after inspecting measured data. **New York City** is the first alternative for a comparable-sales explorer; the UK Land Registry is another potential transaction source. A **South African** property-level product needs independently verified completed-sale data, attributes and reuse rights. Do not substitute municipal valuations, asking prices or aggregate indices for individual sale records.

## Primary sources

- Parcel sales: https://datacatalog.cookcountyil.gov/d/wvhk-k5uv
- Historical residential improvement characteristics: https://datacatalog.cookcountyil.gov/d/x54s-btds
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

## First feasibility experiment

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

## Current limitations

The original record reviewed the publisher documentation but did not verify a complete live join. The Phase 0 script has seven offline tests with fabricated data. **No model, validated valuation, production data import, measured coverage, or actual buyer-facing application currently exists.**
