"""Invented-only lifecycle policy checks; no actual access or data."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from backend.nyc_lifecycle_guard import (
    AuthoritySnapshot, Evidence, IntakeSeal, SourceAuthority, evaluate,
    OPERATIONS, SOURCE_IDS,
)

START = datetime(2026, 11, 1, tzinfo=timezone.utc)
NOW = START + timedelta(days=5)
OWNER = "fixture-owner"


def fixture():
    seals = tuple(IntakeSeal(key, "fixture-revision", f"fixture-intake-{i}",
                            "fixture-policy", START+timedelta(days=i),
                            START+timedelta(days=i+30))
                  for i, key in enumerate(sorted(SOURCE_IDS)))
    evidence = Evidence(OWNER, seals, NOW)
    authority = AuthoritySnapshot(OWNER, tuple(
        SourceAuthority(s, s.original_deadline, "reviewed", "clear", "verified", OPERATIONS)
        for s in seals), NOW)
    return evidence, authority


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.evidence, self.authority = fixture()

    def check(self, operation="read", *, evidence=None, authority=None, now=NOW, owner=OWNER):
        return evaluate(self.evidence if evidence is None else evidence,
                        self.authority if authority is None else authority,
                        owner=owner, operation=operation, now=now)

    def state(self, **changes):
        return replace(self.authority, sources=(
            replace(self.authority.sources[0], **changes), *self.authority.sources[1:]))

    def at(self, now, operation="read", **kwargs):
        return self.check(operation, now=now,
                          authority=replace(self.authority, observed_at=now), **kwargs)

    def assertRefusal(self, result, reason):
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, reason)

    def test_all_six_operations_and_earliest_deadline(self):
        for operation in sorted(OPERATIONS):
            with self.subTest(operation=operation):
                decision = self.check(operation)
                self.assertTrue(decision.allowed)
                self.assertEqual(decision.deadline, START+timedelta(days=30))

    def test_exact_expiry_boundary(self):
        deadline = START+timedelta(days=30)
        self.assertTrue(self.at(deadline-timedelta(microseconds=1)).allowed)
        for operation in OPERATIONS:
            self.assertRefusal(self.at(deadline, operation), "expired")

    def test_shorter_source_terms_override_earliest_intake(self):
        shorter = START+timedelta(days=6)
        authority = replace(self.authority, sources=(
            *self.authority.sources[:-1], replace(self.authority.sources[-1], deadline=shorter)))
        self.assertEqual(self.check(authority=authority).deadline, shorter)
        self.assertRefusal(self.check(authority=replace(authority, observed_at=shorter), now=shorter), "expired")

    def test_revocation_dispute_protection_all_paths(self):
        for changes, reason in (
            ({"permission":"revoked"}, "permission_unavailable"),
            ({"permission":"unknown"}, "permission_unavailable"),
            ({"accuracy":"disputed"}, "accuracy_restricted"),
            ({"accuracy":None}, "accuracy_restricted"),
            ({"protection":"lost"}, "protection_unavailable"),
            ({"protection":True}, "protection_unavailable"),
        ):
            for operation in OPERATIONS:
                with self.subTest(changes=changes, operation=operation):
                    self.assertRefusal(self.check(operation, authority=self.state(**changes)), reason)

    def test_operation_specific_and_unknown_permissions(self):
        only_read = self.state(operations=frozenset({"read"}))
        self.assertTrue(self.check(authority=only_read).allowed)
        for operation in OPERATIONS-{"read"}:
            self.assertRefusal(self.check(operation, authority=only_read), "operation_not_permitted")
        self.assertRefusal(self.check("public_export"), "operation_unknown")
        for invalid in ({"read"}, frozenset({"read","unknown"}), frozenset({True})):
            self.assertRefusal(self.check(authority=self.state(operations=invalid)), "operation_not_permitted")

    def test_incomplete_duplicate_and_extra_dependencies(self):
        deps = self.evidence.dependencies
        for bad in ((), deps[:-1], (deps[0],)*4, (*deps, deps[0]), list(deps)):
            self.assertRefusal(self.check(evidence=replace(self.evidence, dependencies=bad)), "invalid_dependencies")

    def test_missing_duplicate_and_malformed_authority(self):
        items = self.authority.sources
        for bad in (None, (), items[:-1], (items[0],)*4, (*items, items[0]), (None,)*4):
            self.assertRefusal(self.check(authority=replace(self.authority, sources=bad)), "authority_incomplete")

    def test_exact_source_policy_and_revision_seals(self):
        first = self.evidence.dependencies[0]
        for changes in ({"revision":"fixture-new-revision"}, {"policy":"fixture-new-policy"},
                        {"intake_key":"fixture-new-intake"},
                        {"first_intake":START+timedelta(days=1)}):
            modified = replace(self.evidence, dependencies=(
                replace(first, **changes), *self.evidence.dependencies[1:]))
            self.assertRefusal(self.check(evidence=modified), "source_seal_mismatch")

    def test_rebuild_restore_cannot_reset_intake(self):
        rebuilt_at = START+timedelta(days=29)
        rebuilt = replace(self.evidence, built_at=rebuilt_at)
        self.assertEqual(self.at(rebuilt_at, "restore", evidence=rebuilt).deadline,
                         START+timedelta(days=30))
        expiry = START+timedelta(days=30)
        self.assertRefusal(self.at(expiry, "restore", evidence=rebuilt), "expired")
        first = self.evidence.dependencies[0]
        reset = replace(first, first_intake=NOW, original_deadline=NOW+timedelta(days=30))
        rebuilt = replace(self.evidence, dependencies=(reset,*self.evidence.dependencies[1:]))
        self.assertRefusal(self.check("restore", evidence=rebuilt), "source_seal_mismatch")

    def test_restored_old_authority_is_not_current(self):
        later = NOW+timedelta(seconds=1)
        self.assertRefusal(self.check("restore", now=later), "authority_not_current")
        self.assertRefusal(self.check("restore", authority=self.state(permission="revoked")),
                           "permission_unavailable")

    def test_no_extension_even_if_current_authority_claims_longer(self):
        deadline = self.authority.sources[0].deadline
        self.assertRefusal(self.check(authority=self.state(deadline=deadline+timedelta(seconds=1))),
                           "invalid_authority_deadline")

    def test_invalid_times_and_intake_limit(self):
        self.assertRefusal(self.check(now=NOW.replace(tzinfo=None)), "authority_not_current")
        for stamp in (None, NOW.replace(tzinfo=None), NOW+timedelta(days=1), START-timedelta(seconds=1)):
            self.assertRefusal(self.check(evidence=replace(self.evidence, built_at=stamp)), "invalid_build_time")
        first = self.evidence.dependencies[0]
        for changes in ({"first_intake":NOW+timedelta(days=1)},
                        {"original_deadline":first.first_intake+timedelta(days=31)},
                        {"original_deadline":first.first_intake},
                        {"first_intake":first.first_intake.replace(tzinfo=None)}):
            modified = replace(self.evidence, dependencies=(
                replace(first, **changes), *self.evidence.dependencies[1:]))
            self.assertRefusal(self.check(evidence=modified), "invalid_dependencies")

    def test_owner_and_real_mode_refused(self):
        self.assertRefusal(self.check(owner="fixture-other-owner"), "owner_mismatch")
        self.assertRefusal(self.check(authority=replace(self.authority, owner="fixture-other-owner")), "owner_mismatch")
        self.assertRefusal(self.check(evidence=replace(self.evidence, kind="real")), "fixture_only")
        self.assertRefusal(self.check(authority=replace(self.authority, kind="real")), "fixture_only")

    def test_refusals_never_echo_source_tokens(self):
        result = self.check(authority=self.state(permission="INVENTED SECRET"))
        self.assertNotIn("INVENTED SECRET", str(result))
        self.assertNotIn("fixture-intake", str(result))


if __name__ == "__main__":
    unittest.main()
