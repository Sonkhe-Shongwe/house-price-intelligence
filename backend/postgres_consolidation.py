"""Consolidated fictional PostgreSQL source lifecycle, never a real-data loader."""
from datetime import datetime,timezone
from hashlib import sha256
from psycopg import sql
from backend.curated_ingestion_candidate import CANDIDATE_DDL,_plan,_import_rows,import_fixture
from backend.postgres_fixture import FixtureConnection,SCRIPTS
from backend.synthetic_demo import BUILD_ID,in_memory_demo
from backend.durable_fixture import _IMMUTABLE_SOURCE_TABLES
from backend.synthetic_investigation_store import SyntheticInvestigationStore,EvidenceStoreError

REVISIONS={_plan(r)[2]:r for r in ("v1","v2","v3","v4","v5")}
BUILDS=(BUILD_ID,*REVISIONS)
SOURCE_LOCK=194324
TABLES=(*_IMMUTABLE_SOURCE_TABLES,"candidate_manifests","candidate_addresses")
DDL="""
CREATE TABLE active_fixture_build (
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    build_id TEXT NOT NULL REFERENCES curated_builds(build_id),
    generation BIGINT NOT NULL CHECK(generation>=0)
);
CREATE TABLE fixture_build_events (
    generation BIGINT PRIMARY KEY,
    previous_build TEXT REFERENCES curated_builds(build_id),
    build_id TEXT NOT NULL REFERENCES curated_builds(build_id),
    changed_at_utc TEXT NOT NULL
);
"""

def prepare(conn):
    """Caller owns fresh bootstrap transaction; no changes to existing databases."""
    conn.execute(CANDIDATE_DDL,prepare=False)
    adapter=FixtureConnection(conn)
    for revision in REVISIONS.values():_import_rows(adapter,revision)
    conn.execute(DDL,prepare=False)
    conn.execute("INSERT INTO active_fixture_build VALUES(1,%s,0)",(BUILD_ID,))
    conn.execute("INSERT INTO fixture_build_events VALUES(0,NULL,%s,%s)",(BUILD_ID,now()))
    verify_sources(conn)

def now():return datetime.now(timezone.utc).isoformat()

def verify_sources(conn):
    history=conn.execute("SELECT version,script_sha256 FROM schema_migrations ORDER BY version").fetchall()
    if history!=[(i,sha256(p.read_bytes()).hexdigest()) for i,p in SCRIPTS.items()]:
        raise EvidenceStoreError("Migration history mismatch")
    # Exact whole-source union: no unreviewed source rows or invented revisions.
    reference,_=in_memory_demo()
    try:
        reference.executescript(CANDIDATE_DDL)
        for revision in REVISIONS.values():import_fixture(reference,revision)
        for table in TABLES:
            actual=conn.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))).fetchall()
            expected=reference.execute("SELECT * FROM "+table).fetchall()
            if sorted(actual,key=repr)!=sorted(expected,key=repr):
                raise EvidenceStoreError("Consolidated fixture source mismatch")
    finally:reference.close()

def active(conn):
    row=conn.execute("SELECT build_id,generation FROM active_fixture_build WHERE singleton=1").fetchone()
    if row is None or row[0] not in BUILDS:raise EvidenceStoreError("Unknown active build")
    events=conn.execute("SELECT generation,previous_build,build_id FROM fixture_build_events ORDER BY generation").fetchall()
    if not events or events[0]!=(0,None,BUILD_ID) or events[-1]!=(row[1],events[-1][1],row[0]):
        raise EvidenceStoreError("Activation history mismatch")
    if any(g!=i or target not in BUILDS or (i and (prev!=events[i-1][2] or prev==target)) for i,(g,prev,target) in enumerate(events)):
        raise EvidenceStoreError("Invalid activation history")
    return row

def activate(admin_dsn,target,expected_generation):
    """Admin-only CAS; no HTTP endpoint. Rollback is another append-only event."""
    import psycopg
    from backend.postgres_runtime import _dsn_check
    _dsn_check(admin_dsn,"postgres")
    if target not in BUILDS or type(expected_generation) is not int:raise ValueError("Unreviewed build or generation")
    with psycopg.connect(admin_dsn,autocommit=True) as conn:
        with conn.transaction():
            conn.execute("SET LOCAL search_path TO hpi_candidate,pg_catalog")
            conn.execute("SET LOCAL lock_timeout='4000ms'")
            conn.execute("SELECT pg_advisory_xact_lock(%s)",(SOURCE_LOCK,))
            verify_sources(conn)
            old,generation=active(conn)
            if generation!=expected_generation:raise ValueError("Stale activation generation")
            if old==target:return generation
            conn.execute("INSERT INTO fixture_build_events VALUES(%s,%s,%s,%s)",(generation+1,old,target,now()))
            conn.execute("UPDATE active_fixture_build SET build_id=%s,generation=%s WHERE singleton=1",(target,generation+1))
            return generation+1

class RevisionStore(SyntheticInvestigationStore):
    def __init__(self,connection,build):
        if build not in BUILDS:raise EvidenceStoreError("Unreviewed build")
        self.connection=connection
        self.build_id=build
        self._build()
    def _address_rows(self):
        revision=REVISIONS[self.build_id]
        sid=_plan(revision)[1]["address"]["snapshot_id"]
        return self.connection.execute("SELECT pin,display_address,search_key FROM candidate_addresses WHERE snapshot_id=? AND tax_year=2023 ORDER BY display_address,pin",(sid,)).fetchall()
    def search_synthetic_addresses(self,query):
        if self.build_id==BUILD_ID:return super().search_synthetic_addresses(query)
        self._build()
        import re
        from collections import Counter
        key=" ".join(re.findall(r"[a-z0-9]+",query.casefold()))
        rows=self._address_rows()
        norm=lambda x:" ".join(re.findall(r"[a-z0-9]+",x.casefold()))
        counts=Counter(norm(label) for _,label,_ in rows)
        found=[]
        for pin,label,_ in rows:
            if key and key in norm(label):
                ambiguous=counts[norm(label)]>1
                found.append({"address_id":REVISIONS[self.build_id]+"-"+pin,"display_address":label,
                              "ambiguous_address":ambiguous,"parcel_hint":"Synthetic parcel "+str(int(pin)) if ambiguous else None,"identity_scope":"parcel_only"})
        return {"source_kind":"synthetic_fixture","status":"matches" if found else "no_match","candidates":found[:8],"truncated":len(found)>8}
    def resolve_synthetic_address(self,address_id):
        if self.build_id==BUILD_ID:return super().resolve_synthetic_address(address_id)
        self._build()
        for pin,label,_ in self._address_rows():
            if address_id==REVISIONS[self.build_id]+"-"+pin:
                return {"source_kind":"synthetic_fixture","identity_status":"synthetic_mapping_only","identity_scope":"parcel_only",
                        "building_identity_verified":False,"address_id":address_id,"display_address":label,"pin":pin,
                        "parcel_hint":"Synthetic parcel "+str(int(pin))}
        return None

class ConsolidatedStore(RevisionStore):
    """New enquiries bind to active build; older evidence uses its own reviewed build."""
    def __init__(self,conn):
        self.connection=FixtureConnection(conn)
        verify_sources(conn)
        build,_=active(conn)
        super().__init__(self.connection,build)
    def reopen(self,iid):
        row=self.connection.execute("SELECT build_id FROM investigations WHERE investigation_id=?",(iid,)).fetchone()
        if row is None:raise EvidenceStoreError("Investigation not found")
        return RevisionStore(self.connection,row[0]).reopen(iid)
    def _history_rows(self):
        return self.connection.execute("SELECT investigation_id,created_at_utc,analysis_date FROM investigations ORDER BY created_at_utc DESC,investigation_id DESC LIMIT 31").fetchall()
    def shortlist_policy(self,iid):
        return self.connection.execute("SELECT match_policy_version FROM investigations WHERE investigation_id=?",(iid,)).fetchone()
    def verify_map_fixture(self):
        verify_sources(self.connection.raw)
