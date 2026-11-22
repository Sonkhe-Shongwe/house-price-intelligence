#!/usr/bin/env python3
"""Single no-dependency verification command for House Price Intelligence.

Runs the existing research suites plus the synthetic application suite.
Network extraction, dependency installation, browser launch, commit and push
are deliberately excluded. A green result is NOT graphical acceptance.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITES = (
    ("research Phase 0", "audit/phase0", "tests"),
    ("research Phase 1", "audit/phase1", "tests"),
    ("research Phase 2", "audit/phase2", "tests"),
    ("aggregate report exporter", "audit/cloud", "tests"),
    ("P3 synthetic application", ".", "backend/tests"),
)


def execute(label: str, command: list[str], working_dir: Path) -> bool:
    print(f"\n== {label} ==", flush=True)
    result = subprocess.run(command, cwd=working_dir, check=False)
    print(f"{label}: {'PASS' if result.returncode == 0 else 'FAIL'}", flush=True)
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--focus", choices=("all", "app", "research"), default="all",
                        help="Run relevant checks while coding; default runs everything")
    args = parser.parse_args(argv)
    successes: list[bool] = []
    for label, path, tests in SUITES:
        if args.focus == "app" and not label.startswith("P3"):
            continue
        if args.focus == "research" and label.startswith("P3"):
            continue
        successes.append(execute(label,
                                 [sys.executable, "-m", "unittest", "discover", "-s", tests, "-q"],
                                 ROOT / path))
    if args.focus in ("all", "app"):
        node = shutil.which("node")
        if node:
            successes.append(execute("browser JavaScript syntax", [node, "--check", "frontend/app.js"], ROOT))
        else:
            print("\nSKIP: Node.js not installed; JavaScript syntax not verified", flush=True)
            # Not a failing CI check: Node is an optional diagnostic tool.
        print("NOTE: No visual browser execution or public-data permission is verified here.", flush=True)
    checker = ROOT / "tools/check_docs.py"
    if args.focus == "all" and checker.exists():
        successes.append(execute("documentation consistency", [sys.executable, str(checker)], ROOT))
    return 0 if all(successes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
