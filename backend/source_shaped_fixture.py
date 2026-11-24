"""Trusted, code-generated fictional source-shape replay; never external input.
The shape-only dataset identifiers and metadata exist solely to exercise intake.
Persisted fixture manifests are synthetic and never claim publisher provenance.
"""
from copy import deepcopy
from backend.real_source_intake import DATASETS, REQUIRED, OPTIONAL, prepare_intake

def replay_rows():
    rows={role:[] for role in DATASETS}
    prices=("550000.00","487500.01","542750.02","519900.03")
    dates=("2024-06-01","2024-01-18","2024-03-12","2024-05-09")
    areas=(1600,1500,1720,1650)
    for i,(price,when,area) in enumerate(zip(prices,dates,areas),1):
        pin=f"{i:014d}"
        rows["sales"].append(dict(pin=pin,sale_date=when+"T00:00:00",sale_price=price,doc_no=f"REPLAY-FICT-{i}",
            township_code="17",is_multisale=False,num_parcels_sale="1.0",sale_filter_less_than_10k=False,
            sale_filter_deed_type=False,sale_filter_same_sale_within_365=False))
        rows["assessment"].append(dict(pin=pin,year="2023.0",card="1",**{"class":"203"},
            township_code="17",char_bldg_sf=str(area)))
        rows["geography"].append(dict(pin=pin,year="2023.0",nbhd_code="FICT",lat="42.04",lon="-87.68"))
        rows["address"].append(dict(pin=pin,year="2023.0",prop_address_full=f"{i*10} Fictional Replay Lane, Demonstration District"))
    meta={dataset:{"epoch":1,"fields":sorted(REQUIRED[role]|OPTIONAL[role])} for role,dataset in DATASETS.items()}
    plan=prepare_intake(rows=rows,metadata_before=meta,metadata_after=deepcopy(meta),
                        extracted_at_utc="2026-11-24T00:00:00Z")
    # Only this generated sample enters the existing fixture importer. Never
    # use this projection on an arbitrary historical plan or external extract.
    result={role:[] for role in DATASETS}
    for sale in plan["sales"]:
        result["sales"].append({k:v for k,v in sale.items() if k!="assessment_year"})
    for p in plan["parcel_years"]:
        result["assessment"].append({k:p[k] for k in ("pin","tax_year","card_number","assessor_class","building_area_sqft")})
        result["geography"].append({k:p[k] for k in ("pin","tax_year","neighborhood_code","latitude","longitude")})
        if p["address_state"]!="one_nonblank":
            raise ValueError("Fictional replay address unexpectedly unresolved")
        result["address"].append({k:p[k] for k in ("pin","tax_year","display_address")})
    return result
