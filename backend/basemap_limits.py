"""Linux resource controls for disposable contextual basemap qualification.

Not an acquisition entry point, security sandbox, or authority to execute a
third-party binary. The eventual runner must enforce a single outer deadline,
reviewed tool/asset manifests, isolated egress and the one-shot owner marker.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess

from backend.basemap_transport import AcquisitionBlocked, MAX_SECONDS

DISK_LIMIT = 128 * 1024**2
OUTPUT_LIMIT = 50 * 1024**2
ASSET_LIMIT = 32 * 1024**2
TOTAL_PAYLOAD_LIMIT = 96 * 1024**2


def require_disposable_mount(path: Path) -> Path:
    """Require a dedicated, private Linux tmpfs, not a directory size estimate."""
    if not path.is_absolute() or path.is_symlink() or path.resolve() != path:
        raise AcquisitionBlocked("workspace_path_rejected")
    if not path.is_dir() or not os.path.ismount(path):
        raise AcquisitionBlocked("workspace_not_mount")
    # CI uses a simple space-free path. Fail closed on escaped mount names.
    entries = Path("/proc/self/mountinfo").read_text().splitlines()
    matches = [line.split(" - ", 1) for line in entries
               if line.split()[4] == str(path)]
    if len(matches) != 1 or matches[0][1].split()[0] != "tmpfs":
        raise AcquisitionBlocked("workspace_not_tmpfs")
    info = path.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise AcquisitionBlocked("workspace_not_private")
    stat = os.statvfs(path)
    if stat.f_blocks * stat.f_frsize > DISK_LIMIT:
        raise AcquisitionBlocked("workspace_capacity_exceeded")
    return path


def verify_file(path: Path, expected_sha256: str, *, ceiling=OUTPUT_LIMIT) -> int:
    """Check a fixed manifest entry before use; hash equality is not security review."""
    if (not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)
            or not 0 < ceiling <= OUTPUT_LIMIT):
        raise AcquisitionBlocked("file_manifest_invalid")
    if not path.is_file() or path.is_symlink():
        raise AcquisitionBlocked("file_type_rejected")
    size = path.stat().st_size
    if not 0 < size <= ceiling:
        raise AcquisitionBlocked("file_size_rejected")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected_sha256:
        raise AcquisitionBlocked("file_digest_mismatch")
    return size


def run_limited(argv: list[str], *, workdir: Path, executable_sha256: str,
                seconds: float, file_limit: int = OUTPUT_LIMIT) -> None:
    """Internal subprocess guard; do not pass unreviewed executable or user args.

    Linux prlimit sets hard per-file/core limits before exec. tmpfs provides
    aggregate storage capacity. Process-group termination bounds this child,
    not other jobs or escaped descendants; outer workflow isolation is required.
    No captured subprocess output, inherited credentials or shell expansion.
    """
    require_disposable_mount(workdir)
    if not argv or not 0 < seconds <= MAX_SECONDS or not 0 < file_limit <= OUTPUT_LIMIT:
        raise AcquisitionBlocked("process_limits_invalid")
    executable = Path(argv[0])
    if not executable.is_absolute():
        raise AcquisitionBlocked("executable_path_rejected")
    verify_file(executable, executable_sha256)
    prlimit = shutil.which("prlimit", path="/usr/bin:/bin")
    if not prlimit:
        raise AcquisitionBlocked("prlimit_unavailable")
    command = [prlimit, f"--fsize={file_limit}:{file_limit}", "--core=0:0", "--", *argv]
    env = {"PATH": "/usr/bin:/bin", "HOME": str(workdir),
           "TMPDIR": str(workdir), "TMP": str(workdir), "TEMP": str(workdir),
           "LANG": "C.UTF-8", "NO_PROXY": "127.0.0.1,localhost"}
    try:
        child = subprocess.Popen(command, cwd=workdir, env=env,
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        raise AcquisitionBlocked("child_launch_failed") from None
    try:
        try:
            code = child.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            raise AcquisitionBlocked("child_deadline_exhausted") from None
        if code:
            raise AcquisitionBlocked("child_failed")
    finally:
        # Clean up same-group descendants even after a normal parent exit.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait()
