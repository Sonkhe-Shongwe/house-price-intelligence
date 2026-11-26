#!/usr/bin/env python3
"""Offline Markdown link and P0-P8 percentage consistency check.

Runs on GitHub Actions without downloading private data or consulting the web.
External links and anchor fragments are not validated here.
"""
from __future__ import annotations

from pathlib import Path
import json
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
INLINE_LINK = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^\s)]+)(?:\s+[^)]*)?\)")
STAGE_ROW = re.compile(r"^\|\s*(P[0-8])\s*\|")
PERCENT = re.compile(r"^\s*(\d+(?:\.\d+)?)%\s*$")


def documents(root: Path):
    for path in root.rglob("*.md"):
        if any(p in {".git", ".venv", "venv", "node_modules", "output", "outputs", "build", "dist"} for p in path.relative_to(root).parts):
            continue
        yield path


def local_link_errors(root: Path):
    errors = []
    for path in documents(root):
        content = path.read_text(encoding="utf-8")
        # Ignore fenced code blocks which may demonstrate nonexistent files.
        content = re.sub(r"(?ms)^\x60\x60\x60[^\n]*\n.*?^\x60\x60\x60\s*$", "", content)
        for token in INLINE_LINK.findall(content):
            if token.startswith(("#", "//")) or re.match(r"^[a-z][a-z0-9+.-]*:", token, re.I):
                continue
            relative = unquote(token.split("#", 1)[0].split("?", 1)[0])
            if not relative:
                continue
            target = (path.parent / relative).resolve()
            if not target.is_relative_to(root.resolve()) or not target.exists():
                errors.append(f"{path.relative_to(root)}: broken local link -> {token}")
    return errors


def phase_rows(path: Path):
    found = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not STAGE_ROW.match(line):
            continue
        cells = [s.strip() for s in line.strip("|").split("|")]
        if len(cells) < 4:
            raise ValueError(f"{path}: malformed stage row {line}")
        key = cells[0]
        if key in found:
            raise ValueError(f"{path}: duplicate {key} row")
        wt, completed = (PERCENT.fullmatch(x) for x in (cells[2], cells[3]))
        if wt is None or completed is None:
            raise ValueError(f"{path}: missing numeric percentages for {key}")
        found[key] = (float(wt.group(1)), float(completed.group(1)))
    return found


def progress_errors(root: Path):
    brief = root / "docs" / "ROADMAP.md"
    full = root / "docs" / "P_PHASE_ROADMAP.md"
    errors = []
    try:
        br, fu = phase_rows(brief), phase_rows(full)
        expected = {f"P{i}" for i in range(9)}
        if set(br) != expected or set(fu) != expected:
            errors.append("P0-P8 tables must both contain every stage exactly once")
        if br != fu:
            errors.append("P0-P8 stage weights/completions differ across roadmap documents")
        if abs(sum(w for w, _ in fu.values()) - 100) > 0.001:
            errors.append("P0-P8 phase weights do not total 100%")
        total = sum(w * pct / 100 for w, pct in fu.values())
        expected_label = f"{total:.1f}%"
        if expected_label not in brief.read_text(encoding="utf-8"):
            errors.append(f"Roadmap summary does not show computed progress {expected_label}")
        if expected_label not in full.read_text(encoding="utf-8"):
            errors.append(f"Detailed roadmap does not show computed progress {expected_label}")
        for rel in ("docs/DOCUMENTATION_INDEX.md", "README.md"):
            if expected_label not in (root / rel).read_text(encoding="utf-8"):
                errors.append(f"{rel}: current handoff lacks computed progress {expected_label}")
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def active_handoff_errors(root: Path):
    """Protect a few durable current-document contracts against status drift.

    This is deliberately narrow: dated reports and historical sections are
    excluded, and no test count, commit hash or accepted phase score is frozen.
    Passing this check does NOT establish full factual accuracy.
    """
    required = {
        "README.md": ("--fixture-db", "PRs #5 and #6", "--frontend react", "protected-storage", "South African data foundation", "DATA_MANAGER_V1.md"),
        "docs/MASTER_CONTINUATION_PROMPT.md": ("Master Continuation Prompt", "Standing engineering autonomy", "two-to-three-property shortlist", "PROFESSIONAL_FRONTEND_EXCELLENCE_DIRECTIVE.md", "P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md"),
        "docs/ROADMAP.md": ("P6 two-to-three-property shortlist",),
        "docs/DOCUMENTATION_INDEX.md": ("PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md", "archive/CHECKPOINT_EVIDENCE_2026-11-26.md", "archive/DECISION_HISTORY_2026-11-26.md", "archive/DELIVERY_MILESTONE_HISTORY_2026-11-26.md"),
        "docs/GITHUB_SETUP.md": ("`development`", "git switch development", "git pull --ff-only origin development"),
        "frontend/README.md": ("POST /v1/addresses/search", "105 Fictional Court", "building_identity_verified"),
        "docs/engineering/P3_APPLICATION_CONTRACT.md": (
            "## Current synthetic API and data contract on `development`",
            "`p3-draft-v0.3`", "`synthetic_address_candidates`",
        ),
        "docs/CHECKPOINT.md": ("## Current South African data repertoire", "## Current verified implementation on development", "`development`", "`main`", "PROFESSIONAL_FRONTEND_EXCELLENCE_DIRECTIVE.md", "P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md"),
        "docs/P_PHASE_ROADMAP.md": ("## Granular deliverable and acceptance matrix", "P3.11", "P8.8", "P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md"),
        "docs/engineering/P0_DISCOVERY_AND_FEASIBILITY_DIRECTIVE.md": (
            "P0-A Product foundation", "P0-B Market and competitive intelligence",
            "P0-C Data research and feasibility", "P0-D Legal, privacy and ethics",
            "P0-E Technical, financial and operational feasibility", "P0-F Definitive product specification",
            "P0-G Acceptance and closure", "P0-A.1", "P0-A.10", "P0.1-P0.7",
        ),
    }
    forbidden = {
        "README.md": ("not a public service or durable shortlist", "Actual provider-to-buyer integration, full protected storage", "active P0-B market and competitive intelligence"),
        "frontend/README.md": ("**The in-memory data disappear on shutdown**", "7 actual Chromium browser journeys", "**Not implemented:** trusted address search"),
        "docs/ROADMAP.md": ("durable persistence and P6 shortlist/compare remain ahead", "FE1 iconography next", "127 patched tests, not committed"),
        "docs/P_PHASE_ROADMAP.md": ("no production database, real-data property API, accepted buyer UI, durable multi-property shortlist or deployment exists",),
        "docs/engineering/P3_APPLICATION_CONTRACT.md": ("The server uses in-memory SQLite: **no restart persistence** and no completed P6 shortlist",),
        "docs/GITHUB_SETUP.md": ("Code changes are committed to `main`", "git pull --ff-only origin main"),
        "docs/CHECKPOINT.md": ("the stricter sale-price/sales-snapshot guard remains in a review-only patch",),
        "docs/DOCUMENTATION_INDEX.md": ("start FE1, not earlier prototypes", "Atlas candidate, not owner-approved"),
    }
    errors = []
    for rel, tokens in required.items():
        path = root / rel
        try:
            contents = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{rel}: cannot check active guidance: {exc}")
            continue
        for token in tokens:
            if token not in contents:
                errors.append(f"{rel}: missing current guidance: {token}")
    for rel, tokens in forbidden.items():
        try:
            contents = (root / rel).read_text(encoding="utf-8")
        except OSError:
            continue
        for token in tokens:
            if token in contents:
                errors.append(f"{rel}: obsolete current guidance: {token}")
    return errors


def continuation_errors(root: Path):
    """Check routing structure, not factual accuracy or authority."""
    errors = []
    try:
        checkpoint = (root / "docs/CHECKPOINT.md").read_text(encoding="utf-8")
        master = (root / "docs/MASTER_CONTINUATION_PROMPT.md").read_text(encoding="utf-8")
        for name, content, limit in (("checkpoint", checkpoint, 12000), ("master", master, 8000)):
            if len(content.encode("utf-8")) > limit:
                errors.append(f"{name} exceeds bootstrap budget {limit}")
        blocks = re.findall(r"(?ms)^\x60\x60\x60json\s*\n(.*?)^\x60\x60\x60\s*$", checkpoint)
        if len(blocks) != 1:
            raise ValueError("checkpoint must contain exactly one JSON routing block")
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate routing key: {key}")
                result[key] = value
            return result
        state = json.loads(blocks[0], object_pairs_hook=unique)
        keys = {"schema_version", "active_phase", "phase_gate", "task", "blockers", "parked", "authority", "history"}
        if not isinstance(state, dict) or set(state) != keys or type(state["schema_version"]) is not int or state["schema_version"] != 1:
            raise ValueError("invalid routing schema")
        if state["active_phase"] not in [f"P{i}" for i in range(9)]:
            raise ValueError("invalid active phase")
        if state["phase_gate"] not in ("open", "blocked", "accepted"):
            raise ValueError("invalid phase gate")
        task = state["task"]
        if not isinstance(task, dict) or set(task) != {"id", "status", "objective", "scope", "acceptance", "read", "evidence", "stop"}:
            raise ValueError("invalid task fields")
        if task["status"] not in ("ready", "blocked", "complete"):
            raise ValueError("invalid task status")
        for key in ("id", "objective", "scope", "acceptance", "stop"):
            if not isinstance(task[key], str) or not task[key].strip():
                raise ValueError(f"empty or invalid task {key}")
        if not task["id"].startswith(state["active_phase"] + "-"):
            raise ValueError("task ID must belong to active phase")
        for key in ("blockers", "parked"):
            if not isinstance(state[key], list) or any(not isinstance(v, str) or not v.strip() for v in state[key]):
                raise ValueError(f"invalid {key}")
        if (state["phase_gate"] == "blocked" or task["status"] == "blocked") and not state["blockers"]:
            raise ValueError("blocked phase/task needs a blocker")
        for key, refs in (("read", task["read"]), ("evidence", task["evidence"]), ("authority", state["authority"]), ("history", state["history"])):
            if not isinstance(refs, list) or not refs or any(not isinstance(v, str) or not v.strip() for v in refs):
                raise ValueError(f"invalid {key} references")
            if len(set(refs)) != len(refs):
                raise ValueError(f"duplicate {key} references")
            for ref in refs:
                target = (root / ref).resolve()
                if Path(ref).is_absolute() or not target.is_relative_to(root.resolve()) or not target.is_file():
                    raise ValueError(f"invalid {key} reference: {ref}")
        if "docs/DECISIONS.md" not in state["authority"] or "docs/P_PHASE_ROADMAP.md" not in task["read"]:
            raise ValueError("decision or roadmap authority missing")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"continuation: {exc}")
    return errors


def main():
    errors = local_link_errors(ROOT) + progress_errors(ROOT) + active_handoff_errors(ROOT) + continuation_errors(ROOT)
    if errors:
        print("Documentation checks failed:")
        for issue in errors:
            print("- " + issue)
        return 1
    print("Documentation checks passed: local links, P0-P8 arithmetic and current-handoff invariants and continuation routing agree.")
    print("This is not a semantic audit of all historical reports, external URLs or product acceptance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
