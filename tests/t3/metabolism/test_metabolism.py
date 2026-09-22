import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest

from contracts.identity import AgentId, AttemptId
from contracts.provenance import Acceptance
from contracts.resolution import Gene, GeneRef, Metabolism
from contracts.runtime import RunConfig
from metabolism import LocalMetabolism
from metabolism.index import CosineIndex
from mocks import MockMetabolism, UnimplementedExecutor, UnimplementedVerifier, gene_fixture
from persistence import SQLiteStore


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


AGENT = AgentId(role="builder", instance=0)
ATTEMPT = AttemptId(task_id="repair", agent=AGENT, attempt=0)


def gene(name: str = "g", version: int = 1, signals: list[str] | None = None) -> Gene:
    # These are contract fixtures. Live provenance here is validation input,
    # never evidence of actual model use or official remote asset validation.
    return Gene(ref=GeneRef(gene_id=name, version=version, asset_id=f"fixture:{name}:{version}"),
                signals_match=signals or [], strategy=["Inspect failing case", "Repair and verify"],
                source_attempt=ATTEMPT)


def service(tmp_path: Path, clock: Clock) -> LocalMetabolism:
    return LocalMetabolism(SQLiteStore(tmp_path / "cache.sqlite"), "run-a", clock=clock,
                           tau_seconds=10.0)


def test_protocol_body_immutable_and_reference_validation(tmp_path: Path) -> None:
    m = service(tmp_path, Clock())
    contract: Metabolism = m
    original = gene()
    contract.ingest(original)
    contract.ingest(original)
    assert len(m.snapshot()) == 1
    resolved = contract.resolve(original.ref)
    resolved.strategy.append("caller mutation")
    assert contract.resolve(original.ref) == original
    with pytest.raises(ValueError, match="different"):
        m.ingest(original.model_copy(update={"strategy": ["changed"]}))
    with pytest.raises(ValueError, match="asset_id"):
        m.resolve(GeneRef(gene_id="g", asset_id="wrong"))
    with pytest.raises(KeyError):
        m.resolve(GeneRef(gene_id="missing"))


def test_budget_applicability_binding_and_injection_is_not_adoption(tmp_path: Path) -> None:
    m = service(tmp_path, Clock())
    for g in [gene("applicable", signals=["python", "role:builder"]),
              gene("wrong-role", signals=["python", "role:reviewer"]),
              gene("wrong-task", signals=["javascript"]), gene("generic")]:
        m.ingest(g)
    with pytest.raises(ValueError, match="bind_attempt"):
        m.inject(AGENT, 2)
    m.bind_attempt(ATTEMPT, ["PYTHON"])
    chosen = m.inject(AGENT, 1)
    assert len(chosen) == 1
    assert chosen[0].ref.gene_id in {"applicable", "generic"}
    assert m.inject(AGENT, 1) == chosen
    assert all(view.use_count == 0 for view in m.snapshot())
    assert sum(view.injected_count for view in m.snapshot()) == 1
    assert m.usage_records() == []
    with pytest.raises(ValueError, match="budget or signals"):
        m.inject(AGENT, 2)
    m.bind_attempt(ATTEMPT, ["different"])
    with pytest.raises(ValueError, match="budget or signals"):
        m.inject(AGENT, 1)
    m.bind_attempt(ATTEMPT.model_copy(update={"attempt": 1}), ["python"])
    assert {g.ref.gene_id for g in m.inject(AGENT, 20)} == {"applicable", "generic"}
    m.bind_attempt(ATTEMPT.model_copy(update={"attempt": 2}), ["python"])
    assert m.inject(AGENT, 0) == []
    with pytest.raises(ValueError):
        m.inject(AGENT, -1)
    with pytest.raises(ValueError):
        m.inject(AGENT, True)


def test_mark_requires_exact_attempt_and_binds_injected_version(tmp_path: Path) -> None:
    clock = Clock()
    m = service(tmp_path, clock)
    m.ingest(gene())
    m.ingest(gene("other"))
    with pytest.raises(ValueError, match="no injection"):
        m.mark_used("g", ATTEMPT)
    m.bind_attempt(ATTEMPT)
    m.inject(AGENT, 1)
    with pytest.raises(ValueError, match="not injected"):
        m.mark_used("other", ATTEMPT)
    for wrong in [ATTEMPT.model_copy(update={"task_id": "other"}),
                  ATTEMPT.model_copy(update={"attempt": 1}),
                  ATTEMPT.model_copy(update={"agent": AgentId(role="builder", instance=1)})]:
        with pytest.raises(ValueError, match="no injection"):
            m.mark_used("g", wrong)
    m.ingest(gene(version=2))
    clock.now += 1
    m.mark_used("g", ATTEMPT)
    clock.now += 1
    m.mark_used("g", ATTEMPT)
    uses = m.usage_records()
    assert len(uses) == 1 and uses[0].ref.version == 1
    assert uses[0].attempt == ATTEMPT and uses[0].used_at == 1001.0
    assert m.resolve(gene(version=2).ref) == gene(version=2)
    next_attempt = ATTEMPT.model_copy(update={"attempt": 1})
    m.bind_attempt(next_attempt)
    assert m.inject(AGENT, 1)[0].ref.version == 2


def test_run_scoping_restart_and_concurrent_dedup(tmp_path: Path) -> None:
    clock = Clock()
    m = service(tmp_path, clock)
    m.ingest(gene())
    m.bind_attempt(ATTEMPT)
    m.inject(AGENT, 1)
    other_run = LocalMetabolism(m.store, "run-b", clock=clock)
    with pytest.raises(ValueError, match="no injection"):
        other_run.mark_used("g", ATTEMPT)
    reopened = LocalMetabolism(SQLiteStore(tmp_path / "cache.sqlite"), "run-a", clock=clock)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: reopened.mark_used("g", ATTEMPT), range(8)))
    assert reopened.snapshot()[0].use_count == 1
    assert len(reopened.usage_records()) == 1
    other_run.bind_attempt(ATTEMPT)
    other_run.inject(AGENT, 1)
    other_run.mark_used("g", ATTEMPT)
    assert other_run.snapshot()[0].use_count == 2
    assert len(other_run.usage_records()) == 1


def test_decay_units_anchor_tau_half_life_and_monotonicity(tmp_path: Path) -> None:
    clock = Clock()
    m = service(tmp_path, clock)
    m.ingest(gene())
    clock.now += 10 * math.log(2)
    m.decay_weights(clock.now)
    assert m.snapshot()[0].weight == pytest.approx(0.5)
    m.decay_weights(clock.now)
    assert m.snapshot()[0].weight == pytest.approx(0.5)
    clock.now = 1010.0
    m.decay_weights(clock.now)
    assert m.snapshot()[0].weight == pytest.approx(math.exp(-1))
    with pytest.raises(ValueError, match="backwards"):
        m.decay_weights(1000.0)
    for invalid in [float("nan"), float("inf"), -1.0]:
        with pytest.raises(ValueError):
            m.decay_weights(invalid)
    m.bind_attempt(ATTEMPT)
    m.inject(AGENT, 1)
    m.mark_used("g", ATTEMPT)
    assert m.snapshot()[0].weight == 1
    clock.now += 10
    m.decay_weights(clock.now)
    assert m.snapshot()[0].weight == pytest.approx(math.exp(-1))
    reopened = LocalMetabolism(m.store, "run-b", clock=clock, tau_seconds=1000)
    assert reopened.snapshot()[0].tau_seconds == 10  # persisted, not silently reinterpreted


def test_archive_evicts_cache_search_receipts_and_survives_process_restart(tmp_path: Path) -> None:
    clock = Clock()
    m = service(tmp_path, clock)
    m.ingest(gene())
    m.bind_attempt(ATTEMPT)
    m.inject(AGENT, 1)
    m.mark_used("g", ATTEMPT)
    second = LocalMetabolism(SQLiteStore(tmp_path / "cache.sqlite"), "run-b", clock=clock)
    second.bind_attempt(ATTEMPT)
    assert second.inject(AGENT, 1)
    clock.now += 40
    assert m.archive() == ["g"]
    assert m.archive() == []
    assert m.store.get_gene(gene().ref) is None
    assert second.inject(AGENT, 1) == []  # persisted receipt cannot resurrect body
    assert m.merge_candidates() == []
    with pytest.raises(KeyError):
        m.resolve(gene().ref)
    with pytest.raises(KeyError):
        second.mark_used("g", ATTEMPT)
    m.mark_used("g", ATTEMPT)  # identical old adoption remains an idempotent fact
    with pytest.raises(ValueError, match="reactivated"):
        m.ingest(gene())
    script = """
import sys
from contracts.identity import AgentId, AttemptId
from contracts.resolution import GeneRef
from persistence import SQLiteStore
from metabolism import LocalMetabolism
m=LocalMetabolism(SQLiteStore(sys.argv[1]), 'fresh-process', clock=lambda:1040.0)
a=AgentId(role='builder',instance=0)
m.bind_attempt(AttemptId(task_id='repair',agent=a,attempt=0))
assert m.inject(a, 10)==[]
assert m.merge_candidates()==[]
assert m.snapshot()[0].archived_at==1040.0
try:
    m.resolve(GeneRef(gene_id='g'))
except KeyError:
    pass
else:
    raise AssertionError('archived body returned')
"""
    completed = subprocess.run([sys.executable, "-c", script, str(tmp_path / "cache.sqlite")],
                               capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr
    assert m.snapshot()[0].remote_archive_status == "not_synchronized"
    assert m.snapshot()[0].use_count == 1
    assert m.snapshot()[0].source_attempt == ATTEMPT


def test_latest_tombstone_does_not_revert_search_to_old_version(tmp_path: Path) -> None:
    clock = Clock()
    m = service(tmp_path, clock)
    m.ingest(gene(version=1))
    m.bind_attempt(ATTEMPT)
    m.inject(AGENT, 1)
    m.ingest(gene(version=2))
    clock.now += 35
    m.mark_used("g", ATTEMPT)  # v1 adopted; v2 stays old
    assert m.archive() == ["g"]
    m.bind_attempt(ATTEMPT.model_copy(update={"attempt": 1}))
    assert m.inject(AGENT, 2) == []
    assert m.resolve(gene(version=1).ref) == gene(version=1)


def test_merge_only_candidates_no_auto_upgrade_or_side_effect(tmp_path: Path) -> None:
    m = service(tmp_path, Clock())
    for name in ("a", "b", "c"):
        m.ingest(gene(name))
    before = m.snapshot()
    pairs = m.merge_candidates()
    assert len(pairs) == 3
    assert all(len(pair) == 2 for pair in pairs)
    assert m.snapshot() == before
    assert all(view.ref.version == 1 and view.use_count == 0 for view in m.snapshot())


def test_provenance_isolation_replay_lineage_and_no_fake_execution(tmp_path: Path) -> None:
    clock = Clock()
    m = service(tmp_path, clock)
    fixture = gene_fixture("fixture", ["test only"])
    with pytest.raises(ValueError, match="provenance"):
        m.ingest(fixture)
    mock = MockMetabolism(m.store, "mock-run", clock=clock)
    mock.ingest(fixture)
    with pytest.raises(ValueError, match="provenance"):
        mock.ingest(gene())
    assert all(v.provenance == "mock" for v in mock.snapshot())
    m.bind_attempt(ATTEMPT)
    assert m.inject(AGENT, 3) == []
    with pytest.raises(KeyError):
        m.resolve(fixture.ref)
    replay = LocalMetabolism(m.store, "replay-run", provenance="replay", clock=clock)
    replay_gene = gene("replay").model_copy(update={"provenance": "replay"})
    with pytest.raises(ValueError, match="original_run_uri"):
        replay.ingest(replay_gene)
    replay.ingest(replay_gene, original_run_uri="file:///fixture-run")
    assert replay.snapshot()[0].original_run_uri == "file:///fixture-run"
    with pytest.raises(ValueError):
        Acceptance(provenance="mock", task_live="passed")
    with pytest.raises(NotImplementedError):
        UnimplementedVerifier().verify("unused", AGENT)
    with pytest.raises(NotImplementedError):
        UnimplementedExecutor().execute(ATTEMPT, RunConfig(
            run_id="mock-run", workspace=str(tmp_path), writable_paths=["sample.py"],
        ), [])
    assert UnimplementedExecutor.provenance == "mock"


def test_run_attempt_cannot_switch_from_mock_to_live(tmp_path: Path) -> None:
    clock = Clock()
    store = SQLiteStore(tmp_path / "cache.sqlite")
    mock = MockMetabolism(store, "same-run", clock=clock)
    mock.ingest(gene_fixture("fixture", ["not an actual task"]))
    mock.bind_attempt(ATTEMPT)
    mock.inject(AGENT, 1)
    mock.mark_used("fixture", ATTEMPT)
    live = LocalMetabolism(store, "same-run", clock=clock)
    live.bind_attempt(ATTEMPT)
    with pytest.raises(ValueError, match="provenance"):
        live.inject(AGENT, 1)
    with pytest.raises(ValueError, match="provenance"):
        live.mark_used("fixture", ATTEMPT)
    assert live.usage_records() == []


def test_faiss_real_ranking_and_embedding_validation() -> None:
    vectors = np.array([[2.0, 0], [0, 4.0]], dtype=np.float32)
    index = CosineIndex(["first", "second"], lambda _: vectors)
    assert index.neighbors(0)[0] == (0, 1.0)
    assert index.neighbors(1)[0] == (1, 1.0)
    assert vectors[0, 0] == 2.0  # caller embeddings not mutated
    with pytest.raises(ValueError, match="nonfinite"):
        CosineIndex(["nan"], lambda _: np.array([[np.nan]], dtype=np.float32))
    with pytest.raises(ValueError, match="dimension"):
        CosineIndex(["wrong"], lambda _: np.array([[1.0], [2.0]], dtype=np.float32))


def test_failed_index_creation_rolls_back_injection_and_weight(tmp_path: Path) -> None:
    clock = Clock()
    m = LocalMetabolism(SQLiteStore(tmp_path / "cache.sqlite"), "run-a", clock=clock,
                        embedding=lambda _: np.array([[np.nan]], dtype=np.float32))
    m.ingest(gene())
    m.bind_attempt(ATTEMPT)
    clock.now += 10
    with pytest.raises(ValueError, match="nonfinite"):
        m.inject(AGENT, 1)
    assert m.snapshot()[0].weight == 1
    assert m.snapshot()[0].evaluated_at == 1000
    assert m.snapshot()[0].injected_count == 0
    with pytest.raises(ValueError, match="no injection"):
        m.mark_used("g", ATTEMPT)


def test_failed_archive_transaction_preserves_body_and_state(tmp_path: Path) -> None:
    clock = Clock()
    m = service(tmp_path, clock)
    m.ingest(gene("a"))
    clock.now = 2000
    m.ingest(gene("b"))
    clock.now = 1500
    with pytest.raises(ValueError, match="backwards"):
        m.archive()  # a would be removed before b detects the invalid clock
    assert m.resolve(gene("a").ref) == gene("a")
    assert m.store.get_gene(gene("a").ref) == gene("a")
    assert all(v.archived_at is None and v.weight == 1 for v in m.snapshot())
