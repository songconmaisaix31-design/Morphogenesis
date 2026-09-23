import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from swarm.lease import LeaseLost, LeaseManager, canonical_scope
from swarm.models import Lease


def test_ttl_restart_stale_holder_and_renewal_fencing(tmp_path: Path) -> None:
    now = [100.0]
    manager = LeaseManager(tmp_path / "locks", clock=lambda: now[0])
    scope = tmp_path / "project"
    old = manager.acquire(scope, "old", ttl_seconds=10)
    assert old is not None
    restarted = LeaseManager(tmp_path / "locks", clock=lambda: now[0])
    assert restarted.acquire(scope, "new") is None
    renewed = restarted.renew(old, ttl_seconds=20)
    assert renewed is not None and renewed.expires_at == 120
    assert not manager.release(old)
    now[0] = 121
    current = restarted.acquire(scope, "new")
    assert current is not None
    assert not manager.release(renewed)
    assert manager.renew(renewed) is None
    with pytest.raises(LeaseLost):
        with manager.guard(renewed):
            pytest.fail("stale holder promoted")
    assert manager.is_valid(current)
    assert manager.release(current)


def test_parent_child_canonical_alias_collision_and_sibling_progress(tmp_path: Path) -> None:
    manager = LeaseManager(tmp_path / "locks")
    root = tmp_path / "project"
    root.mkdir()
    lease = manager.acquire(root / "src", "a")
    assert lease is not None
    assert manager.acquire(root, "b") is None
    assert manager.acquire(root / "src" / "module.py", "b") is None
    assert manager.acquire(root / "src" / ".." / "src", "b") is None
    assert manager.acquire(root / "src2", "b") is not None
    alias = tmp_path / "alias"
    if os.name == "nt":
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(root)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    else:
        alias.symlink_to(root, target_is_directory=True)
    assert manager.acquire(alias / "src", "c") is None
    assert canonical_scope(alias / "src") == canonical_scope(root / "src")


def test_guard_rechecks_expiry_before_each_write(tmp_path: Path) -> None:
    now = [1.0]
    manager = LeaseManager(tmp_path / "locks", clock=lambda: now[0])
    lease = manager.acquire(tmp_path / "project", "worker", ttl_seconds=2)
    assert lease is not None
    with manager.guard(lease) as assert_owned:
        assert_owned()
        now[0] = 3
        with pytest.raises(LeaseLost):
            assert_owned()


def test_concurrent_process_acquire_has_one_holder(tmp_path: Path) -> None:
    script = '''
import sys
from swarm.lease import LeaseManager
r=LeaseManager(sys.argv[1]).acquire(sys.argv[2],sys.argv[3],ttl_seconds=30)
print(r.model_dump_json() if r else 'busy')
'''
    children = [subprocess.Popen([sys.executable, "-c", script, str(tmp_path / "locks"), str(tmp_path / "project"), str(i)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for i in range(6)]
    results = [child.communicate(timeout=30) for child in children]
    assert all(child.returncode == 0 for child in children), results
    assert sum(out.strip() != "busy" for out, _ in results) == 1


def test_process_crash_ttl_reclaims_and_old_token_cannot_release(tmp_path: Path) -> None:
    script = '''
import sys, os
from swarm.lease import LeaseManager
r=LeaseManager(sys.argv[1]).acquire(sys.argv[2],'crashed',ttl_seconds=0.3)
print(r.model_dump_json(),flush=True)
os._exit(19)
'''
    path = tmp_path / "locks"
    result = subprocess.run([sys.executable, "-c", script, str(path), str(tmp_path / "project")],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 19
    old = Lease.model_validate_json(result.stdout)
    time.sleep(max(0, old.expires_at - time.time()) + .05)
    restarted = LeaseManager(path)
    new = restarted.acquire(tmp_path / "project", "replacement")
    assert new is not None and new.token != old.token
    assert not restarted.release(old)
    assert restarted.is_valid(new)


def test_guard_blocks_competing_reclaim_during_actual_write(tmp_path: Path) -> None:
    manager = LeaseManager(tmp_path / "locks")
    lease = manager.acquire(tmp_path / "project", "a", ttl_seconds=10)
    assert lease is not None
    script = '''
import sys
from pathlib import Path
from swarm.lease import LeaseManager
Path(sys.argv[3]).write_text('started')
r=LeaseManager(sys.argv[1]).acquire(sys.argv[2],'b')
print('acquired' if r else 'busy',flush=True)
'''
    started = tmp_path / "started"
    with manager.guard(lease) as assert_owned:
        child = subprocess.Popen([sys.executable, "-c", script, str(manager.directory), lease.scope, str(started)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.monotonic() + 20
        while not started.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        assert started.exists()
        time.sleep(.05)
        assert child.poll() is None  # Child is blocked by OS lock, not a process-local mutex.
        assert_owned()
        (tmp_path / "protected-effect").write_text("written")
    output, error = child.communicate(timeout=20)
    assert child.returncode == 0 and output.strip() == "busy", error


def test_corrupt_metadata_fails_closed(tmp_path: Path) -> None:
    manager = LeaseManager(tmp_path / "locks")
    manager.state_path.write_text("broken")
    with pytest.raises(ValueError):
        manager.acquire(tmp_path / "project", "worker")


@pytest.mark.parametrize("operation", ["renew", "release"])
def test_concurrent_process_renew_and_release_are_atomic(tmp_path: Path, operation: str) -> None:
    manager = LeaseManager(tmp_path / "locks")
    lease = manager.acquire(tmp_path / "project", "owner")
    assert lease is not None
    script = '''
import sys
from swarm.lease import LeaseManager
from swarm.models import Lease
manager=LeaseManager(sys.argv[1])
lease=Lease.model_validate_json(sys.argv[2])
result=manager.renew(lease,ttl_seconds=60) if sys.argv[3]=='renew' else manager.release(lease)
print('changed' if result else 'fenced')
'''
    children = [subprocess.Popen([sys.executable, "-c", script, str(manager.directory), lease.model_dump_json(), operation],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(4)]
    results = [child.communicate(timeout=30) for child in children]
    assert all(child.returncode == 0 for child in children), results
    assert sum(out.strip() == "changed" for out, _ in results) == 1


def test_configured_os_lock_timeout_is_bounded_and_preserves_holder(tmp_path: Path) -> None:
    manager = LeaseManager(tmp_path / "locks")
    lease = manager.acquire(tmp_path / "project", "owner")
    assert lease is not None
    script = '''
import sys, time
from swarm.lease import LeaseManager
started=time.monotonic()
try:
    LeaseManager(sys.argv[1],lock_timeout_seconds=.05).acquire(sys.argv[2],'contender')
except TimeoutError:
    print(time.monotonic()-started)
else:
    raise AssertionError('contender bypassed OS guard')
'''
    with manager.guard(lease) as assert_owned:
        result = subprocess.run([sys.executable, "-c", script, str(manager.directory), lease.scope],
                                capture_output=True, text=True, timeout=20, check=True)
        assert .04 <= float(result.stdout) < 5
        assert_owned()
    assert manager.is_valid(lease)
    for invalid in (-1, 61, float("nan")):
        with pytest.raises(ValueError):
            LeaseManager(tmp_path / "locks", lock_timeout_seconds=invalid)
