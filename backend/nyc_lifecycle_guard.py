"""Invented-only NYC lifecycle policy rehearsal.

No storage, HTTP, actual authorisation, deletion or real-data activation.
The future trusted service must supply immutable original intake seals and a
fresh independent authority snapshot, outside any restored backup. Never
construct these from a request or from the restored evidence itself.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

from tools.nyc_qualification import FIELDS

SOURCE_IDS = frozenset(FIELDS)
OPERATIONS = frozenset({"read", "save", "reopen", "compare", "export", "restore"})
MAX_RETENTION = timedelta(days=30)
FIXTURE_KIND = "synthetic_lifecycle_rehearsal"


@dataclass(frozen=True)
class IntakeSeal:
    source: str
    revision: str
    intake_key: str
    policy: str
    first_intake: datetime
    original_deadline: datetime


@dataclass(frozen=True)
class SourceAuthority:
    original: IntakeSeal
    deadline: datetime
    permission: str
    accuracy: str
    protection: str
    operations: frozenset


@dataclass(frozen=True)
class Evidence:
    owner: str
    dependencies: tuple
    built_at: datetime
    kind: str = FIXTURE_KIND


@dataclass(frozen=True)
class AuthoritySnapshot:
    owner: str
    sources: tuple
    observed_at: datetime
    kind: str = FIXTURE_KIND


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    deadline: datetime | None = None


def _fixture_token(value):
    return type(value) is str and re.fullmatch(r"fixture-[a-z0-9-]{1,64}", value) is not None


def _utc(value):
    return type(value) is datetime and value.tzinfo is timezone.utc


def _seal_valid(seal, now):
    if (type(seal) is not IntakeSeal or type(seal.source) is not str
            or seal.source not in SOURCE_IDS
            or not all(_fixture_token(v) for v in (seal.revision, seal.intake_key, seal.policy))
            or not _utc(seal.first_intake) or not _utc(seal.original_deadline)):
        return False
    # Use subtraction, avoiding overflow near the datetime representable limit.
    return (seal.first_intake <= now and seal.first_intake < seal.original_deadline
            and seal.original_deadline - seal.first_intake <= MAX_RETENTION)


def _index_seals(items, now):
    if type(items) is not tuple or len(items) != len(SOURCE_IDS):
        return None
    if not all(_seal_valid(item, now) for item in items):
        return None
    result = {item.source: item for item in items}
    return result if set(result) == SOURCE_IDS else None


def evaluate(evidence, authority, *, owner, operation, now):
    """Evaluate a single invented investigation against current authority.

    No result contains source keys, user input or property values. A successful
    rehearsal is not a real permission. The caller must obtain authoritative
    state and the evaluation time in one protected operation; this pure
    function cannot authenticate the caller, prove clock integrity, detect a
    rolled-back authority store or enforce access in another component.
    """
    if type(operation) is not str or operation not in OPERATIONS:
        return Decision(False, "operation_unknown")
    if (type(evidence) is not Evidence or type(authority) is not AuthoritySnapshot
            or evidence.kind != FIXTURE_KIND or authority.kind != FIXTURE_KIND):
        return Decision(False, "fixture_only")
    if (not _fixture_token(owner) or not _fixture_token(evidence.owner)
            or not _fixture_token(authority.owner)
            or owner != evidence.owner or owner != authority.owner):
        return Decision(False, "owner_mismatch")
    if (not _utc(now) or not _utc(authority.observed_at)
            or authority.observed_at != now):
        return Decision(False, "authority_not_current")
    if not _utc(evidence.built_at) or evidence.built_at > now:
        return Decision(False, "invalid_build_time")
    frozen = _index_seals(evidence.dependencies, now)
    if frozen is None:
        return Decision(False, "invalid_dependencies")
    if any(evidence.built_at < seal.first_intake for seal in frozen.values()):
        return Decision(False, "invalid_build_time")
    if (type(authority.sources) is not tuple
            or len(authority.sources) != len(SOURCE_IDS)
            or not all(type(item) is SourceAuthority for item in authority.sources)):
        return Decision(False, "authority_incomplete")
    originals = _index_seals(tuple(item.original for item in authority.sources), now)
    if originals is None:
        return Decision(False, "authority_incomplete")
    current = {item.original.source: item for item in authority.sources}
    if any(frozen[key] != originals[key] for key in SOURCE_IDS):
        return Decision(False, "source_seal_mismatch")

    deadlines = []
    # Sort for stable categorical results when several sources fail.
    for key in sorted(SOURCE_IDS):
        item = current[key]
        original = originals[key]
        if (not _utc(item.deadline) or item.deadline <= original.first_intake
                or item.deadline > original.original_deadline):
            return Decision(False, "invalid_authority_deadline")
        if type(item.permission) is not str or item.permission != "reviewed":
            return Decision(False, "permission_unavailable")
        if type(item.accuracy) is not str or item.accuracy != "clear":
            return Decision(False, "accuracy_restricted")
        if type(item.protection) is not str or item.protection != "verified":
            return Decision(False, "protection_unavailable")
        if (type(item.operations) is not frozenset
                or not all(type(v) is str for v in item.operations)
                or not item.operations <= OPERATIONS or operation not in item.operations):
            return Decision(False, "operation_not_permitted")
        deadlines.append(item.deadline)

    deadline = min(deadlines)
    if now >= deadline:
        return Decision(False, "expired", deadline)
    return Decision(True, "fixture_operation_permitted", deadline)
