"""Preregistered chronological 2025 holdout. Aggregate-only, bounded in-memory.
No identifiers, prices for individuals, request URLs or raw errors are emitted.
Current extracts are not historical publication-time snapshots.
"""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from statistics import mean,median
from urllib.parse import urlencode
import json
import re
from audit.phase0.audit import SALES_ID,BUILDINGS_ID,SALES_REQUIRED,SALES_OPTIONAL,BUILDINGS_REQUIRED,BUILDINGS_OPTIONAL,normalize_pin
from audit.phase1.expand import phase0_class203,enrich_joined,prior_comparables,baseline_price,UNIVERSE_ID
from audit.phase2.matcher import match_property,MatchPolicy
from audit.source_readiness.cohort_audit import meta,query

POLICY_ID="holdout-2025-predeclared-v1"
SPECS={
 SALES_ID:(SALES_REQUIRED,SALES_OPTIONAL,"township_code = '17' AND sale_date >= '2024-01-01T00:00:00' AND sale_date < '2026-01-01T00:00:00'","pin ASC,sale_date ASC,doc_no ASC,:id ASC",5000),
 BUILDINGS_ID:(BUILDINGS_REQUIRED,BUILDINGS_OPTIONAL,"township_code = '17' AND year >= 2023 AND year <= 2024","pin ASC,year ASC,card ASC,:id ASC",40000)
}
UNIVERSE_FIELDS={"pin","year","nbhd_code","lat","lon"}
MIN_REPORT=10
def collect(dataset,fields):
    required,optional,where,order,cap=SPECS[dataset]
    if not required<=fields:raise ValueError("Schema mismatch")
    selected=required|(optional&fields)
    out=[]
    while len(out)<cap:
        n=min(2000,cap-len(out))
        batch=query(dataset,{"$select":",".join(sorted(selected)),"$where":where,"$order":order,"$limit":n,"$offset":len(out)},selected,n)
        out.extend(batch)
        if len(batch)<n:return out
    raise ValueError("Incomplete capped extraction")
def universe(keys,fields):
    if not UNIVERSE_FIELDS<=fields or not keys or len(keys)>500:
        raise ValueError("Universe scope refused")
    if any(not re.fullmatch(r"[0-9]{14}",p) or y not in (2023,2024) for p,y in keys):
        raise ValueError("Invalid cohort keys")
    out=[]
    for y in (2023,2024):
        pins=sorted(p for p,year in keys if y==year)
        for i in range(0,len(pins),35):
            batch=pins[i:i+35]
            where="year = "+str(y)+" AND pin IN ("+",".join("'"+p+"'" for p in batch)+")"
            rows=query(UNIVERSE_ID,{"$select":",".join(sorted(UNIVERSE_FIELDS)),"$where":where,"$order":"pin ASC,year ASC,:id ASC","$limit":500},UNIVERSE_FIELDS,500)
            if len(rows)>=500 or any((normalize_pin(r.get("pin")),int(r["year"])) not in {(p,y) for p in batch} for r in rows):
                raise ValueError("Unexpected universe response")
            out.extend(rows)
    return out
def metrics(cases,key):
    pairs=[(r["actual"],r[key]) for r in cases if r[key] is not None]
    if len(pairs)<MIN_REPORT:return {"count":len(pairs),"mae_usd":None,"mdape_pct":None,"suppressed":True}
    errors=[abs(a-p) for a,p in pairs]
    return {"count":len(pairs),"mae_usd":round(mean(errors),2),"mdape_pct":round(median(e/a*100 for e,(a,_) in zip(errors,pairs)),2),"suppressed":False}
def paired(cases,a,b):
    common=[r for r in cases if r[a] is not None and r[b] is not None]
    return {a:metrics(common,a),b:metrics(common,b)}
def evaluate(rows):
    if any(not r["sale_date"].startswith(("2024-","2025-")) for r in rows):raise ValueError("Out-of-window row")
    subjects=[r for r in rows if r["sale_date"].startswith("2025-")]
    if len(subjects)<MIN_REPORT:raise ValueError("Insufficient later cohort")
    cases=[];tiers=Counter()
    for subject in subjects:
        prior=[r for r in rows if r["sale_date"]<subject["sale_date"]]
        baseline=match_property(subject,prior)
        narrow=match_property(subject,prior,policy=MatchPolicy(radius_km=1.0))
        def price(result):
            if any(c["sale_date"]>=subject["sale_date"] for c in result["comparables"]):raise ValueError("Chronological leak")
            return median(c["sale_price"] for c in result["comparables"]) if result["comparables"] else None
        bp=price(baseline);np=price(narrow)
        tiers[baseline["tier"]]+=1
        cases.append({"actual":subject["sale_price"],"current":bp,"radius_1km":np,
            "strict_neighbourhood":bp if baseline["tier"]=="same_neighborhood" else None,
            "township":baseline_price(prior_comparables(subject,prior)),"tier":baseline["tier"]})
    fallback=[r for r in cases if r["tier"]=="spatial_fallback"]
    return {"subjects":len(subjects),"tier_counts":dict(tiers),
        "all_methods":{k:metrics(cases,k) for k in ("current","radius_1km","strict_neighbourhood","township")},
        "paired_current_township":paired(cases,"current","township"),
        "paired_narrow_current":paired(cases,"radius_1km","current"),
        "fallback_current_township":paired(fallback,"current","township"),
        "fallback_narrow_current":paired(fallback,"radius_1km","current"),
        "policy_adopted":False,"valuation_approved":False}
def main():
    report={"status":"blocked","policy":POLICY_ID,"scope":"township 17, class 203, 2024-2025 sales; 2025 subjects; 2023-2024 prior tax years",
            "extracted_at_utc":datetime.now(timezone.utc).isoformat(),"historical_asof_verified":False,"publication_approved":False}
    try:
        report["stage"]="metadata"
        before={d:meta(d) for d in (*SPECS,UNIVERSE_ID)}
        report["stage"]="sales"
        sales=collect(SALES_ID,before[SALES_ID][0])
        report["sales_rows"]=len(sales)
        report["stage"]="buildings"
        buildings=collect(BUILDINGS_ID,before[BUILDINGS_ID][0])
        report["building_rows"]=len(buildings)
        report["stage"]="join"
        cohort=phase0_class203(sales,buildings)
        keys={(r["pin"],r["characteristics_year"]) for r in cohort}
        report["class203_rows"]=len(cohort)
        report["key_count"]=len(keys)
        report["stage"]="universe"
        geo=universe(keys,before[UNIVERSE_ID][0])
        report["universe_rows"]=len(geo)
        report["stage"]="enrichment"
        enhanced,_=enrich_joined(cohort,geo,[])
        report["stage"]="metadata_recheck"
        if before!={d:meta(d) for d in before}:raise ValueError("Source revision changed")
        report["stage"]="evaluation"
        report.update(evaluate(enhanced),sales_rows=len(sales),building_rows=len(buildings),class203_rows=len(cohort),
                      universe_rows=len(geo),source_update_epochs={d:before[d][1] for d in before},status="completed")
    except Exception as exc:
        report["error_type"]=type(exc).__name__
        reasons={"Schema mismatch":"schema_mismatch","Incomplete capped extraction":"row_cap",
                 "Universe scope refused":"universe_schema_or_scope","Invalid cohort keys":"key_scope",
                 "Unexpected universe response":"unexpected_universe_response","Out-of-window row":"date_scope",
                 "Insufficient later cohort":"too_few_subjects","Chronological leak":"chronology_guard",
                 "Source revision changed":"revision_changed","Response exceeded cap":"response_bytes_cap",
                 "Missing source revision":"missing_revision","Response bound exceeded":"response_row_cap",
                 "Unexpected field in response":"unexpected_field"}
        report["failure_category"]=reasons.get(str(exc),"unclassified_guard")
    Path("reports").mkdir(exist_ok=True)
    Path("reports/holdout-aggregate.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    if report["status"]!="completed":raise SystemExit(1)
if __name__=="__main__":main()
