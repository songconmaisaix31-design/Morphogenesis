"""Explicit installed L1 fixture backend: fixed bytes, no candidate execution.

Only protected host configuration may select this backend and supply its output.
It implements the existing session protocol, records ``provenance=mock`` and
cannot create a sandbox, launch a process, access the network or evaluate code.
Its synthetic isolation record applies only to this in-memory fixture adapter.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from opensandbox.models.execd import Execution, ExecutionError

from orchestration.experiments.executor import DIRECTORY, RUNTIME_PROBE
from orchestration.experiments.generated import (
    ApprovedEnvironment, BackendProfile, GeneratedContext, GeneratedExperimentPlan,
    IsolationCapability, IsolationConfiguration, IsolationReport, effective_environment,
)
from orchestration.experiments.security import verify_isolation
from orchestration.experiments.trusted import IsolationProbeRecord, TrustedProbeRegistry

FixtureOutcome = Literal["succeeded", "failed", "timeout", "unknown"]


class GeneratedFixtureSession:
    owned = True
    kernel_id: str | None = None

    def __init__(self, context: GeneratedContext, entrypoint: str, *, output: bytes | None,
                 outcome: FixtureOutcome, python_version: str) -> None:
        self.id = "mock-" + context.run_id
        self._context = context
        self._entrypoint = entrypoint
        self._output = output
        self._outcome = outcome
        self._python_version = python_version
        self._files: dict[str, bytes] = {}
        self.destroyed = False
        self.closed = False

    def info(self) -> dict[str, Any]:
        return {"id": self.id, "provenance": "mock", "metadata": {
            "morph-run": self._context.run_id, "morph-task": self._context.task_id,
            "morph-worker": self._context.worker_id, "morph-fence": str(self._context.fencing_token)}}

    def renew(self, seconds: int) -> dict[str, Any]:
        return {"seconds": seconds, "provenance": "mock"}

    def upload(self, path: str, data: bytes) -> None:
        if not path.startswith(DIRECTORY + "/") or ".." in path.split("/"):
            raise ValueError("fixture_path_outside_workspace")
        self._files[path] = bytes(data)

    def download(self, path: str, limit: int) -> bytes:
        data = self._files[path]
        if len(data) > limit:
            raise ValueError("artifact_size_limit")
        return data

    def run(self, argv: list[str], seconds: int, directory: str) -> Execution:
        if directory != DIRECTORY or self.closed or self.destroyed:
            raise ValueError("fixture_session_unavailable")
        if argv == ["python3", "-c", RUNTIME_PROBE]:
            self._files[DIRECTORY + "/runtime.json"] = json.dumps({
                "python": self._python_version + ".0", "provenance": "mock"}).encode()
            return Execution(id="mock-runtime", exit_code=0)
        if argv != ["python3", self._entrypoint] or DIRECTORY + "/" + self._entrypoint not in self._files:
            raise ValueError("fixture_command_unsupported")
        # Neither argv nor uploaded candidate bytes are ever interpreted.
        if self._outcome == "unknown":
            raise TimeoutError("fixture_unknown_effect")
        if self._outcome == "timeout":
            return Execution(id="mock-execution", exit_code=None,
                error=ExecutionError(name="TimeoutError", value="mock timeout", timestamp=1))
        if self._output is not None:
            self._files[DIRECTORY + "/output.json"] = self._output
        return Execution(id="mock-execution", exit_code=0 if self._outcome == "succeeded" else 1)

    def run_code(self, code: str) -> Execution:
        raise ValueError("fixture_code_execution_forbidden")

    def cancel(self, command_id: str) -> None:
        return None

    def destroy(self) -> None:
        self.destroyed = True

    def close(self) -> None:
        self.closed = True


class GeneratedFixtureBackend:
    provenance: Literal["live", "replay", "mock"] = "mock"
    capabilities = frozenset({"script", "cpu", "memory", "duration"})

    def __init__(self, *, environment: ApprovedEnvironment, resources: BackendProfile,
                 output: bytes | None, instance_id: str, outcome: FixtureOutcome = "succeeded") -> None:
        if outcome not in {"succeeded", "failed", "timeout", "unknown"}:
            raise ValueError("unsupported_fixture_outcome")
        environment = ApprovedEnvironment.model_validate_json(environment.model_dump_json())
        resources = BackendProfile.model_validate_json(resources.model_dump_json())
        self._configuration = IsolationConfiguration(endpoint="mock://generated-fixture", instance_id=instance_id,
            runtime_profile="fixed-output-fixture-v1", environment=effective_environment(environment),
            resources=resources, network_deny=True, server_process_limit=resources.process_limit)
        self._output = bytes(output) if output is not None else None
        if self._output is not None and len(self._output) > resources.artifact_bytes:
            raise ValueError("fixture_output_size_limit")
        self._outcome = outcome
        self._probe = IsolationProbeRecord(probe_id=instance_id, backend="generated-fixture",
            declared=IsolationCapability(**{name: True for name in IsolationCapability.model_fields}),
            configuration=self._configuration, image_digest=self._configuration.environment.image_digest,
            verified=True, passed=True, evidence_ref="mock-fixed-output-not-live-probe", probed_at=0)
        self.probe_registry = TrustedProbeRegistry((self._probe,))

    def configuration(self, plan: GeneratedExperimentPlan) -> IsolationConfiguration:
        return self._configuration

    def isolation(self) -> IsolationReport:
        return IsolationReport(backend="generated-fixture", declared=self._probe.declared,
            proof_ref=self._probe.probe_id, configuration=self._configuration,
            verified=False, probe="not_run", reasons=("mock_fixture_not_live_isolation",))

    def create(self, plan: GeneratedExperimentPlan, context: GeneratedContext) -> GeneratedFixtureSession:
        if plan.task_id != context.task_id:
            raise ValueError("plan_task_mismatch")
        verify_isolation(self.isolation(), self.probe_registry, plan)
        return GeneratedFixtureSession(context, plan.entrypoint, output=self._output, outcome=self._outcome,
                                       python_version=self._configuration.environment.python_version)
