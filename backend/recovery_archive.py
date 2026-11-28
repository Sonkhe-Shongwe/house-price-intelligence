"""Operator-only encrypted recovery package for an existing reviewed dump and seal.

No database access, network, provisioning, secret logging or automated restore.
A package is not proof of source rights, trusted storage or relational integrity.
"""
import getpass
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

from backend.historical_seal_config import load_historical_seal

MAX_DUMP = 64 * 1024 * 1024
MAX_PACKAGE = MAX_DUMP + 1024 * 1024
MEMBERS = ("database.dump", "seal.json")
REPO = Path(__file__).resolve().parents[1]


class RecoveryRefused(ValueError):
    pass


def _private_directory(path):
    p = Path(path).absolute()
    if (os.name != "posix" or p.resolve(strict=True) != p or not p.is_dir()
            or p.stat().st_uid != os.getuid() or p.stat().st_mode & 0o077
            or p.is_relative_to(REPO)):
        raise RecoveryRefused("Private off-repository directory required")
    return p


def _read_private(path, limit):
    p = Path(path).absolute()
    root = _private_directory(p.parent)
    fd = os.open(root / p.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        st = os.fstat(stream.fileno())
        if (not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid()
                or st.st_nlink != 1 or st.st_mode & 0o077
                or not 0 < st.st_size <= limit):
            raise RecoveryRefused("Private bounded recovery file required")
        data = stream.read(limit + 1)
        if len(data) != st.st_size:
            raise RecoveryRefused("Recovery file changed or exceeded limit")
    return data


def _gpg(payload, passphrase, *, decrypt=False):
    if (not isinstance(passphrase, str) or not re.fullmatch(r"[!-~]{32,128}", passphrase)):
        raise RecoveryRefused("A strong separate recovery passphrase is required")
    with tempfile.TemporaryDirectory() as home:
        read_fd, write_fd = os.pipe()
        try:
            try:
                os.write(write_fd, passphrase.encode("ascii") + b"\n")
            finally:
                os.close(write_fd)
            command = ["gpg", "--no-options", "--homedir", home, "--batch",
                       "--no-tty", "--pinentry-mode", "loopback", "--no-symkey-cache",
                       "--passphrase-fd", str(read_fd), "--output", "-"]
            if decrypt:
                command += ["--max-output", str(MAX_PACKAGE), "--decrypt"]
            else:
                command += ["--compress-algo", "none", "--symmetric", "--cipher-algo", "AES256"]
            result = subprocess.run(command, input=payload, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, pass_fds=(read_fd,), timeout=120)
            if result.returncode or not 0 < len(result.stdout) <= MAX_PACKAGE:
                raise RecoveryRefused("Encrypted recovery operation refused")
            return result.stdout
        finally:
            os.close(read_fd)
            subprocess.run(["gpgconf", "--homedir", home, "--kill", "gpg-agent"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)


def _validated_members(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        entries = archive.infolist()
        if (len(entries) != 2 or {x.filename for x in entries} != set(MEMBERS)
                or any(x.compress_type != zipfile.ZIP_STORED or x.flag_bits & 1
                       or not 0 < x.file_size <= (MAX_DUMP if x.filename == MEMBERS[0] else 4096)
                       for x in entries)):
            raise RecoveryRefused("Recovery package contents refused")
        dump, seal = (archive.read(name) for name in MEMBERS)
    if not dump.startswith(b"PGDMP"):
        raise RecoveryRefused("PostgreSQL custom dump required")
    # Same seal schema, duplicate-key rejection and ownership rules as runtime.
    with tempfile.TemporaryDirectory() as private:
        path = Path(private) / "seal.json"
        _write_new(path, seal)
        load_historical_seal(path)
    return dump, seal


def _write_new(path, data):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink()
        raise


def pack_backup(dump_path, seal_path, destination, passphrase):
    """Publish one authenticated encrypted package without overwriting a backup."""
    dump = _read_private(dump_path, MAX_DUMP)
    if not dump.startswith(b"PGDMP"):
        raise RecoveryRefused("PostgreSQL custom dump required")
    seal = json.dumps(load_historical_seal(seal_path), sort_keys=True).encode()
    target = Path(destination).absolute()
    root = _private_directory(target.parent)
    with io.BytesIO() as plain:
        with zipfile.ZipFile(plain, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr(MEMBERS[0], dump)
            archive.writestr(MEMBERS[1], seal)
        payload = plain.getvalue()
    ciphertext = _gpg(payload, passphrase)
    # Confirm the actual generated bytes are decryptable before publication.
    if _gpg(ciphertext, passphrase, decrypt=True) != payload:
        raise RecoveryRefused("Encrypted package verification failed")
    _publish_ciphertext(root, target, ciphertext)


def _publish_ciphertext(root, target, ciphertext):
    with tempfile.TemporaryDirectory(dir=root) as stage:
        staged = Path(stage) / "package.gpg"
        _write_new(staged, ciphertext)
        os.link(staged, target, follow_symlinks=False)
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

def rekey_backup(archive_path, destination, old_passphrase, new_passphrase):
    """Re-encrypt an existing authenticated package, preserving its payload.

    No database capture, restore, source overwrite or plaintext dump output.
    The existing seal validator uses a private temporary seal file.
    Python memory/swap and device security remain operator responsibilities.
    """
    if old_passphrase == new_passphrase:
        raise RecoveryRefused("A distinct recovery passphrase is required")
    target = Path(destination).absolute()
    root = _private_directory(target.parent)
    if target.exists() or target.is_symlink():
        raise RecoveryRefused("New recovery package destination required")
    payload = _gpg(_read_private(archive_path, MAX_PACKAGE), old_passphrase, decrypt=True)
    _validated_members(payload)
    ciphertext = _gpg(payload, new_passphrase)
    if _gpg(ciphertext, new_passphrase, decrypt=True) != payload:
        raise RecoveryRefused("Re-encrypted package verification failed")
    _publish_ciphertext(root, target, ciphertext)


def verify_backup(archive_path, passphrase):
    """Authenticate and validate the package without publishing plaintext."""
    _validated_members(_gpg(_read_private(archive_path, MAX_PACKAGE), passphrase, decrypt=True))


def unpack_backup(archive_path, destination, passphrase):
    """Authenticate first; publish only into a newly created private directory.

    Does not execute pg_restore. Never restore into an existing database.
    """
    dump, seal = _validated_members(_gpg(_read_private(archive_path, MAX_PACKAGE), passphrase, decrypt=True))
    target = Path(destination).absolute()
    _private_directory(target.parent)
    target.mkdir(mode=0o700)
    try:
        for name, value in zip(MEMBERS, (dump, seal)):
            _write_new(target / name, value)
    except BaseException:
        for name in MEMBERS:
            (target / name).unlink(missing_ok=True)
        target.rmdir()
        raise
    return target / MEMBERS[0], target / MEMBERS[1]


def main():
    args = sys.argv[1:]
    if not sys.stdin.isatty() or not args or (args[0], len(args)) not in (
            ("pack", 4), ("verify", 2), ("unpack", 3), ("rekey", 3)):
        print("Use pack DUMP SEAL NEW_ARCHIVE, verify ARCHIVE, unpack ARCHIVE NEW_DIRECTORY, or rekey ARCHIVE NEW_ARCHIVE interactively", file=sys.stderr)
        return 1
    try:
        secret = getpass.getpass("Existing recovery passphrase (not echoed): " if args[0] == "rekey" else "Separate recovery passphrase (not echoed): ")
        if args[0] == "pack":
            if secret != getpass.getpass("Confirm recovery passphrase: "):
                raise RecoveryRefused("Passphrase confirmation refused")
            pack_backup(*args[1:], secret)
        elif args[0] == "rekey":
            replacement = getpass.getpass("New separate recovery passphrase (not echoed): ")
            if replacement != getpass.getpass("Confirm new recovery passphrase: "):
                raise RecoveryRefused("Passphrase confirmation refused")
            rekey_backup(*args[1:], secret, replacement)
        elif args[0] == "verify":
            verify_backup(args[1], secret)
        else:
            unpack_backup(*args[1:], secret)
    except (Exception, KeyboardInterrupt):
        print("Recovery package operation refused or failed", file=sys.stderr)
        return 1
    print("Recovery package operation verified; no database operation performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
