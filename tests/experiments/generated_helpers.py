"""Shared offline fixtures for generated-candidate tests (no live sandbox/model)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Literal

from opensandbox.models.execd import Execution

from orchestration.experiments.generated import (
    ApprovedEnvironment, BackendProfile, EvaluationSpec, GeneratedContext, GeneratedExperimentPlan,
    GeneratedFile, GeneratedSource, IsolationCapability, IsolationReport,
)
from orchestration.experiments.executor import DIRECTORY, RUNTIME_PROBE
from orchestration.experiments.sandbox_adapter import declared_capability

IMAGE = "python:3.12.13-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36"

GENERATED_CODE = '''\
import json
import math


def solve(n):
    h = 1.0 / n
    f = [math.pi ** 2 * math.sin(math.pi * (i * h)) for i in range(1, n)]
    lower = [-1.0] * (n - 1)
    diag = [2.0] * (n - 1)
    upper = [-1.0] * (n - 1)
    b = [h * h * v for v in f]
    cp = [0.0] * (n - 1)
    dp = [0.0] * (n - 1)
    cp[0] = upper[0] / diag[0]
    dp[0] = b[0] / diag[0]
    for i in range(1, n - 1):
        denom = diag[i] - lower[i] * cp[i - 1]
        cp[i] = upper[i] / denom
        dp[i] = (b[i] - lower[i] * dp[i - 1]) / denom
    x = [0.0] * (n - 1)
    x[-1] = dp[-1]
    for i in range(n - 3, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return [0.0] + x + [0.0]


def main():
    with open("parameters.json", "r", encoding="utf-8") as fh:
        params = json.load(fh)
    n = int(params["parameters"].get("n_intervals", 100))
    u = solve(n)
    h = 1.0 / n
    xs = [i * h for i in range(n + 1)]
    with open("output.json", "w", encoding="utf-8") as fh:
        json.dump({"x": xs, "u": u}, fh)


if __name__ == "__main__":
    main()
'''


def code_sha256() -> str:
    return hashlib.sha256(GENERATED_CODE.encode()).hexdigest()


def make_poisson_plan(*, n_intervals: int = 100, approved: bool = True,
                      dependencies: tuple[str, ...] = (), code: bytes | None = None) -> GeneratedExperimentPlan:
    code = code if code is not None else GENERATED_CODE.encode()
    return GeneratedExperimentPlan(
        plan_id="poisson-fd-v1", project_id="proj-1", branch_id="branch-1", task_id="gen-task-1",
        candidate_asset_id="asset-1", candidate_revision="a" * 40, authorization_ref="env-1",
        files=(GeneratedFile(name="experiment.py", sha256=hashlib.sha256(code).hexdigest(),
                             size_bytes=len(code), source="research-note:poisson"),),
        entrypoint="experiment.py",
        environment=ApprovedEnvironment(image=IMAGE, dependency_lock_sha256="b" * 64,
                                        dependencies=dependencies),
        parameters={"n_intervals": n_intervals}, seeds=(0,),
        evaluation=EvaluationSpec(version="poisson-eval-v1", kind="poisson_reference_v1",
                                  n_intervals=n_intervals, max_abs_tolerance=5e-3, boundary_tolerance=1e-8,
                                  approved=approved, approved_by="reviewer" if approved else None),
        backend=BackendProfile(),
        sources=(GeneratedSource(kind="hypothesis", ref="note:h1", title="Poisson FD hypothesis"),),
        claim="A finite-difference solver reproduces -u'' = pi^2 sin(pi x) on [0,1].",
        hypothesis="u(x) = sin(pi x) on [0,1] with homogeneous Dirichlet boundary.",
    )


def make_context(*, run_id: str = "gen-run-01", author: str = "author-1", reviewer: str = "reviewer-1",
                 task_id: str = "gen-task-1") -> GeneratedContext:
    return GeneratedContext(run_id=run_id, task_id=task_id, worker_id="worker-1",
                            fencing_token=1, author=author, reviewer=reviewer)


def verified_isolation(network_deny: bool = True) -> IsolationReport:
    return IsolationReport(backend="mock", declared=declared_capability(network_deny=network_deny),
                           verified=True, probe="passed")


def unverified_isolation() -> IsolationReport:
    return IsolationReport(backend="mock", declared=declared_capability(network_deny=True),
                           verified=False, probe="not_run", reasons=("isolation_probe_not_run",))


class MockGeneratedSession:
    owned = True
    kernel_id = None
    id = "mock-sandbox"

    def __init__(self, root: Path, mode: str) -> None:
        self.root = root
        self.mode = mode
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
        if self.mode == "probe_fail":
            return Execution(id="probe", exit_code=1)
        if argv[:2] == ["python3", "-c"]:
            (self.root / "runtime.json").write_text(json.dumps({"python": "3.12.13"}))
            return Execution(id="probe", exit_code=0)
        if self.mode == "crash":
            return Execution(id="work", exit_code=2)
        if self.mode == "timeout":
            return Execution(id="work", exit_code=None, error=_timeout_error())
        if self.mode == "unknown":
            return Execution(id="work")
        completed = subprocess.run([sys.executable, *argv[1:]], cwd=self.root,
                                   capture_output=True, timeout=seconds, check=False)
        if self.mode == "missing_output":
            (self.root / "output.json").unlink(missing_ok=True)
        return Execution(id="work", exit_code=completed.returncode)

    def run_code(self, code: str) -> Execution:
        raise AssertionError("code interpreter not enabled in mock")

    def cancel(self, command_id: str) -> None:
        pass

    def destroy(self) -> None:
        self.destroyed = True

    def close(self) -> None:
        self.closed = True


def _timeout_error():
    from opensandbox.models.execd import ExecutionError
    return ExecutionError(name="TimeoutError", value="timeout", timestamp=1)


class MockGeneratedBackend:
    provenance: Literal["mock"] = "mock"
    capabilities = frozenset({"script", "cpu", "memory", "duration"})

    def __init__(self, root: Path, mode: str = "success", *, isolation: IsolationReport | None = None) -> None:
        self.root = root
        self.mode = mode
        self.create_calls = 0
        self.session: MockGeneratedSession | None = None
        self._isolation = isolation if isolation is not None else verified_isolation()

    def isolation(self) -> IsolationReport:
        return self._isolation

    def create(self, plan, context) -> MockGeneratedSession:
        self.create_calls += 1
        self.session = MockGeneratedSession(self.root, self.mode)
        return self.session
