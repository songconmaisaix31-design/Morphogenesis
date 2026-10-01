"""Bounded one-shot execution. Plain archives survive sandbox destruction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import httpx
from opensandbox.models.execd import Execution

from orchestration.experiments.backend import ExperimentBackend, ExperimentSession, UnsupportedCapability
from orchestration.experiments.models import (
    ExperimentArtifact, ExperimentContext, ExperimentPlan, ExperimentResult, ScientificAssessment,
)
from orchestration.experiments.case import get_case
from orchestration.experiments.scientific import assess


DIRECTORY = "/tmp/morph-research"
RUNTIME_PROBE = "import json,platform;from pathlib import Path;Path('runtime.json').write_text(json.dumps({'python':platform.python_version(),'platform':platform.platform()}))"
NOTEBOOK_RUNNER = '''import json,sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient
nb = nbformat.read(sys.argv[1], as_version=4)
nb.cells.insert(0, nbformat.v4.new_code_cell("import sys;sys.argv=" + repr([sys.argv[1],sys.argv[3],sys.argv[4]])))
client = NotebookClient(nb, timeout=int(sys.argv[2]), kernel_name="python3", allow_errors=False)
try:
    with client.setup_kernel():
        Path("kernel.json").write_text(json.dumps({"kernel_id": client.km.kernel_id}))
        client.execute(cleanup_kc=False)
finally:
    nbformat.write(nb, "executed.ipynb")
'''


def digest(data: bytes) -> str:
    # Standard library integrity check only; no custom content identity system.
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, data: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _artifact(root: Path, name: str, data: bytes) -> ExperimentArtifact:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return ExperimentArtifact(name=name, archive_path=name, sha256=digest(data), size_bytes=len(data))


def _execution_state(execution: Execution, *, codeinterpreter: bool = False) -> str:
    if execution.error:
        if execution.error.name in {"TimeoutError", "CommandTimeout", "DeadlineExceeded"}:
            return "timeout"
        return "failed"
    if execution.exit_code is not None:
        return "succeeded" if execution.exit_code == 0 else "failed"
    # Jupyter completion carries no process exit code. It is not synthesized.
    if codeinterpreter and execution.complete is not None:
        return "succeeded"
    return "unknown"


class ExperimentExecutor:
    def __init__(self, backend: ExperimentBackend) -> None:
        self.backend = backend

    def execute(self, plan: ExperimentPlan, context: ExperimentContext,
                archive_root: Path | str) -> ExperimentResult:
        plan = ExperimentPlan.model_validate(plan.model_dump(mode="json"))
        definition = get_case(plan.criteria.version)
        root = Path(archive_root).resolve() / context.run_id
        # Reusing a run after unknown effects is forbidden; no automatic replay.
        root.mkdir(parents=True, exist_ok=False)
        result = ExperimentResult(plan=plan, context=context, archive_path=str(root),
                                  provenance=self.backend.provenance,
                                  scientific=ScientificAssessment(criteria_version=plan.criteria.version))
        _write_json(root / "plan.json", plan.model_dump(mode="json"))
        _write_json(root / "result.json", result.model_dump(mode="json"))
        session: ExperimentSession | None = None
        artifacts: list[ExperimentArtifact] = []

        def persist() -> None:
            nonlocal result
            result = result.model_copy(update={"artifacts": tuple(artifacts)})
            _write_json(root / "result.json", result.model_dump(mode="json"))

        def capture(name: str, data: bytes) -> None:
            artifacts.append(_artifact(root, name, data))
            persist()

        try:
            inputs: dict[str, bytes] = {}
            for label, item in (("code", plan.code), ("data", plan.data)):
                path = Path(item.local_path)
                if path.is_symlink() or not path.is_file() or path.stat().st_size > plan.resources.artifact_bytes:
                    raise ValueError("input_missing_link_or_size_limit")
                raw = path.read_bytes()
                if digest(raw) != item.sha256:
                    raise ValueError("input_digest_mismatch")
                inputs[label] = raw
                capture(f"inputs/{item.name}", raw)
            definition.validate_inputs(plan, inputs["code"], inputs["data"])
            required = {plan.mode, "cpu", "memory", "duration"}
            if plan.persistent_volume:
                required.add("volumes")
            if missing := required - self.backend.capabilities:
                raise UnsupportedCapability(",".join(sorted(missing)))
            # Durable unknown state precedes the only create call.
            result = result.model_copy(update={"cleanup_state": "unknown"})
            persist()
            session = self.backend.create(plan, context)
            if not session.owned:
                raise PermissionError("fresh_owned_sandbox_required")
            result = result.model_copy(update={"sandbox_id": session.id})
            persist()
            capture("sandbox.json", json.dumps(session.info()).encode())
            for label, item in (("code", plan.code), ("data", plan.data)):
                session.upload(f"{DIRECTORY}/{item.name}", inputs[label])
            probe = session.run(["python3", "-c", RUNTIME_PROBE], 10, DIRECTORY)
            capture("runtime-command.json", probe.model_dump_json().encode())
            if _execution_state(probe) != "succeeded":
                result = result.model_copy(update={"execution_state": _execution_state(probe),
                    "exit_code": probe.exit_code, "command_id": probe.id, "reasons": ("runtime_probe_failed",)})
                return self._finish(result, root, artifacts, session)
            runtime = session.download(f"{DIRECTORY}/runtime.json", plan.resources.artifact_bytes)
            capture("runtime.json", runtime)
            version = json.loads(runtime).get("python")
            if not isinstance(version, str) or not version.startswith(plan.environment.python_version + "."):
                raise UnsupportedCapability("python_environment_mismatch")
            if plan.mode == "script":
                argv = ["python3", plan.code.name, plan.data.name, plan.parameters[0]]
                execution = session.run(argv, plan.resources.command_seconds, DIRECTORY)
            elif plan.mode == "notebook":
                session.upload(f"{DIRECTORY}/notebook_runner.py", NOTEBOOK_RUNNER.encode())
                execution = session.run(["python3", "notebook_runner.py", plan.code.name,
                    str(plan.resources.command_seconds), plan.data.name, plan.parameters[0]],
                    plan.resources.command_seconds, DIRECTORY)
            else:
                # No default kernel/session and no shell-based validator.
                code = (f"import os,sys,runpy\nos.chdir({DIRECTORY!r})\n"
                        f"sys.argv={[plan.code.name, plan.data.name, plan.parameters[0]]!r}\n"
                        f"runpy.run_path({plan.code.name!r},run_name='__main__')")
                execution = session.run_code(code)
            capture("execution.json", execution.model_dump_json().encode())
            state = _execution_state(execution, codeinterpreter=plan.mode == "codeinterpreter")
            result = result.model_copy(update={"execution_state": state, "exit_code": execution.exit_code,
                "command_id": execution.id, "kernel_id": session.kernel_id,
                "remote_effect": "known" if state in {"succeeded", "failed", "timeout"} else "unknown"})
            persist()
            # Raw outputs may be useful even when execution failed. Their presence
            # cannot turn an execution failure into scientific acceptance.
            for name in (["metrics.json", "executed.ipynb", "kernel.json"]
                         if plan.mode == "notebook" else ["metrics.json"]):
                try:
                    capture(f"outputs/{name}", session.download(f"{DIRECTORY}/{name}", plan.resources.artifact_bytes))
                except Exception as error:
                    capture(f"download-{name}.json", json.dumps({"error_type": type(error).__name__}).encode())
                    if state == "succeeded":
                        result = result.model_copy(update={"execution_state": "missing_artifact",
                            "reasons": (*result.reasons, "required_artifact_unreadable")})
            if plan.mode == "notebook" and (root / "outputs/kernel.json").is_file():
                result = result.model_copy(update={"kernel_id": json.loads((root / "outputs/kernel.json").read_bytes()).get("kernel_id")})
            if plan.mode != "script" and not result.kernel_id and result.execution_state == "succeeded":
                result = result.model_copy(update={"execution_state": "missing_artifact",
                    "reasons": (*result.reasons, "fresh_kernel_identity_missing")})
            if result.execution_state == "succeeded":
                result = result.model_copy(update={"scientific": assess(plan, inputs["data"],
                    (root / "outputs/metrics.json").read_bytes())})
        except UnsupportedCapability as error:
            result = result.model_copy(update={"execution_state": "unsupported", "reasons": (str(error),)})
        except (httpx.TimeoutException, TimeoutError):
            result = result.model_copy(update={"execution_state": "unknown", "remote_effect": "unknown",
                "reasons": ("transport_timeout_execution_unknown",)})
        except Exception as error:
            # Never persist exception text which could contain URLs/credentials.
            result = result.model_copy(update={"execution_state": "unknown" if session else "failed",
                "reasons": (type(error).__name__,)})
            if session is None and result.cleanup_state == "unknown":
                result = result.model_copy(update={"execution_state": "unknown"})
        return self._finish(result, root, artifacts, session)

    @staticmethod
    def _finish(result: ExperimentResult, root: Path, artifacts: list[ExperimentArtifact],
                session: ExperimentSession | None) -> ExperimentResult:
        if session:
            try:
                if session.owned:
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


def read_result(archive_root: Path | str, run_id: str, *, expected_plan: ExperimentPlan | None = None,
                expected_context: ExperimentContext | None = None) -> ExperimentResult:
    """Verify durable binding, standard file digests, and recompute scientific verdict.

    The root is host-controlled; this function is not an attestation for untrusted
    archives. B must provide its registered plan/context and enforce lease fencing.
    """
    if not run_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in run_id):
        raise ValueError("invalid_run_id")
    root = Path(archive_root).resolve() / run_id
    if root.is_symlink():
        raise ValueError("archive_link_rejected")
    result = ExperimentResult.model_validate_json((root / "result.json").read_bytes())
    if (result.context.run_id != run_id or Path(result.archive_path).resolve() != root or
            ExperimentPlan.model_validate_json((root / "plan.json").read_bytes()) != result.plan):
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
    definition = get_case(result.plan.criteria.version)
    scientific = ScientificAssessment(criteria_version=result.plan.criteria.version)
    if result.execution_state == "succeeded":
        names = {artifact.archive_path for artifact in result.artifacts}
        required = {f"inputs/{result.plan.code.name}", f"inputs/{result.plan.data.name}",
                    "sandbox.json", "execution.json", "runtime.json", "outputs/metrics.json"}
        if result.plan.mode == "notebook":
            required |= {"outputs/kernel.json", "outputs/executed.ipynb"}
        if not required <= names:
            raise ValueError("missing_durable_evidence")
        sandbox_info = json.loads((root / "sandbox.json").read_bytes())
        metadata = sandbox_info.get("metadata", {})
        expected_metadata = {"morph-run": result.context.run_id, "morph-task": result.context.task_id,
                             "morph-worker": result.context.worker_id, "morph-fence": str(result.context.fencing_token)}
        if (not result.sandbox_id or sandbox_info.get("id") != result.sandbox_id or
                any(metadata.get(key) != value for key, value in expected_metadata.items())):
            raise ValueError("sandbox_identity_binding_mismatch")
        if result.plan.mode != "script" and not result.kernel_id:
            raise ValueError("fresh_kernel_identity_missing")
        for input_item in (result.plan.code, result.plan.data):
            if digest((root / "inputs" / input_item.name).read_bytes()) != input_item.sha256:
                raise ValueError("input_digest_mismatch")
        definition.validate_inputs(result.plan, (root / "inputs" / result.plan.code.name).read_bytes(),
                                   (root / "inputs" / result.plan.data.name).read_bytes())
        execution = Execution.model_validate_json((root / "execution.json").read_bytes())
        if _execution_state(execution, codeinterpreter=result.plan.mode == "codeinterpreter") != "succeeded":
            raise ValueError("execution_evidence_mismatch")
        if result.exit_code != execution.exit_code or result.command_id != execution.id:
            raise ValueError("command_binding_mismatch")
        version = json.loads((root / "runtime.json").read_bytes()).get("python", "")
        if not isinstance(version, str) or not version.startswith(result.plan.environment.python_version + "."):
            raise ValueError("runtime_environment_mismatch")
        scientific = assess(result.plan, (root / "inputs" / result.plan.data.name).read_bytes(),
                            (root / "outputs/metrics.json").read_bytes())
    return result.model_copy(update={"scientific": scientific})
