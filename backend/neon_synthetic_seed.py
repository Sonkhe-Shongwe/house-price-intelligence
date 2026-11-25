"""Fixed, invented-only seed plan for the persistent development rehearsal.
No network, DSN, arbitrary input, DDL or live data. The operator executes the
reviewed statements atomically against the explicitly selected development DB.
"""
import copy
import json
from hashlib import sha256
from psycopg import sql
from backend.real_source_intake import DATASETS, REQUIRED, OPTIONAL, prepare_intake
from backend.historical_postgres import _plan_rows
from backend.postgres_fixture import SCRIPTS
from backend.historical_migration import SCRIPT as HISTORICAL_SCRIPT
from backend.buyer_ownership import SCRIPT as BUYER_SCRIPT

APPLICATION_TABLES=tuple(sorted("""
assessment_records buildings candidate_addresses candidate_manifests comparable_evidence
curated_build_sources curated_build_transactions curated_builds historical_address_states
historical_build_manifests investigation_results investigations parcel_geographies parcels
sale_transaction_parcels sale_transactions shortlist_investigations shortlists source_snapshots
synthetic_address_candidates synthetic_address_index workspace_owners
""".split()))
METADATA=("schema_migrations","historical_migrations","buyer_ownership_migrations")
FIXTURE_OWNERS=("fixture-owner-a","fixture-owner-b")


def fixture_intake():
    """Same four invented parcels as the verified historical browser fixture."""
    pin="00000000000001"
    rows={
        "sales":[dict(pin=pin,sale_date="2025-04-01T00:00:00",sale_price="525000.01",doc_no="FICT-1",
            township_code="17",is_multisale=False,num_parcels_sale="1.0",sale_filter_less_than_10k=False,
            sale_filter_deed_type=False,sale_filter_same_sale_within_365=False)],
        "assessment":[dict(pin=pin,year="2024.0",card="1",**{"class":"203"},township_code="17",char_bldg_sf="1600")],
        "geography":[dict(pin=pin,year="2024.0",nbhd_code="FICT",lat="42.04",lon="-87.68")],
        "address":[dict(pin=pin,year="2024.0",prop_address_full="1 Fictional Court")],
    }
    for i in range(2,5):
        p=f"{i:014d}"
        rows["sales"].append(dict(rows["sales"][0],pin=p,doc_no=f"FICT-{i}",sale_date=f"2025-01-0{i}T00:00:00"))
        for role in ("assessment","geography","address"):
            rows[role].append(dict(rows[role][0],pin=p))
        rows["address"][-1]["prop_address_full"]=f"{i} Fictional Court"
    meta={dataset:{"epoch":1,"fields":sorted(REQUIRED[role]|OPTIONAL[role])} for role,dataset in DATASETS.items()}
    return dict(rows=rows,metadata_before=meta,metadata_after=copy.deepcopy(meta),extracted_at_utc="2026-11-24T00:00:00Z")


def fixture_plan():
    return _plan_rows(prepare_intake(**fixture_intake()))


def _migration_check(table,history):
    values=", ".join(sql.SQL("({}, {})").format(sql.Literal(v),sql.Literal(sha256(p.read_bytes()).hexdigest())).as_string() for v,p in history)
    name=sql.Identifier("hpi_candidate",table).as_string()
    return f"EXISTS ((SELECT version,script_sha256 FROM {name} EXCEPT VALUES {values}) UNION ALL (VALUES {values} EXCEPT SELECT version,script_sha256 FROM {name}))"


def seed_statements(*, disposable=False):
    """Only fixed records; caller MUST use a single transaction, never autocommit
    individual statements. Cloud default refuses nonempty or wrong-role targets.
    Disposable variant is for existing PostgreSQL CI only.
    """
    database,owner=("hpi_ingest_fixture","postgres") if disposable else ("hpi_private","hpi_private_owner")
    tables=APPLICATION_TABLES+METADATA
    names=", ".join(sql.Literal(t).as_string() for t in sorted(tables))
    target=f"""DO $$ BEGIN
        IF current_database()<>{sql.Literal(database).as_string()} OR current_user<>{sql.Literal(owner).as_string()}
           OR session_user<>current_user OR current_setting('server_version_num')::integer NOT BETWEEN 170000 AND 179999
           OR (SELECT array_agg(tablename::text ORDER BY tablename) FROM pg_tables WHERE schemaname='hpi_candidate')
              IS DISTINCT FROM ARRAY[{names}]::text[]
        THEN RAISE EXCEPTION 'Invented seed target refused'; END IF;
        END $$"""
    guards=[f"EXISTS(SELECT 1 FROM {sql.Identifier('hpi_candidate',t).as_string()})" for t in APPLICATION_TABLES]
    guards.extend((_migration_check("schema_migrations",SCRIPTS.items()),_migration_check("historical_migrations",[(1,HISTORICAL_SCRIPT)]),
                   _migration_check("buyer_ownership_migrations",[(1,BUYER_SCRIPT)])))
    guards.append("(SELECT count(*) FROM pg_policies WHERE schemaname='hpi_candidate')<>5")
    guards.append("""(SELECT count(*) FROM pg_roles WHERE rolname IN ('hpi_historical_reader','hpi_buyer_runtime')
        AND NOT rolcanlogin AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb
        AND NOT rolinherit AND NOT rolbypassrls AND NOT rolreplication)<>2""")
    guards.append("EXISTS(SELECT 1 FROM pg_stat_activity WHERE usename IN ('hpi_historical_reader','hpi_buyer_runtime'))")
    lock="LOCK TABLE "+", ".join(sql.Identifier("hpi_candidate",t).as_string() for t in tables)+" IN ACCESS EXCLUSIVE MODE"
    statements=["SET LOCAL statement_timeout='15000ms'","SET LOCAL lock_timeout='3000ms'",target,
                "SELECT pg_advisory_xact_lock(194322)","SELECT pg_advisory_xact_lock(194323)",lock,
                "DO $$ BEGIN IF "+" OR ".join(guards)+" THEN RAISE EXCEPTION 'Invented seed requires empty reviewed schema and disabled roles'; END IF; END $$"]
    _,_,rows=fixture_plan()
    for table,entries in rows.items():
        for columns,values,_ in entries:
            statements.append(sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier("hpi_candidate",table),sql.SQL(", ").join(map(sql.Identifier,columns)),
                sql.SQL(", ").join(map(sql.Literal,values))).as_string())
    for owner_id in FIXTURE_OWNERS:
        statements.append(sql.SQL("INSERT INTO hpi_candidate.workspace_owners(owner_id) VALUES ({})").format(sql.Literal(owner_id)).as_string())
    counts={table:len(rows.get(table,())) for table in APPLICATION_TABLES}
    counts["workspace_owners"]=len(FIXTURE_OWNERS)
    checks=[f"(SELECT count(*) FROM {sql.Identifier('hpi_candidate',t).as_string()})<>{n}" for t,n in counts.items()]
    statements.append("DO $$ BEGIN IF "+" OR ".join(checks)+" THEN RAISE EXCEPTION 'Invented seed counts mismatch'; END IF; END $$")
    return tuple(statements)


if __name__=="__main__":
    # Explicit invented-only SQL export; no database or credential access.
    print(json.dumps({"kind":"fixed-invented-development-seed","statements":seed_statements()},separators=(",",":")))
