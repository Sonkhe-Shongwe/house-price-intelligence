# Property data source register

**Updated:** 22 November 2026. URLs and dataset IDs were researched for the pilot. `Verified extraction` means the dataset was successfully queried in the cloud pipeline, **not** that every row is time-correct, legally redistributable or independently verified.

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

## Provenance and control rules

- Pilot dates: sales from **2022-01-01 inclusive to 2025-01-01 exclusive**, Cook County township code `17`; characteristics and geography are linked to the **prior tax year as a proxy**.
- Verified source run: [22 Nov 2026 cloud audit](https://github.com/Sonkhe-Shongwe/house-price-intelligence/actions/runs/45046687782). See the detailed [Phase 0](PHASE0_LIVE_AUDIT_RESULTS.md), [Phase 1](PHASE1_CLOUD_AUDIT_RESULTS.md), and [Phase 2](PHASE2_CLOUD_AUDIT_RESULTS.md) findings for actual counts and limitations.
- Keep publisher URL, dataset ID, extraction timestamp, query, schema and source update timestamp in the internal research layer; raw records never go in Git or public audit artifacts.
- Review data rights **by source and by displayed field** before storing/distributing property-level records in the buyer-facing app. An open-data catalogue listing alone does not settle permitted use.
- Original fallback-source leads came from the separate SA Tech Graduate Playbook. No fallback dataset has been quietly substituted for Cook County.


## 24 November 2026: address candidate and reuse review
Parcel Addresses `3723-97qp`: https://catalog.data.gov/dataset/assessor-parcel-addresses; first published March 2026 according to catalogue. Contains sensitive-to-product owner/taxpayer/mailing fields; excluded from research queries. Only aggregate-only feasibility authorised. See [production readiness contract](../engineering/PRODUCTION_READINESS_V1.md) for field policy, publisher sources, separate bulk agreement caveat and temporal limitations. No property-level display approval.
