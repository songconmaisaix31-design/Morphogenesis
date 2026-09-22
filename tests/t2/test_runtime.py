"""Real graph/store/topology/metabolism + fake CLI: contract_local only."""

from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
import pytest

from bootstrap.sample import prepare_workspace
from bootstrap.verify import SampleVerifier
from contracts.identity import AgentId
from contracts.messages import Envelope
from contracts.resolution import Gene, GeneRef
from contracts.results import TaskResult
from contracts.runtime import RunConfig
from metabolism import LocalMetabolism
from orchestration.codex import CodexExecutor
from orchestration.events import export_events
from orchestration.runtime import Runtime, UnknownExecution, adoption_reader
from persistence import SQLiteStore
from topology import Connection, TopologyEngine
from tests.t2.test_codex import fake_cli


BUILDER = AgentId(role="builder", instance=0)
OTHER = AgentId(role="builder", instance=1)
PLANNER = AgentId(role="planner", instance=0)
REVIEWER = AgentId(role="reviewer", instance=0)


def runtime(tmp_path: Path, saver: SqliteSaver, store: SQLiteStore, *, pause: bool = False,
            adopted: list[str] | None = None, weights: tuple[float, float] = (1, 0.5)) -> Runtime:
    workspace = tmp_path / "task"
    if not workspace.exists():
        prepare_workspace(workspace)
    metabolism = LocalMetabolism(store, "contract-run", provenance="mock")
    topology = TopologyEngine(PLANNER, [Connection(src=PLANNER, dst=BUILDER, weight=weights[0]),
                                         Connection(src=PLANNER, dst=OTHER, weight=weights[1])])
    evidence = tmp_path / "cli-evidence"
    executor = CodexExecutor(evidence, model="fake", provenance="mock", command=fake_cli(tmp_path, adopted=adopted))
    return Runtime(config=RunConfig(run_id="contract-run", workspace=str(workspace), writable_paths=["sample.py"]),
                   saver=saver, events=store, results=store, topology=topology, metabolism=metabolism,
                   executor=executor, verifier=SampleVerifier(tmp_path / "review"), members=[BUILDER, OTHER],
                   reviewer=REVIEWER, provenance="mock", pause_after_execute=pause,
                   bind_experience=metabolism.bind_attempt, adopted_genes=adoption_reader(evidence))


def test_reopen_checkpoint_resumes_review_without_repeating_cli_or_file_write(tmp_path: Path) -> None:
    database, checkpoints = tmp_path / "events.db", tmp_path / "checkpoints.db"
    store = SQLiteStore(database)
    with SqliteSaver.from_conn_string(str(checkpoints)) as saver:
        first = runtime(tmp_path, saver, store, pause=True)
        state = first.start("repair")
        assert state["result"]["status"] == "pending_review"
        assert first.graph.get_state(first.graph_config).next == ("review",)
    source = tmp_path / "task/sample.py"
    before = (source.read_bytes(), source.stat().st_mtime_ns)
    command = tmp_path / "cli-evidence/command.json"
    command_time = command.stat().st_mtime_ns
    store.close()
    reopened = SQLiteStore(database)
    with SqliteSaver.from_conn_string(str(checkpoints)) as saver:
        second = runtime(tmp_path, saver, reopened)
        final = second.resume()
        result = TaskResult.model_validate(final["result"])
        assert result.status == "succeeded"
        assert result.acceptance.task_live == "not_run"
        assert result.verdict.reviewer != result.attempt.agent
        assert final["stop_reason"] == "unknown_usage"
        second.resume()
        weighted = second.topology.snapshot()
        with pytest.raises(ValueError, match="already exists"):
            second.start("another-task")
    with SqliteSaver.from_conn_string(str(checkpoints)) as saver:
        third = runtime(tmp_path, saver, reopened)
        third.resume()
        assert third.topology.snapshot() == weighted
    assert before == (source.read_bytes(), source.stat().st_mtime_ns)
    assert command_time == command.stat().st_mtime_ns
    assert len([e for e in reopened.events("contract-run") if e.payload.get("stage") == "execute_intent"]) == 1
    exported = tmp_path / "events.jsonl"
    assert export_events(reopened, "contract-run", exported) == 5
    assert all(Envelope.model_validate_json(line).provenance == "mock" for line in exported.read_text().splitlines())
    reopened.close()


def test_external_success_before_checkpoint_is_not_reexecuted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database, checkpoints = tmp_path / "events.db", tmp_path / "checkpoints.db"
    store = SQLiteStore(database)
    original_save = store.save_result

    def lost_checkpoint(result: TaskResult) -> None:
        original_save(result)
        raise RuntimeError("injected crash after CLI finished before graph checkpoint")

    monkeypatch.setattr(store, "save_result", lost_checkpoint)
    with SqliteSaver.from_conn_string(str(checkpoints)) as saver:
        first = runtime(tmp_path, saver, store)
        with pytest.raises(RuntimeError, match="injected crash"):
            first.start("repair")
    source = tmp_path / "task/sample.py"
    before = source.stat().st_mtime_ns
    store.close()
    reopened = SQLiteStore(database)
    with SqliteSaver.from_conn_string(str(checkpoints)) as saver:
        second = runtime(tmp_path, saver, reopened)
        with pytest.raises(UnknownExecution, match="no retry"):
            second.resume()
    assert source.stat().st_mtime_ns == before
    reopened.close()


def test_experience_body_is_injected_and_only_explicit_adoption_is_marked(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "events.db")
    with SqliteSaver.from_conn_string(str(tmp_path / "checkpoints.db")) as saver:
        app = runtime(tmp_path, saver, store, adopted=["stable-order"])
        gene = Gene(ref=GeneRef(gene_id="stable-order"), signals_match=["python"],
                    strategy=["Preserve first occurrence order with dict.fromkeys."], provenance="mock")
        app.metabolism.ingest(gene)
        final = app.start("repair")
        assert final["result"]["status"] == "succeeded"
        assert gene.strategy[0] in (tmp_path / "cli-evidence/prompt.txt").read_text()
        events = store.events("contract-run")
        assert any(event.payload.get("adopted_gene_ids") == ["stable-order"] for event in events)
        assert final["adopted_gene_ids"] == ["stable-order"]
        assert isinstance(app.metabolism, LocalMetabolism)
        assert len(app.metabolism.usage_records()) == 1
        assert app.metabolism.usage_records()[0].attempt == TaskResult.model_validate(final["result"]).attempt
    store.close()


def test_distinct_reviewer_is_mandatory(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "events.db")
    with SqliteSaver.from_conn_string(":memory:") as saver:
        app = runtime(tmp_path, saver, store)
        with pytest.raises(ValueError, match="independent reviewer"):
            Runtime(config=app.config, saver=saver, events=store, results=store,
                    topology=app.topology, metabolism=app.metabolism, executor=app.executor,
                    verifier=app.verifier, members=[BUILDER], reviewer=BUILDER)
    store.close()


def test_changed_weights_change_actual_executor_attempt_identity(tmp_path: Path) -> None:
    executed = []
    for name, weights in [("first", (1.0, 0.5)), ("changed", (0.5, 1.0))]:
        root = tmp_path / name
        root.mkdir()
        store = SQLiteStore(root / "events.db")
        with SqliteSaver.from_conn_string(str(root / "checkpoints.db")) as saver:
            app = runtime(root, saver, store, weights=weights)
            state = app.start("repair")
            result = TaskResult.model_validate(state["result"])
            assert result.status == "succeeded"
            executed.append(result.attempt.agent)
            event = next(e for e in store.events("contract-run") if e.payload.get("stage") == "executed")
            assert event.attempt.agent == result.attempt.agent
        store.close()
    assert executed == [BUILDER, OTHER]
