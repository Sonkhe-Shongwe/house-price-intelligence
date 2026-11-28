"""Bounded aggregate-only address-source audit. No row-level download."""
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE="https://datacatalog.cookcountyil.gov"
DATASET="3723-97qp"
YEARS=(2023,2024)
MAX_BYTES=2_000_000
ADDRESS_FIELDS=("prop_address_full","prop_address","property_address","prop_address_street_address")
CITY_FIELDS=("prop_address_city_name","prop_address_city")

def fetch(path):
    req=Request(BASE+path,headers={"Accept":"application/json","User-Agent":"HPI-aggregate-research/1.0"})
    with urlopen(req,timeout=25) as response:
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:
            raise ValueError("Response exceeded cap")
        return json.loads(raw)

def plan(columns):
    if not {"pin","year"}.issubset(columns):
        raise ValueError("Required parcel/year fields not present")
    address=next((c for c in ADDRESS_FIELDS if c in columns),None)
    if "township_code" in columns:
        scope="township_code = '17'"
        scope_label="township 17"
    else:
        city=next((c for c in CITY_FIELDS if c in columns),None)
        if city is None:
            raise ValueError("No supported scope column")
        scope=f"upper({city}) = 'EVANSTON'"
        scope_label="situs city Evanston (not township 17)"
    select="count(*) as row_count, count(pin) as nonnull_pin_count, count(distinct pin) as distinct_pin_count"
    if address:
        select+=f", count({address}) as nonnull_address_count, count(distinct {address}) as distinct_address_count"
    return scope_label,scope,address,select

def validated_counts(payload, address):
    keys={"row_count","nonnull_pin_count","distinct_pin_count"}
    if address:keys|={"nonnull_address_count","distinct_address_count"}
    if not isinstance(payload,list) or len(payload)!=1 or set(payload[0])!=keys:
        raise ValueError("Non-aggregate response refused")
    out={}
    for key,value in payload[0].items():
        if not isinstance(value,(int,str)) or isinstance(value,bool) or not str(value).isascii() or not str(value).isdigit():
            raise ValueError("Invalid aggregate")
        out[key]=int(value)
    if not (out["distinct_pin_count"]<=out["nonnull_pin_count"]<=out["row_count"]):
        raise ValueError("Invalid PIN aggregate")
    if address and not (out["distinct_address_count"]<=out["nonnull_address_count"]<=out["row_count"]):
        raise ValueError("Invalid address aggregate")
    return out

def main():
    report={"dataset_id":DATASET,"extracted_at_utc":datetime.now(timezone.utc).isoformat(),
            "rights_status":"unapproved","historical_asof_verified":False,"years":[]}
    try:
        meta=fetch(f"/api/views/{DATASET}.json")
        columns={c["fieldName"] for c in meta["columns"]}
        label,where,address,select=plan(columns)
        report.update(scope=label,address_field=address,source_updated_epoch=meta.get("rowsUpdatedAt"),
                      metadata_license_id=meta.get("licenseId"))
        # Do not output publisher metadata verbatim or any field values.
        for year in YEARS:
            params={"$select":select,"$where":where+f" AND year = '{year}'","$limit":"1"}
            data=fetch(f"/resource/{DATASET}.json?"+urlencode(params))
            report["years"].append({"year":year,**validated_counts(data,address)})
        report["status"]="aggregate_query_completed"
    except Exception as exc:
        # No raw URL, response body, record identifiers or exception payload.
        report["status"]="blocked"
        report["error_type"]=type(exc).__name__
    Path("reports").mkdir(exist_ok=True)
    Path("reports/address-feasibility.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    if report["status"]!="aggregate_query_completed":
        raise SystemExit(1)

if __name__=="__main__":main()
