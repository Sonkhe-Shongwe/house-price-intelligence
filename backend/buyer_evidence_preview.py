"""Fixture-only minimised buyer evidence projection, never a release grant.
Read through the existing frozen-evidence boundary. No generic dictionary
passthrough, user-selected fields, publisher attribution or new matching.
"""
from datetime import date,datetime
from math import isfinite
import re
from backend.disclosure_guard import DisclosureDenied
from backend.synthetic_investigation_store import SyntheticInvestigationStore

def require(condition):
    if not condition:
        raise DisclosureDenied("Buyer evidence preview refused")

def money(value):
    require(isinstance(value,str) and re.fullmatch(r"(?:0|[1-9][0-9]*)\.[0-9]{2}",value) is not None)
    return value

def project_buyer_evidence(record):
    """Explicit output schema. Input must already be reopened by trusted store."""
    build=record["data_build"]
    require(record["contract_version"]=="p3-draft-v0.3"
            and build["source_kind"]=="synthetic_fixture"
            and build["historical_as_of_verified"] is False
            and build["public_property_display_approved"] is False
            and record["evidence_details_redacted"] is False
            and record["valuation"] is None)
    iid=record["investigation_id"]
    require(isinstance(iid,str) and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",iid) is not None)
    status,tier,count=record["status"],record["tier"],record["selected_count"]
    require(type(count) is int and isinstance(record["comparables"],list)
            and len(record["comparables"])==count)
    require((status=="supported_neighbourhood" and tier=="same_neighborhood" and 3<=count<=5)
            or (status=="exploratory_spatial" and tier=="spatial_fallback" and 3<=count<=5)
            or (status in ("insufficient_data","out_of_coverage") and tier=="none" and count==0))
    analysis=date.fromisoformat(record["analysis_date"])
    require(analysis.isoformat()==record["analysis_date"])
    stamp=build["built_at_utc"]
    require(isinstance(stamp,str) and datetime.fromisoformat(stamp.replace("Z","+00:00")).utcoffset() is not None)
    bid=build["build_id"]
    require(isinstance(bid,str) and re.fullmatch(r"[a-zA-Z0-9._-]{1,100}",bid) is not None)
    sales=[]
    seen=set()
    for rank,row in enumerate(record["comparables"],1):
        when=date.fromisoformat(row["sale_date"])
        age=row["age_days"]; diff=row["size_difference_pct"]; year=row["characteristics_year"]
        require(when.isoformat()==row["sale_date"] and type(age) is int and age==(analysis-when).days
                and 1<=age<=365 and type(diff) in (int,float) and isfinite(diff) and 0<=diff<=25
                and type(year) is int and year==when.year-1 and type(row["same_neighborhood"]) is bool
                and (tier!="same_neighborhood" or row["same_neighborhood"]))
        require(row["pin"] not in seen)
        seen.add(row["pin"])
        sales.append({"rank":rank,"sale_date":when.isoformat(),"sale_price_usd":money(row["sale_price_usd"]),
                      "age_days":age,"area_difference_pct":diff,"assessment_year":year,
                      "location_evidence":"same_neighbourhood" if row["same_neighborhood"] else "exploratory_spatial"})
    asking=record["subject"]["asking_price_usd"]
    return {"contract_version":"buyer-evidence-preview-v1","investigation_id":iid,
            "source_kind":"synthetic_fixture","status":status,"tier":tier,"analysis_date":analysis.isoformat(),
            "selected_count":count,"sales":sales,"asking_price_usd":None if asking is None else money(asking),
            "asking_price_source":"buyer_reported","provenance":{"build_id":bid,"built_at_utc":stamp,
                 "publisher_attributed":False,"historical_asof_verified":False,"public_display_approved":False},
            "geometry_available":False,"building_identity_verified":False,"valuation":None}

def buyer_evidence_preview(store,investigation_id):
    require(isinstance(store,SyntheticInvestigationStore))
    return project_buyer_evidence(store.reopen(investigation_id))
