"""Isolated synthetic curated ingestion candidate over canonical v3 tables.
No real source adapter, network endpoint, arbitrary input or migration of user DBs.
Build-specific address records avoid mutating the legacy shared demo index.
"""
import hashlib
import json
import sqlite3
from backend.schema_migrations import migrate_fixture
from backend.synthetic_investigation_store import SyntheticInvestigationStore
from backend.disclosure_guard import project_fields

STAMP="2026-11-24T00:00:00Z"
ROLES=("sales","assessment","geography","address")
POLICY="fictional-curation-v1"
class ImportRefused(ValueError):pass

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

CANDIDATE_DDL="""
    CREATE TABLE candidate_manifests (
      snapshot_id TEXT PRIMARY KEY REFERENCES source_snapshots(snapshot_id),
      role TEXT NOT NULL, revision TEXT NOT NULL, selected_fields_json TEXT NOT NULL,
      row_count INTEGER NOT NULL CHECK(row_count>=0), content_sha256 TEXT NOT NULL,
      publication_date TEXT CHECK(publication_date IS NULL)
    );
    CREATE TABLE candidate_addresses (
      snapshot_id TEXT NOT NULL REFERENCES source_snapshots(snapshot_id),
      pin TEXT NOT NULL REFERENCES parcels(pin), tax_year INTEGER NOT NULL,
      display_address TEXT NOT NULL, search_key TEXT NOT NULL,
      PRIMARY KEY(snapshot_id,pin,tax_year,search_key)
    );
    """

def open_candidate():
    conn=sqlite3.connect(":memory:")
    migrate_fixture(conn)
    conn.executescript(CANDIDATE_DDL)
    return conn

def fixture_rows(revision):
    if revision in ("v4","v5"):
        from backend.source_shaped_fixture import replay_rows
        return replay_rows(revision)
    if revision not in ("v1","v2","v3"):raise ImportRefused("Only reviewed invented revisions")
    pins=[f"{n:014d}" for n in range(1,7)]
    if revision=="v3":
        # New independent fictional revision; v1/v2 manifests and IDs unchanged.
        labels=("12 Imaginary Cedar Lane, Demonstration District","24 Imaginary Cedar Lane, Demonstration District",
                "8 Imaginary Oak Close, Demonstration District","36 Imaginary Birch Way, Demonstration District",
                "50 Imaginary Grove, Demonstration District","50 Imaginary Grove, Demonstration District")
        return {
            "sales":[{"pin":pins[n-1],"source_row_id":f"row-{n}","document_number":f"DOC-{n}",
                      "sale_date":when,"sale_price_usd_cents":price}
                     for n,when,price in ((2,"2024-01-18",48750000),(3,"2024-03-12",54275000),(4,"2024-05-09",51990000))],
            "assessment":[{"pin":p,"tax_year":2023,"card_number":"1","assessor_class":"203","building_area_sqft":a}
                          for p,a in zip(pins,(1600,1500,1720,1650,1900,1580))],
            "geography":[{"pin":p,"tax_year":2023,"neighborhood_code":"17","latitude":42.04,"longitude":-87.68} for p in pins],
            "address":[{"pin":p,"tax_year":2023,"display_address":label} for p,label in zip(pins,labels)]
        }
    return {
        "sales":[{"pin":p,"source_row_id":f"row-{i}","document_number":f"DOC-{i}",
                  "sale_date":"2024-02-01","sale_price_usd_cents":52500000+(12500 if revision=="v2" and i==2 else 0)}
                 for i,p in enumerate(pins,1) if i in (2,3,4)],
        "assessment":[{"pin":p,"tax_year":2023,"card_number":"1","assessor_class":"203",
                       "building_area_sqft":1600} for p in pins],
        "geography":[{"pin":p,"tax_year":2023,"neighborhood_code":"17","latitude":42.04,"longitude":-87.68} for p in pins],
        "address":[{"pin":p,"tax_year":2023,"display_address":f"{100+min(i,5)} Fictional Way, Demonstration District"}
                   for i,p in enumerate(pins,1)]
    }

def _plan(revision):
    rows=fixture_rows(revision)
    manifests={}
    for role,records in rows.items():
        content=digest(records)
        manifests[role]={"snapshot_id":"fixture-"+role+"-"+digest([revision,content])[:24],
                         "role":role,"revision":revision,"selected_fields_json":json.dumps(sorted(records[0])),
                         "row_count":len(records),"content_sha256":content}
    build_hash=digest([POLICY,manifests])
    return rows,manifests,"candidate-"+build_hash[:24],build_hash

def _verify_or_insert(conn,table,columns,values,key_columns):
    # Identifiers are internal constants from calls below; values are bound.
    where=" AND ".join(c+"=?" for c in key_columns)
    keys=tuple(values[columns.index(c)] for c in key_columns)
    old=conn.execute(f"SELECT {','.join(columns)} FROM {table} WHERE {where}",keys).fetchone()
    if old is not None:
        if old!=tuple(values):raise ImportRefused("Immutable candidate row conflict")
        return
    conn.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",values)

def import_fixture(conn,revision):
    """Atomically import an invented revision. Never update existing source rows."""
    if conn.in_transaction or conn.execute("PRAGMA foreign_keys").fetchone()!=(1,):
        raise ImportRefused("Clean foreign-key-enabled transaction required")
    if conn.execute("SELECT name FROM sqlite_master WHERE name='candidate_manifests'").fetchone() is None:
        raise ImportRefused("Not an isolated ingestion candidate")
    with conn:
        conn.execute("BEGIN IMMEDIATE")
        return _import_rows(conn,revision)

def _import_rows(conn,revision):
    """Internal common implementation; caller holds an atomic import lock."""
    rows,manifests,build_id,build_hash=_plan(revision)
    def put(table,columns,values,keys):
        _verify_or_insert(conn,table,columns.split(),tuple(values),keys.split())
    # An incomplete/tampered existing build must not be silently repaired.
    existing=conn.execute("SELECT 1 FROM curated_builds WHERE build_id=?",(build_id,)).fetchone()
    if existing:_verify_build(conn,revision)
    put("curated_builds","build_id built_at_utc build_hash_sha256 build_kind",
        (build_id,STAMP,build_hash,"synthetic_fixture"),"build_id")
    for role,m in manifests.items():
        sid=m["snapshot_id"]
        put("source_snapshots","snapshot_id dataset_id extracted_at_utc source_query source_updated_at_utc data_sha256 historical_asof_verified public_display_approved",
            (sid,"synthetic-"+role,STAMP,"fabricated",None,m["content_sha256"],0,0),"snapshot_id")
        put("candidate_manifests","snapshot_id role revision selected_fields_json row_count content_sha256 publication_date",
            (sid,role,revision,m["selected_fields_json"],m["row_count"],m["content_sha256"],None),"snapshot_id")
        put("curated_build_sources","build_id snapshot_id source_role",(build_id,sid,"other" if role=="address" else role),"build_id snapshot_id source_role")
        for record in rows[role]:
            p=record["pin"]
            put("parcels","pin township_code",(p,"17"),"pin")
            if role=="sales":
                txn=sid+"-"+record["source_row_id"]
                put("sale_transactions","transaction_id snapshot_id source_row_id document_number sale_date price_usd_cents",
                    (txn,sid,record["source_row_id"],record["document_number"],record["sale_date"],record["sale_price_usd_cents"]),"transaction_id")
                put("sale_transaction_parcels","transaction_id pin",(txn,p),"transaction_id pin")
                put("curated_build_transactions","build_id transaction_id",(build_id,txn),"build_id transaction_id")
            elif role=="assessment":
                put("assessment_records","assessment_id snapshot_id pin tax_year card_number building_id assessor_class building_area_sqft",
                    (sid+"-"+p,sid,p,record["tax_year"],record["card_number"],None,record["assessor_class"],record["building_area_sqft"]),"assessment_id")
            elif role=="geography":
                put("parcel_geographies","snapshot_id pin tax_year neighborhood_code latitude longitude derived_or_backfilled",
                    (sid,p,record["tax_year"],record["neighborhood_code"],record["latitude"],record["longitude"],1),"snapshot_id pin tax_year")
            else:
                label=record["display_address"]
                put("candidate_addresses","snapshot_id pin tax_year display_address search_key",
                    (sid,p,record["tax_year"],label," ".join(label.casefold().split())),"snapshot_id pin tax_year search_key")
    _verify_build(conn,revision)
    return build_id

def _verify_build(conn,revision):
    """Reconstruct immutable source facts, not just a manifest label."""
    rows,manifests,build_id,build_hash=_plan(revision)
    if conn.execute("SELECT built_at_utc,build_hash_sha256,build_kind FROM curated_builds WHERE build_id=?",(build_id,)).fetchone()!=(STAMP,build_hash,"synthetic_fixture"):
        raise ImportRefused("Build manifest mismatch")
    membership=conn.execute("SELECT snapshot_id,source_role FROM curated_build_sources WHERE build_id=?",(build_id,)).fetchall()
    if set(membership)!={(m["snapshot_id"],"other" if role=="address" else role) for role,m in manifests.items()}:
        raise ImportRefused("Build source membership mismatch")
    for role,m in manifests.items():
        sid=m["snapshot_id"]
        expected=(role,revision,m["selected_fields_json"],m["row_count"],m["content_sha256"],None)
        if conn.execute("SELECT role,revision,selected_fields_json,row_count,content_sha256,publication_date FROM candidate_manifests WHERE snapshot_id=?",(sid,)).fetchone()!=expected:
            raise ImportRefused("Source manifest mismatch")
        if conn.execute("SELECT dataset_id,extracted_at_utc,source_query,source_updated_at_utc,data_sha256,historical_asof_verified,public_display_approved FROM source_snapshots WHERE snapshot_id=?",(sid,)).fetchone()!=("synthetic-"+role,STAMP,"fabricated",None,m["content_sha256"],0,0):
            raise ImportRefused("Source provenance mismatch")
        if role=="sales":
            actual=conn.execute("""SELECT p.pin,t.source_row_id,t.document_number,t.sale_date,t.price_usd_cents
               FROM sale_transactions t JOIN sale_transaction_parcels p ON p.transaction_id=t.transaction_id
               WHERE t.snapshot_id=?""",(sid,)).fetchall()
            keys=("pin","source_row_id","document_number","sale_date","sale_price_usd_cents")
            ids={x[0] for x in conn.execute("SELECT transaction_id FROM curated_build_transactions WHERE build_id=?",(build_id,))}
            if ids!={sid+"-"+r["source_row_id"] for r in rows[role]}:raise ImportRefused("Transaction membership mismatch")
            if conn.execute("SELECT COUNT(*) FROM sale_transactions WHERE snapshot_id=?",(sid,)).fetchone()[0]!=len(rows[role]):raise ImportRefused("Transaction count mismatch")
        elif role=="assessment":
            actual=conn.execute("SELECT pin,tax_year,card_number,assessor_class,building_area_sqft FROM assessment_records WHERE snapshot_id=? AND building_id IS NULL",(sid,)).fetchall()
            keys=("pin","tax_year","card_number","assessor_class","building_area_sqft")
            if conn.execute("SELECT COUNT(*) FROM assessment_records WHERE snapshot_id=?",(sid,)).fetchone()[0]!=len(rows[role]):raise ImportRefused("Assessment identity mismatch")
        elif role=="geography":
            actual=conn.execute("SELECT pin,tax_year,neighborhood_code,latitude,longitude FROM parcel_geographies WHERE snapshot_id=? AND derived_or_backfilled=1",(sid,)).fetchall()
            keys=("pin","tax_year","neighborhood_code","latitude","longitude")
            if conn.execute("SELECT COUNT(*) FROM parcel_geographies WHERE snapshot_id=?",(sid,)).fetchone()[0]!=len(rows[role]):raise ImportRefused("Geography count mismatch")
        else:
            actual=conn.execute("SELECT pin,tax_year,display_address FROM candidate_addresses WHERE snapshot_id=? AND search_key=lower(display_address)",(sid,)).fetchall()
            keys=("pin","tax_year","display_address")
            if conn.execute("SELECT COUNT(*) FROM candidate_addresses WHERE snapshot_id=?",(sid,)).fetchone()[0]!=len(rows[role]):raise ImportRefused("Address count mismatch")
        if sorted(actual)!=sorted(tuple(r[k] for k in keys) for r in rows[role]):raise ImportRefused("Source content mismatch")
    for p in {r["pin"] for records in rows.values() for r in records}:
        if conn.execute("SELECT township_code FROM parcels WHERE pin=?",(p,)).fetchone()!=("17",):
            raise ImportRefused("Parcel scope conflict")
    return build_id

def address_candidates(conn,revision,query,year=2023):
    """No guessed physical building identity, no fuzzy address match."""
    build_id=_verify_build(conn,revision)
    _,manifests,_,_=_plan(revision)
    sid=manifests["address"]["snapshot_id"]
    rows=conn.execute("SELECT pin,tax_year,display_address FROM candidate_addresses WHERE snapshot_id=? AND tax_year=? AND search_key=? ORDER BY pin",
                      (sid,year," ".join(query.casefold().split()))).fetchall()
    result=[project_fields(kind="synthetic_fixture",dataset="synthetic-address",query="fabricated",
                           record=dict(zip(("pin","tax_year","display_address"),row)),
                           fields=("pin","tax_year","display_address")) for row in rows]
    return {"build_id":build_id,"identity_scope":"parcel_only","building_identity_verified":False,
            "status":"ambiguous" if len(result)>1 else "one_candidate" if result else "no_match","candidates":result}

def investigation_store(conn,revision):
    return SyntheticInvestigationStore(conn,build_id=_verify_build(conn,revision))
