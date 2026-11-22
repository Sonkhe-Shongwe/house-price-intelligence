# Source register

| Source | URL | Intended use | Verification still needed |
| --- | --- | --- | --- |
| Cook County assessor parcel sales | https://datacatalog.cookcountyil.gov/d/wvhk-k5uv | Completed transaction information | Schema, flags, late reporting, licences, current download |
| Cook County historical residential characteristics | https://datacatalog.cookcountyil.gov/d/x54s-btds | Building attributes by parcel/year/card | Join cardinality, field coverage, historical publication |
| Dataset metadata (sales) | https://datacatalog.cookcountyil.gov/api/views/wvhk-k5uv.json | API fields / source update timestamps | Runtime availability and changes |
| Dataset metadata (buildings) | https://datacatalog.cookcountyil.gov/api/views/x54s-btds.json | API fields / source update timestamps | Runtime availability and changes |
| Assessor valuation/model documentation | https://gitlab.com/ccao-data-science---modeling/models/ccao_res_avm | Reference methodology | Not all features present in two source tables |
| Cook County data policy | https://datacatalog.cookcountyil.gov/stories/s/About-Open-Data/pvqg-z4sc/ | General open-data policy | Dataset-specific display/attribution rights |
| NYC property sales | https://www.nyc.gov/site/finance/property/property-rolling-sales-data.page | First fallback | Classes, prices, size, reuse |
| HM Land Registry | https://www.gov.uk/guidance/about-the-price-paid-data | UK fallback | Record linkage, scope |
| UK EPC | https://get-energy-performance-data.communities.gov.uk/ | Candidate additional attributes | Access and licence |
| SA DeedsWeb | https://www.gov.za/services/services-residents/place-live/subscribe-deedsweb | South African data lead | Paid access, reuse, property attributes |

**Provenance:** Original leads in SA Tech Graduate Playbook, reviewed 22 November 2026. Treat source listings as research leads, not proof that they support the specific product displays or joins. No downloaded datasets are included in this repo.
