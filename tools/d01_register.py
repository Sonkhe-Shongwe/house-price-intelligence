"""Approved private sales registration and in-memory identifier feasibility only."""
from collections import Counter, defaultdict
import csv
from datetime import date
from decimal import localcontext
import io
import json
import os
import re

from tools import hpi_data_manager as dm
from tools import d01_file_profile as fp
from tools.world_bank_pilot import unique, reject_constant

# SG21: 1 office + 3 major region + 4 minor region + 8 erf + 5 portion.
# SG21_26: five further suffixed digits, per sMVPR standard s23-3.
# Candidate-only: no verified mapping of suburb to cadastral allotment.
SG26 = re.compile(r"[A-Z][A-Z0-9]{3}[0-9]{4}([0-9]{8})([0-9]{5})([0-9]{5})")
ERF = re.compile(r"([0-9]{1,8})\s+PINELANDS",re.I)
KEYS = ("SG26_CODE","PRTY_NMBR","SL_LAND_PRCL_KEY")


def cents(v):
    if v is None:
        return None
    with localcontext() as ctx:
        ctx.prec=80
        return int(v*100)


def derive(raw):
    q=fp.profile(raw)
    reader=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),strict=True)
    next(reader)
    rows=list(map(tuple,reader))
    exact=Counter(rows)
    events=Counter()
    for row in rows:
        ref,_,_,_,_,dt,price=(v.strip() for v in row)
        ds,day=fp.sale_date(dt)
        ps,p=fp.number(price,True)
        if ref and ds=="valid":
            events[(ref,day)]+=1
    result=[]
    for ordinal,row in enumerate(rows,1):
        ref,addr,desc,land,dwelling,dt,price=(v.strip() for v in row)
        ds,day=fp.sale_date(dt)
        ps,p=fp.number(price,True)
        ls,l=fp.number(land)
        ws,w=fp.number(dwelling)
        scope=bool(re.search(r"(?:^|\s)PINELANDS$",addr,re.I))
        kind=fp.classify(desc)
        preliminary=bool(ref and scope and kind=="pinelands_erf_style" and ds=="valid"
                         and ps=="positive" and ls=="positive" and ws=="positive")
        ambiguous=bool(exact[row]>1 or (ref and ds=="valid" and events[(ref,day)]>1))
        formula=any(v.lstrip().startswith(("=","+","-","@")) for v in row)
        flags={"description_pattern":kind,"pinelands_address_suffix":scope,
               "price_status":ps,"date_status":ds,"erf_extent_status":ls,
               "dwelling_extent_status":ws,"ambiguous_event":ambiguous,
               "exact_duplicate":exact[row]>1,"formula_like_text":formula,
               "preliminary_candidate":preliminary,
               "screened_candidate":preliminary and not ambiguous and not formula}
        result.append({"source_row_ordinal":ordinal,"valuation_reference":row[0],
                       "registered_description":row[2],
                       "reported_sale_date":day.isoformat() if ds=="valid" else None,
                       "consideration_cents":cents(p),
                       "erf_extent_reported":str(l) if l is not None else None,
                       "dwelling_extent_reported":str(w) if w is not None else None,
                       "quality_flags":flags})
    q.update(retained_rows=len(result),ambiguous_event_rows=sum(x["quality_flags"]["ambiguous_event"] for x in result),
             screened_candidates=sum(x["quality_flags"]["screened_candidate"] for x in result),
             deduplicated=False,address_projected=False,network_requests=0,
             property_join=False,registration_scope="Private reported-sales reference only.")
    return result,q


def match(rows,parcel):
    """Count candidates, not verified links. No prices used for identity matching."""
    if parcel.get("type")!="FeatureCollection" or not isinstance(parcel.get("features"),list):
        raise ValueError("PARCEL_STRUCTURE")
    exact={k:defaultdict(set) for k in KEYS}
    erf=defaultdict(set)
    flags={}
    sg_skipped=0
    for feature in parcel["features"]:
        p=feature["properties"]
        oid=p["OBJECTID"]
        if type(oid) is not int or oid in flags or p["OFC_SBRB_NAME"].strip().casefold()!="pinelands":
            raise ValueError("PARCEL_SCOPE")
        flags[oid]=p["quality_flags"]
        for k in KEYS:
            v=p[k]
            if (k=="SL_LAND_PRCL_KEY" and type(v) is not int) or (k!="SL_LAND_PRCL_KEY" and not isinstance(v,str)):
                raise ValueError("PARCEL_KEY_TYPE")
            exact[k][str(v)].add(oid)
        code=p["SG26_CODE"]
        sg=SG26.fullmatch(code)
        if sg and sg.group(2)=="00000" and sg.group(3)=="00000":
            erf[int(sg.group(1))].add(oid)
        else:
            sg_skipped+=1
    def assessment(cohort):
        counts=Counter({"rows":len(cohort),"exact_any":0,"exact_unique":0,"exact_ambiguous":0,
                        "erf_candidate_unique":0,"erf_candidate_ambiguous":0,"erf_unmatched":0,
                        "erf_not_applicable":0,"methods_agree":0,"methods_conflict":0,
                        "candidate_unique":0,"candidate_ambiguous":0,"candidate_unmatched":0,
                        "candidate_spatial_flag":0})
        per_key={k:0 for k in KEYS}
        for row in cohort:
            ref=row["valuation_reference"]
            hits=set()
            if ref:
                for k in KEYS:
                    h=exact[k].get(ref,set())
                    per_key[k]+=bool(h)
                    hits.update(h)
            counts["exact_any"]+=bool(hits)
            counts["exact_unique"]+=len(hits)==1
            counts["exact_ambiguous"]+=len(hits)>1
            e=ERF.fullmatch(row["registered_description"].strip())
            eh=erf.get(int(e.group(1)),set()) if e and row["quality_flags"]["pinelands_address_suffix"] else set()
            if not e or not row["quality_flags"]["pinelands_address_suffix"]:
                counts["erf_not_applicable"]+=1
            else:
                counts["erf_candidate_unique"]+=len(eh)==1
                counts["erf_candidate_ambiguous"]+=len(eh)>1
                counts["erf_unmatched"]+=not eh
            conflict=bool(hits and eh and hits!=eh)
            counts["methods_agree"]+=bool(hits and eh and hits==eh)
            counts["methods_conflict"]+=conflict
            union=hits|eh
            if not union:
                counts["candidate_unmatched"]+=1
            elif len(union)!=1 or conflict or not flags[next(iter(union))]["unique_key_candidate"]:
                counts["candidate_ambiguous"]+=1
            else:
                counts["candidate_unique"]+=1
                counts["candidate_spatial_flag"]+=flags[next(iter(union))]["spatial_candidate"] is True
        return dict(counts,exact_hits_by_key=per_key)
    return {"status":"CANDIDATE_ASSESSMENT_ONLY","parcel_features":len(flags),
            "parcel_rows_not_eligible_for_erf_rule":sg_skipped,
            "all_reported_sales":assessment(rows),
            "original_preliminary_cohort":assessment([r for r in rows if r["quality_flags"]["preliminary_candidate"]]),
            "screened_cohort":assessment([r for r in rows if r["quality_flags"]["screened_candidate"]]),
            "verified_identity_matches":0,"persistent_join":False,"network_requests":0,
            "method":"Exact text equality across three key domains; separate documented SG21_26 erf component candidate test for unportioned zero-suffix parcels and simple Pinelands descriptions. No valuation-reference prefix stripping.",
            "limitation":"Suburb is not verified cadastral allotment; exact text and unique candidates do not prove identity, historical continuity or join eligibility."}


def register(root,deadline=None,today=None):
    root=dm.workspace(root)
    today=today or date.today()
    deadline=deadline or fp.REVIEW
    if not fp.INTAKE<=today<deadline<=fp.REVIEW:
        raise ValueError("RETENTION_WINDOW")
    for folder in ("01_Source_Catalogue","02_Raw_Data","03_Processed_Data","07_Reports"):
        dm.check_path(root/folder)
        if not (root/folder).is_dir():
            raise ValueError("WORKSPACE_REQUIRED")
    raw=dm.read_bounded(root/dm.SALE_RAW,fp.CAP)
    if dm.sha(raw)!=dm.SALE_SHA or len(raw)!=fp.OBSERVED_BYTES:
        raise ValueError("SNAPSHOT_MISMATCH")
    prior=dm.audit_registered(root,dm.parcel_spec(),today=today)
    if prior["status"]!="integrity checks passed":
        raise ValueError("PARCEL_AUDIT_REQUIRED")
    parcel_manifest=json.loads(dm.read_bounded(root/dm.PARCEL_MANIFEST))
    parcel_bytes=dm.read_bounded(root/dm.PARCEL_OUTPUT,50*dm.MIB)
    if dm.sha(parcel_bytes)!=parcel_manifest["processed_sha256"]:
        raise ValueError("PARCEL_CHECKSUM")
    parcel=json.loads(parcel_bytes,object_pairs_hook=unique,parse_constant=reject_constant)
    if len(parcel["features"])!=prior["quality"]["retained_features"]:
        raise ValueError("PARCEL_COUNT")
    rows,q=derive(raw)
    result=match(rows,parcel)
    data=dm.json_bytes({"dataset_id":"HPI-DATA-011","reported_sales":rows})
    manifest={"dataset_id":"HPI-DATA-011","manager_version":"0.9.0",
              "source":"City of Cape Town GV2025 neighbourhood sales table",
              "source_url":dm.SALE_URL,"attribution":"City of Cape Town; HPI private normalisation and quality flags.",
              "source_identity_evidence":"Owner-observed local checksum, not publisher checksum.",
              "source_bytes":len(raw),"source_sha256":dm.sha(raw),"raw_path":dm.SALE_RAW,
              "first_intake_date":fp.INTAKE.isoformat(),"private_scope_approved_by_owner":True,
              "terms_status":dm.SALE_TERMS,"retention_policy":dm.SALE_POLICY,"retention":dm.SALE_RETENTION,
              "do_not_retain_on_or_after":deadline.isoformat(),"processed_path":dm.SALE_OUTPUT,
              "processed_sha256":dm.sha(data),"quality_report":dm.SALE_REPORT,"quality":q}
    plan=[(root/dm.SALE_OUTPUT,data),(root/dm.SALE_REPORT,dm.json_bytes(q)),(root/dm.SALE_MANIFEST,dm.json_bytes(manifest))]
    for path,payload in plan:
        dm.check_target(path,payload)
    for path,payload in plan:
        dm.publish(path,payload)
    audit=dm.audit_registered(root,dm.sale_spec(),today=today)
    return {"import":"complete","registered":True,"audit":audit,
            "parcel_audit":prior["status"],"identity_feasibility":result}


def owner_register(root,deadline=None):
    if os.name!="nt" or os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        print("STOP: owner-local Windows only.")
        return 1
    try:
        print(json.dumps(register(root,deadline),indent=2))
        return 0
    except Exception:
        print("STOP: snapshot, retention, registration or matching precondition failed; no record values emitted. Review local files before retry.")
        return 1
