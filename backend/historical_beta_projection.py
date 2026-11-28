"""Internal private-beta field preparation; not a route or release grant.
Only the offline historical rehearsal calls this pure projection. The caller
must verify the sealed build and use one repeatable-read transaction. No
permission or source-kind switch is accepted from a browser.
"""
from datetime import date
from math import isfinite
from backend.curated_ingestion_candidate import ImportRefused

def require(ok):
    if not ok:raise ImportRefused("Historical beta field projection refused")

def _money(cents):
    require(type(cents) is int and 2_000_000<=cents<=500_000_000)
    return f"{cents//100}.{cents%100:02d}"

def project_rehearsal(result,selected,transaction_ids,candidates,ids):
    """Explicit allowlist. Use only on code-generated historical rehearsal input.
    No publisher attribution or public-display permission is asserted.
    """
    build=result["data_build"]
    require(build["source_kind"]=="historical_research"
            and build["public_property_display_approved"] is False
            and build["historical_as_of_verified"] is False
            and result["evidence_details_redacted"] is True and result["comparables"]==[]
            and result["valuation"] is None and len(selected)==result["selected_count"])
    status,tier,count=result["status"],result["tier"],len(selected)
    require((status=="supported_neighbourhood" and tier=="same_neighborhood" and 3<=count<=5)
            or (status=="exploratory_spatial" and tier=="spatial_fallback" and 3<=count<=5)
            or (status in ("insufficient_data","out_of_coverage") and tier=="none" and count==0))
    analysis=date.fromisoformat(result["analysis_date"])
    require(analysis.year in (2024,2025))
    records={(r["pin"],r["doc_no"],r["sale_date"]):r for r in candidates}
    seen=set();sales=[]
    for rank,item in enumerate(selected,1):
        key=(item["pin"],item["document"],item["sale_date"])
        require(key in records and len(transaction_ids.get(key,[]))==1 and item["pin"] not in seen)
        seen.add(item["pin"])
        _,snapshot,cents=transaction_ids[key][0]
        row=records[key];when=date.fromisoformat(item["sale_date"])
        age=item["age_days"];area=row["sqft"];diff=item["size_difference_pct"];year=item["characteristics_year"]
        require(snapshot==ids["sales"] and row["build_id"]==build["build_id"]
                and row["class"]=="203" and row["township_code"]=="17"
                and type(age) is int and age==(analysis-when).days and 1<=age<=365
                and type(year) is int and year==when.year-1
                and type(area) in (float,int) and isfinite(area) and 1000<=area<=1800
                and type(diff) in (float,int) and isfinite(diff) and 0<=diff<=25
                and type(item["same_neighborhood"]) is bool
                and (tier!="same_neighborhood" or item["same_neighborhood"]))
        sales.append({"rank":rank,"sale_date":when.isoformat(),"sale_price_usd":_money(cents),
                      "assessment_year":year,"assessed_area_sqft":area,"area_difference_pct":diff,
                      "age_days":age,"location_evidence":"same_neighbourhood" if item["same_neighborhood"] else "exploratory_spatial"})
    return {"contract_version":"historical-beta-evidence-v1","source_kind":"historical_shape_rehearsal",
            "status":status,"tier":tier,"analysis_date":analysis.isoformat(),"selected_count":count,
            "sales":sales,"asking_price_usd":result["subject"]["asking_price_usd"],
            "asking_price_source":"buyer_reported","buyer_reported_area_sqft":result["subject"]["building_area_sqft"],
            "provenance":{"publisher_attributed":False,"build_revision":build["build_id"],
                          "retrieved_at_utc":build["built_at_utc"],"historical_asof_verified":False,
                          "public_display_approved":False},
            "building_identity_verified":False,"geometry_available":False,"valuation":None}
