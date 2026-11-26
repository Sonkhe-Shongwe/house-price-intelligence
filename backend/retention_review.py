"""Read-only retention impact review, disposable historical fixtures only.

Historical build timestamps are extraction timestamps in the canonical importer.
A real pilot additionally needs a private operator inventory of earlier intake,
backups, copies and provider history. This is not a disposal or activation tool.
"""
from datetime import datetime, timedelta, timezone
import re

from backend.curated_ingestion_candidate import ImportRefused
from backend.historical_migration import migration_history
from backend.postgres_ingestion import _check

RETENTION_DAYS = 30

# Fixed schema and parameterised build selection. Do not return raw IDs.
IMPACT = """
WITH snaps AS (
    SELECT DISTINCT snapshot_id FROM curated_build_sources WHERE build_id=%s
), txns AS (
    SELECT transaction_id FROM sale_transactions
    WHERE snapshot_id IN (SELECT snapshot_id FROM snaps)
    UNION SELECT transaction_id FROM curated_build_transactions WHERE build_id=%s
), inv AS (
    SELECT investigation_id FROM investigations WHERE build_id=%s
), members AS (
    SELECT shortlist_id, investigation_id FROM shortlist_investigations
    WHERE investigation_id IN (SELECT investigation_id FROM inv)
), pins AS (
    SELECT pin FROM sale_transaction_parcels WHERE transaction_id IN (SELECT transaction_id FROM txns)
    UNION SELECT pin FROM assessment_records WHERE snapshot_id IN (SELECT snapshot_id FROM snaps)
    UNION SELECT pin FROM parcel_geographies WHERE snapshot_id IN (SELECT snapshot_id FROM snaps)
    UNION SELECT pin FROM historical_address_states WHERE snapshot_id IN (SELECT snapshot_id FROM snaps)
    UNION SELECT subject_pin FROM investigations WHERE investigation_id IN (SELECT investigation_id FROM inv)
      AND subject_pin IS NOT NULL
)
SELECT
    (SELECT count(*) FROM snaps),
    (SELECT count(*) FROM txns),
    (SELECT count(*) FROM assessment_records WHERE snapshot_id IN (SELECT snapshot_id FROM snaps)),
    (SELECT count(*) FROM parcel_geographies WHERE snapshot_id IN (SELECT snapshot_id FROM snaps)),
    (SELECT count(*) FROM historical_address_states WHERE snapshot_id IN (SELECT snapshot_id FROM snaps)),
    (SELECT count(*) FROM inv),
    (SELECT count(*) FROM investigation_results WHERE investigation_id IN (SELECT investigation_id FROM inv)),
    (SELECT count(*) FROM comparable_evidence WHERE investigation_id IN (SELECT investigation_id FROM inv)),
    (SELECT count(*) FROM members),
    (SELECT count(DISTINCT shortlist_id) FROM members),
    (SELECT count(DISTINCT shortlist_id) FROM shortlist_investigations
      WHERE shortlist_id IN (SELECT shortlist_id FROM members)
        AND investigation_id NOT IN (SELECT investigation_id FROM inv)),
    (SELECT count(*) FROM pins),
    (SELECT count(DISTINCT snapshot_id) FROM curated_build_sources
      WHERE snapshot_id IN (SELECT snapshot_id FROM snaps) AND build_id<>%s),
    (SELECT count(DISTINCT transaction_id) FROM curated_build_transactions
      WHERE transaction_id IN (SELECT transaction_id FROM txns) AND build_id<>%s),
    (SELECT count(*) FROM pins p WHERE
      EXISTS (SELECT 1 FROM sale_transaction_parcels r WHERE r.pin=p.pin
        AND r.transaction_id NOT IN (SELECT transaction_id FROM txns))
      OR EXISTS (SELECT 1 FROM assessment_records r WHERE r.pin=p.pin
        AND r.snapshot_id NOT IN (SELECT snapshot_id FROM snaps))
      OR EXISTS (SELECT 1 FROM parcel_geographies r WHERE r.pin=p.pin
        AND r.snapshot_id NOT IN (SELECT snapshot_id FROM snaps))
      OR EXISTS (SELECT 1 FROM historical_address_states r WHERE r.pin=p.pin
        AND r.snapshot_id NOT IN (SELECT snapshot_id FROM snaps))
      OR EXISTS (SELECT 1 FROM candidate_addresses r WHERE r.pin=p.pin)
      OR EXISTS (SELECT 1 FROM synthetic_address_index r WHERE r.pin=p.pin)
      OR EXISTS (SELECT 1 FROM synthetic_address_candidates r WHERE r.pin=p.pin)
      OR EXISTS (SELECT 1 FROM buildings r WHERE r.pin=p.pin)
      OR EXISTS (SELECT 1 FROM investigations r WHERE r.subject_pin=p.pin
        AND r.investigation_id NOT IN (SELECT investigation_id FROM inv)))
"""
COUNTS = ("source_snapshots", "sale_transactions", "assessment_records",
          "geographies", "address_states", "investigations", "frozen_results",
          "comparable_evidence", "shortlist_memberships", "affected_shortlists",
          "mixed_shortlists", "parcel_keys", "shared_snapshots", "shared_transactions",
          "parcel_keys_with_other_references")


def _utc(value):
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.utcoffset() != timedelta(0):
            raise ValueError
        return stamp
    except (ValueError, TypeError, AttributeError, OverflowError):
        raise ImportRefused("Retention timestamp refused") from None


def review_retention(conn, build_id, *, now=None):
    """Count known dependencies in one read-only snapshot, never authorise deletion."""
    _check(conn)
    if not isinstance(build_id, str) or not re.fullmatch(r"historical-[0-9a-f]{64}", build_id):
        raise ImportRefused("Historical build required")
    now = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.utcoffset() != timedelta(0):
        raise ImportRefused("UTC review time required")
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        conn.execute("SET LOCAL search_path TO hpi_candidate,pg_catalog")
        conn.execute("SET LOCAL statement_timeout='5000ms'")
        conn.execute("SET LOCAL lock_timeout='3000ms'")
        if conn.execute("SELECT current_database(),current_user,session_user").fetchone()!=("hpi_ingest_fixture","postgres","postgres"):
            raise ImportRefused("Disposable retention review required")
        migration_history(conn)
        row = conn.execute("""SELECT b.built_at_utc FROM curated_builds b
            JOIN historical_build_manifests m ON m.build_id=b.build_id
            WHERE b.build_id=%s AND b.build_kind='historical_research'""",(build_id,)).fetchone()
        if not row:
            raise ImportRefused("Historical build unavailable")
        source_times = conn.execute("""SELECT DISTINCT s.snapshot_id,s.extracted_at_utc
            FROM source_snapshots s JOIN curated_build_sources c ON c.snapshot_id=s.snapshot_id
            WHERE c.build_id=%s""",(build_id,)).fetchall()
        if len(source_times)!=4:
            raise ImportRefused("Incomplete historical source inventory")
        start = min([_utc(row[0])]+[_utc(item[1]) for item in source_times])
        if start>now or any(_utc(item[1])>now for item in source_times) or _utc(row[0])>now:
            raise ImportRefused("Future intake timestamp")
        expiry = start+timedelta(days=RETENTION_DAYS)
        counts = dict(zip(COUNTS,conn.execute(IMPACT,(build_id,)*5).fetchone()))
    return {"scope":"disposable invented historical build dependency review",
            "status":"expired" if now>=expiry else "within_retention_window",
            "retention_days":RETENTION_DAYS,
            "recorded_intake_utc":start.isoformat(),
            "deadline_utc":expiry.isoformat(),
            "counts":counts, "deletion_authorised":False,
            "external_copy_inventory_required":True}
