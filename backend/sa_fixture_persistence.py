"""Optional additive persistence rehearsal, ONLY disposable fictional fixtures.

No HTTP wiring, live provider, arbitrary import, production auth or RLS.
Use the existing v3 fixture plus a separate checksummed extension ledger.
"""
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
import uuid

from backend import sa_investigation_v2 as sa
from backend.schema_migrations import migrate_fixture

SCRIPT = Path(__file__).with_name("sa_fixture_migration_v1.sql")
TABLES = {"sa_fixture_migrations", "sa_fixture_investigations"}
OWNERS = {"fictional-alice", "fictional-bob"}


class PersistenceError(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _owner(value):
    if not isinstance(value, str) or value not in OWNERS:
        raise PersistenceError("Unknown fictional owner")
    return value


def _id(value):
    if not isinstance(value,str) or not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", value):
        raise PersistenceError("Invalid fictional investigation ID")
    return value


def _seal(owner, iid, request, response):
    return sha256(canonical([owner,iid,request,response]).encode()).hexdigest()


def _sqlite_guard(conn):
    if not isinstance(conn,sqlite3.Connection) or conn.in_transaction:
        raise PersistenceError("Require idle disposable SQLite fixture")
    if any(name != "main" or file for _,name,file in conn.execute("PRAGMA database_list") if name!="temp"):
        raise PersistenceError("Only in-memory SQLite fixture allowed")
    if conn.execute("PRAGMA user_version").fetchone()[0] != 3:
        raise PersistenceError("Require current base v3 fixture")
    migrate_fixture(conn,target_version=3)
    from backend.synthetic_demo import in_memory_demo
    from backend.durable_fixture import _IMMUTABLE_SOURCE_TABLES
    reference,_=in_memory_demo()
    try:
        for table in _IMMUTABLE_SOURCE_TABLES:
            if sorted(conn.execute(f"SELECT * FROM {table}").fetchall(),key=repr)!=sorted(reference.execute(f"SELECT * FROM {table}").fetchall(),key=repr):
                raise PersistenceError("Not the trusted invented fixture")
    finally:
        reference.close()


def _pg_guard(conn):
    # Import only on the explicit disposable PostgreSQL path.
    from backend.postgres_fixture import PostgresFixtureStore, FixtureConnection
    if (conn.info.host,conn.info.dbname,conn.info.user)!=("127.0.0.1","hpi_fixture","postgres") or not conn.autocommit:
        raise PersistenceError("Only disposable loopback compatibility database allowed")
    PostgresFixtureStore(conn)  # exact v3 migration history and immutable invented sources
    return FixtureConnection(conn)


def _digest():
    return sha256(SCRIPT.read_bytes()).hexdigest()


def _verify(db):
    if db.execute("SELECT version,script_sha256 FROM sa_fixture_migrations").fetchall()!=[(1,_digest())]:
        raise PersistenceError("ZA extension migration checksum mismatch")


def _install(db, names):
    present=names & TABLES
    if present:
        if present!=TABLES:
            raise PersistenceError("Incomplete ZA extension")
        _verify(db)
        return
    # Execute individual trusted static statements inside one transaction;
    # avoid sqlite executescript's implicit commit.
    with db:
        if isinstance(db,sqlite3.Connection):
            db.execute("BEGIN IMMEDIATE")
        for stmt in SCRIPT.read_text(encoding="utf-8").split(";"):
            if stmt.strip():
                db.execute(stmt)
        db.execute("INSERT INTO sa_fixture_migrations VALUES (?,?)",(1,_digest()))
    _verify(db)


class FictionalStore:
    def __init__(self, db, owner):
        self._db=db
        self._owner=_owner(owner)
        _verify(db)

    def save(self, request, *, today=None):
        # Generate the response server-side; never accept client evidence.
        response=sa.investigate(request,today=today or date.today())
        iid=str(uuid.uuid4())
        token=response["subject"]["property_key"]["value"]
        asking=response["subject"]["asking_price"]
        cents=None if asking is None else asking["minor_units"]
        _verify(self._db)
        with self._db:
            self._db.execute("""INSERT INTO sa_fixture_investigations
                (owner_key,investigation_id,market,currency,area_unit,namespace,property_token,
                 build_id,policy_version,analysis_date,asking_cents,request_json,response_json,frozen_sha256)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (self._owner,iid,sa.MARKET,"ZAR","m2",sa.NAMESPACE,token,sa.BUILD,sa.POLICY,
                 response["analysis_date"],cents,canonical(request),canonical(response),
                 _seal(self._owner,iid,request,response)))
        return {"investigation_id":iid,"evidence":response}

    def reopen(self,iid):
        _id(iid)
        _verify(self._db)
        row=self._db.execute("""SELECT market,currency,area_unit,namespace,property_token,build_id,
              policy_version,analysis_date,asking_cents,request_json,response_json,frozen_sha256
              FROM sa_fixture_investigations WHERE owner_key=? AND investigation_id=?""",
              (self._owner,iid)).fetchone()
        if row is None:
            raise PersistenceError("Fictional investigation unavailable")
        try:
            req,res=json.loads(row[9]),json.loads(row[10])
            asking=res["subject"]["asking_price"]
            expected=(sa.MARKET,"ZAR","m2",sa.NAMESPACE,res["subject"]["property_key"]["value"],
                      sa.BUILD,sa.POLICY,res["analysis_date"],None if asking is None else asking["minor_units"])
            if (tuple(row[:9])!=expected or row[9]!=canonical(req) or row[10]!=canonical(res)
                or row[11]!=_seal(self._owner,iid,req,res)
                or res["contract_version"]!=sa.VERSION or res["source_kind"]!="synthetic_fixture"
                or res["real_data_approved"] is not False or res["valuation"] is not None):
                raise ValueError("Invalid frozen evidence")
            sa.validate_request(req,date.fromisoformat(res["analysis_date"]))
        except (ValueError,TypeError,KeyError,IndexError) as exc:
            raise PersistenceError("Frozen fictional evidence rejected") from exc
        return {"investigation_id":iid,"evidence":res}

    def history(self):
        _verify(self._db)
        rows=self._db.execute("""SELECT investigation_id FROM sa_fixture_investigations
                    WHERE owner_key=? ORDER BY investigation_id LIMIT 31""",(self._owner,)).fetchall()
        return {"market":"ZA","source_kind":"synthetic_fixture","truncated":len(rows)>30,
                "investigations":[self.reopen(row[0]) for row in rows[:30]]}


def sqlite_store(conn,owner):
    _owner(owner)
    _sqlite_guard(conn)
    names={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    _install(conn,names)
    return FictionalStore(conn,owner)


def postgres_store(conn,owner):
    _owner(owner)
    db=_pg_guard(conn)
    names={r[0] for r in db.execute("SELECT tablename FROM pg_tables WHERE schemaname='hpi_candidate'")}
    _install(db,names)
    return FictionalStore(db,owner)
