"""Local-only NYC research supervisor; never run real records in public CI.

Metadata-only mode is distinct from the single approved record attempt.
The fixed-plan CLI requires a clean reviewed commit, fresh metadata-only
preflight, explicit operator acceptance of residual host risk for this public
research slice, and a durable one-attempt marker. Exact-head CI must be
reviewed by the operator before executing. No durable property-data acceptance.
No raw files, cache, credentials or property-level output are written.
"""
import argparse
from datetime import date, datetime, timezone
import json
import multiprocessing as mp
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

from tools.nyc_collector import Collector, FixturePlan, https_response, strict_pairs
from tools.nyc_qualification import (
    FIELDS, EXPECTED_TYPES, MAX_SECONDS, CURRENT_SNAPSHOT, QualificationError, projection, require,
)

REPO = Path(__file__).resolve().parents[1]
MARKER = "nyc-qualification-2026-11-27.consumed"
MAX_MANIFEST = 16384
MAX_REPORT = 16384

# Observed public metadata and release dates, not property records.
REVIEWED_REVISIONS = {
    "usep-8jbt": "1795635328:1795635300",
    "64uk-42ks": "1795476446:1795465895",
    "bnx9-e6tj": "1794332294:1740778366",
    "8h5j-fqxa": "1794332093:1740778244",
}
REVIEWED_RELEASE = "26v3"
REVIEWED_START = date(2025, 11, 1)
REVIEWED_END = date(2026, 10, 31)
REVIEWED_PUBLICATION = date(2026, 11, 23)


def canonical_workspace():
    # Only one durable, non-record attempt marker per owner workspace.
    return Path.home() / ".hpi-nyc-qualification"


def fixed_sources():
    return {d: {"revision": token, "types": dict(EXPECTED_TYPES[d])}
            for d, token in REVIEWED_REVISIONS.items()}


def reviewed_plan(today):
    require(type(today) is date and today >= REVIEWED_PUBLICATION, "invalid_manifest_dates")
    return FixturePlan(today, REVIEWED_START, REVIEWED_END, REVIEWED_PUBLICATION,
                       REVIEWED_RELEASE, False, CURRENT_SNAPSHOT), fixed_sources()


def enforce_fixed_plan(plan, sources, today):
    expected_plan, expected_sources = reviewed_plan(today)
    require(plan == expected_plan and sources == expected_sources,
            "reviewed_plan_conflict")


def non_dumpable_worker():
    """Verify Linux process-local controls, not host encryption or swap."""
    import ctypes
    import resource
    require(sys.platform.startswith("linux"), "linux_required")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    libc = ctypes.CDLL(None, use_errno=True)
    # PR_SET_DUMPABLE=4, PR_GET_DUMPABLE=3; no system-wide changes.
    require(libc.prctl(4, 0, 0, 0, 0) == 0 and libc.prctl(3, 0, 0, 0, 0) == 0,
            "worker_privacy_unverified")
    require(resource.getrlimit(resource.RLIMIT_CORE) == (0, 0),
            "worker_privacy_unverified")
    return {"core_dumps_disabled": True, "process_dumpable": False}


def disposable_preflight(workspace, plan, sources, today):
    require(workspace == canonical_workspace(), "noncanonical_workspace")
    enforce_fixed_plan(plan, sources, today)
    # Separate metadata-only check; no acquisition marker, no property rows.
    def task():
        protection = non_dumpable_worker()
        require(Collector(https_response).metadata_summary() == sources,
                "reviewed_source_changed")
        return {"workspace_owner_only": True, "source_pins_match": True,
                "worker_controls": protection, "record_attempt_started": False,
                "host_protection_independently_verified": False}
    return supervised(task)


def execute_reviewed(workspace, plan, sources, commit, today):
    """Wired acquisition path for the fixed, disposable research slice.

    Caller must have performed exact clean-checkout and private workspace checks.
    An operational marker, not a protection against deliberate owner bypass.
    """
    require(workspace == canonical_workspace(), "noncanonical_workspace")
    enforce_fixed_plan(plan, sources, today)
    # Confirm process controls in a separate invented-only probe before marker.
    probe = supervised(non_dumpable_worker)
    require(probe == {"status": "completed", "result": {
        "core_dumps_disabled": True, "process_dumpable": False}},
        "worker_privacy_unverified")
    consume(workspace, commit)
    # Marker remains even on transport errors, deadline or source drift.
    return supervised(lambda: live_report(plan, sources))


def private_directory(path, repo=REPO):
    require(os.name == "posix" and hasattr(os, "getuid"), "posix_required")
    require(not any(os.environ.get(k) for k in
                    ("CI", "GITHUB_ACTIONS", "GITHUB_RUN_ID")), "ci_forbidden")
    path = Path(path).absolute()
    require(path.resolve(strict=True) == path and path.is_dir(), "private_directory_required")
    repo = repo.resolve()
    require(not (path == repo or repo in path.parents or path in repo.parents),
            "workspace_must_be_separate")
    info = path.stat()
    require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700,
            "private_directory_permissions")
    return path


def validate_manifest(raw, today):
    fields = {"reviewed_commit", "source_review", "protection_review", "ci_review",
              "cutoff", "covered_from", "covered_through", "snapshot", "version", "sources"}
    require(isinstance(raw, dict) and set(raw) == fields, "invalid_manifest")
    require(isinstance(raw["reviewed_commit"], str)
            and re.fullmatch(r"[0-9a-f]{40}", raw["reviewed_commit"]), "invalid_commit")
    for k in ("source_review", "protection_review", "ci_review"):
        require(isinstance(raw[k], str) and 1 <= len(raw[k].strip()) <= 1000,
                "missing_review_evidence")
    try:
        values = [date.fromisoformat(raw[k]) for k in
                  ("cutoff", "covered_from", "covered_through", "snapshot")]
    except (TypeError, ValueError):
        raise QualificationError("invalid_manifest_dates") from None
    cutoff, start, end, snapshot = values
    require(cutoff == today and start <= end < cutoff and snapshot <= cutoff,
            "invalid_manifest_dates")
    require(isinstance(raw["version"], str)
            and re.fullmatch(r"[0-9]{2}v[0-9]+(?:\.[0-9]+)?", raw["version"]),
            "invalid_snapshot_version")
    sources = raw["sources"]
    require(isinstance(sources, dict) and set(sources) == set(FIELDS),
            "invalid_reviewed_sources")
    for d, entry in sources.items():
        require(isinstance(entry, dict) and set(entry) == {"revision", "types"}
                and isinstance(entry["revision"], str)
                and re.fullmatch(r"[1-9][0-9]*:[1-9][0-9]*", entry["revision"])
                and isinstance(entry["types"], dict)
                and set(entry["types"]) == set(projection(d, subject=d == "64uk-42ks"))
                and all(isinstance(x, str) and x in
                        ("text", "number", "calendar_date", "floating_timestamp",
                         "fixed_timestamp", "money", "checkbox")
                        for x in entry["types"].values()), "invalid_reviewed_sources")
    return FixturePlan(cutoff, start, end, snapshot, raw["version"],
                       False, CURRENT_SNAPSHOT), sources


def read_manifest(workspace):
    fd = os.open(workspace / "reviewed-nyc-plan.json",
                 os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1
                and 0 < info.st_size <= MAX_MANIFEST, "private_manifest_required")
        content = stream.read(MAX_MANIFEST+1)
        require(len(content) == info.st_size, "manifest_size_changed")
    try:
        return json.loads(content, object_pairs_hook=strict_pairs)
    except (ValueError, UnicodeError):
        raise QualificationError("invalid_manifest") from None


def git_clean_exact(commit, repo=REPO):
    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args],
                              check=True, capture_output=True, text=True,
                              timeout=10).stdout.strip()
    require(git("rev-parse", "HEAD") == commit and
            not git("status", "--porcelain", "--untracked-files=all"),
            "checkout_not_reviewed")


def consume(workspace, commit):
    """Atomic durable attempt marker, before first record-session request.

    On any later failure the marker remains. Never delete it to retry.
    The canonical private workspace must be maintained by the operator.
    """
    try:
        fd = os.open(workspace / MARKER, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                     | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        raise QualificationError("attempt_already_consumed") from None
    with os.fdopen(fd, "w", encoding="ascii") as stream:
        stream.write(commit + "\n" + datetime.now(timezone.utc).isoformat() + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    directory_fd = os.open(workspace, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _child(task, slot, length):
    # Child emits only a bounded result into shared memory; no source stderr,
    # stdout, exception traceback or core dump. No source output files.
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        with open(os.devnull, "wb") as sink:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
            result = task()
        value = {"status": "completed", "result": result}
    except QualificationError as exc:
        code = str(exc)
        value = {"status": "blocked", "reason": code if
                 re.fullmatch(r"[a-z][a-z_]{0,79}", code) else "qualification_failure"}
    except BaseException:
        value = {"status": "blocked", "reason": "worker_failure"}
    data = json.dumps(value, ensure_ascii=True, allow_nan=False).encode("ascii")
    if len(data) <= MAX_REPORT:
        slot[:len(data)] = data
        length.value = len(data)


def supervised(task, seconds=MAX_SECONDS):
    """Independent parent deadline even for stuck DNS/transport operations."""
    require(os.name == "posix" and 0 < seconds <= MAX_SECONDS, "invalid_deadline")
    ctx = mp.get_context("fork")
    slot = ctx.RawArray("B", MAX_REPORT)
    length = ctx.RawValue("I", 0)
    worker = ctx.Process(target=_child, args=(task, slot, length), daemon=True)
    worker.start()
    try:
        worker.join(seconds)
        if worker.is_alive():
            raise QualificationError("hard_deadline")
        require(worker.exitcode == 0 and 0 < length.value <= MAX_REPORT,
                "worker_result_unavailable")
        return json.loads(bytes(slot[:length.value]))
    finally:
        if worker.is_alive():
            worker.kill()
            worker.join(5)
        require(not worker.is_alive(), "worker_shutdown_unverified")
        worker.close()


def live_report(plan, sources):
    # Only the fixed collector path; no arbitrary transport, URL or predicate.
    non_dumpable_worker()
    return Collector(https_response)._run(plan, reviewed_sources=sources)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--reviewed-commit", help="Exact reviewed clean commit for the fixed plan")
    parser.add_argument("--accept-disposable-host-risk", action="store_true",
                        help="Operator accepts residual host/swap risk for this public-data study only")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--metadata-only", action="store_true")
    mode.add_argument("--check-plan", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        workspace = private_directory(args.workspace)
        require(not args.accept_disposable_host_risk or
                (args.execute and args.reviewed_commit), "invalid_host_risk_acknowledgement")
        if args.metadata_only:
            result = supervised(lambda: Collector(https_response).metadata_summary())
        elif args.execute and args.reviewed_commit:
            require(args.accept_disposable_host_risk, "disposable_host_risk_not_accepted")
            require(re.fullmatch(r"[0-9a-f]{40}", args.reviewed_commit), "invalid_commit")
            git_clean_exact(args.reviewed_commit)
            require(not (workspace / MARKER).exists(), "attempt_already_consumed")
            today = datetime.now(timezone.utc).date()
            plan, sources = reviewed_plan(today)
            preflight = disposable_preflight(workspace, plan, sources, today)
            if preflight.get("status") != "completed":
                result = preflight
            else:
                require(preflight == {"status": "completed", "result": {
                    "workspace_owner_only": True, "source_pins_match": True,
                    "worker_controls": {"core_dumps_disabled": True,
                                        "process_dumpable": False},
                    "record_attempt_started": False,
                    "host_protection_independently_verified": False}},
                    "preflight_evidence_invalid")
                require(datetime.now(timezone.utc).date() == today, "evaluation_date_changed")
                git_clean_exact(args.reviewed_commit)
                result = execute_reviewed(workspace, plan, sources, args.reviewed_commit, today)
        elif args.check_plan and args.reviewed_commit:
            require(re.fullmatch(r"[0-9a-f]{40}", args.reviewed_commit), "invalid_commit")
            git_clean_exact(args.reviewed_commit)
            require(not (workspace / MARKER).exists(), "attempt_already_consumed")
            today = datetime.now(timezone.utc).date()
            plan, sources = reviewed_plan(today)
            result = disposable_preflight(workspace, plan, sources, today)
        else:
            raw = read_manifest(workspace)
            today = datetime.now(timezone.utc).date()
            plan, sources = validate_manifest(raw, today)
            git_clean_exact(raw["reviewed_commit"])
            require(not (workspace / MARKER).exists(), "attempt_already_consumed")
            if args.check_plan:
                result = disposable_preflight(workspace, plan, sources, today)
            else:
                # A free-form manifest is not activation authority. Use only
                # the fixed plan with explicit risk acknowledgement.
                raise QualificationError("live_activation_not_accepted")
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] in ("completed", "plan_structure_checked") else 1
    except QualificationError as exc:
        code = str(exc)
        print(json.dumps({"status": "blocked", "reason": code if
                          re.fullmatch(r"[a-z][a-z_]{0,79}", code) else "qualification_failure"}))
        return 1
    except Exception:
        print('{"status":"blocked","reason":"local_preflight_failure"}')
        return 1


if __name__ == "__main__":
    sys.exit(main())
