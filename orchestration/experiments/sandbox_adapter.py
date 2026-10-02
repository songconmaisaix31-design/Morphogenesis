"""Local CPU isolation adapter for generated candidates.

This is the R1 "local CPU usable isolation path": a thin configuration and
check in front of the existing OpenSandbox backend. It does not build a second
scheduler. The adapter *declares* the isolation properties the local Linux
OpenSandbox service is expected to enforce, but until a real harmless probe has
verified them (AT-07, this round NOT_RUN), ``IsolationReport.admitted`` is False
and generated candidates fail closed instead of running on the host.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Literal, Protocol

from opensandbox.models.sandboxes import PVC, Volume
from opensandbox.sync.sandbox import SandboxSync

from orchestration.experiments.backend import OpenSandboxBackend, OpenSandboxSession, UnsupportedCapability
from orchestration.experiments.generated import (
    BackendProfile, GeneratedContext, GeneratedExperimentPlan, IsolationCapability, IsolationReport,
)

_DENY_ENV = {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


class GeneratedBackend(Protocol):
    provenance: Literal["live", "replay", "mock"]
    capabilities: frozenset[str]

    def isolation(self) -> IsolationReport: ...
    def create(self, plan: GeneratedExperimentPlan, context: GeneratedContext) -> OpenSandboxSession: ...


def declared_capability(*, network_deny: bool) -> IsolationCapability:
    """The capability set a Linux OpenSandbox sandbox is configured to enforce."""
    return IsolationCapability(
        no_host_write=True, no_credentials=True, no_host_control=True, no_privilege=True,
        export_bounded=True, network_deny=network_deny, cpu_limit=True, memory_limit=True,
        process_limit=True, time_limit=True, self_owned_cleanup=True,
    )


class LocalCpuSandboxBackend:
    """Reuses the OpenSandbox SDK lifecycle; isolation stays unverified until a real probe."""

    def __init__(self, *, domain: str = "127.0.0.1:8097", api_key: str | None = None,
                 protocol: Literal["http", "https"] = "http", network_deny: bool = True) -> None:
        self._opensandbox = OpenSandboxBackend(domain=domain, api_key=api_key, protocol=protocol)
        self._network_deny = network_deny
        self.provenance: Literal["live"] = "live"
        self.capabilities = self._opensandbox.capabilities

    def isolation(self) -> IsolationReport:
        return IsolationReport(
            backend="opensandbox", declared=declared_capability(network_deny=self._network_deny),
            verified=False, probe="not_run", reasons=("isolation_probe_not_run",),
        )

    def create(self, plan: GeneratedExperimentPlan, context: GeneratedContext) -> OpenSandboxSession:
        required = {"script", "cpu", "memory", "duration"}
        if missing := required - self.capabilities:
            raise UnsupportedCapability(",".join(sorted(missing)))
        profile: BackendProfile = plan.backend
        sandbox = SandboxSync.create(plan.environment.image,
            connection_config=self._opensandbox.connection(profile.command_seconds + 15),
            resource={"cpu": str(profile.cpu), "memory": f"{profile.memory_mib}Mi"},
            timeout=timedelta(seconds=profile.lifetime_seconds), ready_timeout=timedelta(seconds=45),
            entrypoint=["tail", "-f", "/dev/null"], env=_DENY_ENV,
            metadata={"morph-run": context.run_id, "morph-task": context.task_id,
                      "morph-worker": context.worker_id, "morph-fence": str(context.fencing_token)})
        return OpenSandboxSession(sandbox, owned=True)
