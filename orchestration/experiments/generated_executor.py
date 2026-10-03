"""Bounded generated-candidate execution reusing the OpenSandbox SDK lifecycle.

The pipeline is prepare -> admit -> run -> evaluate -> report. Admission is
fail-closed: static security gates and a *host-owned* isolation proof must pass
before any sandbox is created. A candidate is never executed on the host. The
trusted assessment is recomputed from the candidate's raw output and is always
``diagnostic`` here; finalization is a separate host-owned step.

Persist/error/cleanup authority is shared with the registered executor via
``orchestration.experiments.executor`` (``finalize_session``, ``_write_json``,
``_artifact``, ``_execution_state``, ``digest``): this module is a thin branch,
not a second executor fact layer.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import cast
import time

import httpx

from orchestration.experiments.backend import ExperimentSession, UnsupportedCapability
from orchestration.experiments.evaluation import evaluate
from orchestration.experiments.executor import (
    DIRECTORY, RUNTIME_PROBE, _artifact, _execution_state, _write_json, digest, finalize_session,
)
from orchestration.experiments.generated import (
    ExecutionAxis, GeneratedAssessment, GeneratedContext, GeneratedExperimentPlan, GeneratedResult,
    IsolationConfiguration, IsolationReport, StaticSecurityReport, effective_environment,
)
from orchestration.experiments.models import ExperimentArtifact
from orchestration.experiments.sandbox_adapter import GeneratedBackend
from orchestration.experiments.security import SecurityRejection, static_checks, verify_isolation
from orchestration.experiments.trusted import TrustedCriteriaRegistry, TrustedProbeRegistry

GENERATED_OUTPUT = "output.json"
GENERATED_PARAMETERS = "parameters.json"


def execution_axis(state: str) -> ExecutionAxis:
    if state == "succeeded":
        return "succeeded"
    if state in {"failed", "timeout", "missing_artifact"}:
        return "failed"
    if state == "unknown":
        return "unknown"
    return "not_run"


def _require_immutable_image(plan: GeneratedExperimentPlan) -> None:
    try:
        effective_environment(plan.environment)
    except ValueError as error:
        raise SecurityRejection(str(error)) from error


@dataclass(frozen=True)
class GeneratedPreparation:
    plan: GeneratedExperimentPlan
    files: dict[str, bytes]
    data: dict[str, bytes]
    static: StaticSecurityReport
    isolation: IsolationReport


class GeneratedExperimentExecutor:
    def __init__(self, backend: GeneratedBackend, *,
                 probe_registry: TrustedProbeRegistry | None = None,
                 criteria_registry: TrustedCriteriaRegistry | None = None) -> None:
        self.backend = backend
        self.probe_registry = probe_registry
        self.criteria_registry = criteria_registry

    def _isolation(self, plan: GeneratedExperimentPlan) -> IsolationReport:
        report = self.backend.isolation()
        configure = getattr(self.backend, "configuration", None)
        configuration = configure(plan) if callable(configure) else None
        if configuration is not None:
            configuration = IsolationConfiguration.model_validate_json(configuration.model_dump_json())
        return report.model_copy(update={"configuration": configuration})

    def prepare(self, plan: GeneratedExperimentPlan, files: dict[str, bytes],
                data: dict[str, bytes] | None = None) -> GeneratedPreparation:
        plan = GeneratedExperimentPlan.model_validate(plan.model_dump(mode="json"))
        data = data or {}
        for manifest, bodies, label in ((plan.files, files, "code"), (plan.data, data, "data")):
            entries = {file.name: file for file in manifest}
            for name, body in bodies.items():
                entry = entries.get(name)
                if entry is None or digest(body) != entry.sha256 or len(body) != entry.size_bytes:
                    raise ValueError(label + "_manifest_digest_mismatch")
            if set(bodies) != set(entries):
                raise ValueError(label + "_manifest_count_mismatch")
        return GeneratedPreparation(plan=plan, files=dict(files), data=dict(data),
                                    static=static_checks(plan, files, data), isolation=self._isolation(plan))

    def admit(self, preparation: GeneratedPreparation) -> None:
        # Recheck current host settings and bytes: a prepared snapshot is not an
        # authorization to reuse a probe after backend or request mutation.
        current = self.prepare(preparation.plan, preparation.files, preparation.data)
        if current != preparation:
            raise SecurityRejection("prepared_configuration_changed")
        if not preparation.static.passed:
            raise SecurityRejection("static_security_failed")
        verify_isolation(preparation.isolation, self.probe_registry, preparation.plan)
        _require_immutable_image(preparation.plan)
        required = {"script", "cpu", "memory", "duration"}
        if missing := required - self.backend.capabilities:
            raise UnsupportedCapability(",".join(sorted(missing)))

    def execute(self, plan: GeneratedExperimentPlan, context: GeneratedContext,
                files: dict[str, bytes], archive_root: Path | str,
                data: dict[str, bytes] | None = None) -> GeneratedResult:
        preparation = self.prepare(plan, files, data)
        root = Path(archive_root).resolve() / context.run_id
        started_at = time.time()
        approval = self.criteria_registry.approval(preparation.plan.evaluation) if self.criteria_registry else None
        if approval is not None and (approval.approved_at > started_at or approval.approved_by == context.author):
            approval = None
        result = GeneratedResult(
            plan=preparation.plan, context=context, archive_path=str(root), provenance=self.backend.provenance,
            started_at=started_at, criteria_approval_json=approval.model_dump_json() if approval else None,
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
            for name, body in preparation.data.items():
                capture(f"inputs/{name}", body)
            result = result.model_copy(update={"cleanup_state": "unknown"})
            persist()
            session = self.backend.create(preparation.plan, context)
            result = result.model_copy(update={"sandbox_id": session.id})
            persist()
            capture("sandbox.json", json.dumps(session.info()).encode())
            for name, body in {**preparation.files, **preparation.data}.items():
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
                return cast(GeneratedResult, finalize_session(result, root, artifacts, session))
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
            except TimeoutError:
                raise  # Frozen export/restore uncertainty must remain unknown.
            except Exception as error:
                capture("download-output.json", json.dumps({"error_type": type(error).__name__}).encode())
                if state == "succeeded":
                    result = result.model_copy(update={"execution_state": "missing_artifact",
                        "reasons": (*result.reasons, "required_artifact_unreadable")})
            result = result.model_copy(update={"assessment": self.evaluate(result, context)})
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
        return cast(GeneratedResult, finalize_session(result, root, artifacts, session))

    def evaluate(self, result: GeneratedResult, context: GeneratedContext) -> GeneratedAssessment:
        plan = result.plan
        state = result.execution_state
        if state != "succeeded":
            return GeneratedAssessment(execution=execution_axis(state), hypothesis="not_evaluated",
                                       contribution="proposed", mode="diagnostic", trusted=False,
                                       evaluator_version=plan.evaluation.version,
                                       reasons=tuple(result.reasons))
        raw = (Path(result.archive_path) / f"outputs/{GENERATED_OUTPUT}").read_bytes()
        return evaluate(plan, raw, reviewer_independent=False).model_copy(update={"execution": "succeeded"})


def read_generated_result(archive_root: Path | str, run_id: str, *,
                          expected_plan: GeneratedExperimentPlan | None = None,
                          expected_context: GeneratedContext | None = None) -> GeneratedResult:
    """Verify durable binding, input/output digests, and recompute the assessment.

    The stored ``assessment`` is never trusted: it is recomputed from the raw
    output and is always diagnostic (host-owned finalization is separate). A
    forged ``accepted``/``final``/``trusted`` assessment in the archive is
    therefore discarded, and a mutable plan field change is rejected.
    """
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
    for file in (*result.plan.files, *result.plan.data):
        path = root / "inputs" / file.name
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("artifact_path_escape")
        # Pre-admission refusal has no input upload; keep it readable, not a
        # scientific result. Any captured input still has to match the manifest.
        if path.exists() and (digest(path.read_bytes()) != file.sha256 or path.stat().st_size != file.size_bytes):
            raise ValueError("input_digest_mismatch")
    if result.execution_state == "succeeded":
        names = {artifact.archive_path for artifact in result.artifacts}
        required = {f"inputs/{file.name}" for file in result.plan.files}
        required |= {f"inputs/{file.name}" for file in result.plan.data}
        required.add(f"outputs/{GENERATED_OUTPUT}")
        if not required <= names:
            raise ValueError("missing_durable_evidence")
        raw = (root / f"outputs/{GENERATED_OUTPUT}").read_bytes()
        assessment = evaluate(result.plan, raw, reviewer_independent=False)
        assessment = assessment.model_copy(update={"execution": "succeeded"})
    else:
        assessment = GeneratedAssessment(execution=execution_axis(result.execution_state),
                                         hypothesis="not_evaluated", contribution="proposed",
                                         mode="diagnostic", trusted=False)
    return result.model_copy(update={"assessment": assessment})
