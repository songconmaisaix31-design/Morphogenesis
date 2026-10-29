"""Offline CLI protocol fixtures, not SWA/provider execution evidence."""
import json
from pathlib import Path
import subprocess

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets.models import AssetSafetyError, FileExpectation, ValidationPolicy
from local_assets.paths import git
from swarm.evomap_executor import canonical_answer
from swarm.models import BudgetPolicy, Locality, Signal
from swarm.pheromone import PheromoneField
from swarm.swa_executor import SwaConfig, SwaExecutor
from swarm.task_ledger import TaskLedger
from swarm.worker_loop import Worker, WorkerConfig


class FakeCLI:
    def __init__(self, *, failure=None, content='{"answer":3,"adopted_asset_ids":[]}'):
        self.calls, self.failure, self.content = [], failure, content

    def __call__(self, argv, timeout):
        self.calls.append(argv)
        stage = argv[1]
        if self.failure == "timeout":
            raise subprocess.TimeoutExpired(argv, timeout, stderr=b"NEVER_LOG_TOKEN")
        identity = {"controller": "C", "run_id": "R", "task_id": "T", "runtime_id": "runtime", "authority_domain": "authority"}
        body = {"ok": True, **identity}
        if "--request-id" in argv:
            body["request_id"] = argv[argv.index("--request-id") + 1]
            if self.failure == "request_identity":
                body["request_id"] = "other-request"
        if stage == "run":
            spec = json.loads(Path(argv[argv.index("--spec-file") + 1]).read_text())
            assert spec["max_workers"] == spec["initial_workers"] == 1
            assert spec["context"] == {"files": [], "references": []}
            assert all(argv[argv.index(flag) + 1] == "disabled" for flag in
                       ("--question-mode", "--development-mode", "--delegation-mode"))
            journal = Path(argv[argv.index("--spec-file") + 1]).with_name("invocation.json")
            assert json.loads(journal.read_text())["request_id"] == argv[argv.index("--request-id") + 1]
            view = {"schema": "swa.run-view.v1", "controller": "C", "run_id": "R", "root_task_id": "T",
                    "complete": True, "status": "completed", "acceptance": "unreviewed", "blockers": [],
                    "failures": [], "questions": [], "tasks": [
                        {"id": "T", "parent_id": None, "status": "completed"},
                        {"id": "child", "parent_id": "T", "status": "completed"}],
                    "dispatches": [{"id": "D", "task_id": "child", "status": "completed", "release_state": "released"}]}
            if self.failure == "release":
                view["dispatches"][0]["release_state"] = "held"
            if self.failure == "missing_child":
                view["tasks"].pop()
            body["result"] = {"native": {"run_view": view}}
        elif stage == "task":
            body["result"] = {"native": {"workers": [{"worker": {"dispatchId": "D", "taskId": "child", "runId": "R"},
                "native_session": {"availability": "complete", "final": {"text": self.content},
                                   "usage": {"known": False}}}]}}
            if self.failure == "dispatch":
                body["result"]["native"]["workers"][0]["worker"]["dispatchId"] = "another"
            if self.failure == "dispatch_joint_drift":
                body["dispatch_id"] = "another"
                body["result"]["native"]["workers"][0]["worker"]["dispatchId"] = "another"
            if self.failure == "incomplete":
                body["result"]["native"]["workers"][0]["native_session"]["availability"] = "partial"
        else:
            assert argv[1:3] == ["controller", "close"]
            body["result"] = {"controller": "C", "close": {"ptyKilled": True}}
        exit_code = self.failure if isinstance(self.failure, int) else (6 if self.failure == "close" and stage == "controller" else 0)
        return subprocess.CompletedProcess(argv, exit_code, json.dumps(body).encode(), b"NEVER_LOG_TOKEN")


@pytest.fixture
def setup(tmp_path):
    target, state, staging = tmp_path / "target", tmp_path / "state", tmp_path / "swa"
    target.mkdir(); staging.mkdir()
    (target / "sum.json").write_text("null\n")
    git(target, "init", "-b", "test")
    git(target, "add", ".")
    git(target, "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "seed")
    head = git(target, "rev-parse", "HEAD").decode().strip()
    executable = tmp_path / "fake-swa"
    executable.write_text("offline fake, never executed")
    api = SwaConfig(executable=executable, endpoint="http://127.0.0.1:4318", project="test", workdir=staging,
                    agent="pi", model="test/model")
    signal = Signal(task_id="sum", signal_id="sum", workspace=str(target), scope=".", kind="opportunity",
                    required_capability="sum", payload={"instruction": "Sum input integers.", "input": [1, 2], "output_path": "sum.json"})
    attempt = AttemptId(task_id="sum", agent=AgentId(role="builder", instance=0), attempt=1)
    return target, state, head, api, signal, attempt


def execute(setup, fake):
    target, state, head, api, signal, attempt = setup
    result = SwaExecutor(api, runner=fake, provenance="mock").execute(signal, attempt, target, state / "execution" / "one",
                                                     base_revision=head, base_head=head)
    return result


def test_complete_native_run_becomes_candidate_and_closes_controller(setup):
    fake = FakeCLI()
    result = execute(setup, fake)
    assert result.candidate.changes[0].after == "3\n"
    assert result.provenance == "mock" and result.usage is None and not result.uncertain
    assert [args[1] for args in fake.calls] == ["run", "task", "controller"]
    assert Path(result.workspace, "sum.json").read_text() == "3\n"
    assert (setup[0] / "sum.json").read_text() == "null\n"
    assert "NEVER_LOG_TOKEN" not in "".join(p.read_text() for p in setup[3].workdir.rglob("*.json"))
    # Reentering an existing attempt cannot create a second SWA task.
    with pytest.raises(FileExistsError):
        execute(setup, fake)
    assert len(fake.calls) == 3


@pytest.mark.parametrize("failure", ["timeout", 6, 8, 130, "release", "missing_child", "dispatch", "dispatch_joint_drift", "incomplete", "close", "request_identity"])
def test_unknown_or_mismatched_result_never_retries_or_promotes(setup, failure):
    fake = FakeCLI(failure=failure)
    result = execute(setup, fake)
    assert result.uncertain and result.candidate is None and result.usage is None
    assert sum(args[1] == "run" for args in fake.calls) == 1
    journal = next(setup[3].workdir.rglob("invocation.json"))
    assert json.loads(journal.read_text())["request_id"]
    if failure == "dispatch_joint_drift":
        assert json.loads(journal.read_text())["dispatch_id"] == "D"
        assert [args[1] for args in fake.calls] == ["run", "task"]


@pytest.mark.parametrize("content", ['not json', '{"answer":3,"adopted_asset_ids":["unavailable"]}'])
def test_invalid_proposal_is_known_rejection_after_cleanup(setup, content):
    fake = FakeCLI(content=content)
    result = execute(setup, fake)
    assert result.candidate is None and not result.uncertain
    assert fake.calls[-1][1:3] == ["controller", "close"]


def test_invalid_scope_and_mock_live_mismatch_fail_before_launch(setup):
    target, state, head, api, signal, attempt = setup
    fake = FakeCLI()
    with pytest.raises(ValueError, match="provenance"):
        SwaExecutor(api, runner=fake)
    executor = SwaExecutor(api, runner=fake, provenance="mock")
    escaped = signal.model_copy(update={"payload": {**signal.payload, "output_path": "../secret.json"}})
    with pytest.raises((AssetSafetyError, ValueError)):
        executor.execute(escaped, attempt, target, state / "execution" / "one", base_revision=head, base_head=head)
    assert not fake.calls


@pytest.mark.parametrize("admitted,allow_unknown,completed", [(False, False, False), (True, False, False), (True, True, True)])
def test_worker_reuses_original_budget_and_validation_gates(setup, admitted, allow_unknown, completed):
    target, state, _, api, signal, _ = setup
    policy = BudgetPolicy(max_cost_usd=1.0, unbounded_reservation_usd=0.1 if admitted else None,
                          allow_unknown_usage=allow_unknown)
    ledger = TaskLedger(state / "tasks.sqlite3", "test", limits=policy.limits)
    acceptance = ValidationPolicy(version="bounded-json-oracle-v1", expectations=(FileExpectation(path="sum.json", content=canonical_answer(3)),))
    ledger.enqueue(signal, acceptance={"validation_policy": acceptance.model_dump(mode="json")})
    PheromoneField(state / "field.sqlite3", ledger=ledger).deposit(signal)
    fake = FakeCLI()
    config = WorkerConfig(state=state, target=target, agent=AgentId(role="builder", instance=0), swarm_id="test",
                          locality=Locality(workspace=str(target), authorized_scopes=(".",)), capabilities={"sum": 1.0},
                          budget=policy, energy=1, energy_policy="claim")
    worker = Worker(config, SwaExecutor(api, runner=fake, provenance="mock"))
    status = worker.run()
    assert (status["completed"] == 1) == completed, status
    assert (target / "sum.json").read_text() == ("3\n" if completed else "null\n")
    assert bool(fake.calls) == admitted
    if admitted:
        assert worker.budget.snapshot().estimated_cost_usd is None
