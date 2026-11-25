"""Internal split-role persistence rehearsal; loopback invented fixtures only.
No live cloud connector, real-data activation or identity provider.
"""
from contextlib import contextmanager
from threading import RLock
from hashlib import sha256
from urllib.parse import urlsplit
from uuid import UUID, uuid4
import json
from backend.buyer_ownership import ROLE as BUYER, _verify_buyer_privileges
from backend.historical_reader import ROLE as READER, _verified, PrivateHistoricalReader
from backend.historical_postgres import _evaluate_verified
from backend.historical_beta_projection import project_rehearsal
from backend.investigation_contract import validate_request
from backend.synthetic_investigation_store import _json, _utc, _exact_money_cents
from backend.curated_ingestion_candidate import ImportRefused
from backend.oidc_boundary import OidcBoundary, AuthDenied

POLICY="historical-beta-rehearsal-v1"
OWNERS=frozenset(("fixture-owner-a","fixture-owner-b"))


def _connection(conn, role):
    if (conn.info.host,conn.info.dbname,conn.info.user)!=("127.0.0.1","hpi_ingest_fixture",role) or not conn.autocommit:
        raise ImportRefused("Restricted disposable connection required")
    if conn.execute("SELECT current_user,session_user").fetchone()!=(role,role):
        raise ImportRefused("Restricted session identity required")


class PrivateBetaRehearsal:
    def __init__(self, reader, writer, seal, boundary):
        _connection(reader,READER)
        _connection(writer,BUYER)
        if reader is writer or reader.info.port!=writer.info.port:
            raise ImportRefused("Separate roles on the same fixture required")
        if (not isinstance(boundary,OidcBoundary)
            or not (urlsplit(boundary.issuer).hostname or "").endswith(".invalid")
            or urlsplit(boundary.origin).hostname not in ("127.0.0.1","localhost")
            or set(boundary.owners.values())!=OWNERS):
            raise ImportRefused("Offline identity fixture required")
        self.reader,self.writer,self.seal,self.boundary=reader,writer,dict(seal),boundary
        self.request_lock=RLock()

    def _owner(self,cookie,method,origin=None,csrf=None):
        owner=self.boundary.authorize(cookie=cookie,method=method,origin=origin,csrf=csrf)
        if owner not in OWNERS:
            raise AuthDenied("Identity rejected")
        return owner

    @contextmanager
    def _source(self):
        _connection(self.reader,READER)
        with self.reader.transaction():
            self.reader.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            self.reader.execute("SET LOCAL statement_timeout='5000ms'")
            self.reader.execute("SET LOCAL lock_timeout='3000ms'")
            self.reader.execute("SELECT pg_advisory_xact_lock_shared(194323)")
            yield _verified(self.reader,self.seal)

    @contextmanager
    def _buyer(self,owner):
        _connection(self.writer,BUYER)
        with self.writer.transaction():
            self.writer.execute("SET LOCAL statement_timeout='5000ms'")
            self.writer.execute("SET LOCAL lock_timeout='3000ms'")
            self.writer.execute("SET LOCAL search_path TO hpi_candidate,pg_catalog")
            _verify_buyer_privileges(self.writer,login=True)
            if self.writer.execute("SELECT nullif(current_setting('hpi.owner_id',true),'')").fetchone()[0] is not None:
                raise ImportRefused("Unexpected buyer owner context")
            self.writer.execute("SELECT set_config('hpi.owner_id',%s,true)",(owner,))
            yield self.writer

    def search(self,query,analysis_date,*,cookie,origin,csrf):
        self._owner(cookie,"POST",origin,csrf)
        _connection(self.reader,READER)
        return PrivateHistoricalReader(self.reader,self.seal).search(query,analysis_date)

    def create(self,request,*,cookie,origin,csrf):
        owner=self._owner(cookie,"POST",origin,csrf)
        validated=validate_request(request)
        # Require a server-resolved address token; never accept a raw PIN or label.
        subject=validated["subject"]
        if subject["pin"] is not None or not subject.get("address_id") or subject["label"] is not None:
            raise ImportRefused("Private fixture address token required")
        with self._source() as (adapter,build,ids,stamp):
            evaluated=_evaluate_verified(adapter,build,ids,stamp,validated)
            result,selected,transactions,_=evaluated
            preview=project_rehearsal(*evaluated,ids)
            raw=_json(preview)
            identifier=str(uuid4())
            created=_utc(None)
            inputs=_json({"building_area_sqft":subject["building_area_sqft"],"asking_price_usd":subject["asking_price_usd"]})
            with self._buyer(owner) as conn:
                conn.execute("""INSERT INTO investigations(investigation_id,build_id,subject_pin,analysis_date,user_input_json,match_policy_version,evidence_status,created_at_utc)
                    VALUES(%s,%s,NULL,%s,%s,%s,%s,%s)""",(identifier,build,result["analysis_date"],inputs,POLICY,result["status"],created))
                conn.execute("INSERT INTO investigation_results VALUES(%s,%s,%s,%s)",(identifier,raw,sha256(raw.encode()).hexdigest(),created))
                for rank,item in enumerate(selected,1):
                    key=(item["pin"],item["document"],item["sale_date"])
                    transaction,snapshot,cents=transactions[key][0]
                    conn.execute("""INSERT INTO comparable_evidence(investigation_id,build_id,rank,transaction_id,selection_tier,explanation,source_snapshot_id,sale_price_usd_cents)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",(identifier,build,rank,transaction,result["tier"],"sealed historical rehearsal",snapshot,cents))
        return {"investigation_id":identifier,**preview}

    def reopen(self,identifier,*,cookie):
        owner=self._owner(cookie,"GET")
        try:
            if str(UUID(identifier))!=identifier:
                raise ValueError
        except (TypeError,ValueError,AttributeError):
            raise ImportRefused("Investigation unavailable") from None
        with self._source() as (adapter,build,ids,_):
            with self._buyer(owner) as conn:
                row=conn.execute("""SELECT i.build_id,i.evidence_status,i.analysis_date,i.match_policy_version,r.response_json,r.result_sha256
                    FROM investigations i JOIN investigation_results r USING(investigation_id) WHERE i.investigation_id=%s""",(identifier,)).fetchone()
                if row is None or row[0]!=build or row[3]!=POLICY or sha256(row[4].encode()).hexdigest()!=row[5]:
                    raise ImportRefused("Investigation unavailable")
                preview=json.loads(row[4])
                if (preview.get("source_kind")!="historical_shape_rehearsal" or preview.get("status")!=row[1]
                    or preview.get("analysis_date")!=row[2] or preview.get("provenance",{}).get("build_revision")!=build
                    or preview.get("valuation") is not None):
                    raise ImportRefused("Saved evidence mismatch")
                evidence=conn.execute("""SELECT rank,transaction_id,source_snapshot_id,sale_price_usd_cents,selection_tier,build_id
                    FROM comparable_evidence WHERE investigation_id=%s ORDER BY rank""",(identifier,)).fetchall()
                sales=preview["sales"]
                if len(evidence)!=len(sales) or len(sales)!=preview["selected_count"]:
                    raise ImportRefused("Saved evidence mismatch")
                for rank,(item,sale) in enumerate(zip(evidence,sales),1):
                    number,transaction,snapshot,cents,tier,bid=item
                    if (number!=rank or sale["rank"]!=rank or snapshot!=ids["sales"] or tier!=preview["tier"]
                        or bid!=build or _exact_money_cents(sale["sale_price_usd"])!=cents):
                        raise ImportRefused("Saved evidence mismatch")
                    source=adapter.execute("""SELECT t.snapshot_id,t.sale_date,t.price_usd_cents FROM sale_transactions t
                        JOIN curated_build_transactions b ON b.transaction_id=t.transaction_id WHERE t.transaction_id=? AND b.build_id=?""",(transaction,build)).fetchone()
                    if source!=(snapshot,sale["sale_date"],cents):
                        raise ImportRefused("Saved source evidence mismatch")
        return {"investigation_id":identifier,**preview}
