"""Approved single GV2025 table, local aggregate-only exploratory profiling."""
from collections import Counter, defaultdict
import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import os
import re

from tools.hpi_data_manager import read_bounded, workspace

FILENAME = "CapeTown_Pinelands_PropertySales_2026.csv"
HEADERS = ("Valuation Reference", "Physical Address", "Registered Description",
           "ERF EXTENT", "DWELLING EXTENT", "Sale Date", "Sale Price")
EXPECTED = 839
OBSERVED_BYTES = 83267
CAP = 1024 * 1024
INTAKE = date(2026,11,27)
REVIEW = date(2026,12,27)
NUMBER = re.compile(r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+|[0-9]{1,3}(?: [0-9]{3})+)(?:\.[0-9]+)?")
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")


class ProfileStop(ValueError):
    pass


def number(text, currency=False):
    s=text.strip()
    if not s:
        return "missing",None
    if currency and s[:1].upper()=="R":
        s=s[1:].strip()
    negative=s.startswith("-")
    if negative:
        s=s[1:]
    if len(s)>60 or not NUMBER.fullmatch(s):
        return "invalid",None
    try:
        v=Decimal(s.replace(",","").replace(" ",""))
        if negative:
            v=-v
        if currency and v.as_tuple().exponent < -2:
            return "invalid",None
        return ("positive" if v>0 else "zero" if v==0 else "negative"),v
    except InvalidOperation:
        return "invalid",None


def sale_date(text):
    if not text:
        return "missing",None
    if not re.fullmatch(r"\d{4}/\d{2}/\d{2}",text):
        return "invalid",None
    try:
        d=datetime.strptime(text,"%Y/%m/%d").date()
        return ("future" if d>INTAKE else "valid"),d
    except ValueError:
        return "invalid",None


def classify(desc):
    # Description patterns only; not legal tenure verification.
    if re.match(r"^SS\s*\d",desc,re.I):
        return "sectional_style"
    if re.fullmatch(r"[0-9]+\s+PINELANDS",desc,re.I):
        return "pinelands_erf_style"
    return "other_or_unknown"


def profile(raw):
    if not isinstance(raw,bytes) or not 0<len(raw)<=CAP:
        raise ProfileStop("BYTE_LIMIT")
    try:
        reader=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),strict=True)
        headers=next(reader,[])
        if tuple(headers)!=HEADERS:
            raise ProfileStop("HEADER_MISMATCH")
        rows=[]
        for row in reader:
            if len(row)!=7 or len(rows)>=EXPECTED:
                raise ProfileStop("ROW_STRUCTURE_OR_LIMIT")
            if any(len(v)>4096 or any(ord(c)<32 for c in v) or EMAIL.search(v) for v in row):
                raise ProfileStop("UNEXPECTED_TEXT")
            rows.append(tuple(row))
    except (UnicodeError,csv.Error):
        raise ProfileStop("INVALID_CSV") from None
    if len(rows)!=EXPECTED:
        raise ProfileStop("ROW_COUNT")
    missing=dict.fromkeys(HEADERS,0)
    ref_counts=Counter()
    row_counts=Counter(rows)
    event_counts=Counter()
    same_ref_date_prices=defaultdict(set)
    dates_by_ref=defaultdict(set)
    price_states=Counter()
    date_states=Counter()
    land_states=Counter()
    dwelling_states=Counter()
    classes=Counter()
    address_scope=Counter()
    years=Counter()
    candidate=0
    complete_area_candidate=0
    formula_like=0
    for row in rows:
        for h,v in zip(HEADERS,row):
            missing[h]+=not v.strip()
        formula_like+=any(v.lstrip().startswith(("=","+","-","@")) for v in row)
        ref,addr,desc,land,dwelling,dt,price=(v.strip() for v in row)
        if ref:
            ref_counts[ref]+=1
        scope=bool(re.search(r"(?:^|\s)PINELANDS$",addr,re.I))
        address_scope["pinelands_suffix" if scope else "other_or_missing"]+=1
        kind=classify(desc)
        classes[kind]+=1
        ps,p=number(price,True)
        ds,day=sale_date(dt)
        ls,_=number(land)
        ws,_=number(dwelling)
        price_states[ps]+=1
        date_states[ds]+=1
        land_states[ls]+=1
        dwelling_states[ws]+=1
        if ds=="valid":
            years[str(day.year)]+=1
        if ref and ds=="valid":
            dates_by_ref[ref].add(day)
            if p is not None:
                event_counts[(ref,day,p)]+=1
                same_ref_date_prices[(ref,day)].add(p)
        if ref and scope and kind=="pinelands_erf_style" and ds=="valid" and ps=="positive":
            candidate+=1
            complete_area_candidate+=ls=="positive" and ws=="positive"
    duplicates=lambda counts: {"groups":sum(n>1 for n in counts.values()),
                               "rows":sum(n for n in counts.values() if n>1)}
    return {
        "status":"PROFILED","rows":len(rows),"columns":len(HEADERS),
        "missing_by_column":missing,"distinct_nonblank_references":len(ref_counts),
        "repeated_reference_groups":duplicates(ref_counts),
        "exact_duplicate_rows":duplicates(row_counts),
        "repeated_reference_date_price":duplicates(event_counts),
        "reference_date_conflicting_prices":sum(len(v)>1 for v in same_ref_date_prices.values()),
        "references_with_multiple_valid_sale_dates":sum(len(v)>1 for v in dates_by_ref.values()),
        "address_scope":dict(address_scope),"description_patterns":dict(classes),
        "price_quality":dict(price_states),"sale_date_quality":dict(date_states),
        "sale_year_counts":dict(sorted(years.items())),
        "erf_extent_quality":dict(land_states),"dwelling_extent_quality":dict(dwelling_states),
        "preliminary_erf_sale_rows_before_duplicate_review":candidate,
        "preliminary_erf_sale_rows_with_positive_both_extents":complete_area_candidate,
        "rows_with_formula_like_text":formula_like,
        "limitations":"Reported sales only; no verified registration, arm's-length status, tenure, event identity, historical area, legal parcel identity or join. Repeated keys are not automatically duplicates."
    }


def owner_profile(root):
    if os.name!="nt" or os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        print("STOP: owner-local Windows only.")
        return 1
    if not INTAKE<=date.today()<REVIEW:
        print("STOP: retention review required; no automatic deletion.")
        return 1
    try:
        raw=read_bounded(workspace(root)/"02_Raw_Data"/FILENAME,CAP)
        report=profile(raw)
        report.update(file=FILENAME,bytes=len(raw),matches_attachment_size=len(raw)==OBSERVED_BYTES,
                      sha256=hashlib.sha256(raw).hexdigest(),intake_date=INTAKE.isoformat(),
                      review_by=REVIEW.isoformat(),files_modified=False,
                      network_requests=0,registered=False,property_join=False)
    except ProfileStop as exc:
        print(json.dumps({"status":"STOP","reason":str(exc),"registered":False}))
        return 1
    except Exception:
        print("STOP: local read or profile failed; no individual values emitted.")
        return 1
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0
