"""Shared offline fixtures for generated-candidate tests (no live sandbox/model).

The candidate code is inert: it is only ever *statically* inspected, never
executed, evaluated or interpreted. Raw outputs are fixed per plan case by the
fixture, and the mock backend writes those fixed bytes without invoking Python.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Literal

from opensandbox.models.execd import Execution, ExecutionError

from orchestration.experiments.generated import (
    ApprovedEnvironment, BackendProfile, EvaluationSpec, GeneratedContext, GeneratedExperimentPlan,
    GeneratedFile, GeneratedSource, IsolationCapability, IsolationReport,
)
from orchestration.experiments.executor import DIRECTORY, RUNTIME_PROBE
from orchestration.experiments.trusted import (
    IsolationProbeRecord, TrustedCriteriaRecord, TrustedCriteriaRegistry, TrustedProbeRegistry,
)

IMAGE = "python:3.12.13-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36"
IMAGE_DIGEST = IMAGE.split("@", 1)[1]


def full_capability(*, network_deny: bool = True) -> IsolationCapability:
    """Hypothetical fully-capable backend (mock only). The real OpenSandbox adapter
    declares process_limit=False in orchestration.experiments.sandbox_adapter."""
    return IsolationCapability(
        no_host_write=True, no_credentials=True, no_host_control=True, no_privilege=True,
        export_bounded=True, network_deny=network_deny, cpu_limit=True, memory_limit=True,
        process_limit=True, time_limit=True, self_owned_cleanup=True,
    )

# Inert candidate code: static-checked only, never executed by any fixture.
GENERATED_CODE = '''\
import json
import math


def main():
    with open("parameters.json", "r", encoding="utf-8") as fh:
        params = json.load(fh)
    n = int(params["parameters"].get("n_intervals", 100))
    u = [math.sin(math.pi * (i / n)) for i in range(n + 1)]
    with open("output.json", "w", encoding="utf-8") as fh:
        json.dump({"x": [i / n for i in range(n + 1)], "u": u}, fh)


if __name__ == "__main__":
    main()
'''


def code_sha256() -> str:
    return hashlib.sha256(GENERATED_CODE.encode()).hexdigest()


def uniform_x(n_intervals: int) -> list[float]:
    return [i / n_intervals for i in range(n_intervals + 1)]


def poisson_reference_output(n_intervals: int) -> bytes:
    return json.dumps({"x": uniform_x(n_intervals),
                       "u": [math.sin(math.pi * x) for x in uniform_x(n_intervals)]}).encode()


def poisson_wrong_output(n_intervals: int) -> bytes:
    return json.dumps({"x": uniform_x(n_intervals), "u": [0.0] * (n_intervals + 1)}).encode()


def poisson_scored_output(n_intervals: int) -> bytes:
    body = json.loads(poisson_reference_output(n_intervals))
    body["score"] = 0.0
    body["passed"] = True
    return json.dumps(body).encode()


def make_poisson_plan(*, n_intervals: int = 100, dependencies: tuple[str, ...] = (),
                      code: bytes | None = None, approved: bool = False) -> GeneratedExperimentPlan:
    code = code if code is not None else GENERATED_CODE.encode()
    return GeneratedExperimentPlan(
        plan_id="poisson-fd-v1", project_id="proj-1", branch_id="branch-1", task_id="gen-task-1",
        candidate_asset_id="asset-1", candidate_revision="a" * 40, authorization_ref="env-1",
        files=(GeneratedFile(name="experiment.py", sha256=hashlib.sha256(code).hexdigest(),
                             size_bytes=len(code), source="research-note:poisson"),),
        entrypoint="experiment.py",
        environment=ApprovedEnvironment(image=IMAGE, image_digest=IMAGE_DIGEST,
                                        dependency_lock_sha256="b" * 64, dependencies=dependencies),
        parameters={"n_intervals": n_intervals}, seeds=(0,),
        evaluation=EvaluationSpec(version="poisson-eval-v1", kind="poisson_reference_v1",
                                  n_intervals=n_intervals, max_abs_tolerance=5e-3, boundary_tolerance=1e-8,
                                  approved=approved, approved_by="reviewer" if approved else None),
        backend=BackendProfile(),
        sources=(GeneratedSource(kind="hypothesis", ref="note:h1", title="Poisson FD hypothesis"),),
        claim="A finite-difference solver reproduces -u'' = pi^2 sin(pi x) on [0,1].",
        hypothesis="u(x) = sin(pi x) on [0,1] with homogeneous Dirichlet boundary.",
    )


def approved_criteria_registry(spec: EvaluationSpec, *, approved_by: str = "trusted-reviewer") -> TrustedCriteriaRegistry:
    return TrustedCriteriaRegistry(records=(TrustedCriteriaRecord(
        spec=spec, approved_by=approved_by, approved_at=1_000_000.0),))


def make_context(*, run_id: str = "gen-run-01", author: str = "author-1", reviewer: str = "reviewer-1",
                 task_id: str = "gen-task-1") -> GeneratedContext:
    return GeneratedContext(run_id=run_id, task_id=task_id, worker_id="worker-1",
                            fencing_token=1, author=author, reviewer=reviewer)


def probe_record(*, backend: str = "mock") -> IsolationProbeRecord:
    return IsolationProbeRecord(probe_id="probe-1", backend=backend,
                                declared=full_capability(), image_digest=IMAGE_DIGEST,
                                verified=True, passed=True, evidence_ref="probe-run-1", probed_at=1_000_000.0)


def verified_probe_registry(*, backend: str = "mock") -> TrustedProbeRegistry:
    return TrustedProbeRegistry(records=(probe_record(backend=backend),))


def mock_isolation(backend: str = "mock") -> IsolationReport:
    return IsolationReport(backend=backend, declared=full_capability(),
                           verified=False, probe="not_run", proof_ref="probe-1",
                           reasons=("isolation_probe_not_run",))


class MockGeneratedSession:
    owned = True
    kernel_id = None
    id = "mock-sandbox"

    def __init__(self, root: Path, *, output: bytes | None, entry_exit_code: int, timeout: bool,
                 probe_fail: bool) -> None:
        self.root = root
        self.output = output
        self.entry_exit_code = entry_exit_code
        self.timeout = timeout
        self.probe_fail = probe_fail
        self.destroyed = False
        self.closed = False
        self.calls = 0
        root.mkdir(parents=True, exist_ok=True)

    def info(self) -> dict:
        return {"id": self.id, "status": {"state": "RUNNING"},
                "metadata": {"morph-run": "gen-run-01", "morph-task": "gen-task-1",
                             "morph-worker": "worker-1", "morph-fence": "1"}}

    def renew(self, seconds: int) -> dict:
        return {"seconds": seconds}

    def upload(self, path: str, data: bytes) -> None:
        target = self.root / path.removeprefix(DIRECTORY + "/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def download(self, path: str, limit: int) -> bytes:
        raw = (self.root / path.removeprefix(DIRECTORY + "/")).read_bytes()
        if len(raw) > limit:
            raise ValueError("artifact_size_limit")
        return raw

    def run(self, argv: list[str], seconds: int, directory: str) -> Execution:
        self.calls += 1
        if argv[:2] == ["python3", "-c"]:
            if self.probe_fail:
                return Execution(id="probe", exit_code=1)
            (self.root / "runtime.json").write_text(json.dumps({"python": "3.12.13"}))
            return Execution(id="probe", exit_code=0)
        if self.timeout:
            return Execution(id="work", exit_code=None,
                             error=ExecutionError(name="TimeoutError", value="timeout", timestamp=1))
        if self.output is not None:
            (self.root / "output.json").write_bytes(self.output)
        return Execution(id="work", exit_code=self.entry_exit_code)

    def run_code(self, code: str) -> Execution:
        raise AssertionError("code interpreter not enabled in mock")

    def cancel(self, command_id: str) -> None:
        pass

    def destroy(self) -> None:
        self.destroyed = True

    def close(self) -> None:
        self.closed = True


class MockGeneratedBackend:
    provenance: Literal["mock"] = "mock"
    capabilities = frozenset({"script", "cpu", "memory", "duration"})

    def __init__(self, root: Path, *, output: bytes | None = None, entry_exit_code: int = 0,
                 timeout: bool = False, probe_fail: bool = False,
                 isolation: IsolationReport | None = None, backend_name: str = "mock") -> None:
        self.root = root
        self.output = output
        self.entry_exit_code = entry_exit_code
        self.timeout = timeout
        self.probe_fail = probe_fail
        self._isolation = isolation if isolation is not None else mock_isolation(backend=backend_name)
        self.create_calls = 0
        self.session: MockGeneratedSession | None = None

    def isolation(self) -> IsolationReport:
        return self._isolation

    def create(self, plan, context) -> MockGeneratedSession:
        self.create_calls += 1
        self.session = MockGeneratedSession(self.root, output=self.output,
                                            entry_exit_code=self.entry_exit_code, timeout=self.timeout,
                                            probe_fail=self.probe_fail)
        return self.session
