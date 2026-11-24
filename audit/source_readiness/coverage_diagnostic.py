"""FA1: count-only source coverage checks; never retrieves individual rows.
Does not prove parcel-level join eligibility or historical publication time.
"""
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
import json
from audit.phase0.audit import SALES_ID,BUILDINGS_ID
from audit.source_readiness.cohort_audit import meta,query
from audit.source_readiness.address_audit import validated_counts

def counts(dataset,where,fields):
    if "pin" not in fields:raise ValueError("Missing count field")
    selected="count(*) as row_count,count(pin) as nonnull_pin_count,count(distinct pin) as distinct_pin_count"
    return validated_counts(query(dataset,{"$select":selected,"$where":where,"$limit":1},
        {"row_count","nonnull_pin_count","distinct_pin_count"},1),None)

def main():
    report={"status":"blocked","scope":"township 17, 2024 and 2025 sale dates; 2023 and 2024 assessment years",
        "extracted_at_utc":datetime.now(timezone.utc).isoformat(),"historical_asof_verified":False,
        "publication_approved":False,"join_eligibility_verified":False}
    try:
        before={d:meta(d) for d in (SALES_ID,BUILDINGS_ID)}
        sf,bf=before[SALES_ID][0],before[BUILDINGS_ID][0]
        if not {"pin","township_code","sale_date"}<=sf or not {"pin","township_code","year","class"}<=bf:
            raise ValueError("Missing scope field")
        sales={};building={}
        for y in (2024,2025):
            scope=f"township_code = '17' AND sale_date >= '{y}-01-01T00:00:00' AND sale_date < '{y+1}-01-01T00:00:00'"
            sales[str(y)]={"all":counts(SALES_ID,scope,sf)}
            if "class" in sf:sales[str(y)]["reported_class203"]=counts(SALES_ID,scope+" AND class = '203'",sf)
        for y in (2023,2024):
            scope=f"township_code = '17' AND year = {y}"
            building[str(y)]={"all":counts(BUILDINGS_ID,scope,bf),
                "class203":counts(BUILDINGS_ID,scope+" AND class = '203'",bf)}
        if before!={d:meta(d) for d in before}:raise ValueError("Source revision changed")
        report.update(status="completed",sales=sales,assessment=building,
                      source_update_epochs={d:before[d][1] for d in before})
    except Exception as exc:report["error_type"]=type(exc).__name__
    Path("reports").mkdir(exist_ok=True)
    Path("reports/coverage-diagnostic.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    if report["status"]!="completed":raise SystemExit(1)
if __name__=="__main__":main()
