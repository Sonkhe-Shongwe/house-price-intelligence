"""Replay bounded research cohort in memory; publish aggregate JSON only.
No property rows, identifiers, query URLs, raw errors or hashes of individual records
are logged or stored. Current-source replay is not the archived 2026-11-22 cohort.
"""
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
import json
import re
from urllib.parse import urlencode
from audit.source_readiness.address_audit import fetch
from audit.phase1.expand import phase0_class203
from audit.phase0.audit import (SALES_ID, BUILDINGS_ID, SALES_REQUIRED, SALES_OPTIONAL,
                               BUILDINGS_REQUIRED, BUILDINGS_OPTIONAL, normalize_pin)
ADDRESS="3723-97qp"
CAPS={SALES_ID:5000,BUILDINGS_ID:50000}
PAGE=2000
MAX_KEYS=500
BATCH=35
POLICY="phase0-v2-class203-prior-tax-year"
SPECS={
    SALES_ID:(SALES_REQUIRED,SALES_OPTIONAL,
        "township_code = '17' AND sale_date >= '2022-01-01T00:00:00' AND sale_date < '2025-01-01T00:00:00'",
        "pin ASC,sale_date ASC,doc_no ASC,:id ASC"),
    BUILDINGS_ID:(BUILDINGS_REQUIRED,BUILDINGS_OPTIONAL,
        "township_code = '17' AND year >= 2021 AND year <= 2023",
        "pin ASC,year ASC,card ASC,:id ASC"),
}

def meta(dataset):
    data=fetch(f"/api/views/{dataset}.json")
    fields={c["fieldName"] for c in data["columns"]}
    stamp=data.get("rowsUpdatedAt")
    if type(stamp) is not int:raise ValueError("Missing source revision")
    return fields,stamp

def query(dataset,params,allowed,cap):
    rows=fetch(f"/resource/{dataset}.json?"+urlencode(params))
    if not isinstance(rows,list) or len(rows)>cap:
        raise ValueError("Response bound exceeded")
    if any(not isinstance(row,dict) or set(row)-allowed for row in rows):
        raise ValueError("Unexpected field in response")
    return rows

def collect(dataset,fields):
    required,optional,where,order=SPECS[dataset]
    if not required<=fields:raise ValueError("Source schema changed")
    selected=required|(optional&fields)
    result=[]
    while len(result)<CAPS[dataset]:
        limit=min(PAGE,CAPS[dataset]-len(result))
        rows=query(dataset,{"$select":",".join(sorted(selected)),"$where":where,
                 "$order":order,"$limit":limit,"$offset":len(result)},selected,limit)
        result.extend(rows)
        if len(rows)<limit:return result
    raise ValueError("Extraction cap reached; incomplete cohort refused")

def keyset(cohort):
    keys={(row["pin"],row["characteristics_year"]) for row in cohort}
    if not keys or len(keys)>MAX_KEYS or any(not re.fullmatch(r"[0-9]{14}",p) or y not in (2021,2022,2023) for p,y in keys):
        raise ValueError("Cohort out of bounds")
    return keys

def address_rows(keys,fields):
    chosen={"pin","year","prop_address_full"}
    if not chosen<=fields:raise ValueError("Missing address fields")
    out=[]
    for year in sorted({y for _,y in keys}):
        pins=sorted(p for p,y in keys if y==year)
        for i in range(0,len(pins),BATCH):
            batch=pins[i:i+BATCH]
            where="year = "+str(year)+" AND pin IN ("+",".join("'"+p+"'" for p in batch)+")"
            rows=query(ADDRESS,{"$select":",".join(sorted(chosen)),"$where":where,"$limit":500,
                         "$order":"pin ASC,year ASC,:id ASC"},chosen,500)
            if len(rows)>=500:raise ValueError("Address batch capped")
            if any((normalize_pin(r.get("pin")),int(r["year"])) not in {(p,year) for p in batch} for r in rows):
                raise ValueError("Unexpected address key")
            out.extend(rows)
    return out

def summarise(cohort,rows):
    keys=keyset(cohort)
    grouped=defaultdict(list)
    for r in rows:
        key=(normalize_pin(r.get("pin")),int(r["year"]))
        if key not in keys:raise ValueError("Unexpected address key")
        value=r.get("prop_address_full")
        if value is not None and not isinstance(value,str):raise ValueError("Invalid address type")
        grouped[key].append(" ".join(value.casefold().split()) if value else "")
    counts=Counter()
    state={}
    by_label=defaultdict(set)
    for key in keys:
        records=grouped[key]
        labels={v for v in records if v}
        if not records:kind="no_record"
        elif not labels:kind="blank_only"
        elif len(records)!=1:kind="multiple_rows"
        else:
            kind="one_nonblank_row"
            by_label[(key[1],next(iter(labels)))].add(key[0])
        counts[kind]+=1
        state[key]=kind
    shared={p for (year,label),pins in by_label.items() if len(pins)>1 for p in [(pin,year) for pin in pins]}
    return {"cohort_sales":len(cohort),"distinct_pin_year_keys":len(keys),
            "address_rows":len(rows),"key_states":{k:counts[k] for k in ("no_record","blank_only","multiple_rows","one_nonblank_row")},
            "sales_with_one_nonblank_address_row":sum(state[(r["pin"],r["characteristics_year"])]=="one_nonblank_row" for r in cohort),
            "keys_sharing_label_with_other_single_row_keys_same_year":len(shared),
            "building_identity_verified":False,"historical_asof_verified":False}

def main():
    report={"status":"blocked","policy":POLICY,"scope":"township 17, sales 2022-2024, prior tax years 2021-2023, class 203",
            "extracted_at_utc":datetime.now(timezone.utc).isoformat(),"publication_approved":False,
            "archived_baseline_sales":273,"archived_baseline_keys":262}
    try:
        before={d:meta(d) for d in (*SPECS,ADDRESS)}
        sales=collect(SALES_ID,before[SALES_ID][0])
        buildings=collect(BUILDINGS_ID,before[BUILDINGS_ID][0])
        cohort=phase0_class203(sales,buildings)
        rows=address_rows(keyset(cohort),before[ADDRESS][0])
        after={d:meta(d) for d in before}
        if before!=after:raise ValueError("Source changed during extraction")
        report.update(summarise(cohort,rows),sales_rows=len(sales),building_rows=len(buildings),
                      source_update_epochs={d:before[d][1] for d in before},status="completed_current_source_replay")
    except Exception as exc:
        report["error_type"]=type(exc).__name__
    Path("reports").mkdir(exist_ok=True)
    Path("reports/cohort-aggregate.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    if report["status"]=="blocked":raise SystemExit(1)

if __name__=="__main__":main()
