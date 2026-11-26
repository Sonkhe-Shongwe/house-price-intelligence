import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from tools.check_docs import continuation_errors


class ContinuationRoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()
        for name in ("MASTER_CONTINUATION_PROMPT.md", "DECISIONS.md", "P_PHASE_ROADMAP.md", "history.md"):
            (self.root / "docs" / name).write_text("test", encoding="utf-8")
        self.state = {"schema_version": 1, "active_phase": "P0", "phase_gate": "blocked",
                      "task": {"id": "P0-TEST", "status": "ready", "objective": "Inspect metadata", "scope": "read only",
                               "acceptance": "Evidence recorded", "stop": "Before intake",
                               "read": ["docs/P_PHASE_ROADMAP.md"], "evidence": ["docs/history.md"]},
                      "blockers": ["rights"], "parked": [], "authority": ["docs/DECISIONS.md"], "history": ["docs/history.md"]}

    def write(self, raw=None, suffix=""):
        body = json.dumps(self.state) if raw is None else raw
        (self.root / "docs/CHECKPOINT.md").write_text("\x60\x60\x60json\n" + body + "\n\x60\x60\x60\n" + suffix, encoding="utf-8")
        return continuation_errors(self.root)

    def test_ready_task_in_blocked_phase(self):
        self.assertEqual(self.write(), [])

    def test_phase_mismatch(self):
        self.state["task"]["id"] = "P1-TEST"
        self.assertTrue(self.write())

    def test_blocker_required(self):
        self.state["blockers"] = []
        self.assertTrue(self.write())

    def test_missing_and_escaping_refs(self):
        for ref in ("docs/missing.md", "../outside.md"):
            self.state["task"]["evidence"] = [ref]
            self.assertTrue(self.write())

    def test_duplicate_key(self):
        self.assertTrue(self.write(json.dumps(self.state)[:-1] + ', "active_phase": "P1"}'))

    def test_missing_authority_and_stop(self):
        self.state["authority"] = ["docs/history.md"]
        self.assertTrue(self.write())
        self.state["authority"] = ["docs/DECISIONS.md"]
        self.state["task"]["stop"] = ""
        self.assertTrue(self.write())

    def test_budget_and_multiple_blocks(self):
        self.assertTrue(self.write(suffix="x" * 12001))
        self.assertTrue(self.write(suffix="\x60\x60\x60json\n{}\n\x60\x60\x60\n"))

    def test_unsupported_status(self):
        self.state["task"]["status"] = "approved"
        self.assertTrue(self.write())
