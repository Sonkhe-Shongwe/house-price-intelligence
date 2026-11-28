"""Offline-testable bounded source collection contract; no default live transport.
Caller injects metadata(dataset)->(fields, epoch), and
page(dataset, params, allowed_fields, cap)->list. No network or file IO here.
Independent counts and stable metadata reconcile responses, not publisher
authentication or historical publication-time proof.
"""
from audit.phase0.audit import normalize_pin,whole_count
from audit.phase1.expand import phase0_class203
from audit.source_readiness.holdout_audit import SPECS
from backend.real_source_intake import DATASETS, REQUIRED, OPTIONAL, CAPS, IntakeRefused, _metadata, prepare_intake

def collect_intake(*, metadata, page, extracted_at_utc):
    def metadata_snapshot():
        result={}
        for dataset in DATASETS.values():
            fields,epoch=metadata(dataset)
            result[dataset]={"fields":sorted(fields),"epoch":epoch}
        _metadata(result,result)
        return result
    before=metadata_snapshot()
    def request(dataset,params,fields,cap):
        result=page(dataset,params,fields,cap)
        if not isinstance(result,list) or len(result)>cap or any(not isinstance(row,dict) or set(row)-fields for row in result):
            raise IntakeRefused("unexpected_collection_response")
        return result
    def count(dataset,where,cap):
        data=request(dataset,{"$select":"count(*) as row_count","$where":where,"$limit":1},{"row_count"},1)
        n=whole_count(data[0].get("row_count")) if len(data)==1 else None
        if n is None or n>=cap:
            raise IntakeRefused("collection_count_missing_or_capped")
        return n
    def bounded_pages(role,where,order,cap,page_size):
        dataset=DATASETS[role]
        fields=REQUIRED[role]|(OPTIONAL[role]&set(before[dataset]["fields"]))
        n=count(dataset,where,cap)
        rows=[]
        while len(rows)<n:
            limit=min(page_size,n-len(rows))
            batch=request(dataset,{"$select":",".join(sorted(fields)),"$where":where,"$order":order,
                      "$limit":limit,"$offset":len(rows)},fields,limit)
            if len(batch)!=limit:
                raise IntakeRefused("collection_page_count_mismatch")
            rows.extend(batch)
        # Explicit terminal page prevents accepting additional unexpected rows.
        if request(dataset,{"$select":",".join(sorted(fields)),"$where":where,"$order":order,
                    "$limit":1,"$offset":n},fields,1):
            raise IntakeRefused("collection_terminal_page_not_empty")
        if count(dataset,where,cap)!=n:
            raise IntakeRefused("collection_count_changed")
        return rows
    rows={}
    for role in ("sales","assessment"):
        _,_,where,order,cap=SPECS[DATASETS[role]]
        rows[role]=bounded_pages(role,where,order,cap,2000)
    if any(str(x.get("sale_date",""))[:4] not in ("2024","2025") or whole_count(x.get("township_code"))!=17 for x in rows["sales"]):
        raise IntakeRefused("unexpected_sale_scope")
    if any(whole_count(x.get("year")) not in (2023,2024) or whole_count(x.get("township_code"))!=17 for x in rows["assessment"]):
        raise IntakeRefused("unexpected_assessment_scope")
    cohort=phase0_class203(rows["sales"],rows["assessment"])
    keys={(x["pin"],x["characteristics_year"]) for x in cohort}
    if not keys or len(keys)>500 or any(len(p)!=14 or not p.isascii() or not p.isdigit() or y not in (2023,2024) for p,y in keys):
        raise IntakeRefused("collection_cohort_scope")
    for role in ("geography","address"):
        rows[role]=[]
        for year in (2023,2024):
            pins=sorted(p for p,y in keys if y==year)
            for i in range(0,len(pins),35):
                batch=pins[i:i+35]
                where="year = "+str(year)+" AND pin IN ("+",".join("'"+p+"'" for p in batch)+")"
                returned=bounded_pages(role,where,"pin ASC,year ASC,:id ASC",500,500)
                expected={(p,year) for p in batch}
                if any((normalize_pin(x.get("pin")),whole_count(x.get("year"))) not in expected for x in returned):
                    raise IntakeRefused("collection_enrichment_scope")
                rows[role].extend(returned)
                if len(rows[role])>=CAPS[role]:
                    raise IntakeRefused("collection_enrichment_cap")
    after=metadata_snapshot()
    result={"rows":rows,"metadata_before":before,"metadata_after":after,"extracted_at_utc":extracted_at_utc}
    # Validate exact same boundary before returning a private operator intake.
    prepare_intake(**result)
    return result
