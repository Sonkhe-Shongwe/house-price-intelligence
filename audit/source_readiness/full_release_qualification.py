"""FR1-FR3: same frozen holdout window, bounded aggregate qualification.
Never emit raw records, PINs, addresses, sale-level prices, URLs or exceptions.
No matcher or screening policy change. Current extracts are retrospective.
"""
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import json
import re
from audit.phase0.audit import (SALES_ID,BUILDINGS_ID,normalize_pin,sale_reject_reasons,
    building_rows_by_key,join_sale_to_prior_building,whole_count)
from audit.phase1.expand import phase0_class203,enrich_joined,UNIVERSE_ID
from audit.source_readiness import holdout_audit as holdout
from audit.source_readiness.cohort_audit import meta
from audit.source_readiness.address_audit import fetch
YEARS=("2024","2025")
ADDRESS="3723-97qp"

def building_scope(rows):
    """Validate exact integer-equivalent values, never round or widen geography/year."""
    counts={y:Counter() for y in ("2023","2024")}
    invalid=Counter()
    for row in rows:
        town=whole_count(row.get("township_code"))
        year=whole_count(row.get("year"))
        if town!=17:invalid["township"]+=1
        if year not in (2023,2024):invalid["year"]+=1
        if town==17 and year in (2023,2024):
            count=counts[str(year)]
            count["rows"]+=1
            count["noncanonical_township_encoding"]+=str(row.get("township_code"))!="17"
            try:legacy=int(row["year"])
            except (ValueError,TypeError,KeyError):legacy=None
            count["legacy_year_parser_rejects"]+=legacy!=year
    return {"by_year":{y:dict(v) for y,v in counts.items()},"out_of_scope":dict(invalid)}

def diagnose(sales,buildings):
    lookup=building_rows_by_key(buildings)
    all_pins={p for p,_ in lookup}
    seen=set()
    cohort=[]
    counts={y:Counter() for y in YEARS}
    screens={y:Counter() for y in YEARS}
    joins={y:Counter() for y in YEARS}
    class203={y:Counter() for y in YEARS}
    for sale in sales:
        y=str(sale.get("sale_date",""))[:4]
        if y not in YEARS or whole_count(sale.get("township_code"))!=17:raise ValueError("Unexpected sales scope")
        c=counts[y];c["source_rows"]+=1
        is203=str(sale.get("class","")).strip()=="203"
        if is203:class203[y]["reported_class203"]+=1
        reasons=sale_reject_reasons(sale)
        if reasons:
            c["screen_rejected"]+=1;screens[y].update(reasons)
            if is203:class203[y]["screen_rejected"]+=1
            continue
        key=(normalize_pin(sale["pin"]),str(sale["doc_no"]),str(sale["sale_date"])[:10])
        if key in seen:
            c["duplicate_rejected"]+=1
            if is203:class203[y]["duplicate_rejected"]+=1
            continue
        seen.add(key);c["screened_unique"]+=1
        joined,error=join_sale_to_prior_building(sale,lookup)
        if error:
            c["join_rejected"]+=1;joins[y][error]+=1
            if is203:class203[y]["join_rejected"]+=1
            if error=="no_prior_building":
                c["missing_prior_pin_seen_other_year" if key[0] in all_pins else "missing_prior_pin_absent_all_selected_years"]+=1
            continue
        c["joined_all_classes"]+=1
        if joined["class"]!="203":
            c["joined_other_class"]+=1
            if is203:class203[y]["prior_class_not203"]+=1
            continue
        c["eligible_class203"]+=1
        if is203:class203[y]["eligible_class203"]+=1
        else:c["eligible_class203_not_reported203"]+=1
        joined["characteristics_year"]=int(y)-1
        cohort.append(joined)
    if cohort!=phase0_class203(sales,buildings):raise ValueError("Original policy parity failed")
    for y,c in counts.items():
        if c["source_rows"]!=c["screen_rejected"]+c["duplicate_rejected"]+c["screened_unique"] or c["screened_unique"]!=c["join_rejected"]+c["joined_all_classes"] or c["joined_all_classes"]!=c["joined_other_class"]+c["eligible_class203"]:
            raise ValueError("Funnel reconciliation failed")
    stages=("source_rows","screen_rejected","duplicate_rejected","screened_unique","join_rejected","joined_all_classes","joined_other_class","eligible_class203","eligible_class203_not_reported203","missing_prior_pin_seen_other_year","missing_prior_pin_absent_all_selected_years")
    return cohort,{y:{"funnel":{k:counts[y][k] for k in stages},
        "screen_reasons_overlapping":dict(screens[y]),"join_reasons_exclusive":dict(joins[y]),
        "reported_class203_subset":dict(class203[y])} for y in YEARS}

def license_summary():
    out={}
    for d in (SALES_ID,BUILDINGS_ID,UNIVERSE_ID,ADDRESS):
        raw=fetch(f"/api/views/{d}.json")
        license_id=raw.get("licenseId")
        # Return only a bounded token, never arbitrary free text from metadata.
        if license_id is not None and (not isinstance(license_id,str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}",license_id)):
            raise ValueError("Unexpected license metadata")
        stamp=raw.get("rowsUpdatedAt")
        if type(stamp) is not int:raise ValueError("Missing source revision")
        out[d]={"license_id":license_id,"source_updated_epoch":stamp}
    return out

def main():
    report={"status":"blocked","scope":"township 17, 2024-2025 sales, 2023-2024 assessment years, prior class203",
            "extracted_at_utc":datetime.now(timezone.utc).isoformat(),"publication_approved":False,
            "historical_asof_verified":False,"policy_unchanged":True}
    try:
        report["stage"]="metadata"
        rights=license_summary()
        before={d:meta(d) for d in (*holdout.SPECS,UNIVERSE_ID)}
        report["source_metadata"]=rights
        report["stage"]="sales_extraction"
        sales=holdout.collect(SALES_ID,before[SALES_ID][0])
        report["sales_rows"]=len(sales)
        report["stage"]="building_extraction"
        buildings=holdout.collect(BUILDINGS_ID,before[BUILDINGS_ID][0])
        report["building_rows"]=len(buildings)
        report["stage"]="building_scope"
        scope=building_scope(buildings)
        report["building_scope"]=scope
        if scope["out_of_scope"]:raise ValueError("Unexpected building scope")
        report["stage"]="diagnosis"
        cohort,summary=diagnose(sales,buildings)
        # Diagnostic counterfactual only. No modification of the canonical
        # join or holdout policy. Exact numeric equivalents, no imputation.
        normalized=[{**b,"year":whole_count(b["year"])} for b in buildings]
        normalized_cohort,normalized_summary=diagnose(sales,normalized)
        report["year_encoding_sensitivity"]={
            "canonical":{y:summary[y]["funnel"]["eligible_class203"] for y in YEARS},
            "normalized_exact_year":{y:normalized_summary[y]["funnel"]["eligible_class203"] for y in YEARS},
            "not_adopted":True}
        keys={(r["pin"],r["characteristics_year"]) for r in cohort}
        geo=holdout.universe(keys,before[UNIVERSE_ID][0])
        enriched,_=enrich_joined(cohort,geo,[])
        for y in YEARS:
            rows=[r for r in enriched if r["sale_date"].startswith(y+"-")]
            summary[y]["geography"]={"eligible":len(rows),"neighbourhood_present":sum(bool(r.get("nbhd_code")) for r in rows),
                "coordinates_present":sum(r.get("lat") is not None and r.get("lon") is not None for r in rows)}
        report["stage"]="metadata_recheck"
        if before!={d:meta(d) for d in before} or rights!=license_summary() or any(rights[d]["source_updated_epoch"]!=before[d][1] for d in before):
            raise ValueError("Source revision changed")
        report.update(years=summary,source_metadata=rights,sales_rows=len(sales),building_rows=len(buildings),
                      eligible_class203=len(cohort),universe_rows=len(geo))
        report["stage"]="holdout"
        n=summary["2025"]["funnel"]["eligible_class203"]
        if n>=holdout.MIN_REPORT:
            report["validation"]=holdout.evaluate(enriched)
            report["holdout_status"]="evaluated_fixed_policy"
        else:report["holdout_status"]="blocked_insufficient_subjects"
        report["status"]="completed"
    except Exception as exc:
        report["error_type"]=type(exc).__name__
        categories={"Schema mismatch":"schema_mismatch","Incomplete capped extraction":"row_cap",
            "Response exceeded cap":"response_byte_cap","Response bound exceeded":"response_row_cap",
            "Unexpected field in response":"unexpected_fields","Unexpected building scope":"building_scope_mismatch",
            "Unexpected sales scope":"sales_scope_mismatch","Original policy parity failed":"parity_failed",
            "Funnel reconciliation failed":"funnel_failed","Universe scope refused":"universe_scope",
            "Invalid cohort keys":"invalid_keys","Unexpected universe response":"universe_response",
            "Source revision changed":"revision_changed","Missing source revision":"missing_revision"}
        report["failure_category"]=categories.get(str(exc),"unclassified_guard")
    Path("reports").mkdir(exist_ok=True)
    Path("reports/full-release-qualification.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    if report["status"]!="completed":raise SystemExit(1)
if __name__=="__main__":main()
