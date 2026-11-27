import sqlite3
import unittest
from datetime import date
from unittest.mock import patch

from backend import sa_investigation_v2 as sa
from backend import sa_fixture_persistence as persistence
from backend.sa_fixture_restart import DisposableRestartRehearsal, _install_restart
from backend.synthetic_demo import in_memory_demo, example_request
from backend.synthetic_shortlists import SyntheticShortlistService

TODAY = date(2026, 1, 1)


def request(token="fictional-erf-000001", price="2500000.01"):
    return {"contract_version":sa.VERSION,"market":"ZA","currency":"ZAR","area_unit":"m2",
            "subject_key":sa.wire_key(token),"analysis_date":"2025-07-01","mode":"as_of",
            "asking_price":price}


def command(shortlist, row, action="add", **extra):
    return shortlist.mutate({"action":action,"investigation_id":row["investigation_id"],**extra})


class SARestartTests(unittest.TestCase):
    def test_reopen_frozen_notes_and_us_preserved(self):
        with DisposableRestartRehearsal() as rehearsal:
            with rehearsal.open() as (db,us,za,shortlist):
                original=us.create(example_request())
                service=SyntheticShortlistService(us)
                sid=service.create({"label":"Fictional US shortlist"})["shortlist_id"]
                us_list=service.add(sid,{"investigation_id":original["investigation_id"],"note_text":"US note"})
                a=za.save(request(),today=TODAY)
                b=za.save(request("fictional-erf-000010","1.02"),today=TODAY)
                command(shortlist,a);command(shortlist,b)
                command(shortlist,a,"note",note_text="Fictional extent question")
                frozen=command(shortlist,b,"note",note_text="Unresolved identity")
                with self.assertRaises(persistence.PersistenceError):
                    persistence.sqlite_store(db,"fictional-alice")
            with patch.object(sa,"investigate",side_effect=RuntimeError("no recomputation")):
                with rehearsal.open("fictional-bob") as (_,_,bob,bob_list):
                    self.assertEqual(bob_list.get()["investigations"],[])
                    with self.assertRaises(persistence.PersistenceError):
                        bob.reopen(a["investigation_id"])
                    with self.assertRaises(persistence.PersistenceError):
                        command(bob_list,a)
                with rehearsal.open() as (db,us,za,shortlist):
                    self.assertEqual(shortlist.get(),frozen)
                    self.assertEqual(za.reopen(a["investigation_id"]),a)
                    self.assertEqual(za.reopen(b["investigation_id"]),b)
                    self.assertEqual(a["evidence"]["subject"]["asking_price"]["minor_units"],250000001)
                    self.assertEqual(b["evidence"]["comparables"],[])
                    self.assertEqual(us.reopen(original["investigation_id"]),original)
                    self.assertEqual(SyntheticShortlistService(us).get(sid),us_list)
                    command(shortlist,b,"remove")
                    self.assertEqual(command(shortlist,b)["notes"][b["investigation_id"]],"")
                    self.assertEqual(db.execute("PRAGMA user_version").fetchone(),(3,))
                with rehearsal.open() as (_,_,za,shortlist):
                    self.assertEqual(shortlist.get()["investigations"],[a,b])
                    self.assertEqual(shortlist.get()["notes"][b["investigation_id"]],"")
                    self.assertEqual(za.reopen(b["investigation_id"]),b)
        self.assertFalse(rehearsal._path.exists())

    def test_mutation_failure_rolls_back_disk_and_memory(self):
        with DisposableRestartRehearsal() as rehearsal:
            with rehearsal.open() as (_,_,za,shortlist):
                a=za.save(request(),today=TODAY)
                before=command(shortlist,a)
                write=shortlist._write_snapshot
                def failed_write():
                    write()
                    raise sqlite3.OperationalError("injected failure")
                with patch.object(shortlist,"_write_snapshot",side_effect=failed_write):
                    with self.assertRaises(sqlite3.OperationalError):
                        command(shortlist,a,"note",note_text="Must roll back")
                self.assertEqual(shortlist.get(),before)
            with rehearsal.open() as (_,_,_,shortlist):
                self.assertEqual(shortlist.get(),before)

    def test_extension_ddl_failure_rolls_back(self):
        conn,_=in_memory_demo()
        try:
            persistence.sqlite_store(conn,"fictional-alice")
            conn.execute("CREATE TABLE sa_restart_shortlists (bad INT)")
            conn.commit()
            with self.assertRaises(sqlite3.Error):
                _install_restart(conn)
            self.assertIsNone(conn.execute("SELECT name FROM sqlite_master WHERE name='sa_restart_migrations'").fetchone())
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone(),(3,))
        finally:
            conn.close()

    def test_schema_source_ledger_and_frozen_tamper_refused(self):
        for sql in ("CREATE TABLE rogue (x INT)",
                    "UPDATE source_snapshots SET source_query='changed'",
                    "UPDATE sa_restart_migrations SET script_sha256='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'",
                    "UPDATE sa_fixture_investigations SET asking_cents=1",
                    "UPDATE sa_restart_shortlists SET snapshot_json='{}'"):
            with self.subTest(sql=sql), DisposableRestartRehearsal() as rehearsal:
                with rehearsal.open() as (db,_,za,shortlist):
                    a=za.save(request(),today=TODAY);command(shortlist,a)
                    db.execute(sql);db.commit()
                with self.assertRaises(persistence.PersistenceError):
                    with rehearsal.open():
                        self.fail("Corrupt fixture exposed")

    def test_missing_or_replaced_target_refused(self):
        with DisposableRestartRehearsal() as rehearsal:
            rehearsal._path.rename(rehearsal._path.with_suffix(".old"))
            with self.assertRaises(OSError):
                with rehearsal.open():
                    self.fail("Missing target recreated")
            rehearsal._path.touch()
            with self.assertRaises(persistence.PersistenceError):
                with rehearsal.open():
                    self.fail("Replacement target accepted")
