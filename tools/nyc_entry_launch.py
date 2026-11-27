"""NYC-ENTRY-P1 local candidate: no actual acquisition activation.

Preflight has no network; separate private notice review retrieves only one
public metadata document. Never paste the review context into chat or logs.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

from tools import nyc_address_frame as frame
from tools.nyc_launch import private_directory, git_clean_exact, non_dumpable_worker, supervised
from tools.nyc_metadata_notice import _decode, project_notice
from tools.nyc_metadata_observe import _fetch
from tools.nyc_qualification import QualificationError, require

AUTHORITY = "NYC-ENTRY-P1"
MARKER = "nyc-entry-p1-2026-11-28.consumed"
MAX_CONTEXT = 24000


def workspace():
    require(sys.platform.startswith("linux") and os.name == "posix"
            and not any(os.environ.get(k) for k in
                        ("CI", "GITHUB_ACTIONS", "GITHUB_RUN_ID", "SSLKEYLOGFILE")),
            "local_environment_required")
    require("microsoft" in Path("/proc/sys/kernel/osrelease").read_text().lower(),
            "wsl_required")
    path = Path.home() / ".hpi-nyc-entry-p1"
    path.mkdir(mode=0o700, exist_ok=True)
    return private_directory(path)


def guest_swap_absent():
    with open("/proc/swaps", encoding="ascii") as stream:
        require(stream.readline(4096).split() == ["Filename", "Type", "Size", "Used", "Priority"],
                "guest_swap_unverified")
        return not bool(stream.read(1))


def protection_probe():
    return {**non_dumpable_worker(), "guest_swap_absent": guest_swap_absent()}


def preflight(directory, commit):
    git_clean_exact(commit)
    require(not os.path.lexists(directory / MARKER), "attempt_already_consumed")
    outcome = supervised(protection_probe, seconds=15)
    require(outcome.get("status") == "completed", "process_protection_unverified")
    controls = outcome["result"]
    require(type(controls) is dict and set(controls) == {
        "core_dumps_disabled", "process_dumpable", "guest_swap_absent"}
        and controls["core_dumps_disabled"] is True
        and controls["process_dumpable"] is False
        and type(controls["guest_swap_absent"]) is bool, "process_protection_unverified")
    return {"authority": AUTHORITY, "reviewed_commit": commit,
            "workspace_owner_only": True, **controls,
            "preflight_passed": controls["guest_swap_absent"],
            "host_protection_independently_verified": False,
            "notice_review_required": True, "attempt_consumed": False,
            "record_requests": 0, "live_enabled": False}


def notice_context(payload):
    """Exact pinned public metadata subset for private interactive review."""
    projected = project_notice(frame.DATASET, payload, frame.REVISION)
    raw = _decode(payload)
    custom = raw.get("metadata", {}).get("custom_fields", {})
    require(type(custom) is dict and all(type(group) is dict
            and all(type(value) in (str, int, float, bool, type(None))
                    for value in group.values()) for group in custom.values()),
            "notice_context_unreviewable")
    result = {"dataset": frame.DATASET, "revision": frame.REVISION,
              "description": raw.get("description"), "attribution": raw.get("attribution"),
              "attributionLink": raw.get("attributionLink"), "custom_fields": custom,
              "recognised_notices": projected["notice_fields"],
              "reference_links": projected["reference_links"],
              "license_id": projected["license_id"],
              "license_detail": projected["license_detail"],
              "manual_review_required": True, "record_requests": 0}
    encoded = json.dumps(result, ensure_ascii=True, allow_nan=False)
    require(len(encoded) <= MAX_CONTEXT, "notice_context_limit")
    return result


def consume(directory, commit):
    """Distinct durable non-record marker for future guarded activation."""
    try:
        fd = os.open(directory / MARKER, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                     | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        raise QualificationError("attempt_already_consumed") from None
    with os.fdopen(fd, "w", encoding="ascii") as stream:
        stream.write(commit + "\n" + datetime.now(timezone.utc).isoformat() + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-commit", required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--review-notices", action="store_true")
    modes.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        require(re.fullmatch(r"[0-9a-f]{40}", args.reviewed_commit), "invalid_commit")
        require(not args.execute, "activation_pending")
        directory = workspace()
        git_clean_exact(args.reviewed_commit)
        if args.preflight:
            report = preflight(directory, args.reviewed_commit)
            print(json.dumps(report, sort_keys=True))
            return 0 if report["preflight_passed"] else 1
        require(sys.stdout.isatty(), "private_interactive_review_required")
        report = notice_context(_fetch(frame.DATASET))
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True))
        return 0
    except QualificationError as exc:
        reason = str(exc)
        print(json.dumps({"status":"blocked", "reason": reason if
              re.fullmatch(r"[a-z][a-z_]{0,79}", reason) else "preflight_refused"}))
        return 1
    except Exception:
        print('{"status":"blocked","reason":"local_preflight_failure"}')
        return 1


if __name__ == "__main__":
    sys.exit(main())
