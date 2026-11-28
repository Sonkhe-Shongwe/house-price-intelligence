"""Manifest-bound tool/asset acquisition primitive; not a live runner.

No approved production asset manifest exists yet. The eventual reviewed
one-shot runner supplies immutable entries from source control, not from
browser input or upstream metadata. No archive extraction or execution here.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import http.client
import os
from pathlib import Path
import re
import ssl
import time
from types import MappingProxyType

from backend.basemap_limits import ASSET_LIMIT, require_disposable_mount
from backend.basemap_transport import AcquisitionBlocked, MAX_SECONDS, _length

# Intentionally empty until actual released binaries and required assets have
# passed security, exact source, byte size, SHA-256 and licence review.
REVIEWED_ASSETS = ()


@dataclass(frozen=True)
class Asset:
    name: str
    host: str
    path: str
    size: int
    sha256: str
    notice: str


def _connect(host: str, timeout: float):
    return http.client.HTTPSConnection(
        host, 443, timeout=timeout, context=ssl.create_default_context()
    )


def _valid(asset: Asset) -> bool:
    return (
        re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}", asset.name) is not None
        and re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*\.[a-z]{2,}", asset.host) is not None
        and re.fullmatch(r"/[a-zA-Z0-9._/-]{1,1024}", asset.path) is not None
        and all(segment not in ("", ".", "..") for segment in asset.path[1:].split("/"))
        and type(asset.size) is int and 0 < asset.size <= ASSET_LIMIT
        and re.fullmatch(r"[0-9a-f]{64}", asset.sha256) is not None
        and bool(asset.notice.strip())
    )


class BoundedAssets:
    """Sequential, no redirect or retry, reserve declared bytes before GET.

    32 MiB maximum, independent of the archive transport's 64 MiB. The
    acquisition supervisor must enforce the shared outer 600-second deadline.
    Test-only injected connections and mount checks never enter a live runner.
    """
    def __init__(self, workdir: Path, *, manifest=REVIEWED_ASSETS,
                 _connection_factory=_connect, _mount_check=require_disposable_mount,
                 _clock=time.monotonic, _byte_limit=ASSET_LIMIT, _seconds=MAX_SECONDS):
        if not (0 < _byte_limit <= ASSET_LIMIT and 0 < _seconds <= MAX_SECONDS):
            raise ValueError("limits may only be tightened")
        entries = tuple(manifest)
        if (not all(isinstance(a, Asset) and _valid(a) for a in entries)
                or len({a.name for a in entries}) != len(entries)
                or len({(a.host, a.path) for a in entries}) != len(entries)
                or sum(a.size for a in entries) > _byte_limit):
            raise AcquisitionBlocked("asset_manifest_invalid")
        self.workdir = _mount_check(workdir)
        self.entries = MappingProxyType({a.name: a for a in entries})
        self._factory = _connection_factory
        self._clock = _clock
        self._deadline = _clock() + _seconds
        self._byte_limit = _byte_limit
        self.reserved_bytes = 0
        self.received_bytes = 0
        self.attempted = set()
        self.blocked = False

    def _remaining(self):
        left = self._deadline - self._clock()
        if left <= 0:
            raise AcquisitionBlocked("asset_deadline_exhausted")
        return left

    def fetch(self, name: str) -> Path:
        conn = response = None
        target = None
        created = success = False
        try:
            if self.blocked:
                raise AcquisitionBlocked("asset_transport_blocked")
            asset = self.entries.get(name)
            if asset is None or name in self.attempted:
                raise AcquisitionBlocked("asset_not_authorised")
            self._remaining()
            target = self.workdir / asset.name
            # Do not overwrite an existing file or follow a symlink.
            if target.exists() or target.is_symlink():
                raise AcquisitionBlocked("asset_target_exists")
            if self.reserved_bytes + asset.size > self._byte_limit:
                raise AcquisitionBlocked("asset_byte_budget")
            self.attempted.add(name)
            self.reserved_bytes += asset.size
            conn = self._factory(asset.host, min(15, self._remaining()))
            conn.request("GET", asset.path, headers={
                "Accept-Encoding": "identity",
                "User-Agent": "HousePriceIntelligence-bounded-context-rehearsal/1",
            })
            response = conn.getresponse()
            self._remaining()
            if response.status != 200:
                raise AcquisitionBlocked("asset_status_rejected")
            if _length(response) != asset.size:
                raise AcquisitionBlocked("asset_length_mismatch")
            digest = hashlib.sha256()
            count = 0
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            created = True
            with os.fdopen(fd, "wb") as handle:
                while count < asset.size:
                    self._remaining()
                    chunk = response.read1(min(65536, asset.size-count))
                    self.received_bytes += len(chunk)
                    if not chunk:
                        raise AcquisitionBlocked("asset_truncated")
                    if len(chunk) > asset.size-count:
                        raise AcquisitionBlocked("asset_length_mismatch")
                    handle.write(chunk)
                    digest.update(chunk)
                    count += len(chunk)
                    self._remaining()
            if digest.hexdigest() != asset.sha256:
                raise AcquisitionBlocked("asset_digest_mismatch")
            success = True
            return target
        except AcquisitionBlocked:
            self.blocked = True
            raise
        except Exception:
            self.blocked = True
            raise AcquisitionBlocked("asset_transport_failed") from None
        finally:
            if response is not None:
                response.close()
            if conn is not None:
                conn.close()
            if created and not success:
                target.unlink(missing_ok=True)
