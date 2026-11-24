"""Private historical read preparation. No public endpoint, activation or network extraction.
A deployment-controlled seal is required; it is NOT a signature or a publisher licence.
The database reader is an internal trusted service principal, not a buyer account.
"""
from datetime import date
from hmac import compare_digest
import re
from psycopg import sql
from backend.curated_ingestion_candidate import ImportRefused
from backend.historical_migration import migration_history
from backend.historical_postgres import _plan_rows, _verify, _address_options, _address_key, _review_verified
from backend.postgres_fixture import FixtureConnection
from backend.postgres_ingestion import _check
from backend.real_source_intake import DATASETS, POLICY, digest, prepare_intake

ROLE="hpi_historical_reader"
SCHEMA="hpi_candidate"
# Static SQL scoped to the sealed build and its source snapshots. No buyer tables.
READ_TABLES=("schema_migrations","historical_migrations","curated_builds","curated_build_sources",
    "source_snapshots","historical_build_manifests","historical_address_states","parcels",
    "assessment_records","parcel_geographies","sale_transactions","sale_transaction_parcels","curated_build_transactions")

def provision_reader(conn,password):
    _check(conn)
    if not isinstance(password,str) or len(password)<24:
        raise ImportRefused("Random reader password required")
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(194323)")
        migration_history(conn)
        if conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s",(ROLE,)).fetchone():
            raise ImportRefused("Reader role already exists")
        conn.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS PASSWORD {}").format(sql.Identifier(ROLE),sql.Literal(password)))
        conn.execute("REVOKE ALL ON SCHEMA hpi_candidate FROM PUBLIC")
        conn.execute("REVOKE CONNECT,TEMPORARY ON DATABASE hpi_ingest_fixture FROM PUBLIC")
        conn.execute(sql.SQL("GRANT CONNECT ON DATABASE hpi_ingest_fixture TO {}").format(sql.Identifier(ROLE)))
        conn.execute(sql.SQL("GRANT USAGE ON SCHEMA hpi_candidate TO {}").format(sql.Identifier(ROLE)))
        conn.execute(sql.SQL("GRANT SELECT ON {} TO {}").format(
            sql.SQL(",").join(sql.Identifier(SCHEMA,t) for t in READ_TABLES),sql.Identifier(ROLE)))

def _reader(conn):
    if (conn.info.host,conn.info.dbname,conn.info.user)!=("127.0.0.1","hpi_ingest_fixture",ROLE) or not conn.autocommit:
        raise ImportRefused("Restricted loopback historical reader required")
    role=conn.execute("SELECT current_user,session_user,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolinherit FROM pg_roles WHERE rolname=current_user").fetchone()
    if role!=(ROLE,ROLE,False,False,False,False,False):
        raise ImportRefused("Invalid historical reader role")
    # Reject privilege drift, including ownership, inherited grants and temp schema.
    if conn.execute("SELECT has_schema_privilege(current_user,'hpi_candidate','CREATE'),has_database_privilege(current_user,current_database(),'TEMP')").fetchone()!=(False,False):
        raise ImportRefused("Historical reader privilege drift")
    rows=conn.execute("""SELECT c.relname,has_table_privilege(current_user,c.oid,'SELECT'),
        has_table_privilege(current_user,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER'),
        has_any_column_privilege(current_user,c.oid,'INSERT,UPDATE,REFERENCES'),
        pg_get_userbyid(c.relowner)=current_user
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='hpi_candidate' AND c.relkind IN ('r','p')""").fetchall()
    if {name for name,read,*_ in rows if read}!=set(READ_TABLES) or any(write or column or owner for _,_,write,column,owner in rows):
        raise ImportRefused("Historical reader privilege drift")
    if conn.execute("SELECT EXISTS(SELECT 1 FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user))").fetchone()[0]:
        raise ImportRefused("Historical reader role membership drift")
    migration_history(conn)

def _ids(build):
    if not isinstance(build,str) or not re.fullmatch(r"historical-[a-f0-9]{64}",build):
        raise ImportRefused("Invalid historical build")
    return {role:"historical-"+digest([build.removeprefix("historical-"),role]) for role in DATASETS}

def _fingerprint(conn,build):
    """Hash complete scoped relational evidence, including source flags and joins.
    Read all columns of the frozen tables so unexpected row edits change the seal.
    """
    ids=_ids(build); sid=tuple(ids.values()); parts={}
    queries={
      "build":("SELECT * FROM curated_builds WHERE build_id=?",(build,)),
      "manifest":("SELECT * FROM historical_build_manifests WHERE build_id=?",(build,)),
      "membership":("SELECT * FROM curated_build_sources WHERE build_id=?",(build,)),
      "snapshots":("SELECT * FROM source_snapshots WHERE snapshot_id IN (?,?,?,?)",sid),
      "assessment":("SELECT * FROM assessment_records WHERE snapshot_id=?",(ids["assessment"],)),
      "geography":("SELECT * FROM parcel_geographies WHERE snapshot_id=?",(ids["geography"],)),
      "addresses":("SELECT * FROM historical_address_states WHERE snapshot_id=?",(ids["address"],)),
      "sales":("SELECT * FROM sale_transactions WHERE snapshot_id=?",(ids["sales"],)),
      "links":("SELECT l.* FROM sale_transaction_parcels l JOIN sale_transactions t ON t.transaction_id=l.transaction_id WHERE t.snapshot_id=?",(ids["sales"],)),
      "transactions":("SELECT * FROM curated_build_transactions WHERE build_id=?",(build,)),
      "parcels":("SELECT p.* FROM parcels p WHERE p.pin IN (SELECT pin FROM assessment_records WHERE snapshot_id=?)",(ids["assessment"],)),
    }
    for name,(query,params) in queries.items():
        records=conn.execute(query,params).fetchall()
        parts[name]=sorted(digest(list(row)) for row in records)
    return digest(parts)

def seal_historical(conn,**intake):
    """Admin verifies against original intake once; store seal outside database.
    Do not log or expose to browser. No authenticity claim beyond verified input.
    """
    _check(conn)
    build,ids,rows=_plan_rows(prepare_intake(**intake))
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(194323)")
        migration_history(conn)
        adapter=FixtureConnection(conn)
        _verify(adapter,build,ids,rows)
        return {"build_id":build,"relational_sha256":_fingerprint(adapter,build)}

def _verified(conn,seal):
    _reader(conn)
    if not isinstance(seal,dict) or set(seal)!={"build_id","relational_sha256"}:
        raise ImportRefused("Trusted historical seal required")
    build=seal["build_id"]; ids=_ids(build)
    expected=seal["relational_sha256"]
    if not isinstance(expected,str) or not re.fullmatch(r"[a-f0-9]{64}",expected):
        raise ImportRefused("Invalid historical seal")
    adapter=FixtureConnection(conn)
    if not compare_digest(_fingerprint(adapter,build),expected):
        raise ImportRefused("Historical relational seal mismatch")
    row=adapter.execute("SELECT built_at_utc,build_kind FROM curated_builds WHERE build_id=?",(build,)).fetchone()
    if row is None or row[1]!="historical_research":
        raise ImportRefused("Historical build unavailable")
    snapshots=adapter.execute("SELECT dataset_id,historical_asof_verified,public_display_approved FROM source_snapshots WHERE snapshot_id IN (?,?,?,?)",tuple(ids.values())).fetchall()
    if set(snapshots)!={(d,0,0) for d in DATASETS.values()}:
        raise ImportRefused("Historical source disclosure boundary mismatch")
    return adapter,build,ids,row[0]

class PrivateHistoricalReader:
    """Internal read-only service with one server-selected external seal.
    This is not a public HTTP route; no raw extract required after sealing.
    """
    def __init__(self,conn,seal):
        self.conn=conn
        self.seal=dict(seal)
    def search(self,query,analysis_date):
        if not isinstance(query,str) or not query.strip() or len(query)>240:
            raise ImportRefused("Invalid historical address query")
        try:
            when=date.fromisoformat(analysis_date)
            if when.isoformat()!=analysis_date or when.year not in (2024,2025):raise ValueError
        except (TypeError,ValueError):
            raise ImportRefused("Historical analysis date outside intake window") from None
        with self.conn.transaction():
            self.conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            self.conn.execute("SET LOCAL statement_timeout='5000ms'")
            adapter,build,ids,_=_verified(self.conn,self.seal)
            matches=_address_options(adapter,build,ids["address"],when.year-1).get(_address_key(query),[])
            return {"status":"one_eligible_candidate" if len(matches)==1 else "ambiguous" if matches else "no_match",
                    "candidate_count":len(matches),"address_id":matches[0][1] if len(matches)==1 else None,
                    "identity_scope":"parcel_only","building_identity_verified":False}
    def review(self,request):
        with self.conn.transaction():
            self.conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            self.conn.execute("SET LOCAL statement_timeout='5000ms'")
            adapter,build,ids,stamp=_verified(self.conn,self.seal)
            return _review_verified(adapter,build,ids,stamp,request)
