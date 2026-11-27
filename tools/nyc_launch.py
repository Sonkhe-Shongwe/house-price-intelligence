"""Local-only NYC research supervisor; never run real records in public CI.

Metadata-only mode is distinct from the single approved record attempt.
No activation manifest is provided: reviewed current source metadata, terms,
temporal coverage, exact-head CI and actual local protection must be established
first. A manifest is a record of those reviews, not proof that they occurred.
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
    FIELDS, MAX_SECONDS, CURRENT_SNAPSHOT, QualificationError, projection, require,
)

REPO = Path(__file__).resolve().parents[1]
MARKER = "nyc-qualification-2026-11-27.consumed"
MAX_MANIFEST = 16384
MAX_REPORT = 16384


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
    return Collector(https_response)._run(plan, reviewed_sources=sources)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--metadata-only", action="store_true")
    mode.add_argument("--check-plan", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        workspace = private_directory(args.workspace)
        if args.metadata_only:
            result = supervised(lambda: Collector(https_response).metadata_summary())
        else:
            raw = read_manifest(workspace)
            plan, sources = validate_manifest(raw, datetime.now(timezone.utc).date())
            git_clean_exact(raw["reviewed_commit"])
            require(not (workspace / MARKER).exists(), "attempt_already_consumed")
            if args.check_plan:
                result = {"status": "plan_structure_checked",
                          "protection_independently_verified_by_tool": False,
                          "acquisition_started": False}
            else:
                # Operational hold: no live activation until reviewed source
                # revisions and actual local protection evidence are accepted
                # in the authoritative checkpoint, then reviewed code enables it.
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
