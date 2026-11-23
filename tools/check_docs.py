#!/usr/bin/env python3
"""Offline Markdown link and P0-P8 percentage consistency check.

Runs on GitHub Actions without downloading private data or consulting the web.
External links and anchor fragments are not validated here.
"""
from __future__ import annotations

from pathlib import Path
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
        "README.md": ("--fixture-db", "PRs #5 and #6"),
        "docs/MASTER_CONTINUATION_PROMPT.md": ("Master Continuation Prompt v1.4", "two-to-three-property shortlist"),
        "docs/ROADMAP.md": ("P6 two-to-three-property shortlist", "22.8%"),
        "docs/DOCUMENTATION_INDEX.md": ("PROFESSIONAL_UI_AND_MAPPING_RESEARCH_2026-11-23.md",),
        "docs/GITHUB_SETUP.md": ("`development`", "git switch development", "git pull --ff-only origin development"),
        "frontend/README.md": ("POST /v1/addresses/search", "105 Fictional Court", "building_identity_verified"),
        "docs/engineering/P3_APPLICATION_CONTRACT.md": (
            "## Current synthetic API and data contract on `development`",
            "`p3-draft-v0.3`", "`synthetic_address_candidates`",
        ),
        "docs/CHECKPOINT.md": ("## Current verified implementation on development", "`development`", "`main`"),
        "docs/P_PHASE_ROADMAP.md": ("## Granular deliverable and acceptance matrix", "P3.11", "P8.8"),
    }
    forbidden = {
        "README.md": ("not a public service or durable shortlist",),
        "frontend/README.md": ("**The in-memory data disappear on shutdown**", "7 actual Chromium browser journeys"),
        "docs/ROADMAP.md": ("durable persistence and P6 shortlist/compare remain ahead",),
        "docs/P_PHASE_ROADMAP.md": ("no production database, real-data property API, accepted buyer UI, durable multi-property shortlist or deployment exists",),
        "docs/engineering/P3_APPLICATION_CONTRACT.md": ("The server uses in-memory SQLite: **no restart persistence** and no completed P6 shortlist",),
        "docs/GITHUB_SETUP.md": ("Code changes are committed to `main`", "git pull --ff-only origin main"),
        "frontend/README.md": ("**Not implemented:** trusted address search",),
        "docs/ROADMAP.md": ("127 patched tests, not committed",),
        "docs/CHECKPOINT.md": ("the stricter sale-price/sales-snapshot guard remains in a review-only patch",),
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


def main():
    errors = local_link_errors(ROOT) + progress_errors(ROOT) + active_handoff_errors(ROOT)
    if errors:
        print("Documentation checks failed:")
        for issue in errors:
            print("- " + issue)
        return 1
    print("Documentation checks passed: local links, P0-P8 arithmetic and current-handoff invariants agree.")
    print("This is not a semantic audit of all historical reports, external URLs or product acceptance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
