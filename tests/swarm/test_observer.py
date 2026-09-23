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


def test_observer_reads_hot_wal_without_changing_business_data(tmp_path: Path) -> None:
    path = tmp_path / "field.sqlite3"
    db = sqlite3.connect(path)
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE signals (body TEXT)")
        db.execute('INSERT INTO signals VALUES (?)', ('{"concentration": 19}',))
        db.commit()
        before = snapshot(tmp_path)
        view = read_database(path)
        assert view["state"] == "ok"
        assert view["tables"]["signals"] == [{"body": {"concentration": 19}}]
        assert {k: v for k, v in snapshot(tmp_path).items() if not k.endswith('-shm')} == {
            k: v for k, v in before.items() if not k.endswith('-shm')}
        assert set(snapshot(tmp_path)) == set(before)
        db.execute('INSERT INTO signals VALUES (?)', ('{"concentration": 20}',))
        db.commit()
        assert len(read_database(path)["tables"]["signals"]) == 2
    finally:
        db.close()


def test_mirror_states_are_readonly_and_do_not_expose_payload(tmp_path: Path) -> None:
    import json
    from swarm.observer import read_mirror
    for state in ("pending", "received", "rejected", "unknown"):
        (tmp_path / (state + ".json")).write_text(json.dumps({
            "state": state, "payload_json": "not-for-display", "provenance": "mock"}), encoding="utf-8")
    before = snapshot(tmp_path)
    view = read_mirror(tmp_path)
    assert {row["state"] for row in view["records"]} == {"pending", "confirmed", "rejected", "unknown"}
    assert "not-for-display" not in json.dumps(view)
    assert not any(row["hub_promoted"] for row in view["records"])
    assert snapshot(tmp_path) == before
