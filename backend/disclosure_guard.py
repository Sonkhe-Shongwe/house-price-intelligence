"""Fail-closed disclosure policy. No real-data release grants exist.
Source kind and dataset are server-derived, never user-supplied grants.
"""
class DisclosureDenied(ValueError):
    pass

FIXTURE_FIELDS={
    "synthetic-sales":frozenset({"pin","sale_date","sale_price_usd_cents","document_number"}),
    "synthetic-assessment":frozenset({"pin","tax_year","card_number","assessor_class","building_area_sqft"}),
    "synthetic-geography":frozenset({"pin","tax_year","neighborhood_code","latitude","longitude"}),
    "synthetic-address":frozenset({"pin","tax_year","display_address"}),
}

def require_fixture_build(kind,sources):
    if kind!="synthetic_fixture":
        raise DisclosureDenied("Real-source builds are disabled in this candidate")
    if any(not isinstance(dataset,str) or not dataset.startswith("synthetic-") or query!="fabricated"
           for dataset,query in sources):
        raise DisclosureDenied("Build references a non-fixture source snapshot")

def project_fields(*,kind,dataset,query,record,fields):
    """Explicit whitelist; no real grants or generic record passthrough."""
    require_fixture_build(kind,[(dataset,query)])
    allowed=FIXTURE_FIELDS.get(dataset,frozenset())
    if not isinstance(fields,(list,tuple)) or not fields or any(not isinstance(f,str) or f not in allowed or f not in record for f in fields):
        raise DisclosureDenied("Field disclosure not approved")
    if len(set(fields))!=len(fields):
        raise DisclosureDenied("Duplicate requested field")
    return {field:record[field] for field in fields}
