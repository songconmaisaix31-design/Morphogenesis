"""TTL records protected by OS file locks, including the actual promotion effect."""

from __future__ import annotations

import math
import os
from pathlib import Path
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from uuid import uuid4

from pydantic import TypeAdapter

from swarm.models import Lease

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

_LEASES = TypeAdapter(list[Lease])


def canonical_scope(scope: str | Path) -> str:
    path = Path(scope)
    if not path.is_absolute():
        raise ValueError("lease scope must be absolute")
    return os.path.normcase(str(path.resolve()))


def scopes_collide(first: str, second: str) -> bool:
    a, b = Path(canonical_scope(first)), Path(canonical_scope(second))
    return a == b or a.is_relative_to(b) or b.is_relative_to(a)


class LeaseLost(RuntimeError):
    pass


class LeaseManager:
    def __init__(self, directory: str | Path, *, clock: Callable[[], float] = time.time,
                 lock_timeout_seconds: float = 10.0) -> None:
        if not math.isfinite(lock_timeout_seconds) or not 0 <= lock_timeout_seconds <= 60:
            raise ValueError("lock_timeout_seconds must be finite and between zero and 60")
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.lock_timeout_seconds = lock_timeout_seconds
        self.state_path = self.directory / "leases.json"
        self.lock_path = self.directory / "leases.lock"

    def _now(self) -> float:
        now = self.clock()
        if not math.isfinite(now) or now < 0:
            raise ValueError("invalid clock")
        return now

    @staticmethod
    def _ttl(ttl: float) -> None:
        if not math.isfinite(ttl) or ttl <= 0:
            raise ValueError("TTL must be positive and finite")

    @contextmanager
    def _locked(self) -> Iterator[None]:
        # The sidecar inode is never replaced/deleted. Only metadata is replaced.
        with self.lock_path.open("a+b") as handle:
            if sys.platform == "win32":
                if handle.seek(0, os.SEEK_END) == 0:
                    handle.write(b"\0")
                    handle.flush()
            acquired = False
            deadline = time.monotonic() + self.lock_timeout_seconds
            try:
                while not acquired:
                    try:
                        handle.seek(0)
                        if sys.platform == "win32":
                            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                        else:
                            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        acquired = True
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise TimeoutError("lease metadata lock busy") from None
                        time.sleep(0.01)
                yield
            finally:
                if acquired:
                    handle.seek(0)
                    if sys.platform == "win32":
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _read(self) -> list[Lease]:
        if not self.state_path.exists():
            return []
        # Corruption fails closed; never erase unknown ownership.
        return _LEASES.validate_json(self.state_path.read_bytes())

    def _write(self, leases: list[Lease]) -> None:
        temporary = self.directory / ("leases." + uuid4().hex + ".tmp")
        try:
            with temporary.open("xb") as handle:
                handle.write(_LEASES.dump_json(leases))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.state_path)
        finally:
            temporary.unlink(missing_ok=True)

    def acquire(self, scope: str | Path, worker_id: str, *, ttl_seconds: float = 30) -> Lease | None:
        self._ttl(ttl_seconds)
        if not worker_id.strip():
            raise ValueError("worker_id is required")
        scope = canonical_scope(scope)
        with self._locked():
            now = self._now()
            leases = [lease for lease in self._read() if lease.expires_at > now]
            if any(scopes_collide(scope, lease.scope) for lease in leases):
                return None
            result = Lease(scope=scope, worker_id=worker_id, token=uuid4().hex, expires_at=now + ttl_seconds)
            self._write([*leases, result])
            return result

    def _assert_owned(self, lease: Lease) -> None:
        if lease.expires_at <= self._now() or lease not in self._read():
            raise LeaseLost("lease expired or fenced by a different holder")
        if canonical_scope(lease.scope) != lease.scope:
            raise LeaseLost("lease canonical scope changed")

    def renew(self, lease: Lease, *, ttl_seconds: float = 30) -> Lease | None:
        self._ttl(ttl_seconds)
        with self._locked():
            try:
                self._assert_owned(lease)
            except LeaseLost:
                return None
            renewed = lease.model_copy(update={"expires_at": self._now() + ttl_seconds})
            self._write([renewed if row == lease else row for row in self._read()])
            return renewed

    def release(self, lease: Lease) -> bool:
        with self._locked():
            try:
                self._assert_owned(lease)
            except LeaseLost:
                return False
            self._write([row for row in self._read() if row != lease])
            return True

    def is_valid(self, lease: Lease) -> bool:
        with self._locked():
            try:
                self._assert_owned(lease)
                return True
            except LeaseLost:
                return False

    @contextmanager
    def guard(self, lease: Lease) -> Iterator[Callable[[], None]]:
        """Hold only across promotion; caller checks expiry before each effect."""
        with self._locked():
            self._assert_owned(lease)
            yield lambda: self._assert_owned(lease)

    def snapshot(self) -> list[Lease]:
        with self._locked():
            return self._read()
