"""P0 NYC bounded acquisition: executable against an injected response transport.

No application runtime switch, credentials or record persistence. The local
launcher owns the operational protection and one-attempt boundary; ordinary
tests use invented responses only.
"""
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import http.client
import json
import re
import ssl
import time
from urllib.parse import urlencode

from tools.nyc_qualification import (
    Budget, FIELDS, MAX_AUX_ROWS, MAX_BATCH, MAX_KEYS, MAX_SALES, MAX_SECONDS,
    MAX_SUBJECTS, QualificationError, Subject, Sale, Master, Legal,
    bbl, valid_key, batches, require, complete_rows, projection,
    validate_projection, subject_query, sales_query, master_query, legal_query,
    comparable_attribute_query, verify_metadata, qualify, doc_value,
    HISTORICAL, CURRENT_SNAPSHOT, AREA_METHOD,
)

HOST = "data.cityofnewyork.us"


@contextmanager
def https_response(path, timeout):
    """Fixed-origin TLS GET; never redirect, use proxies, or log query values.

    A future protected launcher must provide an independent hard process
    deadline (DNS and blocking socket operations are not a hard wall clock).
    Not called by CI or any application/command entrypoint.
    """
    require(re.fullmatch(r"/(?:api/views/[a-z0-9]{4}-[a-z0-9]{4}\.json|"
                         r"resource/[a-z0-9]{4}-[a-z0-9]{4}\.json\?[^\r\n]+)", path),
            "invalid_endpoint")
    require(0 < timeout <= 15, "invalid_timeout")
    conn = http.client.HTTPSConnection(HOST, timeout=timeout,
                                      context=ssl.create_default_context())
    try:
        conn.request("GET", path, headers={"Accept": "application/json",
                                           "Accept-Encoding": "identity",
                                           "Connection": "close"})
        response = conn.getresponse()
        try:
            yield response
        finally:
            response.close()
    finally:
        conn.close()


def uint(value):
    require(type(value) in (int, str) and re.fullmatch(r"[0-9]+", str(value)),
            "invalid_integer")
    return int(value)


def exact_cents(value):
    require(type(value) in (int, str, Decimal)
            and re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", str(value)),
            "invalid_money")
    return int(Decimal(str(value))*100)


def day(value):
    require(isinstance(value, str)
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)?", value),
            "invalid_date")
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        raise QualificationError("invalid_date") from None


def numeric_key(value):
    # Socrata Number may be encoded as an integral decimal string.
    require(type(value) in (int, str, Decimal)
            and re.fullmatch(r"[0-9]{10}(?:\.0+)?", str(value)), "invalid_bbl")
    key = str(value).split(".")[0]
    require(valid_key(key), "invalid_bbl")
    return key


def strict_pairs(items):
    result = {}
    for k, v in items:
        require(k not in result, "duplicate_json_field")
        result[k] = v
    return result


def invalid_constant(_):
    raise QualificationError("invalid_json_number")


@dataclass(frozen=True)
class FixturePlan:
    """Invented manifest only. No production/live constructor or activation.

    A real plan must bind exact approved source releases and independently
    reviewed date/area/rights evidence to the protected one-time launcher.
    """
    cutoff: date
    covered_from: date
    covered_through: date
    snapshot: date
    version: str
    # Explicit fixture evidence, never inferred from DOF row presence.
    historical_area_verified: bool = False
    mode: str = HISTORICAL


class Collector:
    def __init__(self, transport, clock=time.monotonic):
        self._transport = transport
        self._clock = clock
        self._start = clock()
        self.budget = Budget()
        self._used = False

    def _elapsed(self):
        seconds = self._clock()-self._start
        require(0 <= seconds < MAX_SECONDS, "time_limit")
        return seconds

    def _json(self, dataset, params=None):
        require(dataset in FIELDS, "unsupported_source")
        path = (f"/api/views/{dataset}.json" if params is None else
                f"/resource/{dataset}.json?"+urlencode(params))
        remaining = self.budget.reserve(int(self._elapsed()))
        content = bytearray()
        try:
            with self._transport(path, min(15, MAX_SECONDS-self._elapsed())) as response:
                require(response.status == 200, "http_status")
                require(response.getheader("Content-Type", "").split(";")[0].strip().lower()
                        == "application/json", "unexpected_content_type")
                require(response.getheader("Content-Encoding", "identity").lower()
                        == "identity", "unexpected_encoding")
                length = response.getheader("Content-Length")
                # Exact boundary and short read validation. No unbounded/chunked
                # response without independent framing proof in this version.
                require(length is not None, "missing_content_length")
                expected = uint(length)
                require(0 < expected <= remaining, "byte_limit")
                while len(content) < expected:
                    self._elapsed()
                    chunk = response.read1(min(65536, expected-len(content)))
                    require(type(chunk) is bytes and 0 < len(chunk) <= expected-len(content),
                            "incomplete_response")
                    content.extend(chunk)
                self._elapsed()
            value = json.loads(content, object_pairs_hook=strict_pairs,
                               parse_float=Decimal, parse_constant=invalid_constant)
            # Account even if a subsequent schema validation rejects the result.
            self.budget.account(len(content), 0, "metadata", int(self._elapsed()))
            return value
        except QualificationError:
            raise
        except Exception:
            # Never print raw exception, URL, record, query, or response.
            raise QualificationError("transport_or_json_failure") from None

    def _metadata(self, dataset):
        raw = self._json(dataset)
        require(isinstance(raw, dict) and raw.get("id") == dataset
                and isinstance(raw.get("columns"), list), "source_schema_unverified")
        # Exclude cached contents and sample values.
        columns = raw["columns"]
        require(all(isinstance(c, dict) and isinstance(c.get("fieldName"), str)
                    and isinstance(c.get("dataTypeName"), str) for c in columns),
                "source_schema_unverified")
        types = {c["fieldName"]: c["dataTypeName"] for c in columns}
        require(len(types) == len(columns), "source_schema_unverified")
        revisions = [raw.get(k) for k in ("rowsUpdatedAt", "viewLastModified")]
        require(all(type(x) is int and x > 0 for x in revisions), "source_revision_unverified")
        result = {"id": dataset, "revision": ":".join(map(str, revisions)),
                  "fields": list(types)}
        verify_metadata(dataset, result, result, subject=dataset == "64uk-42ks")
        return result, types

    def _count(self, query, select="count(*) as n", names=("n",)):
        params = query.parameters(count=True)
        params["$select"] = select
        rows = self._json(query.dataset, params)
        require(isinstance(rows, list) and len(rows) == 1
                and isinstance(rows[0], dict) and set(rows[0]) == set(names),
                "invalid_count")
        return tuple(uint(rows[0][name]) for name in names)

    def _rows(self, query, kind="aux", subject=False, expected=None):
        count = self._count(query)[0] if expected is None else expected
        cap = (MAX_SALES-self.budget.sales_rows if kind == "sales"
               else MAX_AUX_ROWS-self.budget.aux_rows)
        require(0 <= count <= min(query.limit, cap), "count_limit")
        if count == 0:
            return ()
        params = query.parameters()
        params["$limit"] = str(count)
        rows = self._json(query.dataset, params)
        require(isinstance(rows, list), "invalid_rows")
        # Even unexpected returned rows consume budget; then fail closed.
        self.budget.account(0, len(rows), kind, int(self._elapsed()))
        validate_projection(query.dataset, rows, subject=subject)
        return complete_rows(rows, count, min(query.limit, cap))

    def run_fixture(self, plan):
        require(type(plan) is FixturePlan and self._transport is not https_response,
                "live_execution_disabled")
        require(not self._used, "attempt_already_consumed")
        self._used = True
        try:
            return self._run(plan)
        except QualificationError:
            raise
        except Exception:
            raise QualificationError("normalisation_failure") from None

    def metadata_summary(self):
        """Return only exact projected field types/revisions, never cached examples."""
        result = {}
        for dataset in FIELDS:
            metadata, types = self._metadata(dataset)
            result[dataset] = {"revision": metadata["revision"],
                               "types": {name: types[name] for name in projection(
                                   dataset, subject=dataset == "64uk-42ks")}}
        return result

    def _run(self, plan, reviewed_sources=None):
        require(all(type(x) is date for x in (plan.cutoff, plan.covered_from,
                    plan.covered_through, plan.snapshot))
                and plan.snapshot <= plan.cutoff and isinstance(plan.version, str)
                and bool(plan.version), "invalid_plan")
        require(plan.mode in (HISTORICAL, CURRENT_SNAPSHOT), "unknown_comparison_mode")
        require(plan.mode != CURRENT_SNAPSHOT or plan.historical_area_verified is False,
                "mixed_temporal_evidence")
        before = {d: self._metadata(d) for d in FIELDS}
        if reviewed_sources is not None:
            require(plan.mode == CURRENT_SNAPSHOT and plan.historical_area_verified is False
                    and isinstance(reviewed_sources, dict)
                    and set(reviewed_sources) == set(FIELDS), "invalid_reviewed_sources")
            for d, (metadata, types) in before.items():
                expected = {"revision": metadata["revision"],
                            "types": {name: types[name] for name in projection(
                                d, subject=d == "64uk-42ks")}}
                require(reviewed_sources[d] == expected, "reviewed_source_changed")
        # Published PLUTO ZIP and BBL are Number; rolling borough is Text.
        require(before["64uk-42ks"][1].get("zipcode") == "number"
                and before["64uk-42ks"][1].get("bbl") == "number"
                and before["usep-8jbt"][1].get("borough") == "text",
                "source_type_unverified")
        if plan.mode == CURRENT_SNAPSHOT:
            require(before["64uk-42ks"][1].get("areasource") == "text",
                    "source_type_unverified")
        sq = subject_query(plan.mode)
        n, keys, addresses = self._count(sq,
            "count(*) as n,count(distinct bbl) as keys,count(distinct address) as addresses",
            ("n", "keys", "addresses"))
        require(n >= MAX_SUBJECTS and n == keys == addresses, "ambiguous_subject_frame")
        rows = self._rows(sq, subject=True, expected=MAX_SUBJECTS)
        subjects = []
        labels = []
        for row in rows:
            key = numeric_key(row["bbl"])
            label = row["address"]
            require(isinstance(label, str) and bool(label.strip())
                    and row["borough"] == "QN" and uint(row["zipcode"]) == 11361
                    and row["bldgclass"] == "A2" and uint(row["numbldgs"]) == 1
                    and uint(row["unitsres"]) == uint(row["unitstotal"]) == 1
                    and uint(row["bldgarea"]) > 0 and row["version"] == plan.version,
                    "subject_scope_conflict")
            if plan.mode == CURRENT_SNAPSHOT:
                require(row.get("areasource") == AREA_METHOD, "subject_area_method_conflict")
            labels.append(" ".join(label.upper().split()))
            subjects.append(Subject(key, uint(row["bldgarea"]), plan.snapshot,
                                    plan.version, True, True, row.get("areasource")))
        require(len(set(labels)) == MAX_SUBJECTS
                and [s.key for s in subjects] == sorted({s.key for s in subjects}),
                "ambiguous_subject_frame")
        # Subject rows/addresses do not leave memory or appear in output.
        del rows, labels
        raw_sales = self._rows(sales_query(plan.covered_from, plan.covered_through,
                                         plan.cutoff), "sales")
        sales = []
        for row in raw_sales:
            require(row["borough"] in ("4", "QUEENS") and row["neighborhood"] == "BAYSIDE"
                    and uint(row["zip_code"]) == 11361
                    and row["building_class_at_time_of_sale"] == "A2", "sale_scope_conflict")
            key = bbl(4, row["block"], row["lot"])
            sold = day(row["sale_date"])
            require(plan.covered_from <= sold <= plan.covered_through
                    and sold < plan.cutoff, "sale_date_scope_conflict")
            # Malformed/missing descriptive fields abstain, not fabricated zero.
            try:
                price = exact_cents(row["sale_price"])
                area = uint(row["gross_square_feet"])
                eligible = (price > 0 and area > 0 and uint(row["residential_units"]) == 1
                            and uint(row["commercial_units"]) == 0
                            and uint(row["total_units"]) == 1)
            except (QualificationError, KeyError):
                price, area, eligible = 0, 0, False
            sales.append(Sale(key, sold, price, area, eligible,
                              plan.mode == HISTORICAL and plan.historical_area_verified is True))
        del raw_sales
        all_keys = {s.key for s in subjects} | {s.key for s in sales}
        require(len(all_keys) <= MAX_KEYS, "key_limit")
        # Verify present-day candidate shape separately; cannot prove historical area.
        attrs = {}
        for batch in batches({s.key for s in sales}):
            for row in self._rows(comparable_attribute_query(batch)):
                key = numeric_key(row["bbl"])
                require(key in batch and key not in attrs, "attribute_identity_conflict")
                require(row.get("version") == plan.version, "attribute_version_conflict")
                attrs[key] = row
        checked = []
        for s in sales:
            a = attrs.get(s.key, {})
            try:
                current_shape = (a["borough"] == "QN" and a["bldgclass"] == "A2"
                                 and uint(a["zipcode"]) == 11361
                                 and uint(a["numbldgs"]) == uint(a["unitsres"])
                                 == uint(a["unitstotal"]) == 1 and uint(a["bldgarea"]) > 0)
            except (KeyError, QualificationError):
                current_shape = False
            if plan.mode == CURRENT_SNAPSHOT and current_shape:
                checked.append(replace(s, eligible=s.eligible and current_shape,
                                       snapshot_area=uint(a["bldgarea"]),
                                       snapshot_date=plan.snapshot,
                                       snapshot_version=plan.version,
                                       area_source=a.get("areasource")))
            else:
                checked.append(replace(s, eligible=s.eligible and current_shape))
        sales = checked
        # No ACRIS requests for already unqualified events.
        events = [s for s in sales if s.eligible and (
            s.dated_area if plan.mode == HISTORICAL else
            s.snapshot_area == s.area and s.area_source == AREA_METHOD)]
        # Avoid repeating the same instrument search across batches.
        events = list({(s.day, s.cents): s for s in events}.values())
        masters = []
        seen_docs = set()
        for i in range(0, len(events), MAX_BATCH):
            batch = events[i:i+MAX_BATCH]
            pairs = {(s.day, s.cents) for s in batch}
            for row in self._rows(master_query(batch)):
                doc = row["document_id"]
                require(doc_value(doc) and doc not in seen_docs, "master_identity_conflict")
                seen_docs.add(doc)
                mday, cents = day(row["document_date"]), exact_cents(row["document_amt"])
                require((mday, cents) in pairs, "master_scope_conflict")
                # Missing transfer percentage never accepted.
                pct = row.get("percent_trans")
                try:
                    pct = Decimal(str(pct))
                    if not pct.is_finite():
                        pct = Decimal(-1)
                except InvalidOperation:
                    pct = Decimal(-1)
                masters.append(Master(doc, row.get("doc_type", ""), mday,
                                      day(row["recorded_datetime"]), cents, pct))
        legals = []
        docs = sorted(seen_docs)
        for i in range(0, len(docs), MAX_BATCH):
            batch = docs[i:i+MAX_BATCH]
            for row in self._rows(legal_query(batch)):
                require(row["document_id"] in batch, "legal_scope_conflict")
                key = bbl(row["borough"], row["block"], row["lot"])
                all_keys.add(key)
                require(len(all_keys) <= MAX_KEYS, "key_limit")
                legals.append(Legal(row["document_id"], key, row.get("partial_lot") == "E",
                                    row.get("property_type") == "D1",
                                    all(row.get(k) == "N" for k in
                                        ("easement", "air_rights", "subterranean_rights"))))
        after = {d: self._metadata(d) for d in FIELDS}
        for d in FIELDS:
            verify_metadata(d, before[d][0], after[d][0], subject=d == "64uk-42ks")
            require(before[d][1] == after[d][1], "source_type_changed")
        result = qualify(subjects, sales, masters, legals, cutoff=plan.cutoff,
                         covered_from=plan.covered_from, covered_through=plan.covered_through,
                         frame_complete=True, source_complete=True, source_versions_stable=True,
                         mode=plan.mode)
        result.update(fixture_only=reviewed_sources is None, frame_count=n,
                      evaluation_cutoff=plan.cutoff.isoformat(),
                      sales_covered_from=plan.covered_from.isoformat(),
                      sales_covered_through=plan.covered_through.isoformat(),
                      requests=self.budget.requests, bytes_received=self.budget.bytes_received,
                      auxiliary_rows=self.budget.aux_rows,
                      source_revisions={d: before[d][0]["revision"] for d in FIELDS})
        return result
