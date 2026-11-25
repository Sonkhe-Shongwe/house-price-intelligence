"""Internal split-role persistence rehearsal; loopback invented fixtures only.
No live cloud connector, real-data activation or identity provider.
"""
from contextlib import contextmanager
from threading import RLock
from hashlib import sha256
from urllib.parse import urlsplit
from uuid import UUID, uuid4
import json
import re
from backend.buyer_ownership import ROLE as BUYER, _verify_buyer_privileges
from backend.historical_reader import ROLE as READER, _verified, PrivateHistoricalReader
from backend.historical_seal_config import load_historical_seal
from backend.historical_postgres import _evaluate_verified
from backend.historical_beta_projection import project_rehearsal
from backend.investigation_contract import validate_request
from backend.synthetic_investigation_store import _json, _utc, _exact_money_cents
from backend.curated_ingestion_candidate import ImportRefused
from backend.oidc_boundary import OidcBoundary, AuthDenied
from backend.synthetic_shortlists import MAX_ENTRIES, ShortlistError, _uuid, _note, _require_object

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

    @classmethod
    def from_seal_file(cls, reader, writer, seal_path, boundary):
        """Load operator-held private seal and verify source before serving.
        
        Still loopback invented fixtures only. No cloud or live-source switch.
        """
        service = cls(reader, writer, load_historical_seal(seal_path), boundary)
        with service._source():
            pass
        return service

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
            # Internal build-scoped duplicate-detection key for invented parcels.
            # Not a public identifier or an anonymity guarantee.
            pin=result["subject"]["pin"]
            if not isinstance(pin,str) or not re.fullmatch(r"[0-9]{14}",pin):
                raise ImportRefused("Unresolved comparison identity")
            parcel_key=sha256((build+":"+pin).encode()).hexdigest()
            inputs=_json({"building_area_sqft":subject["building_area_sqft"],"asking_price_usd":subject["asking_price_usd"],"parcel_key":parcel_key})
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
                preview,_=self._saved(conn,adapter,build,ids,identifier)
        return preview

    def _saved(self,conn,adapter,build,ids,identifier):
        """One frozen-evidence verifier for reopen and comparison."""
        row=conn.execute("""SELECT i.build_id,i.evidence_status,i.analysis_date,i.match_policy_version,r.response_json,r.result_sha256,i.user_input_json
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
        key=json.loads(row[6]).get("parcel_key")
        return {"investigation_id":identifier,**preview},key

    @staticmethod
    def _comparison_payload(payload):
        payload=_require_object(payload,{"label","entries"},{"label","entries"})
        label=payload["label"]
        if (not isinstance(label,str) or not 1<=len(label.strip())<=80
                or any(ord(c)<32 for c in label)):
            raise ShortlistError("invalid_shortlist_label")
        entries=payload["entries"]
        if not isinstance(entries,list) or not 2<=len(entries)<=MAX_ENTRIES:
            raise ShortlistError("comparison_requires_two_or_three")
        clean=[]
        for item in entries:
            item=_require_object(item,{"investigation_id","note_text"},{"investigation_id"})
            clean.append((_uuid(item["investigation_id"]),_note(item.get("note_text",""))))
        if len({iid for iid,_ in clean})!=len(clean):
            raise ShortlistError("duplicate_investigation",409)
        return label.strip(),clean

    def _comparison_entries(self,conn,adapter,build,ids,members):
        if not 2<=len(members)<=MAX_ENTRIES:
            raise ImportRefused("Stored comparison size invalid")
        seen=set(); entries=[]
        for iid,note in members:
            result,key=self._saved(conn,adapter,build,ids,iid)
            if not isinstance(key,str) or not re.fullmatch(r"[a-f0-9]{64}",key):
                raise ImportRefused("Comparison identity unavailable")
            if key in seen:
                raise ShortlistError("duplicate_property",409)
            seen.add(key)
            entries.append({"investigation_id":iid,"note_text":_note(note or ""),"investigation":result})
        return entries

    def create_comparison(self,payload,*,cookie,origin,csrf):
        owner=self._owner(cookie,"POST",origin,csrf)
        label,members=self._comparison_payload(payload)
        sid=str(uuid4()); created=_utc(None)
        with self._source() as (adapter,build,ids,_):
            with self._buyer(owner) as conn:
                entries=self._comparison_entries(conn,adapter,build,ids,members)
                conn.execute("INSERT INTO shortlists(shortlist_id,label,created_at_utc) VALUES(%s,%s,%s)",(sid,label,created))
                for iid,note in members:
                    conn.execute("INSERT INTO shortlist_investigations(shortlist_id,investigation_id,note_text) VALUES(%s,%s,%s)",(sid,iid,note))
        return {"source_kind":"historical_shape_rehearsal","shortlist_id":sid,"label":label,"created_at_utc":created,"entries":entries}

    def reopen_comparison(self,identifier,*,cookie):
        owner=self._owner(cookie,"GET")
        sid=_uuid(identifier)
        with self._source() as (adapter,build,ids,_):
            with self._buyer(owner) as conn:
                row=conn.execute("SELECT label,created_at_utc FROM shortlists WHERE shortlist_id=%s",(sid,)).fetchone()
                if row is None:
                    raise ImportRefused("Comparison unavailable")
                members=conn.execute("SELECT investigation_id,note_text FROM shortlist_investigations WHERE shortlist_id=%s ORDER BY member_order",(sid,)).fetchall()
                entries=self._comparison_entries(conn,adapter,build,ids,members)
        return {"source_kind":"historical_shape_rehearsal","shortlist_id":sid,"label":row[0],"created_at_utc":row[1],"entries":entries}
