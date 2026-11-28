"""One bounded private Cook County rehearsal; no row-level reporting.
No live transport on import. The live entry point is guarded by the one-shot CI
workflow and only prints a fixed aggregate report. Never print raw exceptions.
"""
from collections import Counter
from datetime import datetime,timezone
import json
import logging
import os
import secrets
import sys
import psycopg
from psycopg.conninfo import conninfo_to_dict
from audit.phase2.matcher import match_property
from backend.real_source_collection import collect_intake
from backend.real_source_intake import DATASETS,prepare_intake,IntakeRefused
from backend.postgres_ingestion import initialise
from backend.historical_postgres import import_historical
from backend.historical_reader import ROLE,PrivateHistoricalReader,provision_reader,seal_historical
from backend.curated_ingestion_candidate import ImportRefused

POLICY="private-real-rehearsal-v1"
TOKEN="owner-approved-2026-11-24-private-real-rehearsal-v1"
DATABASE="hpi_ingest_fixture"

def require(condition):
    if not condition:
        raise ImportRefused("Rehearsal invariant failed")

def new_report():
    return {"policy":POLICY,"status":"blocked","stage":"preflight",
            "historical_asof_verified":False,"public_display_approved":False,
            "valuation_approved":False,"permanent_storage":False}

def _scope(dsn):
    p=conninfo_to_dict(dsn)
    require(p.get("host")=="127.0.0.1" and p.get("user")=="postgres"
            and p.get("dbname")=="hpi_fixture" and p.get("hostaddr","127.0.0.1")=="127.0.0.1"
            and not set(p)-{"host","port","dbname","user","password","hostaddr","connect_timeout"})

def verify_rehearsal(dsn,intake,report):
    """Use the canonical importer and independent pure matcher on every 2025 subject.
    No raw data is returned. All database resources are disposable.
    """
    _scope(dsn)
    report["stage"]="intake"
    plan=prepare_intake(**intake)
    report["source_rows"]={role:len(intake["rows"][role]) for role in DATASETS}
    report["source_epochs"]={role:plan["source_manifests"][role]["source_epoch"] for role in DATASETS}
    report["extracted_at_utc"]=plan["source_manifests"]["sales"]["extracted_at_utc"]
    report["eligible_sales_by_year"]={y:sum(s["sale_date"].startswith(y+"-") for s in plan["sales"]) for y in ("2024","2025")}
    report["parcel_year_keys"]=len(plan["parcel_years"])
    subjects=[s for s in plan["sales"] if s["sale_date"].startswith("2025-")]
    require(len(subjects)>=10)
    by_key={(p["pin"],p["tax_year"]):p for p in plan["parcel_years"]}
    report["address_states"]={k:sum(p["address_state"]==k for p in by_key.values()) for k in ("one_nonblank","ambiguous","missing","blank")}
    report["geography_coverage"]={"neighborhood":sum(bool(p["neighborhood_code"]) for p in by_key.values()),
                                  "coordinate_pair":sum(p["latitude"] is not None and p["longitude"] is not None for p in by_key.values())}
    labels=Counter((p["tax_year"]," ".join(p["display_address"].casefold().split()))
                   for p in by_key.values() if p["address_state"]=="one_nonblank")
    report["shared_label_keys"]=sum(n for n in labels.values() if n>1)
    def matcher_row(s):
        p=by_key[s["pin"],s["assessment_year"]]
        return {"pin":s["pin"],"doc_no":s["document_number"],"sale_date":s["sale_date"],
                "sale_price":s["sale_price_usd_cents"]/100,"class":p["assessor_class"],
                "township_code":p["township_code"],"sqft":p["building_area_sqft"],
                "nbhd_code":p["neighborhood_code"],"lat":p["latitude"],"lon":p["longitude"],
                "characteristics_year":p["tax_year"]}
    population=[matcher_row(s) for s in plan["sales"]]
    report["stage"]="database"
    with psycopg.connect(dsn,autocommit=True) as admin:
        require(admin.execute("SELECT 1 FROM pg_database WHERE datname=%s",(DATABASE,)).fetchone() is None)
        require(admin.execute("SELECT 1 FROM pg_roles WHERE rolname=%s",(ROLE,)).fetchone() is None)
        admin.execute("CREATE DATABASE hpi_ingest_fixture")
        try:
            with psycopg.connect(dsn,dbname=DATABASE,autocommit=True) as conn:
                initialise(conn)
                report["stage"]="import"
                build=import_historical(conn,**intake)
                require(import_historical(conn,**intake)==build)
                expected=len(plan["sales"])
                require(conn.execute("SELECT COUNT(*) FROM hpi_candidate.sale_transactions").fetchone()[0]==expected)
                require(conn.execute("SELECT COUNT(*) FROM hpi_candidate.assessment_records").fetchone()[0]==len(by_key))
                require(conn.execute("SELECT COUNT(*) FROM hpi_candidate.source_snapshots").fetchone()[0]==4)
                require(conn.execute("SELECT COUNT(*) FROM hpi_candidate.investigations").fetchone()[0]==0)
                report["stored_sales"]=expected
                report["stored_parcel_years"]=len(by_key)
                report["stored_source_snapshots"]=4
                report["idempotent_import_verified"]=True
                report["stage"]="seal"
                seal=seal_historical(conn,**intake)
                require(seal["build_id"]==build)
                password=secrets.token_urlsafe(32)
                provision_reader(conn,password)
                report["stage"]="restricted_reader"
                with psycopg.connect(dsn,dbname=DATABASE,user=ROLE,password=password,autocommit=True) as rd:
                    reader=PrivateHistoricalReader(rd,seal)
                    for statement in ("SELECT count(*) FROM hpi_candidate.investigations",
                                      "UPDATE hpi_candidate.sale_transactions SET price_usd_cents=price_usd_cents",
                                      "CREATE TABLE hpi_candidate.forbidden(x int)","CREATE TEMP TABLE forbidden(x int)"):
                        try:
                            rd.execute(statement)
                        except psycopg.errors.InsufficientPrivilege:
                            pass
                        else:
                            raise ImportRefused("Reader permission denial failed")
                    report["reader_permission_denials_verified"]=4
                    report["stage"]="address_and_match"
                    status=Counter(); address=Counter(); selected=0
                    for sale in subjects:
                        p=by_key[sale["pin"],sale["assessment_year"]]
                        request={"township_code":"17","class_code":"203","analysis_date":sale["sale_date"],
                                 "subject":{"pin":sale["pin"],"building_area_sqft":p["building_area_sqft"]}}
                        result=reader.review(request)
                        reference=matcher_row(sale)
                        # Buyer matcher excludes the same parcel; source subject document
                        # is not supplied by the buyer request, so omit it for parity.
                        reference.pop("doc_no")
                        direct=match_property(reference,population)
                        expected_status=("supported_neighbourhood" if direct["tier"]=="same_neighborhood" else
                                         "exploratory_spatial" if direct["tier"]=="spatial_fallback" else "insufficient_data")
                        require(result["status"]==expected_status and result["tier"]==direct["tier"]
                                and result["selected_count"]==direct["selected_count"] and result["reason"]==direct["reason"])
                        require(set(result)=={"status","reason","selected_count","tier","warnings","evidence_details_redacted",
                                              "valuation","source_kind","historical_asof_verified","public_display_approved"})
                        require(result["valuation"] is None and result["evidence_details_redacted"] is True
                                and result["historical_asof_verified"] is False and result["public_display_approved"] is False)
                        status[expected_status]+=1
                        selected+=result["selected_count"]
                        if p["address_state"]!="one_nonblank":
                            address["unavailable"]+=1
                            continue
                        found=reader.search(p["display_address"],sale["sale_date"])
                        n=labels[p["tax_year"]," ".join(p["display_address"].casefold().split())]
                        require(found["candidate_count"]==n and found["building_identity_verified"] is False)
                        if n==1:
                            require(found["status"]=="one_eligible_candidate" and isinstance(found["address_id"],str))
                            request["subject"].pop("pin")
                            request["subject"]["address_id"]=found["address_id"]
                            require(reader.review(request)==result)
                            address["unique_token_review"]+=1
                        else:
                            require(found["status"]=="ambiguous" and found["address_id"] is None)
                            address["ambiguous_withheld"]+=1
                    report["reviewed_2025_subjects"]=len(subjects)
                    report["matched_status_counts"]={k:status[k] for k in ("supported_neighbourhood","exploratory_spatial","insufficient_data")}
                    report["selected_comparable_count_total"]=selected
                    report["address_review_counts"]={k:address[k] for k in ("unique_token_review","ambiguous_withheld","unavailable")}
                    report["canonical_match_parity_verified"]=len(subjects)
                    report["seal_verified"]=True
                require(conn.execute("SELECT COUNT(*) FROM hpi_candidate.investigations").fetchone()[0]==0)
                report["saved_investigations"]=0
        finally:
            # Preserve the failure stage unless cleanup itself fails.
            try:
                admin.execute("DROP DATABASE hpi_ingest_fixture")
                admin.execute("DROP ROLE IF EXISTS hpi_historical_reader")
                report["disposable_database_removed"]=True
            except Exception:
                report["stage"]="cleanup"
                raise
    report.update(status="completed",stage="completed")
    return report

def main():
    # No default execution path for the live collector. CI sets these only after
    # checking the unique marker addition and successful offline tests.
    report=new_report()
    logging.disable(logging.CRITICAL)
    try:
        require(os.environ.get("HPI_PRIVATE_REHEARSAL_TOKEN")==TOKEN and os.environ.get("GITHUB_ACTIONS")=="true"
                and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and os.environ.get("GITHUB_REF")=="refs/heads/development")
        dsn=os.environ["HPI_PG_DSN"]
        _scope(dsn)
        from audit.source_readiness.cohort_audit import meta,query
        report["stage"]="collection"
        intake=collect_intake(metadata=meta,page=query,extracted_at_utc=datetime.now(timezone.utc).isoformat())
        verify_rehearsal(dsn,intake,report)
    except Exception as exc:
        # The message may contain raw records, SQL, URLs or credentials. Only a
        # fixed class category is output, never str(exc), repr(exc), or traceback.
        report["error_category"]=("source_or_invariant" if isinstance(exc,(IntakeRefused,ImportRefused,ValueError))
                                  else "database" if isinstance(exc,psycopg.Error) else "transport_or_runtime")
    print(json.dumps(report,sort_keys=True),flush=True)
    return 0 if report["status"]=="completed" else 1

if __name__=="__main__":
    sys.exit(main())
