"""Bounded NYC qualification core. No network, file, CLI or runtime activation.

Only the offline contract is implemented. A separately reviewed protected
collector must prove metadata, completeness and source semantics before any
real use. Never pass actual rows to public CI.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
import re

MAX_SUBJECTS = 30
MAX_SALES = 500
MAX_KEYS = 500
MAX_AUX_ROWS = 10_000
MAX_BATCH = 35
MAX_REQUESTS = 100
MAX_BYTES = 20 * 1024 * 1024
MAX_SECONDS = 1800

# Candidate projections; exact API schema and type preflight still required.
FIELDS = {
    "usep-8jbt": ("borough", "block", "lot", "neighborhood", "zip_code",
                  "building_class_at_time_of_sale", "gross_square_feet",
                  "residential_units", "commercial_units", "total_units",
                  "sale_date", "sale_price"),
    "64uk-42ks": ("bbl", "borough", "zipcode", "bldgclass", "numbldgs",
                  "unitsres", "unitstotal", "bldgarea", "version"),
    "bnx9-e6tj": ("document_id", "doc_type", "document_date", "document_amt",
                  "recorded_datetime", "percent_trans", "good_through_date"),
    "8h5j-fqxa": ("document_id", "borough", "block", "lot", "partial_lot",
                  "easement", "air_rights", "subterranean_rights", "property_type",
                  "good_through_date"),
}
SUBJECT_FIELDS = FIELDS["64uk-42ks"] + ("address",)

class QualificationError(ValueError):
    """Safe categorical error, never includes source values."""


def require(ok, reason):
    if not ok:
        raise QualificationError(reason)


def bbl(borough, block, lot):
    # Exact integer strings; reject decimals, exponents, whitespace and bools.
    parts = [str(x) for x in (borough, block, lot)]
    require(all(re.fullmatch(r"[0-9]+", x) for x in parts), "invalid_bbl")
    a, b, c = map(int, parts)
    require(1 <= a <= 5 and 1 <= b <= 99999 and 1 <= c <= 9999, "invalid_bbl")
    return f"{a}{b:05d}{c:04d}"


def valid_key(key):
    return (isinstance(key, str) and re.fullmatch(r"4[0-9]{9}", key)
            and key[1:6] != "00000" and key[6:] != "0000")


def batches(keys):
    keys = tuple(keys)
    require(len(keys) <= MAX_KEYS and len(set(keys)) == len(keys)
            and all(valid_key(x) for x in keys), "invalid_key_batch")
    return tuple(tuple(sorted(keys)[i:i+MAX_BATCH])
                 for i in range(0, len(keys), MAX_BATCH))


@dataclass
class Budget:
    requests: int = 0
    bytes_received: int = 0
    aux_rows: int = 0
    sales_rows: int = 0
    elapsed: int = 0

    def reserve(self, elapsed):
        # Call before each request; actual monotonic timing enforced by collector.
        require(type(elapsed) is int and self.elapsed <= elapsed < MAX_SECONDS,
                "time_limit")
        require(self.requests < MAX_REQUESTS, "request_limit")
        require(self.bytes_received < MAX_BYTES, "byte_limit")
        self.requests += 1
        self.elapsed = elapsed
        return MAX_BYTES - self.bytes_received

    def account(self, byte_count, row_count, kind, elapsed):
        require(self.requests > 0 and type(byte_count) is int and byte_count >= 0
                and type(row_count) is int and row_count >= 0, "invalid_budget")
        require(kind in ("sales", "aux", "metadata"), "invalid_budget_kind")
        require(type(elapsed) is int and self.elapsed <= elapsed <= MAX_SECONDS,
                "time_limit")
        require(self.bytes_received + byte_count <= MAX_BYTES, "byte_limit")
        require(kind != "metadata" or row_count == 0, "invalid_metadata_rows")
        require(self.sales_rows + (row_count if kind == "sales" else 0)
                <= MAX_SALES, "sale_limit")
        require(self.aux_rows + (row_count if kind == "aux" else 0)
                <= MAX_AUX_ROWS, "aux_limit")
        self.elapsed = elapsed
        self.bytes_received += byte_count
        self.sales_rows += row_count if kind == "sales" else 0
        self.aux_rows += row_count if kind == "aux" else 0


def complete_rows(rows, count, limit):
    """Independent count and complete returned scope; never silently truncate."""
    require(type(count) is int and type(limit) is int and 0 <= count <= limit,
            "count_limit")
    require(len(rows) == count, "incomplete_result")
    return tuple(rows)


def projection(dataset, *, subject=False):
    require(dataset in FIELDS and (not subject or dataset == "64uk-42ks"),
            "unsupported_source")
    return SUBJECT_FIELDS if subject else FIELDS[dataset]


def validate_projection(dataset, rows, *, subject=False):
    allowed = set(projection(dataset, subject=subject))
    require(all(isinstance(row, dict) and set(row) <= allowed for row in rows),
            "unexpected_source_field")


@dataclass(frozen=True)
class Subject:
    key: str
    area: int
    snapshot: date
    version: str
    # Candidate must be verified against the fixed, sales-independent scope.
    eligible: bool
    unique_address: bool


@dataclass(frozen=True)
class Sale:
    key: str
    day: date
    cents: int
    area: int
    eligible: bool
    # Requires documentary proof of historical area applicability, not current PLUTO.
    dated_area: bool


@dataclass(frozen=True)
class Master:
    doc: str
    kind: str
    day: date
    registered: date
    cents: int
    percent: Decimal


@dataclass(frozen=True)
class Legal:
    doc: str
    key: str
    whole: bool
    dwelling: bool
    # False for easement/air/subterranean rights or missing indicators.
    ordinary_rights: bool


def positive_int(value):
    return type(value) is int and value > 0


def day_value(value):
    return type(value) is date


def doc_value(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9]{1,32}", value))


def qualify(subjects, sales, masters, legals, *, cutoff, covered_from,
            covered_through, frame_complete=False, source_complete=False,
            source_versions_stable=False):
    """Aggregate-only proof core; normalised inputs, no I/O or public display.

    subjects must be the first 30 eligible unique candidates in stable BBL
    order, selected independently before looking at sales. Frame and source
    completeness flags are evidence prerequisites, not inferred from row count.
    A future collector must establish them, including all legal rows for each
    candidate document (not only the matching lot). A DEED match is not
    independent arm's-length certification.
    """
    subjects, sales, masters, legals = map(tuple, (subjects, sales, masters, legals))
    require(frame_complete is True and source_complete is True
            and source_versions_stable is True, "incomplete_source_evidence")
    require(all(day_value(x) for x in (cutoff, covered_from, covered_through))
            and covered_from <= covered_through <= cutoff, "invalid_coverage")
    require(len(subjects) == MAX_SUBJECTS and len(sales) <= MAX_SALES
            and len(masters) + len(legals) + len(subjects) <= MAX_AUX_ROWS,
            "scope_limit")
    require(all(isinstance(x, Subject) for x in subjects)
            and all(isinstance(x, Sale) for x in sales)
            and all(isinstance(x, Master) for x in masters)
            and all(isinstance(x, Legal) for x in legals), "invalid_input_type")
    keys = [x.key for x in subjects]
    require(all(valid_key(x) for x in keys) and keys == sorted(set(keys)),
            "subject_frame_identity")
    require(all(valid_key(x.key) for x in sales), "sale_identity")
    require(len(set(keys) | {x.key for x in sales}) <= MAX_KEYS, "key_limit")
    require(all(doc_value(x.doc) for x in (*masters, *legals)), "document_identity")
    # Legals for other boroughs must be kept to identify multi-lot transfers;
    # never discard them before grouping.
    require(all(isinstance(x.key, str) and re.fullmatch(r"[1-5][0-9]{9}", x.key)
                and x.key[1:6] != "00000" and x.key[6:] != "0000" for x in legals),
            "legal_identity")
    by_doc = defaultdict(list)
    legal_by_doc = defaultdict(list)
    by_event = defaultdict(list)
    for m in masters:
        by_doc[m.doc].append(m)
    for l in legals:
        legal_by_doc[l.doc].append(l)
        by_event[l.key].append(l.doc)

    # Duplicate reported events are ambiguous, not silently deduplicated.
    event_counts = Counter((s.key, s.day, s.cents) for s in sales)
    rejected = Counter()
    candidates = []
    for s in sales:
        if not (day_value(s.day) and positive_int(s.cents) and positive_int(s.area)
                and s.eligible is True):
            rejected["invalid_sale"] += 1
            continue
        if not (max(covered_from, cutoff-timedelta(days=365)) <= s.day
                <= covered_through and s.day < cutoff):
            rejected["outside_earlier_window"] += 1
            continue
        if s.dated_area is not True:
            rejected["dated_area_unqualified"] += 1
            continue
        if event_counts[(s.key, s.day, s.cents)] != 1:
            rejected["duplicate_sale"] += 1
            continue
        # Search all matching document candidates before screening their type/lot.
        docs = []
        for doc in set(by_event[s.key]):
            for m in by_doc[doc]:
                if m.day == s.day and m.cents == s.cents:
                    docs.append(m)
        if len(docs) != 1:
            rejected["missing_or_ambiguous_deed"] += 1
            continue
        m = docs[0]
        ls = legal_by_doc[m.doc]
        if not (len(by_doc[m.doc]) == len(ls) == 1 and ls[0].key == s.key
                and ls[0].whole is True and ls[0].dwelling is True
                and ls[0].ordinary_rights is True and m.kind == "DEED"
                and type(m.percent) is Decimal and m.percent == Decimal("100")
                and day_value(m.registered) and s.day <= m.registered <= cutoff):
            rejected["not_whole_qualified_deed"] += 1
            continue
        candidates.append((s, m.doc))
    doc_counts = Counter(d for _, d in candidates)
    qualified = []
    for s, d in candidates:
        if doc_counts[d] != 1:
            rejected["reused_document"] += 1
        else:
            qualified.append(s)

    statuses = Counter()
    for subject in subjects:
        if not (subject.eligible is True and subject.unique_address is True
                and positive_int(subject.area) and day_value(subject.snapshot)
                and subject.snapshot <= cutoff and isinstance(subject.version, str)
                and bool(subject.version.strip())):
            statuses["unresolved_subject"] += 1
            continue
        # Rank without price; distinct other BBL, area difference, newest, BBL.
        ordered = sorted((s for s in qualified if s.key != subject.key
                          and 4*abs(s.area-subject.area) <= subject.area),
                         key=lambda s: (abs(s.area-subject.area), -s.day.toordinal(), s.key))
        distinct = set()
        for s in ordered:
            distinct.add(s.key)
            if len(distinct) == 5:
                break
        statuses["supported" if len(distinct) >= 3 else "insufficient"] += 1
    return {
        "subject_count": len(subjects), "sale_count": len(sales),
        "qualified_sales": len(qualified), "sale_exclusions": dict(rejected),
        "subject_statuses": dict(statuses),
        "engineering_floor_met": statuses["supported"] >= 10,
        "lookback_fully_covered": covered_from <= cutoff-timedelta(days=365)
        and covered_through >= cutoff-timedelta(days=1),
        "historical_asof_verified": False,
        "representative_coverage_verified": False,
        "market_approved": False,
    }



# Offline query templates only; transport is intentionally absent. No free-form
# predicates, arbitrary dataset, account/token, raw comparable address or parties.
@dataclass(frozen=True, repr=False)
class Query:
    dataset: str
    fields: tuple
    where: str
    limit: int
    order: str = ""

    def parameters(self, count=False):
        if count:
            return {"$select": "count(*) as n", "$where": self.where, "$limit": "1"}
        result = {"$select": ",".join(self.fields), "$where": self.where,
                  "$limit": str(self.limit)}
        if self.order:
            result["$order"] = self.order
        return result


def subject_query():
    """First 30 candidates; uniqueness and independent frame proof still required."""
    return Query("64uk-42ks", SUBJECT_FIELDS,
                 "borough = 'QN' AND zipcode = '11361' AND bldgclass = 'A2' "
                 "AND numbldgs = 1 AND unitsres = 1 AND unitstotal = 1 "
                 "AND bldgarea > 0 AND address IS NOT NULL AND address != ''",
                 MAX_SUBJECTS, "bbl ASC")


def sales_query(covered_from, covered_through, cutoff):
    require(all(day_value(x) for x in (covered_from, covered_through, cutoff))
            and covered_from <= covered_through <= cutoff, "invalid_coverage")
    lo = max(covered_from, cutoff-timedelta(days=365))
    hi = min(covered_through+timedelta(days=1), cutoff)
    require(lo < hi, "empty_earlier_window")
    return Query("usep-8jbt", FIELDS["usep-8jbt"],
                 "borough in ('4','QUEENS') AND neighborhood = 'BAYSIDE' "
                 "AND zip_code = '11361' AND building_class_at_time_of_sale = 'A2' "
                 f"AND sale_date >= '{lo.isoformat()}T00:00:00' "
                 f"AND sale_date < '{hi.isoformat()}T00:00:00'",
                 MAX_SALES)


def master_query(events):
    """Find potential instruments by exact reported day and amount.

    No assumption that document recording borough equals property borough.
    All matching document types retained for ambiguity screening. Full legal
    rows must subsequently be obtained by document ID, never just the target lot.
    """
    events = tuple(events)
    require(0 < len(events) <= MAX_BATCH, "invalid_event_batch")
    require(all(isinstance(s, Sale) and valid_key(s.key) and day_value(s.day)
                and positive_int(s.cents) and s.cents <= 99999999999999
                and s.day < date.max for s in events), "invalid_event")
    pairs = sorted(set((s.day, s.cents) for s in events))
    clauses = []
    for day, cents in pairs:
        amount = f"{cents//100}.{cents%100:02d}"
        clauses.append(f"(document_date >= '{day.isoformat()}T00:00:00' AND "
                       f"document_date < '{(day+timedelta(days=1)).isoformat()}T00:00:00' "
                       f"AND document_amt = {amount})")
    return Query("bnx9-e6tj", FIELDS["bnx9-e6tj"], " OR ".join(clauses),
                 MAX_AUX_ROWS)


def legal_query(documents):
    documents = tuple(documents)
    require(0 < len(documents) <= MAX_BATCH
            and all(doc_value(x) for x in documents)
            and len(set(documents)) == len(documents), "invalid_document_batch")
    literal = ",".join("'" + x + "'" for x in sorted(documents))
    return Query("8h5j-fqxa", FIELDS["8h5j-fqxa"],
                 f"document_id in ({literal})", MAX_AUX_ROWS)


def comparable_attribute_query(keys):
    keys = tuple(keys)
    require(0 < len(keys) <= MAX_BATCH and all(valid_key(x) for x in keys)
            and len(set(keys)) == len(keys), "invalid_key_batch")
    # Current attributes only; never set Sale.dated_area from this query.
    return Query("64uk-42ks", FIELDS["64uk-42ks"],
                 "bbl in (" + ",".join(sorted(keys)) + ")", MAX_BATCH)


def verify_metadata(dataset, before, after, *, subject=False):
    """Validate expected field availability and pinned update identity.

    Accept only the narrow metadata projection prepared by a future collector,
    not whole source metadata (which may contain cached address examples).
    Source types, date/class semantics and notices must be checked separately.
    """
    def valid(m):
        return (isinstance(m, dict) and set(m) == {"id", "revision", "fields"}
                and m["id"] == dataset and isinstance(m["revision"], str)
                and bool(m["revision"].strip())
                and isinstance(m["fields"], (tuple, list))
                and all(isinstance(x, str) for x in m["fields"])
                and set(projection(dataset, subject=subject)) <= set(m["fields"]))
    require(valid(before) and valid(after), "source_schema_unverified")
    require(before["revision"] == after["revision"]
            and set(before["fields"]) == set(after["fields"]), "source_revision_changed")
