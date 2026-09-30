"""Contract-local faults with real public script output; no sandbox/live claim."""

from pathlib import Path
import json
import subprocess
import sys
from typing import Literal

import httpx
from opensandbox.models.execd import Execution, ExecutionComplete, ExecutionError
import pytest

from orchestration.experiments import ExperimentContext, ExperimentExecutor, read_result
from orchestration.experiments.case import public_case
from orchestration.experiments.executor import DIRECTORY


CASE = Path(__file__).resolve().parents[2] / "demo/research_case"


class LocalContractSession:
    owned = True
    kernel_id = None
    id = "mock-sandbox"

    def __init__(self, root: Path, mode: str = "success") -> None:
        self.root = root
        self.mode = mode
        self.destroyed = self.closed = False
        self.calls = 0
        root.mkdir()

    def info(self):
        return {"id": self.id, "status": {"state": "RUNNING"}}

    def renew(self, seconds):
        return {"seconds": seconds}

    def upload(self, path, data):
        name = path.removeprefix(DIRECTORY + "/")
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def download(self, path, limit):
        raw = (self.root / path.removeprefix(DIRECTORY + "/")).read_bytes()
        if len(raw) > limit:
            raise ValueError("artifact_size_limit")
        return raw

    def run(self, argv, seconds, directory):
        self.calls += 1
        if self.calls == 1:
            (self.root / "runtime.json").write_text(json.dumps({"python": "3.12.13"}))
            return Execution(id="probe", exit_code=0)
        if self.mode == "transport_timeout":
            raise httpx.ReadTimeout("do not log this secret")
        if self.mode == "unknown":
            return Execution(id="work", complete=ExecutionComplete(timestamp=1, execution_time_in_millis=1))
        if self.mode in {"failed", "timeout"}:
            return Execution(id="work", exit_code=None if self.mode == "timeout" else 7,
                error=ExecutionError(name="TimeoutError" if self.mode == "timeout" else "CommandExecError",
                                     value="failure", timestamp=1))
        # Only the committed public script runs on the host, inside pytest temp.
        completed = subprocess.run([sys.executable, *argv[1:]], cwd=self.root,
            capture_output=True, timeout=seconds, check=False)
        assert completed.returncode == 0, completed.stderr
        if self.mode == "missing":
            (self.root / "metrics.json").unlink()
        if self.mode == "negative":
            data = json.loads((self.root / "metrics.json").read_bytes())
            data["sample_variance"] = 0.5
            (self.root / "metrics.json").write_text(json.dumps(data))
        return Execution(id="work", exit_code=completed.returncode)

    def run_code(self, code):
        raise AssertionError("code interpreter not enabled in mock")

    def cancel(self, command_id):
        pass

    def destroy(self):
        self.destroyed = True
        if self.mode == "cleanup_unknown":
            raise httpx.ReadTimeout("secret")

    def close(self):
        self.closed = True


class LocalContractBackend:
    provenance: Literal["mock"] = "mock"
    capabilities = frozenset({"script", "cpu", "memory", "duration"})

    def __init__(self, root, mode="success"):
        self.root = root
        self.mode = mode
        self.create_calls = 0
        self.session = None

    def create(self, plan, context):
        self.create_calls += 1
        if self.mode == "create_unknown":
            raise httpx.ReadTimeout("secret")
        self.session = LocalContractSession(self.root, self.mode)
        return self.session


def context(run="contract-01"):
    return ExperimentContext(run_id=run, task_id="nist-task", worker_id="contract-worker", fencing_token=1)


@pytest.mark.parametrize("order", ["original", "reverse"])
def test_public_case_raw_outputs_recomputed_after_sandbox_cleanup(tmp_path, order):
    plan = public_case(CASE, order=order)
    backend = LocalContractBackend(tmp_path / "work")
    result = ExperimentExecutor(backend).execute(plan, context(), tmp_path / "archive")
    assert result.execution_state == "succeeded"
    assert result.scientific.verdict == "passed"
    assert result.scientific.metrics["variance_absolute_error"] < 1e-9
    assert result.scientific.metrics["naive_variance_absolute_error"] > 0.001
    assert result.provenance == "mock" and result.exit_code == 0
    assert result.cost_usd is None and result.usage is None
    assert backend.session.destroyed and backend.session.closed
    loaded = read_result(tmp_path / "archive", context().run_id, expected_plan=plan, expected_context=context())
    assert loaded == result
    with pytest.raises(FileExistsError):
        ExperimentExecutor(backend).execute(plan, context(), tmp_path / "archive")
    assert backend.create_calls == 1


@pytest.mark.parametrize("mode,state,science", [
    ("failed", "failed", "not_evaluated"), ("timeout", "timeout", "not_evaluated"),
    ("unknown", "unknown", "not_evaluated"), ("transport_timeout", "unknown", "not_evaluated"),
    ("missing", "missing_artifact", "not_evaluated"), ("negative", "succeeded", "failed"),
    ("create_unknown", "unknown", "not_evaluated"),
])
def test_failures_do_not_become_scientific_success_or_retry(tmp_path, mode, state, science):
    backend = LocalContractBackend(tmp_path / "work", mode)
    result = ExperimentExecutor(backend).execute(public_case(CASE), context(), tmp_path / "archive")
    assert result.execution_state == state
    assert result.scientific.verdict == science
    assert backend.create_calls == 1
    if backend.session:
        assert backend.session.destroyed and backend.session.closed
    if state == "unknown":
        assert result.exit_code is None and result.remote_effect == "unknown"
    assert "secret" not in (Path(result.archive_path) / "result.json").read_text()


def test_resource_and_optional_capabilities_are_explicit(tmp_path):
    backend = LocalContractBackend(tmp_path / "work")
    plan = public_case(CASE).model_copy(update={"persistent_volume": "not-provisioned"})
    result = ExperimentExecutor(backend).execute(plan, context(), tmp_path / "archive")
    assert result.execution_state == "unsupported" and result.scientific.verdict == "not_evaluated"
    assert backend.create_calls == 0


def test_binding_integrity_and_raw_recalculation(tmp_path):
    plan = public_case(CASE)
    backend = LocalContractBackend(tmp_path / "work")
    result = ExperimentExecutor(backend).execute(plan, context(), tmp_path / "archive")
    with pytest.raises(ValueError, match="expected_context_mismatch"):
        read_result(tmp_path / "archive", context().run_id, expected_context=context().model_copy(update={"fencing_token": 2}))
    with pytest.raises(ValueError, match="expected_plan_mismatch"):
        read_result(tmp_path / "archive", context().run_id, expected_plan=plan.model_copy(update={"parameters": ("reverse",)}))
    record = Path(result.archive_path) / "result.json"
    fake = json.loads(record.read_bytes())
    fake["scientific"]["metrics"]["sample_variance"] = 999
    record.write_text(json.dumps(fake))
    assert read_result(tmp_path / "archive", context().run_id).scientific.metrics["sample_variance"] != 999
    (Path(result.archive_path) / "outputs/metrics.json").write_text("{}")
    with pytest.raises(ValueError, match="artifact_digest_mismatch"):
        read_result(tmp_path / "archive", context().run_id)


def test_cleanup_ambiguity_is_not_known_success(tmp_path):
    backend = LocalContractBackend(tmp_path / "work", "cleanup_unknown")
    result = ExperimentExecutor(backend).execute(public_case(CASE), context(), tmp_path / "archive")
    assert result.scientific.verdict == "passed"
    assert result.cleanup_state == result.remote_effect == "unknown"
    assert backend.create_calls == 1 and backend.session.closed
