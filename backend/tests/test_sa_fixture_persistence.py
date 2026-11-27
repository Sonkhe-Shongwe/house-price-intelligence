import sqlite3
import unittest
from datetime import date
from unittest.mock import patch

from backend import sa_investigation_v2 as sa
from backend import sa_fixture_persistence as persistence
from backend.synthetic_demo import in_memory_demo,example_request
from backend.synthetic_shortlists import SyntheticShortlistService


def request(token="fictional-erf-000001"):
    return {"contract_version":sa.VERSION,"market":"ZA","currency":"ZAR","area_unit":"m2",
            "subject_key":sa.wire_key(token),"analysis_date":"2025-07-01","mode":"as_of",
            "asking_price":"2500000.01"}


class SAPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.db,self.us=in_memory_demo()
        self.today=date(2026,1,1)
    def tearDown(self):self.db.close()

    def test_additive_frozen_owner_scoped_and_us_preserved(self):
        before=self.us.create(example_request())
        shortlists=SyntheticShortlistService(self.us)
        sid=shortlists.create({"label":"Fictional US comparison"})["shortlist_id"]
        original=shortlists.add(sid,{"investigation_id":before["investigation_id"]})
        a=persistence.sqlite_store(self.db,"fictional-alice")
        first=a.save(request(),today=self.today)
        weak=a.save(request("fictional-erf-000010"),today=self.today)
        b=persistence.sqlite_store(self.db,"fictional-bob")
        self.assertEqual(b.history()["investigations"],[])
        with self.assertRaises(persistence.PersistenceError):b.reopen(first["investigation_id"])
        with patch.object(sa,"investigate",side_effect=RuntimeError("do not recompute")):
            self.assertEqual(a.reopen(first["investigation_id"]),first)
            self.assertEqual(a.reopen(weak["investigation_id"]),weak)
        self.assertEqual(first["evidence"]["subject"]["asking_price"]["minor_units"],250000001)
        self.assertEqual(weak["evidence"]["comparables"],[])
        self.assertEqual(self.us.reopen(before["investigation_id"]),before)
        self.assertEqual(shortlists.get(sid),original)
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone()[0],3)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM sa_fixture_migrations").fetchone()[0],1)
        self.assertEqual(len(a.history()["investigations"]),2)

    def test_tamper_and_wrong_market(self):
        a=persistence.sqlite_store(self.db,"fictional-alice")
        with self.assertRaises(sa.ContractError):a.save(request()|{"currency":"USD"},today=self.today)
        self.assertEqual(a.history()["investigations"],[])
        first=a.save(request(),today=self.today)
        self.db.execute("UPDATE sa_fixture_investigations SET asking_cents=1")
        self.db.commit()
        with self.assertRaises(persistence.PersistenceError):a.reopen(first["investigation_id"])
        self.db.execute("UPDATE sa_fixture_migrations SET script_sha256=?",("x"*64,))
        self.db.commit()
        with self.assertRaises(persistence.PersistenceError):persistence.sqlite_store(self.db,"fictional-alice")

    def test_unknown_and_partial_schema_refused(self):
        empty=sqlite3.connect(":memory:")
        try:
            with self.assertRaises(persistence.PersistenceError):persistence.sqlite_store(empty,"fictional-alice")
        finally:empty.close()
        self.db.execute("CREATE TABLE sa_fixture_migrations (bad INT)")
        self.db.commit()
        with self.assertRaises(persistence.PersistenceError):persistence.sqlite_store(self.db,"fictional-alice")
        self.assertIsNone(self.db.execute("SELECT name FROM sqlite_master WHERE name='sa_fixture_investigations'").fetchone())

    def test_extension_failure_rolls_back(self):
        self.db.execute("CREATE TABLE idx_sa_fixture_owner (bad INT)")
        self.db.commit()
        with self.assertRaises(sqlite3.Error):persistence.sqlite_store(self.db,"fictional-alice")
        self.assertIsNone(self.db.execute("SELECT name FROM sqlite_master WHERE name='sa_fixture_migrations'").fetchone())
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone()[0],3)
