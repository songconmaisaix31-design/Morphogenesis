"""Two real SQLite connections race only at an unprotected admission read.

The scheduling hook returns the original SQLite cursor and changes no data or
SQL result. An admission transaction naturally removes that unsafe interleave.
No process, candidate, bridge or network execution is involved.
"""
from concurrent.futures import ThreadPoolExecutor
import sqlite3
from threading import Barrier

import pytest

from local_assets import store as store_module
from local_assets.models import AssetSafetyError
from local_assets.store import LocalAssetStore


class NoExecutionBridge:
    def __getattr__(self, name):
        raise AssertionError("store initialization must not call a candidate/SDK bridge")


def race(root, configurations, monkeypatch):
    root.mkdir(parents=True)
    database = root / "assets.sqlite3"
    original_connect = sqlite3.connect
    # An empty WAL database avoids testing unrelated journal-mode migration.
    with original_connect(database) as db:
        db.execute("PRAGMA journal_mode=WAL")
    rendezvous = Barrier(2, timeout=8)

    class AdmissionConnection(sqlite3.Connection):
        def execute(self, sql, parameters=()):
            cursor = super().execute(sql, parameters)
            normalized = " ".join(sql.upper().split())
            if (normalized.startswith("SELECT VALUE FROM ASSET_STORE_SETTINGS")
                    and parameters == ("generated_research_provenance",) and not self.in_transaction):
                rendezvous.wait()
            return cursor

    def connect(*args, **kwargs):
        return original_connect(*args, **kwargs, factory=AdmissionConnection)

    def initialize(configuration):
        try:
            return LocalAssetStore(root, bridge=NoExecutionBridge(), **configuration)
        except Exception as exc:
            return exc

    with monkeypatch.context() as scheduling:
        scheduling.setattr(store_module.sqlite3, "connect", connect)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(initialize, configuration) for configuration in configurations]
            outcomes = [future.result(timeout=20) for future in futures]
    with original_connect(database) as db:
        settings = dict(db.execute("SELECT name,value FROM asset_store_settings"))
    return outcomes, settings, database


@pytest.mark.parametrize("provenance", ["live", "mock"])
def test_concurrent_identical_store_settings_both_admit_without_unique_collision(tmp_path, monkeypatch, provenance):
    options = {"research_provenance": provenance}
    if provenance == "mock":
        options["fixture_workspace"] = tmp_path
    outcomes, settings, _ = race(tmp_path / "assets", [options, options], monkeypatch)
    errors = [outcome for outcome in outcomes if isinstance(outcome, Exception)]
    assert errors == [], "same immutable settings must support simultaneous workers"
    assert len(outcomes) == 2
    assert settings == {"generated_research_provenance": provenance,
                        "fixture_workspace": str(tmp_path.resolve()) if provenance == "mock" else ""}
    for store in outcomes:
        assert store.research_provenance == provenance
        assert store.adoptions() == []


@pytest.mark.parametrize("conflict", ["provenance", "fixture_workspace"])
def test_concurrent_conflicting_store_settings_refuse_atomically_and_preserve_winner(tmp_path, monkeypatch, conflict):
    nested = tmp_path / "nested"
    configurations = [
        {"research_provenance": "live"},
        {"research_provenance": "mock", "fixture_workspace": tmp_path},
    ] if conflict == "provenance" else [
        {"research_provenance": "mock", "fixture_workspace": tmp_path},
        {"research_provenance": "mock", "fixture_workspace": nested},
    ]
    outcomes, settings, database = race(nested / "assets", configurations, monkeypatch)
    successful = [outcome for outcome in outcomes if isinstance(outcome, LocalAssetStore)]
    errors = [outcome for outcome in outcomes if isinstance(outcome, Exception)]
    assert len(successful) == len(errors) == 1
    assert isinstance(errors[0], AssetSafetyError), "conflicting authority must be a domain refusal, not SQLite corruption"
    assert str(errors[0]) == "asset_store_provenance_conflict"
    winner = successful[0]
    assert settings == {"generated_research_provenance": winner.research_provenance,
                        "fixture_workspace": str(winner.fixture_workspace) if winner.fixture_workspace else ""}
    reopened = LocalAssetStore(database.parent, bridge=NoExecutionBridge(),
        research_provenance=winner.research_provenance, fixture_workspace=winner.fixture_workspace)
    assert reopened.adoptions() == []
    with sqlite3.connect(database) as db:
        with pytest.raises(sqlite3.DatabaseError, match="immutable_local_evidence"):
            db.execute("UPDATE asset_store_settings SET value='caller-replacement' WHERE name='fixture_workspace'")
        assert dict(db.execute("SELECT name,value FROM asset_store_settings")) == settings
