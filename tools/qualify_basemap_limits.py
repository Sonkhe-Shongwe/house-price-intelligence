"""Actual Linux tmpfs and process-limit proof using invented files only.

Run as a regular user inside the CI-created private 128 MiB tmpfs.
No public requests, extractor installation, real archive or property data.
"""
import errno
import hashlib
import json
import os
from pathlib import Path
import sys
import time

# Invoked as python -m tools.qualify_basemap_limits.
from backend.basemap_limits import (
    require_disposable_mount, verify_file, run_limited, DISK_LIMIT,
    OUTPUT_LIMIT,
)
from backend.basemap_transport import AcquisitionBlocked


def rejects(expected, fn):
    try:
        fn()
    except AcquisitionBlocked as error:
        assert str(error) == expected, str(error)
    else:
        raise AssertionError(f"Missing rejection: {expected}")


def main():
    work = require_disposable_mount(Path(sys.argv[1]))
    assert not list(work.iterdir()), "Disposable proof requires an empty mount"
    capacity = os.statvfs(work).f_blocks * os.statvfs(work).f_frsize
    assert 0 < capacity <= DISK_LIMIT
    # Proof of the actual filesystem aggregate limit, not periodic polling.
    try:
        for name in ("quota-a", "quota-b"):
            with (work/name).open("xb") as file:
                os.posix_fallocate(file.fileno(), 0, 48 * 1024**2)
        with (work/"quota-over").open("xb") as file:
            try:
                os.posix_fallocate(file.fileno(), 0, 33 * 1024**2)
            except OSError as error:
                assert error.errno == errno.ENOSPC, error.errno
            else:
                raise AssertionError("128 MiB aggregate quota not enforced")
    finally:
        for name in ("quota-a", "quota-b", "quota-over"):
            (work/name).unlink(missing_ok=True)

    # Use the installed Python interpreter only, never a downloaded executable.
    executable = Path(sys.executable).resolve()
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    assert verify_file(executable, digest) > 0
    rejects("file_digest_mismatch", lambda: verify_file(executable, "0"*64))
    rejects("workspace_not_mount", lambda: require_disposable_mount(work/"subdir"))
    output = work/"invented-output.bin"
    def run(code, seconds=5, file_limit=1024):
        run_limited([str(executable), "-c", code], workdir=work,
                    executable_sha256=digest, seconds=seconds, file_limit=file_limit)
    run("from pathlib import Path; Path('invented-output.bin').write_bytes(b'x'*512)")
    assert output.stat().st_size == 512
    output.unlink()
    rejects("child_failed", lambda: run(
        "from pathlib import Path; Path('invented-output.bin').write_bytes(b'x'*2048)"))
    assert output.stat().st_size <= 1024
    output.unlink()
    start = time.monotonic()
    rejects("child_deadline_exhausted", lambda: run("import time; time.sleep(20)", seconds=0.2))
    assert time.monotonic()-start < 5
    # An untrusted child's inherited environment must not carry CI credentials.
    run("import os; assert 'HPI_FIXTURE_SECRET' not in os.environ")
    assert not list(work.iterdir())
    print(json.dumps({"status":"passed","scope":"invented resource-limit proof",
          "tmpfs_capacity_bytes":capacity,"aggregate_enospc":True,
          "file_limit_bytes":1024,"approved_output_limit_bytes":OUTPUT_LIMIT,
          "child_timeout_seconds":0.2,"digest_rejection":True,
          "credentials_not_inherited":True,"real_acquisition":False}))


if __name__ == "__main__":
    os.environ["HPI_FIXTURE_SECRET"] = "invented-value"
    main()
