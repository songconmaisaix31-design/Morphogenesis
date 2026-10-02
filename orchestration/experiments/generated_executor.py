"""Bounded generated-candidate execution reusing the OpenSandbox SDK lifecycle.

The pipeline is prepare -> admit -> run -> evaluate -> report. Admission is
fail-closed: static security gates and a *verified* isolation report must pass
before any sandbox is created. A candidate is never executed on the host. The
trusted assessment is recomputed from the candidate's raw output, never from a
self-reported score.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import httpx

from orchestration.experiments.backend import ExperimentSession, UnsupportedCapability
from orchestration.experiments.evaluation import evaluate
from orchestration.experiments.executor import DIRECTORY, RUNTIME_PROBE, _execution_state, digest
from orchestration.experiments.generated import (
    ExecutionAxis, GeneratedAssessment, GeneratedContext, GeneratedExperimentPlan, GeneratedResult,
    IsolationReport, StaticSecurityReport,
)
from orchestration.experiments.models import ExperimentArtifact
from orchestration.experiments.sandbox_adapter import GeneratedBackend
from orchestration.experiments.security import SecurityRejection, static_checks, verify_isolation

GENERATED_OUTPUT = "output.json"
GENERATED_PARAMETERS = "parameters.json"


def _write_json(path: Path, data: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _artifact(root: Path, name: str, data: bytes) -> ExperimentArtifact:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return ExperimentArtifact(name=name, archive_path=name, sha256=digest(data), size_bytes=len(data))


def execution_axis(state: str) -> ExecutionAxis:
    if state == "succeeded":
        return "succeeded"
    if state in {"failed", "timeout", "missing_artifact"}:
        return "failed"
    if state == "unknown":
        return "unknown"
    return "not_run"


@dataclass(frozen=True)
class GeneratedPreparation:
    plan: GeneratedExperimentPlan
    files: dict[str, bytes]
    static: StaticSecurityReport
    isolation: IsolationReport


class GeneratedExperimentExecutor:
    def __init__(self, backend: GeneratedBackend) -> None:
        self.backend = backend

    def prepare(self, plan: GeneratedExperimentPlan, files: dict[str, bytes]) -> GeneratedPreparation:
        plan = GeneratedExperimentPlan.model_validate(plan.model_dump(mode="json"))
        manifest = {file.name: file for file in plan.files}
        for name, body in files.items():
            entry = manifest.get(name)
            if entry is None or digest(body) != entry.sha256 or len(body) != entry.size_bytes:
                raise ValueError("manifest_digest_mismatch")
        if set(files) != set(manifest):
            raise ValueError("manifest_count_mismatch")
        return GeneratedPreparation(plan=plan, files=dict(files),
                                    static=static_checks(plan, files), isolation=self.backend.isolation())

    def admit(self, preparation: GeneratedPreparation) -> None:
        if not preparation.static.passed:
            raise SecurityRejection("static_security_failed")
        verify_isolation(preparation.isolation)
        required = {"script", "cpu", "memory", "duration"}
        if missing := required - self.backend.capabilities:
            raise UnsupportedCapability(",".join(sorted(missing)))

    def execute(self, plan: GeneratedExperimentPlan, context: GeneratedContext,
                files: dict[str, bytes], archive_root: Path | str) -> GeneratedResult:
        preparation = self.prepare(plan, files)
        root = Path(archive_root).resolve() / context.run_id
        result = GeneratedResult(
            plan=preparation.plan, context=context, archive_path=str(root), provenance=self.backend.provenance,
            admission=preparation.static, isolation=preparation.isolation,
            assessment=GeneratedAssessment(execution="not_run", evaluator_version=preparation.plan.evaluation.version))
        root.mkdir(parents=True, exist_ok=False)
        _write_json(root / "plan.json", preparation.plan.model_dump(mode="json"))
        _write_json(root / "result.json", result.model_dump(mode="json"))
        artifacts: list[ExperimentArtifact] = []
        session: ExperimentSession | None = None

        def persist() -> None:
            result_ = result.model_copy(update={"artifacts": tuple(artifacts)})
            _write_json(root / "result.json", result_.model_dump(mode="json"))

        def capture(name: str, data: bytes) -> None:
            artifacts.append(_artifact(root, name, data))
            persist()

        try:
            if preparation.plan.task_id != context.task_id:
                raise ValueError("plan_task_mismatch")
            self.admit(preparation)
            for name, body in preparation.files.items():
                capture(f"inputs/{name}", body)
            result = result.model_copy(update={"cleanup_state": "unknown"})
            persist()
            session = self.backend.create(preparation.plan, context)
            result = result.model_copy(update={"sandbox_id": session.id})
            persist()
            capture("sandbox.json", json.dumps(session.info()).encode())
            for name, body in preparation.files.items():
                session.upload(f"{DIRECTORY}/{name}", body)
            parameters = {"parameters": preparation.plan.parameters, "seeds": list(preparation.plan.seeds)}
            session.upload(f"{DIRECTORY}/{GENERATED_PARAMETERS}", json.dumps(parameters).encode())
            probe = session.run(["python3", "-c", RUNTIME_PROBE], 10, DIRECTORY)
            capture("runtime-command.json", probe.model_dump_json().encode())
            if _execution_state(probe) != "succeeded":
                state = _execution_state(probe)
                result = result.model_copy(update={"execution_state": state, "exit_code": probe.exit_code,
                    "reasons": ("runtime_probe_failed",),
                    "assessment": result.assessment.model_copy(update={"execution": execution_axis(state)})})
                return self._finish(result, root, artifacts, session)
            runtime = session.download(f"{DIRECTORY}/runtime.json", preparation.plan.backend.artifact_bytes)
            capture("runtime.json", runtime)
            version = json.loads(runtime).get("python")
            if not isinstance(version, str) or not version.startswith(preparation.plan.environment.python_version + "."):
                raise UnsupportedCapability("python_environment_mismatch")
            execution = session.run(["python3", preparation.plan.entrypoint],
                                    preparation.plan.backend.command_seconds, DIRECTORY)
            capture("execution.json", execution.model_dump_json().encode())
            state = _execution_state(execution)
            result = result.model_copy(update={"execution_state": state, "exit_code": execution.exit_code,
                "remote_effect": "known" if state in {"succeeded", "failed", "timeout"} else "unknown"})
            persist()
            try:
                capture(f"outputs/{GENERATED_OUTPUT}",
                        session.download(f"{DIRECTORY}/{GENERATED_OUTPUT}", preparation.plan.backend.artifact_bytes))
            except Exception as error:
                capture("download-output.json", json.dumps({"error_type": type(error).__name__}).encode())
                if state == "succeeded":
                    result = result.model_copy(update={"execution_state": "missing_artifact",
                        "reasons": (*result.reasons, "required_artifact_unreadable")})
            result = result.model_copy(update={"assessment": self.evaluate(result, context)})
            if result.execution_state == "succeeded" and not result.assessment.trusted:
                raise ValueError("trusted_assessment_unavailable")
        except UnsupportedCapability as error:
            result = result.model_copy(update={"execution_state": "unsupported", "reasons": (str(error),),
                "assessment": result.assessment.model_copy(update={"execution": "not_run"})})
        except SecurityRejection as error:
            result = result.model_copy(update={"execution_state": "unsupported", "reasons": (str(error),),
                "assessment": result.assessment.model_copy(update={"execution": "not_run"})})
        except (httpx.TimeoutException, TimeoutError):
            result = result.model_copy(update={"execution_state": "unknown", "remote_effect": "unknown",
                "reasons": ("transport_timeout_execution_unknown",)})
        except Exception as error:
            result = result.model_copy(update={"execution_state": "unknown", "reasons": (type(error).__name__,)})
        return self._finish(result, root, artifacts, session)

    def evaluate(self, result: GeneratedResult, context: GeneratedContext) -> GeneratedAssessment:
        plan = result.plan
        state = result.execution_state
        reviewer_independent = context.reviewer != context.author
        if state != "succeeded":
            return GeneratedAssessment(execution=execution_axis(state), hypothesis="not_evaluated",
                                       contribution="proposed", mode="diagnostic", trusted=False,
                                       evaluator_version=plan.evaluation.version,
                                       reasons=tuple(result.reasons))
        raw = (Path(result.archive_path) / f"outputs/{GENERATED_OUTPUT}").read_bytes()
        assessment = evaluate(plan, raw, reviewer_independent=reviewer_independent)
        return assessment.model_copy(update={"execution": "succeeded"})

    @staticmethod
    def _finish(result: GeneratedResult, root: Path, artifacts: list[ExperimentArtifact],
                session: ExperimentSession | None) -> GeneratedResult:
        if session:
            try:
                session.destroy()
                result = result.model_copy(update={"cleanup_state": "destroyed"})
            except Exception as error:
                result = result.model_copy(update={"cleanup_state": "unknown", "remote_effect": "unknown",
                    "reasons": (*result.reasons, "cleanup_" + type(error).__name__)})
            finally:
                try:
                    session.close()
                except Exception as error:
                    result = result.model_copy(update={"reasons": (*result.reasons, "close_" + type(error).__name__)})
        result = result.model_copy(update={"artifacts": tuple(artifacts)})
        _write_json(root / "result.json", result.model_dump(mode="json"))
        return result


def read_generated_result(archive_root: Path | str, run_id: str, *,
                          expected_plan: GeneratedExperimentPlan | None = None,
                          expected_context: GeneratedContext | None = None) -> GeneratedResult:
    """Verify durable binding, input digests, and recompute the trusted assessment."""
    if not run_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in run_id):
        raise ValueError("invalid_run_id")
    root = Path(archive_root).resolve() / run_id
    if root.is_symlink():
        raise ValueError("archive_link_rejected")
    result = GeneratedResult.model_validate_json((root / "result.json").read_bytes())
    if (result.context.run_id != run_id or Path(result.archive_path).resolve() != root or
            GeneratedExperimentPlan.model_validate_json((root / "plan.json").read_bytes()) != result.plan):
        raise ValueError("archive_binding_mismatch")
    if expected_plan is not None and expected_plan != result.plan:
        raise ValueError("expected_plan_mismatch")
    if expected_context is not None and expected_context != result.context:
        raise ValueError("expected_context_mismatch")
    for item in result.artifacts:
        path = root / item.archive_path
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("artifact_path_escape")
        raw = path.read_bytes()
        if len(raw) != item.size_bytes or digest(raw) != item.sha256:
            raise ValueError("artifact_digest_mismatch")
    for file in result.plan.files:
        if digest((root / "inputs" / file.name).read_bytes()) != file.sha256:
            raise ValueError("input_digest_mismatch")
    if result.execution_state == "succeeded":
        raw = (root / f"outputs/{GENERATED_OUTPUT}").read_bytes()
        assessment = evaluate(result.plan, raw, reviewer_independent=result.context.reviewer != result.context.author)
        assessment = assessment.model_copy(update={"execution": "succeeded"})
    else:
        assessment = result.assessment
    return result.model_copy(update={"assessment": assessment})
