"""Thin official SDK adapter, including explicit attached-session ownership."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
from pathlib import PurePosixPath
import shlex
from typing import Any, Literal, Protocol

from code_interpreter.sync import CodeInterpreterSync
from opensandbox.config import ConnectionConfigSync
from opensandbox.exceptions import InvalidArgumentException
from opensandbox.models import DirectoryListEntry, WriteEntry
from opensandbox.models.execd import Execution, RunCommandOpts
from opensandbox.models.sandboxes import PVC, Volume
from opensandbox.sync.sandbox import SandboxSync
from opensandbox.transport import RetryPolicy

from orchestration.experiments.models import ExperimentContext, ExperimentPlan
from orchestration.experiments.frozen_export import ExportUnknown, FrozenDockerExport, export_path

# Only the configured Docker freeze/archive adapter implements path stability.
# This implementation flag is NOT probe verification or a live authorization.
ATOMIC_EXPORT_SCOPE_SUPPORTED = True


class UnsupportedCapability(ValueError):
    """Requested backend feature is not enabled; never silently downgrade."""


def _command_text(argv: list[str]) -> str:
    # SDK 1.1.0 accepts argv, but pinned execd v1.1.0 requires shell command text.
    # Keep the SDK's input constraints and quote each literal for its Linux shell.
    if not argv or not argv[0] or any(not isinstance(arg, str) or "\0" in arg for arg in argv):
        raise InvalidArgumentException("argv requires a non-empty executable and strings without NUL")
    return shlex.join(argv)


class ExperimentSession(Protocol):
    id: str
    owned: bool
    kernel_id: str | None

    def info(self) -> dict[str, Any]: ...
    def renew(self, seconds: int) -> dict[str, Any]: ...
    def upload(self, path: str, data: bytes) -> None: ...
    def download(self, path: str, limit: int) -> bytes: ...
    def run(self, argv: list[str], seconds: int, directory: str) -> Execution: ...
    def run_code(self, code: str) -> Execution: ...
    def cancel(self, command_id: str) -> None: ...
    def destroy(self) -> None: ...
    def close(self) -> None: ...


class ExperimentBackend(Protocol):
    provenance: Literal["live", "replay", "mock"]
    capabilities: frozenset[str]

    def create(self, plan: ExperimentPlan, context: ExperimentContext) -> ExperimentSession: ...


class OpenSandboxSession:
    def __init__(self, sandbox: SandboxSync, *, owned: bool,
                 export_control: FrozenDockerExport | None = None) -> None:
        self.sandbox = sandbox
        self.id = sandbox.id
        self.owned = owned
        self.kernel_id: str | None = None
        self.interpreter: CodeInterpreterSync | None = None
        self.command_ids: set[str] = set()
        self.export_control = export_control
        self._export_unknown = False

    def _check_export_binding(self) -> None:
        if self._export_unknown:
            raise ExportUnknown("previous_export_effect_unknown")
        if self.export_control is not None:
            if not self.owned:
                raise PermissionError("attached_session_read_only")
            if self.export_control.sandbox_id is None:
                self.export_control.bind(self.id)
            self.export_control.inspect_bound(paused=False)

    def _frozen_download(self, path: str, limit: int) -> bytes:
        export_path(path, limit)  # Reject invalid paths before any lifecycle action.
        self._check_export_binding()
        control = self.export_control
        assert control is not None
        try:
            try:
                self.sandbox.pause()  # Original official lifecycle, exactly once.
            except Exception as error:
                raise ExportUnknown("sandbox_pause_effect_unknown") from error
            control.inspect_bound(paused=True)
            return control.download(path, limit)
        except ExportUnknown:
            self._export_unknown = True
            raise
        finally:
            # Reconcile a possibly partially applied pause by read-only inspect.
            # Never blindly repeat pause/resume after an unknown response.
            try:
                if control.inspect_bound():
                    previous = self.sandbox
                    config = previous.connection_config.model_copy(update={"transport": None,
                        "request_timeout": timedelta(seconds=10)})
                    resumed = SandboxSync.resume(self.id, connection_config=config,
                                                 resume_timeout=timedelta(seconds=10))
                    if resumed.id != self.id:
                        resumed.close()
                        raise ExportUnknown("sandbox_resume_identity_changed")
                    self.sandbox = resumed
                    previous.close()
                    control.inspect_bound(paused=False)
            except Exception as error:
                self._export_unknown = True
                raise ExportUnknown("sandbox_resume_or_pause_state_unknown") from error

    def info(self) -> dict[str, Any]:
        return self.sandbox.get_info().model_dump(mode="json")

    def renew(self, seconds: int) -> dict[str, Any]:
        if not self.owned:
            raise PermissionError("attached_session_read_only")
        if not 1 <= seconds <= 900:
            raise ValueError("bounded_renewal_required")
        return self.sandbox.renew(timedelta(seconds=seconds)).model_dump(mode="json")

    def upload(self, path: str, data: bytes) -> None:
        if not self.owned:
            raise PermissionError("attached_session_read_only")
        self._check_export_binding()
        # execd interprets decimal digit strings as octal: mode=700, not 0o700.
        self.sandbox.files.create_directories([WriteEntry(path=str(PurePosixPath(path).parent), mode=700)])
        self.sandbox.files.write_file(path, data, mode=600)

    def download(self, path: str, limit: int) -> bytes:
        if self.export_control is not None:
            return self._frozen_download(path, limit)
        # Executor outputs have one fixed sandbox root. The raw SDK filesystem
        # accepts arbitrary absolute paths; do not expose that as an export API.
        root = PurePosixPath("/tmp/morph-research")
        candidate = PurePosixPath(path)
        if (not path.startswith(str(root) + "/") or "\\" in path or "\0" in path
                or any(part in {"", ".", ".."} for part in path.split("/")[1:])
                or not candidate.is_relative_to(root)):
            raise PermissionError("artifact_path_escape")
        if type(limit) is not int or not 1 <= limit <= 16777216:
            raise ValueError("artifact_size_limit")
        # Official directory listing reports link types without traversing them.
        # Inspect every ancestor, including the export root. Unsupported/missing
        # type metadata is not permission to fall back to an unchecked download.
        parent = PurePosixPath("/")
        for component in candidate.parts[1:]:
            child = parent / component
            entries = self.sandbox.files.list_directory(DirectoryListEntry(path=str(parent), depth=1))
            matches = [entry for entry in entries if entry.path == str(child)]
            if len(matches) != 1 or matches[0].entry_type is None:
                raise UnsupportedCapability("bounded_export_metadata_unsupported")
            entry = matches[0]
            if entry.entry_type not in {"file", "directory", "symlink"}:
                raise UnsupportedCapability("bounded_export_metadata_unsupported")
            expected = "file" if child == candidate else "directory"
            if entry.entry_type != expected:
                raise PermissionError("artifact_path_escape")
            if child == candidate and entry.size > limit:
                raise ValueError("artifact_size_limit")
            parent = child
        # Execd offset/limit count lines. Range bounds bytes, with one extra byte
        # to detect overflow independently even if the server ignores Range.
        chunks: Iterator[bytes] = self.sandbox.files.read_bytes_stream(path, range_header=f"bytes=0-{limit}")
        data = bytearray()
        for chunk in chunks:
            data.extend(chunk)
            if len(data) > limit:
                raise ValueError("artifact_size_limit")
        return bytes(data)

    def run(self, argv: list[str], seconds: int, directory: str) -> Execution:
        if not self.owned:
            raise PermissionError("attached_session_read_only")
        self._check_export_binding()
        execution = self.sandbox.commands.run(_command_text(argv), opts=RunCommandOpts(
            timeout=timedelta(seconds=seconds), working_directory=directory))
        if execution.id:
            self.command_ids.add(execution.id)
        return execution

    def start(self, argv: list[str], seconds: int, directory: str) -> Execution:
        """Delegate background execution and cancellation to official command APIs."""
        if not self.owned:
            raise PermissionError("attached_session_read_only")
        self._check_export_binding()
        execution = self.sandbox.commands.run(_command_text(argv), opts=RunCommandOpts(background=True,
            timeout=timedelta(seconds=seconds), working_directory=directory))
        if execution.id:
            self.command_ids.add(execution.id)
        return execution

    def command_status(self, command_id: str) -> dict[str, Any]:
        return self.sandbox.commands.get_command_status(command_id).model_dump(mode="json")

    def command_logs(self, command_id: str) -> dict[str, Any]:
        return self.sandbox.commands.get_background_command_logs(command_id).model_dump(mode="json")

    def run_code(self, code: str) -> Execution:
        if not self.owned:
            raise PermissionError("attached_session_read_only")
        self._check_export_binding()
        # Always an explicit fresh context, never the SDK's default shared kernel.
        self.interpreter = CodeInterpreterSync.create(sandbox=self.sandbox)
        context = self.interpreter.codes.create_context("python")
        if not context.id:
            raise RuntimeError("fresh_kernel_identity_missing")
        self.kernel_id = context.id
        execution = self.interpreter.codes.run(code, context=context)
        if execution.id:
            self.command_ids.add(execution.id)
        return execution

    def cancel(self, command_id: str) -> None:
        if not self.owned or command_id not in self.command_ids:
            raise PermissionError("command_ownership_required")
        if self.interpreter:
            self.interpreter.codes.interrupt(command_id)
        else:
            self.sandbox.commands.interrupt(command_id)

    def destroy(self) -> None:
        if not self.owned:
            raise PermissionError("attached_sandbox_must_not_be_killed")
        if self.sandbox.id != self.id:
            raise PermissionError("owned_sandbox_identity_changed")
        self.sandbox.kill()

    def close(self) -> None:
        # The pinned 1.1.0 interpreter has no public close(); its HTTP adapters
        # share the sandbox connection transport closed by SandboxSync.close().
        try:
            self.sandbox.close()
        finally:
            if self.export_control is not None:
                self.export_control.close()


class OpenSandboxBackend:
    provenance: Literal["live", "replay", "mock"] = "live"

    def __init__(self, *, domain: str = "127.0.0.1:8097", api_key: str | None = None,
                 protocol: Literal["http", "https"] = "http", use_server_proxy: bool = True,
                 codeinterpreter: bool = False, notebook: bool = False, volumes: bool = False) -> None:
        self.domain = domain
        self.api_key = api_key
        self.protocol = protocol
        self.use_server_proxy = use_server_proxy
        self.capabilities = frozenset({"script", "cpu", "memory", "duration"} |
            ({"codeinterpreter"} if codeinterpreter else set()) |
            ({"notebook"} if notebook else set()) | ({"volumes"} if volumes else set()))

    def connection(self, request_seconds: int = 45) -> ConnectionConfigSync:
        return ConnectionConfigSync(domain=self.domain, api_key=self.api_key, protocol=self.protocol,
            request_timeout=timedelta(seconds=request_seconds), use_server_proxy=self.use_server_proxy,
            retry_policy=RetryPolicy.disabled(), disable_metrics=True)

    def create(self, plan: ExperimentPlan, context: ExperimentContext) -> OpenSandboxSession:
        required = {plan.mode, "cpu", "memory", "duration"}
        if plan.persistent_volume:
            required.add("volumes")
        if missing := required - self.capabilities:
            raise UnsupportedCapability(",".join(sorted(missing)))
        volumes = ([Volume(name="research", pvc=PVC(claimName=plan.persistent_volume),
                           mountPath="/mnt/research")] if plan.persistent_volume else None)
        sandbox = SandboxSync.create(plan.environment.image,
            connection_config=self.connection(plan.resources.command_seconds + 15),
            resource={"cpu": str(plan.resources.cpu), "memory": f"{plan.resources.memory_mib}Mi"},
            timeout=timedelta(seconds=plan.resources.lifetime_seconds), ready_timeout=timedelta(seconds=45),
            entrypoint=(["/opt/code-interpreter/code-interpreter.sh"]
                        if plan.mode == "codeinterpreter" else ["tail", "-f", "/dev/null"]),
            env={"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"},
            metadata={"morph-run": context.run_id, "morph-task": context.task_id,
                      "morph-worker": context.worker_id, "morph-fence": str(context.fencing_token)},
            volumes=volumes)
        return OpenSandboxSession(sandbox, owned=True)

    def connect(self, sandbox_id: str) -> OpenSandboxSession:
        # Attaching borrows the HTTP handle; it does not confer lifecycle ownership.
        return OpenSandboxSession(SandboxSync.connect(sandbox_id,
            connection_config=self.connection()), owned=False)
