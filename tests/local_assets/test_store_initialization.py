"""Real SQLite contention in one process; no candidate, process or network execution."""

from concurrent.futures import ThreadPoolExecutor
import os
import socket
import sqlite3
import subprocess
import threading

import pytest

from local_assets.models import AssetSafetyError
from local_assets.store import LocalAssetStore


@pytest.fixture(autouse=True)
def no_process_or_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("store initialization fixture forbids processes and network")
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(os, "system", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)


def unbound_database(tmp_path, root):
    """An empty legacy database with the real schema but no provenance binding."""
    template = LocalAssetStore(tmp_path / "schema-template")
    with template.connection() as db:
        schema = [row[0] for row in db.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    root.mkdir(parents=True)
    database = root / "assets.sqlite3"
    with sqlite3.connect(database) as db:
        db.executescript("PRAGMA journal_mode=WAL;\n" + ";\n".join(schema) + ";")
    return database


def concurrent_initializers(monkeypatch, database, requests):
    """Pause each first write transaction behind a real external SQLite writer.

    With a deferred check-then-insert, both readers observe the missing setting
    before this writer releases. With atomic binding, readers serialize behind
    it and observe the winner's complete settings. No production timeout or SQL
    result is replaced, and both implicit and explicit BEGIN are accepted.
    """
    ready = threading.Barrier(len(requests) + 1, timeout=10)
    original_connect = sqlite3.connect
    holder = original_connect(database, timeout=10)
    holder.execute("BEGIN IMMEDIATE")

    def connect(*args, **kwargs):
        db = original_connect(*args, **kwargs)
        def trace(statement):
            if statement.lstrip().upper().startswith("BEGIN"):
                ready.wait()
        db.set_trace_callback(trace)
        return db

    def initialize(request):
        mode, workspace = request
        store = LocalAssetStore(database.parent, research_provenance=mode, fixture_workspace=workspace)
        return store.research_provenance, str(store.fixture_workspace) if store.fixture_workspace else ""

    try:
        with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=len(requests)) as pool:
            patch.setattr(sqlite3, "connect", connect)
            futures = [pool.submit(initialize, request) for request in requests]
            try:
                ready.wait()
            finally:
                holder.rollback()
            results = []
            for future in futures:
                try:
                    results.append(future.result(timeout=10))
                except Exception as error:
                    results.append(error)
            return results
    finally:
        holder.close()


def assert_binding_and_immutability(database, expected):
    with sqlite3.connect(database) as db:
        assert dict(db.execute("SELECT name, value FROM asset_store_settings")) == {
            "generated_research_provenance": expected[0], "fixture_workspace": expected[1]}
        for statement in ("UPDATE asset_store_settings SET value='changed'",
                          "DELETE FROM asset_store_settings"):
            with pytest.raises(sqlite3.IntegrityError, match="immutable_local_evidence"):
                db.execute(statement)


@pytest.mark.parametrize("mode", ["live", "mock"])
def test_concurrent_same_settings_all_succeed(tmp_path, monkeypatch, mode):
    database = unbound_database(tmp_path, tmp_path / "fixture" / "assets")
    workspace = tmp_path / "fixture" if mode == "mock" else None
    expected = (mode, str(workspace.resolve()) if workspace else "")
    results = concurrent_initializers(monkeypatch, database, [(mode, workspace)] * 2)
    assert results == [expected, expected], results
    assert_binding_and_immutability(database, expected)


@pytest.mark.parametrize("conflict", ["provenance", "fixture_workspace"])
def test_concurrent_conflicting_settings_bind_one_complete_pair(tmp_path, monkeypatch, conflict):
    fixture = tmp_path / "fixture"
    database = unbound_database(tmp_path, fixture / "assets")
    requests = [("mock", fixture), ("live", None) if conflict == "provenance" else ("mock", tmp_path)]
    results = concurrent_initializers(monkeypatch, database, requests)
    successes = [result for result in results if isinstance(result, tuple)]
    failures = [result for result in results if isinstance(result, Exception)]
    assert len(successes) == len(failures) == 1, results
    assert isinstance(failures[0], AssetSafetyError), results
    assert str(failures[0]) == "asset_store_provenance_conflict"
    assert_binding_and_immutability(database, successes[0])
    rejected = requests[results.index(failures[0])]
    with pytest.raises(AssetSafetyError, match="asset_store_provenance_conflict"):
        LocalAssetStore(database.parent, research_provenance=rejected[0], fixture_workspace=rejected[1])


def test_populated_legacy_store_cannot_become_mock_and_rolls_back_binding(tmp_path):
    database = unbound_database(tmp_path, tmp_path / "fixture" / "assets")
    with sqlite3.connect(database) as db:
        db.execute("INSERT INTO assets VALUES (?, ?)", ("legacy-asset", "retained legacy fixture"))
    with pytest.raises(AssetSafetyError, match="existing_store_cannot_become_mock_fixture"):
        LocalAssetStore(database.parent, research_provenance="mock", fixture_workspace=tmp_path)
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT * FROM asset_store_settings").fetchall() == []
        assert db.execute("SELECT * FROM assets").fetchall() == [("legacy-asset", "retained legacy fixture")]
    LocalAssetStore(database.parent)
    assert_binding_and_immutability(database, ("live", ""))
