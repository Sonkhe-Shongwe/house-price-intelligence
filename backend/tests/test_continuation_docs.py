import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from tools.check_docs import catalogue_errors, continuation_errors, progress_errors, selected_anchor_errors, current_scope_errors


class ContinuationRoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()
        for name in ("MASTER_CONTINUATION_PROMPT.md", "DECISIONS.md", "P_PHASE_ROADMAP.md", "history.md"):
            (self.root / "docs" / name).write_text("test", encoding="utf-8")
        self.state = {"schema_version": 2, "active_phase": "P0", "phase_gate": "blocked",
                      "task": {"id": "P0-TEST", "status": "ready", "objective": "Inspect metadata", "scope": "read only",
                               "acceptance": "Evidence recorded", "stop": "Before intake",
                               "read": ["docs/P_PHASE_ROADMAP.md"], "read_ranges": {"docs/P_PHASE_ROADMAP.md": [[1, 1, "test", "test"]]}, "evidence": ["docs/history.md"]},
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

    def test_stale_range_marker(self):
        (self.root / "docs/P_PHASE_ROADMAP.md").write_text("changed", encoding="utf-8")
        self.assertTrue(any("stale boundary" in e for e in self.write()))

    def test_missing_ranges(self):
        self.state["task"]["read_ranges"] = {}
        self.assertTrue(self.write())

    def test_overlap_and_out_of_bounds(self):
        for value in ([[1, 1, "test", "test"], [1, 1, "test", "test"]], [[1, 2, "test", "test"]]):
            self.state["task"]["read_ranges"]["docs/P_PHASE_ROADMAP.md"] = value
            self.assertTrue(self.write())

    def test_catalogue_missing_and_complete(self):
        index = self.root / "docs/DOCUMENTATION_INDEX.md"
        index.write_text("[one](history.md)", encoding="utf-8")
        self.assertTrue(catalogue_errors(self.root))
        index.write_text("\n".join(f"[{p.name}]({p.name})" for p in index.parent.glob("*.md") if p != index), encoding="utf-8")
        self.assertEqual(catalogue_errors(self.root), [])

    def test_canonical_progress_total(self):
        roadmap = self.root / "docs/P_PHASE_ROADMAP.md"
        rows = [f"| P{i} | Test | {20 if i == 0 else 10}% | 50% |" for i in range(9)]
        roadmap.write_text("\n".join(rows + ["| **Total** | Test | 100% | **50.0% weighted** |"]), encoding="utf-8")
        self.assertEqual(progress_errors(self.root), [])
        roadmap.write_text(roadmap.read_text(encoding="utf-8").replace("50.0% weighted", "51.0% weighted"), encoding="utf-8")
        self.assertTrue(progress_errors(self.root))

    def test_selected_authority_anchor_requires_heading_and_route(self):
        src = self.root / "docs/DECISIONS.md"
        dest = self.root / "docs/history.md"
        routes = (("docs/DECISIONS.md", "docs/history.md", "prior-authority-consumed"),)
        dest.write_text("## Prior authority consumed\n", encoding="utf-8")
        src.write_text("[decision](history.md#prior-authority-consumed)\n", encoding="utf-8")
        self.assertEqual(selected_anchor_errors(self.root, routes), [])
        dest.write_text("## Other heading\n", encoding="utf-8")
        self.assertTrue(selected_anchor_errors(self.root, routes))
        dest.write_text("## Prior authority consumed\n", encoding="utf-8")
        src.write_text("[decision](history.md#other-heading)\n", encoding="utf-8")
        self.assertTrue(selected_anchor_errors(self.root, routes))
        src.write_text("[decision](history.md#prior-authority-consumed)\n", encoding="utf-8")
        dest.write_text("## Prior authority consumed\n## Prior authority consumed\n", encoding="utf-8")
        self.assertTrue(selected_anchor_errors(self.root, routes))

    def test_current_scope_refuses_stale_current_not_history(self):
        (self.root / "docs/engineering").mkdir()
        directive = self.root / "docs/engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md"
        directive.write_text("**Current direction:** Use checkpoint\n", encoding="utf-8")
        decision = self.root / "docs/DECISIONS.md"
        decision.write_text("Historical: Neither attempt has been consumed\nCurrent operating scope: no replay\n", encoding="utf-8")
        self.assertEqual(current_scope_errors(self.root), [])
        decision.write_text("Current operating scope: Neither attempt has been consumed\n", encoding="utf-8")
        self.assertTrue(current_scope_errors(self.root))

