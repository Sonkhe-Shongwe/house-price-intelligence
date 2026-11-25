"""Shared empty-schema buyer ownership candidate, not a live runtime launcher."""
from hashlib import sha256
from pathlib import Path
from psycopg import sql
from backend.historical_migration import migration_history
from backend.curated_ingestion_candidate import ImportRefused
from backend.postgres_runtime import BUYER_TABLES, POLICIES, SEQUENCE, expected_qual, compact_sql

SCRIPT = Path(__file__).parent / "postgres_ownership_candidate.sql"
ROLE = "hpi_buyer_runtime"
SCHEMA = "hpi_candidate"


def _prepare_empty_buyer_schema(conn):
    """Caller must enforce target boundary; credentials and accounts are never seeded."""
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(194322)")
        migration_history(conn)
        conn.execute("SET LOCAL search_path TO hpi_candidate,pg_catalog")
        if conn.execute("SELECT to_regclass('workspace_owners'),to_regclass('buyer_ownership_migrations')").fetchone() != (None, None):
            raise ImportRefused("Existing buyer ownership requires review")
        if conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s",(ROLE,)).fetchone():
            raise ImportRefused("Existing buyer role requires review")
        for table in BUYER_TABLES:
            if conn.execute(sql.SQL("SELECT EXISTS(SELECT 1 FROM {})").format(sql.Identifier(SCHEMA,table))).fetchone()[0]:
                raise ImportRefused("Nonempty buyer table")
        raw=SCRIPT.read_bytes()
        conn.execute(raw.decode("utf-8"),prepare=False)
        conn.execute("CREATE TABLE buyer_ownership_migrations(version INTEGER PRIMARY KEY,script_sha256 TEXT NOT NULL)")
        conn.execute("INSERT INTO buyer_ownership_migrations VALUES(1,%s)",(sha256(raw).hexdigest(),))
        conn.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS NOREPLICATION").format(sql.Identifier(ROLE)))
        conn.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(conn.info.dbname),sql.Identifier(ROLE)))
        conn.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(sql.Identifier(SCHEMA),sql.Identifier(ROLE)))
        conn.execute(sql.SQL("GRANT SELECT, INSERT ON {} TO {}").format(sql.SQL(",").join(sql.Identifier(SCHEMA,t) for t in BUYER_TABLES),sql.Identifier(ROLE)))
        conn.execute(sql.SQL("GRANT UPDATE(note_text), DELETE ON hpi_candidate.shortlist_investigations TO {}").format(sql.Identifier(ROLE)))
        conn.execute(sql.SQL("GRANT USAGE ON SEQUENCE {} TO {}").format(sql.Identifier(SCHEMA,SEQUENCE),sql.Identifier(ROLE)))
        _verify_staged_buyer(conn)


def _verify_staged_buyer(conn):
    """Effective permissions on the dedicated buyer writer; no historical-source reads."""
    flags=conn.execute("SELECT rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolinherit,rolbypassrls,rolreplication FROM pg_roles WHERE rolname=%s",(ROLE,)).fetchone()
    if flags!=(False,False,False,False,False,False,False):
        raise ImportRefused("Buyer role flags drift")
    if conn.execute("SELECT EXISTS(SELECT 1 FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=%s))",(ROLE,)).fetchone()[0]:
        raise ImportRefused("Buyer role membership drift")
    if conn.execute("""SELECT has_database_privilege(%s,current_database(),'CONNECT'),
       has_database_privilege(%s,current_database(),'CREATE,TEMP'),
       has_schema_privilege(%s,'hpi_candidate','USAGE'),
       has_schema_privilege(%s,'hpi_candidate','CREATE'),
       has_schema_privilege(%s,'public','CREATE')""",(ROLE,)*5).fetchone()!=(True,False,True,False,False):
        raise ImportRefused("Buyer namespace drift")
    rows=conn.execute("""WITH rel AS MATERIALIZED (
      SELECT c.oid,c.relname,c.relrowsecurity,c.relowner FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='hpi_candidate' AND c.relkind IN ('r','p','v','m','f'))
      SELECT relname,relrowsecurity,pg_get_userbyid(relowner),
      has_table_privilege(%s,oid,'SELECT'),has_table_privilege(%s,oid,'INSERT'),has_table_privilege(%s,oid,'DELETE'),
      has_table_privilege(%s,oid,'UPDATE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN'),
      has_any_column_privilege(%s,oid,'SELECT'),has_any_column_privilege(%s,oid,'INSERT'),
      has_any_column_privilege(%s,oid,'REFERENCES'),
      ARRAY(SELECT a.attname::text FROM pg_attribute a WHERE a.attrelid=rel.oid AND a.attnum>0
       AND NOT a.attisdropped AND has_column_privilege(%s,rel.oid,a.attnum,'UPDATE') ORDER BY a.attname)
      FROM rel""",(ROLE,)*8).fetchall()
    if not set(BUYER_TABLES)<={r[0] for r in rows}:
        raise ImportRefused("Buyer relations missing")
    for name,rls,owner,read,insert,delete,other,colread,colinsert,colref,updates in rows:
        buyer=name in BUYER_TABLES
        if (owner==ROLE or rls!=buyer or read!=buyer or insert!=buyer or colread!=buyer or colinsert!=buyer
            or delete!=(name=="shortlist_investigations") or other or colref
            or updates!=(["note_text"] if name=="shortlist_investigations" else [])):
            raise ImportRefused("Buyer relation privilege drift")
    seq=conn.execute("""WITH seq AS MATERIALIZED (
      SELECT c.oid,c.relname,c.relowner FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='hpi_candidate' AND c.relkind='S')
      SELECT relname,pg_get_userbyid(relowner),has_sequence_privilege(%s,oid,'USAGE'),
      has_sequence_privilege(%s,oid,'SELECT,UPDATE') FROM seq""",(ROLE,ROLE)).fetchall()
    if len(seq)!=1 or seq[0][0]!=SEQUENCE or seq[0][1]==ROLE or seq[0][2:]!=(True,False):
        raise ImportRefused("Buyer sequence drift")
    policies=conn.execute("SELECT tablename,policyname,permissive,roles::text,cmd,qual,with_check FROM pg_policies WHERE schemaname='hpi_candidate'").fetchall()
    if len(policies)!=len(POLICIES) or {p[0] for p in policies}!=set(POLICIES):
        raise ImportRefused("Buyer policy inventory drift")
    for table,name,permissive,roles,cmd,qual,check in policies:
        if (name!=POLICIES[table] or permissive!="PERMISSIVE" or roles!="{public}" or cmd!="ALL"
            or check is not None or compact_sql(qual)!=compact_sql(expected_qual(table))):
            raise ImportRefused("Buyer policy definition drift")
    if conn.execute("SELECT version,script_sha256 FROM hpi_candidate.buyer_ownership_migrations ORDER BY version").fetchall()!=[(1,sha256(SCRIPT.read_bytes()).hexdigest())]:
        raise ImportRefused("Buyer ownership checksum drift")
