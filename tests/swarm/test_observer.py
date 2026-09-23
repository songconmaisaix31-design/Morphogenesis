from pathlib import Path
import sqlite3

from swarm.observer import observe, read_database


def snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


def test_observing_missing_state_never_creates_it(tmp_path: Path) -> None:
    state = tmp_path / "missing"
    assert observe(state)["health"] == "partial"
    assert not state.exists()


def test_observer_does_not_expire_lease_or_mutate_database(tmp_path: Path) -> None:
    path = tmp_path / "field.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE signals (body TEXT)")
        db.execute('INSERT INTO signals VALUES (?)', ('{"concentration": 8}',))
    leases = tmp_path / "leases"
    leases.mkdir()
    (leases / "lease.json").write_text('{"worker_id":"old","expires_at":1}', encoding="utf-8")
    before = snapshot(tmp_path)
    view = observe(tmp_path)
    assert view["readonly"] is True
    assert read_database(path)["state"] == "ok"
    assert snapshot(tmp_path) == before


def test_observer_hot_wal_is_explicitly_unavailable_and_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "field.sqlite3"
    db = sqlite3.connect(path)
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE signals (body TEXT)")
        db.commit()
        before = snapshot(tmp_path)
        assert read_database(path)["state"] == "busy"
        assert snapshot(tmp_path) == before
    finally:
        db.close()
