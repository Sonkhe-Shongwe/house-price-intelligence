"""Inactive historical-research import into the existing disposable PostgreSQL schema.
No network, HTTP endpoint, runtime activation, or real-property publication.
Input is operator-side; caller authenticates source and completeness separately.
"""
import json
from datetime import datetime, timezone
from collections import defaultdict
from backend.real_source_intake import prepare_intake, digest
from backend.curated_ingestion_candidate import ImportRefused, _verify_or_insert
from backend.postgres_ingestion import _check
from backend.postgres_fixture import FixtureConnection
from backend.investigation_contract import build_investigation, validate_request
from backend.synthetic_investigation_store import CuratedReadQueries

DDL = """
CREATE TABLE historical_build_manifests (
    build_id TEXT PRIMARY KEY REFERENCES curated_builds(build_id),
    policy TEXT NOT NULL, source_manifests_json TEXT NOT NULL
);
CREATE TABLE historical_address_states (
    snapshot_id TEXT NOT NULL REFERENCES source_snapshots(snapshot_id),
    pin TEXT NOT NULL REFERENCES parcels(pin),
    tax_year INTEGER NOT NULL,
    address_state TEXT NOT NULL CHECK(address_state IN ('one_nonblank','ambiguous','missing','blank')),
    display_address TEXT,
    CHECK ((address_state='one_nonblank') = (display_address IS NOT NULL)),
    PRIMARY KEY(snapshot_id,pin,tax_year)
);
"""

def _plan_rows(plan):
    """Use canonical tables, with build-bound source IDs and no fixture aliases."""
    bh=plan["build_hash_sha256"]
    build="historical-"+bh
    manifests=plan["source_manifests"]
    ids={role: "historical-"+digest([bh,role]) for role in manifests}
    rows=defaultdict(list)
    def add(table,columns,values,keys):
        rows[table].append((tuple(columns.split()),tuple(values),tuple(keys.split())))
    stamp=manifests["sales"]["extracted_at_utc"]
    add("curated_builds","build_id built_at_utc build_hash_sha256 build_kind",
        (build,stamp,bh,"historical_research"),"build_id")
    add("historical_build_manifests","build_id policy source_manifests_json",
        (build,plan["policy"],json.dumps(manifests,sort_keys=True,separators=(",",":"))),"build_id")
    for role,m in manifests.items():
        sid=ids[role]
        add("source_snapshots","snapshot_id dataset_id extracted_at_utc source_query source_updated_at_utc data_sha256 historical_asof_verified public_display_approved",
            (sid,m["dataset_id"],stamp,plan["policy"],datetime.fromtimestamp(m["source_epoch"], timezone.utc).isoformat(),m["content_sha256"],0,0),"snapshot_id")
        add("curated_build_sources","build_id snapshot_id source_role",
            (build,sid,"other" if role=="address" else role),"build_id snapshot_id source_role")
    for p in sorted({row["pin"] for row in plan["parcel_years"]}):
        add("parcels","pin township_code",(p,"17"),"pin")
    for row in plan["parcel_years"]:
        p,y=row["pin"],row["tax_year"]
        sid=ids["assessment"]
        add("assessment_records","assessment_id snapshot_id pin tax_year card_number building_id assessor_class building_area_sqft",
            (sid+"-"+p+"-"+str(y),sid,p,y,row["card_number"],None,row["assessor_class"],row["building_area_sqft"]),"assessment_id")
        add("parcel_geographies","snapshot_id pin tax_year neighborhood_code latitude longitude derived_or_backfilled",
            (ids["geography"],p,y,row["neighborhood_code"],row["latitude"],row["longitude"],1),"snapshot_id pin tax_year")
        add("historical_address_states","snapshot_id pin tax_year address_state display_address",
            (ids["address"],p,y,row["address_state"],row["display_address"]),"snapshot_id pin tax_year")
    for sale in plan["sales"]:
        sid=ids["sales"]; txn=sid+"-"+sale["source_row_id"]
        add("sale_transactions","transaction_id snapshot_id source_row_id document_number sale_date price_usd_cents",
            (txn,sid,sale["source_row_id"],sale["document_number"],sale["sale_date"],sale["sale_price_usd_cents"]),"transaction_id")
        add("sale_transaction_parcels","transaction_id pin",(txn,sale["pin"]),"transaction_id pin")
        add("curated_build_transactions","build_id transaction_id",(build,txn),"build_id transaction_id")
    return build,ids,rows

def _verify(conn,build,ids,rows):
    """Fail closed on missing, modified or extra build-bound records."""
    for table,entries in rows.items():
        for columns,values,keys in entries:
            predicate=" AND ".join(k+"=?" for k in keys)
            actual=conn.execute("SELECT "+",".join(columns)+" FROM "+table+" WHERE "+predicate,
                                tuple(values[columns.index(k)] for k in keys)).fetchone()
            if actual!=values:
                raise ImportRefused("Historical curated row mismatch")
    for table,field,value in (
        ("curated_build_sources","build_id",build),("curated_build_transactions","build_id",build),
        ("sale_transactions","snapshot_id",ids["sales"]),("assessment_records","snapshot_id",ids["assessment"]),
        ("parcel_geographies","snapshot_id",ids["geography"]),("historical_address_states","snapshot_id",ids["address"])):
        if conn.execute("SELECT COUNT(*) FROM "+table+" WHERE "+field+"=?",(value,)).fetchone()[0]!=len(rows[table]):
            raise ImportRefused("Historical curated membership mismatch")
    if conn.execute("""SELECT COUNT(*) FROM sale_transaction_parcels p
                       JOIN sale_transactions t ON t.transaction_id=p.transaction_id
                       WHERE t.snapshot_id=?""",(ids["sales"],)).fetchone()[0]!=len(rows["sale_transaction_parcels"]):
        raise ImportRefused("Historical transaction link mismatch")

def import_historical(conn, **intake):
    """Rebuild the plan internally, never trust user-provided build/approval flags.
    On repeated input verify existing data rather than silently repair it.
    """
    _check(conn)
    plan=prepare_intake(**intake)
    build,ids,rows=_plan_rows(plan)
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(194323)")
        adapter=FixtureConnection(conn)
        if conn.execute("SELECT to_regclass('candidate_manifests')").fetchone()[0] is None:
            raise ImportRefused("Unknown ingestion candidate")
        if conn.execute("SELECT to_regclass('historical_build_manifests')").fetchone()[0] is None:
            conn.execute(DDL,prepare=False)
        if adapter.execute("SELECT 1 FROM curated_builds WHERE build_id=?",(build,)).fetchone() is not None:
            _verify(adapter,build,ids,rows)
            return build
        for table,entries in rows.items():
            for columns,values,keys in entries:
                _verify_or_insert(adapter,table,columns,values,keys)
        _verify(adapter,build,ids,rows)
    return build

def review_historical(conn, request, **intake):
    """Private operator-side read of a verified inactive build, not a served API.
    Reuse canonical subject/candidate queries and redacted evidence contract.
    No persistence of investigation, no detailed comparable disclosure.
    """
    _check(conn)
    plan=prepare_intake(**intake)
    build,ids,rows=_plan_rows(plan)
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(194323)")
        adapter=FixtureConnection(conn)
        _verify(adapter,build,ids,rows)
        # Shared read queries have no create/reopen or disclosure capability.
        store=CuratedReadQueries(adapter,build)
        validated=validate_request(request)
        if validated["subject"].get("address_id") is not None:
            raise ImportRefused("Historical address resolution not yet enabled")
        subject=store._resolved_subject(validated)
        candidates,_=store._candidates(validated)
        provenance={"build_id":build,"built_at_utc":plan["source_manifests"]["sales"]["extracted_at_utc"],
                    "source_kind":"historical_research","source_snapshot_ids":sorted(ids.values())}
        result=build_investigation(validated,resolved_subject=subject,candidate_sales=candidates,data_build=provenance)
        return {"status":result["status"],"reason":result["reason"],"selected_count":result["selected_count"],
                "tier":result["tier"],"warnings":result["warnings"],"evidence_details_redacted":True,
                "valuation":None,"source_kind":"historical_research","historical_asof_verified":False,
                "public_display_approved":False}
